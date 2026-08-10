#!/usr/bin/env python3
"""
taos.maps — Coupling map generation workflow.

Creates atmosphere↔ocean, atmosphere↔land, land↔river, and SPA
interpolation maps using TempestRemap (via ncremap).

Grid names and files for ocean, land, and river components are read
from the project.yaml grid section:
  grid.ocn_name / grid.ocn_file
  grid.lnd_name / grid.lnd_file
  grid.rof_name / grid.rof_file   (optional — river maps are skipped when unset)
  grid.spa_name / grid.spa_file   (optional, defaults to ne30pg2)
  grid.ocn_flip_a2o_direction     (optional, default false — see below)
  grid.lnd_flip_a2o_direction     (optional, default false — see below)
  grid.rof_flip_a2o_direction     (optional, default false — see below)

Ocean and land maps pair their component grid with the atmosphere grid.
River maps instead pair the river grid with the *land* grid, matching how
the components are actually coupled, and are generated only when
grid.rof_file is set — there is no separate enable switch. That makes the
river grid a per-grid setting in the grids: list: give it to the one grid
whose land grid it pairs with, and the other grids skip river maps and
reuse the resulting files.

The --a2o switch controls the order in which ncremap hands the two grids
to TempestRemap's GenerateOverlapMesh, which is picky about that order and
fails outright when it is wrong. Each component generates two maps and
exactly one of them carries --a2o:

  grid.<comp>_flip_a2o_direction: false   --a2o on the reference→component map
  grid.<comp>_flip_a2o_direction: true    --a2o on the component→reference map

where the reference grid is the atmosphere grid for ocn and lnd, and the
land grid for rof.

The switch is never simply "off" — putting it on exactly one direction is
what keeps the grid pair in a consistent order. --a2o swaps the two grids,
and the two map directions have already swapped source and destination
relative to each other, so flagging one direction hands
GenerateOverlapMesh the same grid first both times.

The default suits a component grid finer than its reference grid, which is
the common case (e.g. an r05 land grid under ne30pg2). Set the flip true
for a component whose grid is coarser than its reference grid — an RRM
atmosphere over a lower-resolution land grid, or an r0125 river grid under
a high-resolution land grid — which otherwise fails with a
GenerateOverlapMesh error.

Usage
-----
    python -m taos.maps path/to/project.yaml --create-maps-ocn --create-maps-lnd
    python -m taos.maps path/to/project.yaml --create-maps-rof
"""
import os
import re

from taos.config import taos_config
from taos.util import clr, ensure_dir, print_line, run_cmd, timer

# -------------------------------------------------------------------
# default remap algorithms (overridable via maps.algorithms in project.yaml
# or the --algorithms command-line argument)
_DEFAULT_ALGORITHMS = ['traave', 'trbilin', 'trfv2', 'trintbilin']

# -------------------------------------------------------------------
# per-component default algorithms, for components that do not need the
# full set — land↔river coupling only exchanges conservative fluxes
_DEFAULT_ALGORITHMS_BY_COMPONENT = {'rof': ['traave']}

# -------------------------------------------------------------------
# internal helpers


def _resolve_algorithms(cfg, override=None, component=None):
    """Return the list of remap algorithms to use for <component>.

    Precedence: explicit override (e.g. CLI arg) > maps.algorithms in
    project.yaml > the built-in default for this component > the built-in
    default list.  Accepts either a YAML list or a comma-separated string.

    maps.algorithms may also be a mapping keyed by component, so a project
    can shorten the list for one component without repeating it for the
    others.  Any component not named falls back to a 'default' key if
    present, then to the built-in defaults:

        maps:
          algorithms:
            default: [traave, trbilin, trfv2, trintbilin]
            rof: [traave]
    """
    value = override if override is not None else cfg.get('maps.algorithms')
    if isinstance(value, dict):
        value = value.get(component, value.get('default'))
    if value is None:
        return list(_DEFAULT_ALGORITHMS_BY_COMPONENT.get(component,
                                                         _DEFAULT_ALGORITHMS))
    if isinstance(value, str):
        value = [v.strip() for v in value.split(',') if v.strip()]
    return list(value)


