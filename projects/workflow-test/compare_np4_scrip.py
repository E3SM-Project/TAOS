#!/usr/bin/env python3
"""
compare_np4_scrip.py — Generate np4 SCRIP files via both methods for comparison.

Produces four files in compare_np4/ (relative to this script's directory):
  {grid}_np4_scrip_python.nc  — Python implementation
  {grid}_np4_mbda_python.nc
  {grid}_np4_scrip_homme.nc   — homme_tool + HOMME2SCRIP.py (requires E3SM env)
  {grid}_np4_mbda_homme.nc

Usage
-----
    python compare_np4_scrip.py [--grid-name NAME] [--python-only]

    --grid-name   Grid to process (default: ne30).
    --python-only Skip the homme_tool path (useful on login nodes).

The homme path requires an active compute allocation and the E3SM module
environment (get_case_env).  Run inside `salloc` or via `sbatch`, or pass
--python-only to skip it.

for interactive workflow at NERSC:
    salloc --nodes 1 --qos interactive --time 4:00:00 --constraint cpu --account=e3sm
    salloc --nodes 1 --qos interactive --time 4:00:00 --cpus-per-task=32 --constraint cpu --account=m2637
    python compare_np4_scrip.py --grid-name=ne30
    python compare_np4_scrip.py --grid-name=ne120
    python compare_np4_scrip.py --grid-name=ne256
    python compare_np4_scrip.py --grid-name=ne512
    python compare_np4_scrip.py --grid-name=ne1024
    python compare_np4_scrip.py --grid-name=ne2048

    python compare_np4_scrip.py --grid-name=ne4 --python-only
    python compare_np4_scrip.py --grid-name=ne30 --python-only
    python compare_np4_scrip.py --grid-name=ne2048 --python-only
"""
import argparse, pathlib, sys, textwrap
from time import perf_counter

proj_dir = pathlib.Path(__file__).parent
repo_root = proj_dir.parents[1]   # projects/2026-workflow-test → projects → repo root
sys.path.insert(0, str(repo_root))

from taos import taos_config
from taos.grid import _create_np4_scrip, _grid_paths
from taos.util import run_cmd, timer

# -----------------------------------------------------------------------------
# arguments

parser = argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--grid-name',   default='ne30', help='Grid to process (default: ne30)')
parser.add_argument('--python-only', action='store_true', help='Skip the homme_tool path')
args = parser.parse_args()

# -----------------------------------------------------------------------------
# load config

cfg = taos_config(proj_dir / 'project.yaml')
grid_cfg = cfg.for_grid(args.grid_name)

grid_name     = grid_cfg['grid.name']
unified_bin   = grid_cfg['paths.unified_bin']
e3sm_src_root = grid_cfg['paths.e3sm_src_root']
homme_tool_root = grid_cfg.get('paths.homme_tool_root', '')
p = _grid_paths(grid_cfg)

# -----------------------------------------------------------------------------
# output paths — written to compare_np4/ in the project directory

out_dir = pathlib.Path('/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/2026-workflow-test/compare_np4')
# out_dir = proj_dir / 'compare_np4'
out_dir.mkdir(exist_ok=True)

scrip_python = str(out_dir / f'{grid_name}_np4_scrip_python.nc')
mbda_python  = str(out_dir / f'{grid_name}_np4_mbda_python.nc')
scrip_homme  = str(out_dir / f'{grid_name}_np4_scrip_homme.nc')
mbda_homme   = str(out_dir / f'{grid_name}_np4_mbda_homme.nc')

# template file that homme_tool writes (fixed name, in homme_tool_root)
grid_template = f'{homme_tool_root}/{grid_name}_ne0np4_tmp1.nc'
nl_file       = f'{homme_tool_root}/input.grd.{grid_name}.compare.nl'

# -----------------------------------------------------------------------------
# Python path

print(f'\n{"="*70}')
print(f'  Python np4 SCRIP: {grid_name}')
print(f'{"="*70}')
print(f'  exodus : {p["grid_file_exodus"]}')
print(f'  scrip  : {scrip_python}')
print(f'  mbda   : {mbda_python}')

t_python_start = perf_counter()
with timer.time(f'Python np4 SCRIP+MBDA ({grid_name})'):
    _create_np4_scrip(p['grid_file_exodus'], scrip_python, mbda_python)
t_python_end = perf_counter()

# -----------------------------------------------------------------------------
# homme_tool path

if args.python_only:
    print('\n  Skipping homme_tool path (--python-only).')
else:
    if not homme_tool_root:
        print('\n  WARNING: paths.homme_tool_root is not configured — skipping homme path.')
    else:
        print(f'\n{"="*70}')
        print(f'  homme_tool np4 SCRIP: {grid_name}')
        print(f'{"="*70}')
        print(f'  exodus   : {p["grid_file_exodus"]}')
        print(f'  template : {grid_template}')
        print(f'  scrip    : {scrip_homme}')
        print(f'  mbda     : {mbda_homme}')

        t_homme_start = perf_counter()
        env_prefix = f'eval $({e3sm_src_root}/cime/CIME/Tools/get_case_env)'

        # write namelist
        nl_content = textwrap.dedent(f"""\
            &ctl_nl
            ne = 0
            mesh_file = "{p['grid_file_exodus']}"
            /
            &vert_nl
            /
            &analysis_nl
            output_dir = "{homme_tool_root}/"
            output_prefix="{grid_name}_"
            tool = 'grid_template_tool'
            output_timeunits=1
            output_frequency=1
            output_varnames1='area','corners','cv_lat','cv_lon'
            output_type='netcdf4p'
            io_stride = 1
            /
            """)
        pathlib.Path(nl_file).write_text(nl_content)

        homme2scrip = f'{e3sm_src_root}/components/homme/test/tool/python/HOMME2SCRIP.py'

        with timer.time(f'homme_tool np4 template ({grid_name})'):
            run_cmd(f'cd {homme_tool_root} && {env_prefix} &&'
                    f' srun -c 32 -N $SLURM_NNODES {homme_tool_root}/src/tool/homme_tool < {nl_file}')

        with timer.time(f'HOMME2SCRIP ({grid_name})'):
            run_cmd(f'{env_prefix} &&'
                    f' {unified_bin}/python {homme2scrip}'
                    f' --src_file {grid_template}'
                    f' --dst_file {scrip_homme}')

        with timer.time(f'ncap2 + ncrename np4 SCRIP→MBDA ({grid_name})'):
            run_cmd(f'{unified_bin}/ncap2 -v -5 -O'
                    f' -s "lon=grid_center_lon;lat=grid_center_lat;area=grid_area"'
                    f' {scrip_homme} {mbda_homme}')
            run_cmd(f'{unified_bin}/ncrename -d grid_size,ncol {mbda_homme}')
        t_homme_end = perf_counter()

timer._record(f'Total (Python workflow) ({grid_name})', t_python_end - t_python_start, print_msg=False)
if not args.python_only and homme_tool_root:
    timer._record(f'Total (homme_tool workflow) ({grid_name})', t_homme_end - t_homme_start, print_msg=False)
timer.summary()
print()
