#!/usr/bin/env python3
"""
check_config.py — Print all resolved TAOS configuration values.

Usage
-----
    python show_config.py                  # uses project.yaml in this directory
    python show_config.py /path/to/project.yaml
"""
import sys
from pathlib import Path

from taos import taos_config, taos_config_error
from taos.util import clr, print_line

# ------------------------------------------------------------------------------

def _item(key: str, val: str, key_width: int = 22) -> None:
    key_str = f'{key:<{key_width}}'
    if val:
        print(f'    {key_str} = {val}')
    else:
        print(f'    {key_str} = {clr.YELLOW}(not set){clr.END}')

def _section(title: str) -> None:
    print_line()
    print(f'  {clr.BOLD}{title}{clr.END}')

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

    _section('DETECTED MACHINE')
    _item('machine', cfg.machine)

    _section('MACHINE PATHS')
    for k, v in cfg.paths.items():
        _item(k, v)

    _section('SLURM SETTINGS')
    for k, v in cfg.slurm.items():
        _item(k, v)

    _section('PROJECT SETTINGS')
    for k, v in cfg.project.items():
        _item(k, v)

    for grid_cfg in cfg.iter_grids():
        grid_name = grid_cfg.grid.get('name', '(unnamed)')
        _section(f'GRID: {grid_name}')
        for k, v in grid_cfg.grid.items():
            _item(k, str(v) if v is not None else '')

    _section('DERIVED PATHS')
    for k, v in cfg.derived.items():
        _item(k, v)

    print_line()

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