def _unified_env_prefix(cfg):
    """Return a bash one-liner that sources the E3SM unified environment."""
    return f'source {cfg["paths.unified_src"]}'


def _resolve_flip_a2o(cfg, component):
    """Return the a2o-direction setting for <component> ('ocn', 'lnd', 'rof').

    False (the default) puts --a2o on the reference→component map, which is
    what a component grid finer than its reference grid needs.  True puts it
    on the component→reference map instead, for a coarser component grid.
    The reference grid is the atmosphere grid for ocn and lnd, and the land
    grid for rof.
    """
    value = cfg.get(f'grid.{component}_flip_a2o_direction', False)
    if isinstance(value, str):
        return value.strip().lower() in ('true', 'yes', 'on', '1')
    return bool(value)


def _check_map(path):
    if not os.path.exists(path):
        raise RuntimeError(f'Failed to create map file: {path}')


def _ncremap_pair(env_prefix, alg, src_file, dst_file, map_file, a2o=False):
    """Build and run a single ncremap command, then check the output."""
    a2o_flag = ' --a2o' if a2o else ''
    cmd = (f'{env_prefix} &&'
           f' ncremap{a2o_flag} --alg_typ={alg}'
           f' --grd_src="{src_file}" --grd_dst="{dst_file}"'
           f' --map_fl="{map_file}"')
    # Label: map filename without the trailing timestamp (.YYYYMMDD.nc)
    label = 'ncremap: ' + re.sub(r'\.\d{8}\.nc$', '', os.path.basename(map_file))
    with timer.time(label):
        run_cmd(cmd)
    _check_map(map_file)


# -------------------------------------------------------------------
# public API


def create_maps_ocn(cfg, algorithms=None):
    """
    Create atmosphere↔ocean coupling maps with TempestRemap.

    Generates two map files (both directions) per algorithm.

    Parameters
    ----------
    cfg : taos_config
    algorithms : list of str, optional
        Remap algorithms to use.  Defaults to maps.algorithms from
        project.yaml, or the built-in list if unset.

    Notes
    -----
    --a2o goes on the atm→ocn map; set grid.ocn_flip_a2o_direction true to
    move it to the ocn→atm map, which is what GenerateOverlapMesh needs
    when the ocean grid is coarser than the atmosphere grid.
    """
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    ocn_grid_name = cfg['grid.ocn_name']
    ocn_grid_file = cfg['grid.ocn_file']
    maps_root     = cfg['derived.maps_root']
    ensure_dir(maps_root)
    timestamp     = cfg['project.timestamp']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    env_prefix    = _unified_env_prefix(cfg)
    flip_a2o      = _resolve_flip_a2o(cfg, 'ocn')

    with timer.time('create_maps_ocn'):
        print_line()
        print(f'\n  {clr.GREEN}Creating ocean map files with TempestRemap{clr.END}')
        print(f'  {clr.GREEN}--a2o goes on the'
              f' {"ocn->atm" if flip_a2o else "atm->ocn"} maps'
              f' (grid.ocn_flip_a2o_direction = {flip_a2o}){clr.END}')

        algorithms = _resolve_algorithms(cfg, algorithms, 'ocn')
        for alg in algorithms:
            map_file = f'{maps_root}/map_{ocn_grid_name}_to_{atm_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, ocn_grid_file, atm_grid_file, map_file, a2o=flip_a2o)
            map_file = f'{maps_root}/map_{atm_grid_name}_to_{ocn_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, atm_grid_file, ocn_grid_file, map_file, a2o=not flip_a2o)

        print(f'\n  {clr.GREEN}Ocean map file creation SUCCESSFUL{clr.END}')


