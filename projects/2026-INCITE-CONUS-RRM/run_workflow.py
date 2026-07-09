#!/usr/bin/env python3
"""
run_workflow.py — Project-level orchestrator for TAOS workflows.

Edit this script to describe the pipeline for your specific project.
Submit SLURM jobs or call taos module functions directly as needed.

for interactive workflow at NERSC:
    salloc --nodes 1 --qos interactive --time 4:00:00 --constraint cpu --account=e3sm
    python run_workflow.py
    
    salloc --nodes 1 --qos interactive --time 4:00:00 --constraint cpu --account=m2637
    salloc --nodes 4 --qos interactive --time 4:00:00 --cpus-per-task=32 --constraint cpu --account=m2637

    source activate ux_env
    python run_workflow.py
    
"""
import os, pathlib
from taos import taos_config
from taos.util import run_cmd, print_line

#-------------------------------------------------------------------------------
# load config — shared settings (paths, slurm) read once from base config

proj_dir  = pathlib.Path(__file__).parent
cfg       = taos_config(proj_dir / 'project.yaml')

logs_root        = cfg['derived.slurm_log_root']
slurm_account    = cfg['slurm.account']
slurm_constraint = cfg.get('slurm.constraint', '')
slurm_qos        = cfg.get('slurm.qos', 'regular')

#-------------------------------------------------------------------------------
# step flags — set to False (or comment out) to skip a step

use_batch = False  # set False to run steps directly on the current node

# do_grid   = True
# do_maps   = True
do_domain = True
# do_topo   = True


topo_args = ''
# topo_args += ' --stage grid'
# topo_args += ' --stage remap'
# topo_args += ' --stage smooth'
# topo_args += ' --stage sgh'
# topo_args += ' --stage remap,smooth,sgh'
# topo_args += ' --stage smooth,sgh'
topo_args += ' --stage all'
# topo_args += ' --force-new-3km-data'

#-------------------------------------------------------------------------------
# select which grids to process - use None to process all grids in project.yaml,
# or list specific grid names to process a subset

# active_grids = None
# active_grids = ['2026-incite-conus-128x2'] # smaller grid for testing
active_grids = ['2026-incite-conus-1024x2']
# active_grids = ['2026-incite-conus-1024x3']
# active_grids = ['2026-incite-conus-1024x4']
# active_grids = ['2026-incite-conus-128x2']

#-------------------------------------------------------------------------------
# SLURM resource settings - use sepearate specs foreach grid, as well as maps vs topo

MAPS_SLURM = {
    '2026-incite-conus-128x2':  '--nodes=1 --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x2': '--nodes=1 --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x3': '--nodes=1 --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x4': '--nodes=1 --cpus-per-task=32 --time=12:00:00',
}

TOPO_SLURM = {
    '2026-incite-conus-128x2':  '--nodes=4  --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x2': '--nodes=1 --time=12:00:00',
    # '2026-incite-conus-1024x2': '--nodes=16 --cpus-per-task=32 --time=48:00:00',
    '2026-incite-conus-1024x3': '--nodes=32 --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x4': '--nodes=64 --cpus-per-task=32 --time=12:00:00',
}

#-------------------------------------------------------------------------------
# submit one set of jobs per grid

for grid_cfg in cfg.iter_grids():
    if active_grids is not None and grid_cfg['grid.name'] not in active_grids:
        continue

    grid_cfg.validate()
    grid_name = grid_cfg['grid.name']
    print_line()

    sbatch = f'sbatch'
    sbatch += f' --export=ALL'
    sbatch += f' --output={logs_root}/%x-%j.slurm.main.out'
    sbatch += f' --account={slurm_account}'
    if slurm_constraint:
        sbatch += f' --constraint={slurm_constraint}'
    if slurm_qos:
        sbatch += f' --qos={slurm_qos}'
    sbatch += f' --mail-user={cfg["slurm.mail_user"]}'
    sbatch += f' --mail-type={cfg["slurm.mail_type"]}'

    yaml_path = proj_dir / 'project.yaml'

    #---------------------------------------------------------------------------
    # grid files (np4/pg2/3km SCRIP and MBDA)

    if locals().get('do_grid', False):
        cmd = f'python -m taos.topo {yaml_path} --grid-name {grid_name} --stage grid'
        if use_batch:
            run_cmd(f'{sbatch} --job-name=gen_grid_{grid_name} --nodes=1 --ntasks-per-node=32 --time=0:30:00 --wrap="{cmd}"')
        else:
            run_cmd(cmd)

    #---------------------------------------------------------------------------
    # maps and domain (chained: domain depends on map files produced by maps)

    if locals().get('do_maps', False) or locals().get('do_domain', False):
        cmd = ''
        if locals().get('do_maps', False):
            map_args = ''
            map_args += ' --create-maps-ocn'
            map_args += ' --create-maps-lnd'
            cmd += f'python -m taos.maps {yaml_path} --grid-name {grid_name} {map_args}'
        if locals().get('do_domain', False):
            if cmd: cmd += ' && '
            cmd += f'python -m taos.domain {yaml_path} --grid-name {grid_name}'
        if use_batch:
            maps_slurm_opts = MAPS_SLURM.get(grid_name, '--nodes=1 --cpus-per-task=32 --time=6:00:00')
            run_cmd(f'{sbatch} --job-name=gen_maps_domain_{grid_name} {maps_slurm_opts} --wrap="{cmd}"')
        else:
            run_cmd(cmd)

    #---------------------------------------------------------------------------
    # topography

    if locals().get('do_topo', False):

        cmd = f'python -m taos.topo {yaml_path} --grid-name {grid_name} {topo_args}'
        if use_batch:
            topo_slurm_opts = TOPO_SLURM.get(grid_name, '--nodes=4 --cpus-per-task=32 --time=0:30:00')
            run_cmd(f'{sbatch} --job-name=gen_topo_{grid_name} {topo_slurm_opts} --wrap="{cmd}"')
        else:
            run_cmd(cmd)

print_line()
