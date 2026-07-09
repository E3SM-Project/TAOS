#!/usr/bin/env python3
"""
taos.domain — Domain file generation workflow.

Creates E3SM domain files for a new atmosphere grid using the
generate_domain_files_E3SM.py tool from the E3SM source tree.

Optionally creates the ocean→atmosphere coupling map if it doesn't exist.

Usage
-----
    python -m taos.domain path/to/project.yaml
    python -m taos.domain path/to/project.yaml --create-domain-map
"""
import os

from taos.config import taos_config
from taos.util import clr, print_line, run_cmd, timer

# -------------------------------------------------------------------
# internal helpers


def _unified_env_prefix(cfg):
    """Return a bash one-liner that sources the E3SM unified environment."""
    return f'source {cfg["paths.unified_src"]}'


# -------------------------------------------------------------------
# public API


def create_domain(cfg, create_domain_map=False):
    """
    Generate E3SM domain files for the atmosphere grid.

    Parameters
    ----------
    cfg : taos_config
    create_domain_map : bool
        If True, generate the ocean→atmosphere coupling map before creating
        the domain files. Requires that the grid files already exist.
    """
    # -------------------------------------------------------------------
    # resolve paths
    grid_name     = cfg['grid.name']
    atm_grid_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    ocn_grid_name = cfg['grid.ocn_name']
    ocn_grid_file = cfg['grid.ocn_file']
    maps_root     = cfg['derived.maps_root']
    domn_root     = cfg['derived.domn_root']
    timestamp     = cfg['project.timestamp']
    e3sm_src_root = cfg['paths.e3sm_src_root']
    atm_grid_file = f'{cfg["derived.grid_root"]}/{atm_grid_name}_scrip.nc'
    map_file      = f'{maps_root}/map_{ocn_grid_name}_to_{atm_grid_name}_traave.{timestamp}.nc'
    domn_tool     = f'{e3sm_src_root}/tools/generate_domain_files/generate_domain_files_E3SM.py'
    env_prefix    = _unified_env_prefix(cfg)

    # -------------------------------------------------------------------
    # print summary
    print_line()
    print(f'\n  {clr.BOLD}DOMAIN WORKFLOW VARIABLES:{clr.END}')
    print(f'    grid_name     = {grid_name}')
    print(f'    atm_grid_name = {atm_grid_name}')
    print(f'    ocn_grid_name = {ocn_grid_name}')
    print(f'    atm_grid_file = {atm_grid_file}')
    print(f'    ocn_grid_file = {ocn_grid_file}')
    print(f'    map_file      = {map_file}')
    print(f'    domn_root     = {domn_root}')
    print_line()

    with timer.time('create_domain'):
        # -------------------------------------------------------------------
        # optionally create the coupling map first
        if create_domain_map:
            cmd = (f'{env_prefix} &&'
                   f' ncremap -a traave'
                   f' --src_grd={ocn_grid_file}'
                   f' --dst_grd={atm_grid_file}'
                   f' --map_file={map_file}')
            with timer.time('domain: ncremap ocn→atm map'):
                run_cmd(cmd)

        if not os.path.exists(map_file):
            raise RuntimeError(
                f'Map file does not exist: {map_file}\n'
                f'Run with --create-domain-map or create it via taos.maps first.'
            )

        # -------------------------------------------------------------------
        # generate domain files
        cmd = (f'{env_prefix} &&'
               f' python {domn_tool}'
               f' -m {map_file}'
               f' -o {ocn_grid_name}'
               f' -l {grid_name}'
               f' --date-stamp={timestamp}'
               f' --output-root={domn_root}')
        with timer.time('domain: generate_domain_files_E3SM.py'):
            run_cmd(cmd)

        print(f'\n  {clr.GREEN}Domain file generation SUCCESSFUL{clr.END}')


# -------------------------------------------------------------------
# entry point


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create domain files for a TAOS project.')
    parser.add_argument('project_yaml', help='Path to project.yaml')
    parser.add_argument('--create-domain-map', action='store_true',
                        help='Generate the ocean→atmosphere coupling map before creating domain files')
    parser.add_argument('--grid-name', default=None,
                        help='Grid name to process (selects from grids: list; default: base grid:)')
    args = parser.parse_args()

    cfg = taos_config(args.project_yaml)
    if args.grid_name:
        cfg = cfg.for_grid(args.grid_name)
    cfg.validate()
    timer.start_total()
    create_domain(cfg, create_domain_map=args.create_domain_map)
    timer.summary()