def create_maps_lnd(cfg, algorithms=None):
    """
    Create atmosphere↔land coupling maps with TempestRemap.

    Generates two map files (both directions) per algorithm.

    Parameters
    ----------
    cfg : taos_config
    algorithms : list of str, optional
        Remap algorithms to use.  Defaults to maps.algorithms from
        project.yaml, or the built-in list if unset.

    Notes
    -----
    --a2o goes on the atm→lnd map; set grid.lnd_flip_a2o_direction true to
    move it to the lnd→atm map, which is what GenerateOverlapMesh needs
    when the land grid is coarser than the atmosphere grid (e.g. a pg2 land
    grid paired with a more highly refined RRM atmosphere grid).
    """
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    lnd_grid_name = cfg['grid.lnd_name']
    lnd_grid_file = cfg['grid.lnd_file']
    maps_root     = cfg['derived.maps_root']
    ensure_dir(maps_root)
    timestamp     = cfg['project.timestamp']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    env_prefix    = _unified_env_prefix(cfg)
    flip_a2o      = _resolve_flip_a2o(cfg, 'lnd')

    with timer.time('create_maps_lnd'):
        print_line()
        print(f'\n  {clr.GREEN}Creating land map files with TempestRemap{clr.END}')
        print(f'  {clr.GREEN}--a2o goes on the'
              f' {"lnd->atm" if flip_a2o else "atm->lnd"} maps'
              f' (grid.lnd_flip_a2o_direction = {flip_a2o}){clr.END}')

        algorithms = _resolve_algorithms(cfg, algorithms, 'lnd')
        for alg in algorithms:
            map_file = f'{maps_root}/map_{lnd_grid_name}_to_{atm_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, lnd_grid_file, atm_grid_file, map_file, a2o=flip_a2o)
            map_file = f'{maps_root}/map_{atm_grid_name}_to_{lnd_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, atm_grid_file, lnd_grid_file, map_file, a2o=not flip_a2o)

        print(f'\n  {clr.GREEN}Land map file creation SUCCESSFUL{clr.END}')


def create_maps_rof(cfg, algorithms=None):
    """
    Create land↔river coupling maps with TempestRemap.

    Generates two map files (both directions) per algorithm.  Unlike the
    ocean and land maps, these pair the river grid with the land grid
    rather than the atmosphere grid, matching how the components couple.

    Does nothing unless grid.rof_file is set, so the river grid can be
    given to just the one grid entry whose land grid it pairs with; the
    other grids skip river maps and reuse the files it produces.

    Parameters
    ----------
    cfg : taos_config
    algorithms : list of str, optional
        Remap algorithms to use.  Defaults to maps.algorithms from
        project.yaml, or the built-in list if unset.  The land↔river
        coupling only needs the conservative map in practice, so this is
        typically run with just traave.

    Notes
    -----
    --a2o goes on the lnd→rof map; set grid.rof_flip_a2o_direction true to
    move it to the rof→lnd map, which is what GenerateOverlapMesh needs
    when the river grid is coarser than the land grid (e.g. an r0125 river
    grid under a high-resolution RRM land grid).
    """
    rof_grid_name = cfg.get('grid.rof_name')
    rof_grid_file = cfg.get('grid.rof_file')
    lnd_grid_name = cfg.get('grid.lnd_name')
    lnd_grid_file = cfg.get('grid.lnd_file')

    # -------------------------------------------------------------------
    # no river grid configured - nothing to do for this grid
    if not rof_grid_file:
        print_line()
        print(f'\n  {clr.GREEN}No river grid set (grid.rof_file)'
              f' - skipping river maps{clr.END}')
        return

    if not rof_grid_name:
        raise RuntimeError('grid.rof_file is set but grid.rof_name is not - '
                           'both are needed to name the river map files.')
    if not lnd_grid_file or not lnd_grid_name:
        raise RuntimeError('grid.rof_file is set but the land grid is not - '
                           'river maps are generated against the land grid, '
                           'so grid.lnd_name and grid.lnd_file are required.')

    maps_root = cfg['derived.maps_root']
    ensure_dir(maps_root)
    timestamp  = cfg['project.timestamp']
    env_prefix = _unified_env_prefix(cfg)
    flip_a2o   = _resolve_flip_a2o(cfg, 'rof')

    with timer.time('create_maps_rof'):
        print_line()
        print(f'\n  {clr.GREEN}Creating river map files with TempestRemap{clr.END}')
        print(f'  {clr.GREEN}--a2o goes on the'
              f' {"rof->lnd" if flip_a2o else "lnd->rof"} maps'
              f' (grid.rof_flip_a2o_direction = {flip_a2o}){clr.END}')

        algorithms = _resolve_algorithms(cfg, algorithms, 'rof')
        for alg in algorithms:
            map_file = f'{maps_root}/map_{lnd_grid_name}_to_{rof_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, lnd_grid_file, rof_grid_file, map_file, a2o=not flip_a2o)
            map_file = f'{maps_root}/map_{rof_grid_name}_to_{lnd_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, rof_grid_file, lnd_grid_file, map_file, a2o=flip_a2o)

        print(f'\n  {clr.GREEN}River map file creation SUCCESSFUL{clr.END}')


