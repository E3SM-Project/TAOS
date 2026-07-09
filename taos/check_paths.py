#!/usr/bin/env python3
"""
check_paths.py — Check whether expected TAOS paths exist on disk.

Prints a color-coded status for each path (green = OK, red = missing).
Exits with code 1 if any path is missing.

Usage
-----
    python check_paths.py                  # uses project.yaml in this directory
    python check_paths.py /path/to/project.yaml
"""
import os
import sys
from pathlib import Path

from taos import taos_config, taos_config_error
from taos.util import clr, print_line

# ------------------------------------------------------------------------------

def _check(label: str, path: str, check_fn) -> bool:
    """Print a colored status line. Returns True if the check passed."""
    label_str = f'{label:<25}'
    if not path:
        print(f'    {label_str} => {clr.YELLOW}(not set){clr.END}')
        return False
    if check_fn(path):
        print(f'    {label_str} => {clr.GREEN}OK{clr.END}')
        return True
    else:
        print(f'    {label_str} => {clr.RED}does not exist{clr.END}')
        print(f'    {" " * 25}    {path}')
        return False

def _check_dir(label: str, path: str)  -> bool: return _check(label, path, os.path.isdir)
def _check_file(label: str, path: str) -> bool: return _check(label, path, os.path.isfile)

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

    results = []

    # --- Derived data directories (created when workflow runs) ---------------
    print_line()
    proj_name = cfg.project.get('name', '')
    derived_note = '' if proj_name and proj_name not in ('UNSET',) else f'  {clr.YELLOW}(requires project.name to be set){clr.END}'
    print(f'  {clr.BOLD}DERIVED DATA DIRECTORIES{clr.END}{derived_note}')
    for key in ['data_root', 'grid_root', 'maps_root', 'topo_root',
                'init_root', 'domn_root']:
        results.append(_check_dir(key, cfg.derived.get(key, '')))

    # --- Log directories (created in the project code directory) -------------
    print_line()
    print(f'  {clr.BOLD}LOG DIRECTORIES{clr.END}')
    for key in ['slurm_log_root', 'hiccup_log_root']:
        results.append(_check_dir(key, cfg.derived.get(key, '')))

    # --- Machine tool directories --------------------------------------------
    print_line()
    print(f'  {clr.BOLD}MACHINE DIRECTORIES{clr.END}')
    for key in ['grid_data_root', 'e3sm_src_root', 'DIN_LOC_ROOT',
                'unified_bin', 'homme_tool_root']:
        results.append(_check_dir(key, cfg.paths.get(key, '')))

    # --- Machine files -------------------------------------------------------
    print_line()
    print(f'  {clr.BOLD}MACHINE FILES{clr.END}')
    for key in ['topo_file_src', 'mbda_path', 'unified_src']:
        results.append(_check_file(key, cfg.paths.get(key, '')))

    # --- Summary -------------------------------------------------------------
    print_line()
    n_ok    = sum(results)
    n_total = len(results)
    if n_ok == n_total:
        print(f'  {clr.GREEN}{n_ok} of {n_total} paths OK{clr.END}')
    else:
        n_bad = n_total - n_ok
        print(f'  {clr.RED}{n_bad} of {n_total} paths missing or not set{clr.END}')
    print_line()

    sys.exit(0 if n_ok == n_total else 1)

# ------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
