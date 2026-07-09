#!/usr/bin/env python3
"""
check_grids.py — Print expected file paths for each grid in a TAOS project.

Prints grid, topo, and map file paths for each configured grid, with a
color-coded indicator showing whether each file currently exists on disk.

Usage
-----
    python show_grids.py                  # uses project.yaml in this directory
    python show_grids.py /path/to/project.yaml
"""
import os
import sys
from pathlib import Path

from taos import taos_config, taos_config_error
from taos.grid import _grid_paths
from taos.topo import _topo_paths
from taos.util import clr, print_line

# ------------------------------------------------------------------------------

_MAP_ALGORITHMS = ['traave', 'trbilin', 'trfv2', 'trintbilin']


def _file(label: str, path: str, key_width: int = 22) -> None:
    label_str = f'{label:<{key_width}}'
    if not path:
        print(f'    {label_str}  {clr.YELLOW}(not set){clr.END}')
        return
    status = f'{clr.GREEN}exists{clr.END}' if os.path.isfile(path) else f'{clr.RED}missing{clr.END}'
    print(f'    {label_str}  [{status}]  {path}')


def _subsection(title: str) -> None:
    print(f'\n  {clr.BOLD}{title}{clr.END}')


# ------------------------------------------------------------------------------

def main():
    if len(sys.argv) > 1:
        cfg_path = Path(sys.argv[1])
    else:
        cfg_path = Path(__file__).parent / 'project.yaml'

    try:
        cfg = taos_config(cfg_path)
    except (FileNotFoundError, taos_config_error) as e:
        print(f'\n  {clr.RED}ERROR:{clr.END} {e}\n')
        sys.exit(1)

    for grid_cfg in cfg.iter_grids():
        grid_name = grid_cfg.grid.get('name', '(unnamed)')
        pg2_name  = grid_cfg.get('grid.name_pg2', grid_name + 'pg2')
        ocn_name  = grid_cfg.get('grid.ocn_name', '')
        lnd_name  = grid_cfg.get('grid.lnd_name', '')
        spa_name  = grid_cfg.get('grid.spa_name', 'ne30pg2')
        spa_file  = grid_cfg.get('grid.spa_file', '')
        maps_root = grid_cfg['derived.maps_root']
        domn_root = grid_cfg['derived.domn_root']
        timestamp = grid_cfg['project.timestamp']

        gp = _grid_paths(grid_cfg)
        tp = _topo_paths(grid_cfg)

        print_line()
        print(f'  {clr.BOLD}GRID: {grid_name}{clr.END}')

        # -------------------------------------------------------------------
        # grid files

        _subsection('Grid files')
        _file('exodus (input)',   gp['grid_file_exodus'])
        _file('np4 scrip',        gp['grid_file_np4_scrip'])
        _file('np4 mbda',         gp['grid_file_np4_mbda'])
        _file('pg2 scrip',        gp['grid_file_pg2_scrip'])
        _file('pg2 mbda',         gp['grid_file_pg2_mbda'])
        _file('3km exodus',       gp['grid_file_3km_exodus'])
        _file('3km scrip',        gp['grid_file_3km_scrip'])
        _file('3km mbda',         gp['grid_file_3km_mbda'])

        # -------------------------------------------------------------------
        # topo files

        _subsection('Topo files')
        _file('3km remapped',     tp['topo_file_3km'])
        _file('np4 remapped',     tp['topo_file_1_np4'])
        _file('pg2 remapped',     tp['topo_file_1_pg2'])
        _file('np4 smoothed',     tp['topo_file_2'])
        _file('3km→np4 (SGH)',    tp['topo_file_3km_1'])
        _file('3km smoothed',     tp['topo_file_3km_2'])
        _file('3km→pg2 (SGH)',    tp['topo_file_3km_pg2'])
        _file('FINAL',            tp['topo_file_final'])

        # -------------------------------------------------------------------
        # map files

        if ocn_name:
            _subsection(f'Ocean map files  ({ocn_name} ↔ {pg2_name})')
            for alg in _MAP_ALGORITHMS:
                _file(f'ocn→atm  {alg}', f'{maps_root}/map_{ocn_name}_to_{pg2_name}_{alg}.{timestamp}.nc', key_width=26)
                _file(f'atm→ocn  {alg}', f'{maps_root}/map_{pg2_name}_to_{ocn_name}_{alg}.{timestamp}.nc', key_width=26)

        if lnd_name:
            _subsection(f'Land map files   ({lnd_name} ↔ {pg2_name})')
            for alg in _MAP_ALGORITHMS:
                _file(f'lnd→atm  {alg}', f'{maps_root}/map_{lnd_name}_to_{pg2_name}_{alg}.{timestamp}.nc', key_width=26)
                _file(f'atm→lnd  {alg}', f'{maps_root}/map_{pg2_name}_to_{lnd_name}_{alg}.{timestamp}.nc', key_width=26)

        if spa_file:
            _subsection(f'SPA map file     ({spa_name} → {pg2_name})')
            _file(f'spa→atm  traave', f'{maps_root}/map_{spa_name}_to_{pg2_name}_traave.{timestamp}.nc', key_width=26)

        # -------------------------------------------------------------------
        # domain output directory

        _subsection('Domain output directory')
        status = f'{clr.GREEN}exists{clr.END}' if os.path.isdir(domn_root) else f'{clr.RED}missing{clr.END}'
        print(f'    [{status}]  {domn_root}')

    print_line()


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
