#!/usr/bin/env python3
"""
taos.maps — Coupling map generation workflow.

Creates atmosphere↔ocean, atmosphere↔land, and SPA interpolation maps
using TempestRemap (via ncremap).

Grid names and files for ocean, land, and routing components are read
from the project.yaml grid section:
  grid.ocn_name / grid.ocn_file
  grid.lnd_name / grid.lnd_file
  grid.rof_name / grid.rof_file   (optional, defaults to lnd)
  grid.spa_name / grid.spa_file   (optional, defaults to ne30pg2)

Usage
-----
    python -m taos.maps path/to/project.yaml --create-maps-ocn --create-maps-lnd
"""
import os
import re

from taos.config import taos_config
from taos.util import clr, print_line, run_cmd, timer

# -------------------------------------------------------------------
# default remap algorithms (overridable via maps.algorithms in project.yaml
# or the --algorithms command-line argument)
_DEFAULT_ALGORITHMS = ['traave', 'trbilin', 'trfv2', 'trintbilin']

# -------------------------------------------------------------------
# internal helpers


def _resolve_algorithms(cfg, override=None):
    """Return the list of remap algorithms to use.

    Precedence: explicit override (e.g. CLI arg) > maps.algorithms in
    project.yaml > the built-in default list.  Accepts either a YAML list
    or a comma-separated string.
    """
    value = override if override is not None else cfg.get('maps.algorithms')
    if value is None:
        return list(_DEFAULT_ALGORITHMS)
    if isinstance(value, str):
        value = [v.strip() for v in value.split(',') if v.strip()]
    return list(value)


def _unified_env_prefix(cfg):
    """Return a bash one-liner that sources the E3SM unified environment."""
    return f'source {cfg["paths.unified_src"]}'


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
    """
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    ocn_grid_name = cfg['grid.ocn_name']
    ocn_grid_file = cfg['grid.ocn_file']
    maps_root     = cfg['derived.maps_root']
    timestamp     = cfg['project.timestamp']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    env_prefix    = _unified_env_prefix(cfg)

    with timer.time('create_maps_ocn'):
        print_line()
        print(f'\n  {clr.GREEN}Creating ocean map files with TempestRemap{clr.END}')

        algorithms = _resolve_algorithms(cfg, algorithms)
        for alg in algorithms:
            map_file = f'{maps_root}/map_{ocn_grid_name}_to_{atm_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, ocn_grid_file, atm_grid_file, map_file)
            map_file = f'{maps_root}/map_{atm_grid_name}_to_{ocn_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, atm_grid_file, ocn_grid_file, map_file, a2o=True)

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
    """
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    lnd_grid_name = cfg['grid.lnd_name']
    lnd_grid_file = cfg['grid.lnd_file']
    maps_root     = cfg['derived.maps_root']
    timestamp     = cfg['project.timestamp']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    env_prefix    = _unified_env_prefix(cfg)

    with timer.time('create_maps_lnd'):
        print_line()
        print(f'\n  {clr.GREEN}Creating land map files with TempestRemap{clr.END}')

        algorithms = _resolve_algorithms(cfg, algorithms)
        for alg in algorithms:
            map_file = f'{maps_root}/map_{lnd_grid_name}_to_{atm_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, lnd_grid_file, atm_grid_file, map_file)
            map_file = f'{maps_root}/map_{atm_grid_name}_to_{lnd_grid_name}_{alg}.{timestamp}.nc'
            _ncremap_pair(env_prefix, alg, atm_grid_file, lnd_grid_file, map_file, a2o=True)

        print(f'\n  {clr.GREEN}Land map file creation SUCCESSFUL{clr.END}')


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
    parser.add_argument('--create-maps-spa', action='store_true', help='Create SPA map (EAMxx)')
    parser.add_argument('--grid-name', default=None,
                        help='Grid name to process (selects from grids: list; default: base grid:)')
    parser.add_argument('--algorithms', default=None,
                        help='Comma-separated remap algorithms for ocn/lnd maps '
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
    if args.create_maps_spa:
        create_maps_spa(cfg)
    timer.summary()