def create_maps_spa(cfg):
    """
    Create SPA (EAMxx) interpolation map with TempestRemap.

    Parameters
    ----------
    cfg : taos_config
    """
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    spa_grid_name = cfg.get('grid.spa_name', 'ne30pg2')
    spa_grid_file = cfg['grid.spa_file']
    maps_root     = cfg['derived.maps_root']
    ensure_dir(maps_root)
    timestamp     = cfg['project.timestamp']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    env_prefix    = _unified_env_prefix(cfg)

    with timer.time('create_maps_spa'):
        print_line()
        print(f'\n  {clr.GREEN}Creating SPA map file with TempestRemap{clr.END}')
        map_file = f'{maps_root}/map_{spa_grid_name}_to_{atm_grid_name}_traave.{timestamp}.nc'
        _ncremap_pair(env_prefix, 'traave', spa_grid_file, atm_grid_file, map_file)
        print(f'\n  {clr.GREEN}SPA map file creation SUCCESSFUL{clr.END}')


# -------------------------------------------------------------------
# entry point


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create coupling map files for a TAOS project.')
    parser.add_argument('project_yaml', help='Path to project.yaml')
    parser.add_argument('--create-maps-ocn', action='store_true', help='Create ocean coupling maps')
    parser.add_argument('--create-maps-lnd', action='store_true', help='Create land coupling maps')
    parser.add_argument('--create-maps-rof', action='store_true',
                        help='Create land↔river coupling maps (skipped unless grid.rof_file is set)')
    parser.add_argument('--create-maps-spa', action='store_true', help='Create SPA map (EAMxx)')
    parser.add_argument('--grid-name', default=None,
                        help='Grid name to process (selects from grids: list; default: base grid:)')
    parser.add_argument('--algorithms', default=None,
                        help='Comma-separated remap algorithms for ocn/lnd/rof maps '
                             '(overrides maps.algorithms in project.yaml; '
                             f'default: {",".join(_DEFAULT_ALGORITHMS)})')
    args = parser.parse_args()

    cfg = taos_config(args.project_yaml)
    if args.grid_name:
        cfg = cfg.for_grid(args.grid_name)
    cfg.validate()

    algorithms = _resolve_algorithms(cfg, args.algorithms) if args.algorithms else None

    timer.start_total()
    if args.create_maps_ocn:
        create_maps_ocn(cfg, algorithms=algorithms)
    if args.create_maps_lnd:
        create_maps_lnd(cfg, algorithms=algorithms)
    if args.create_maps_rof:
        create_maps_rof(cfg, algorithms=algorithms)
    if args.create_maps_spa:
        create_maps_spa(cfg)
    timer.summary()
