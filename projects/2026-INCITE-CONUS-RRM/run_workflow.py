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
import subprocess as sp
from taos import taos_config
from taos.util import clr, run_cmd, print_line

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

use_batch = True  # set False to run steps directly on the current node

# do_grid   = True
# do_maps   = True
do_domain = True
# do_topo   = True

#-------------------------------------------------------------------------------
# map generation — one batch job is submitted per (component, algorithm) pair,
# so each job only has to fit a single map pair inside the 48h wall clock cap.
# A failed or timed-out algorithm can then be re-run on its own by trimming
# these lists, without redoing the maps that already completed.

# map_components = ['spa']
# map_components = ['lnd']
map_components = ['ocn']
# map_components = ['ocn','lnd','spa']


# map_algorithms = ['traave','trbilin','trfv2','trintbilin']
map_algorithms = ['traave']

#-------------------------------------------------------------------------------
# topography options

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
active_grids = ['2026-incite-conus-1024x2']
# active_grids = ['2026-incite-conus-1024x3']
# active_grids = ['2026-incite-conus-1024x4']

# smaller grid for testing
# active_grids = ['2026-incite-conus-128x2'] 
# active_grids = ['2026-incite-conus-128x3']


# # shorter names?
# active_grids = ['conus1024x2v1']
# active_grids = ['conus1024x3v1']
# active_grids = ['conus1024x4v1']

#-------------------------------------------------------------------------------
# SLURM resource settings - use sepearate specs foreach grid, as well as maps vs topo
#
# NOTE on --cpus-per-task for map jobs: TempestRemap (GenerateOverlapMesh /
# GenerateOfflineMap in the unified env) is linked without OpenMP or MPI, so it
# is strictly serial. Under the default "regular" QOS on Perlmutter the whole
# node is allocated exclusively (OverSubscribe=EXCLUSIVE, DefMemPerNode=
# UNLIMITED), so a --nodes=1 job already owns all ~503 GB no matter what
# --cpus-per-task is set to. Raising it buys neither memory nor speed here.
# --cpus-per-task only governs memory under the "shared" QOS, where the limit
# is 1905 MB per logical CPU - see the commented example below.

MAPS_SLURM_DEFAULT = '--nodes=1 --time=12:00:00'

MAPS_SLURM = {
    '2026-incite-conus-1024x2': '--nodes=1 --time=12:00:00',
    '2026-incite-conus-1024x3': '--nodes=1 --time=48:00:00',
    '2026-incite-conus-1024x4': '--nodes=1 --time=48:00:00',
    # smaller grid for testing
    '2026-incite-conus-128x2':  '--nodes=1 --time=12:00:00',
    '2026-incite-conus-128x3':  '--nodes=1 --time=12:00:00',
}

# per-algorithm overrides, keyed by (grid_name, algorithm) - these win over
# MAPS_SLURM above. Useful because traave is far more expensive than the rest.
# Options listed here come after the QOS in the sbatch line, so a --qos here
# overrides the project default.
MAPS_SLURM_ALG = {
    # ('2026-incite-conus-1024x3','traave'): '--nodes=1 --time=48:00:00',
    # shared QOS example - charges only for the cores requested, and
    # --cpus-per-task then does set the memory limit (1905 MB per CPU):
    # ('2026-incite-conus-1024x3','trbilin'): '--qos=shared --ntasks=1 --cpus-per-task=64 --time=48:00:00',
}

DOMAIN_SLURM = '--nodes=1 --time=12:00:00'

TOPO_SLURM = {
    '2026-incite-conus-1024x2': '--nodes=1 --time=12:00:00',
    # '2026-incite-conus-1024x2': '--nodes=16 --cpus-per-task=32 --time=48:00:00',
    '2026-incite-conus-1024x3': '--nodes=32 --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-1024x4': '--nodes=64 --cpus-per-task=32 --time=12:00:00',
    # smaller grid for testing
    '2026-incite-conus-128x2':  '--nodes=4  --cpus-per-task=32 --time=12:00:00',
    '2026-incite-conus-128x3':  '--nodes=4  --cpus-per-task=32 --time=12:00:00',
}

#-------------------------------------------------------------------------------
# job submission helper

def submit(sbatch_prefix, job_name, slurm_opts, cmd, depends=None):
    """
    Submit a single step as a batch job and return its SLURM job ID.

    When use_batch is False the command is run directly on the current node
    and None is returned. <depends> is a list of job IDs (None entries are
    ignored) that must all finish successfully before this job starts.
    """
    if not use_batch:
        run_cmd(cmd)
        return None
    depends = [d for d in (depends or []) if d]
    dep_opt = f' --dependency=afterok:{":".join(depends)}' if depends else ''
    full_cmd = (f'{sbatch_prefix} --parsable --job-name={job_name}'
                f' {slurm_opts}{dep_opt} --wrap="{cmd}"')
    print(f'\n  {clr.GREEN}{full_cmd}{clr.END}')
    result = sp.run(full_cmd, shell=True, check=True, text=True,
                    capture_output=True, executable='/bin/bash')
    job_id = result.stdout.strip().split(';')[0]
    print(f'  => submitted job {job_id}')
    return job_id

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
    # maps — one independent job per (component, algorithm) pair

    map_job_ids = []
    if locals().get('do_maps', False):
        # one job per (component, algorithm); spa is always traave and only
        # produces a single map, so it gets one job rather than one per algorithm
        map_jobs = [(c, a) for c in map_components if c != 'spa' for a in map_algorithms]
        if 'spa' in map_components:
            map_jobs.append(('spa', 'traave'))

        for component, alg in map_jobs:
            cmd = (f'python -m taos.maps {yaml_path} --grid-name {grid_name}'
                   f' --create-maps-{component}')
            if component != 'spa':
                cmd += f' --algorithms={alg}'
            job_name = f'gen_maps_{component}_{alg}_{grid_name}'
            slurm_opts = MAPS_SLURM_ALG.get(
                (grid_name, alg), MAPS_SLURM.get(grid_name, MAPS_SLURM_DEFAULT))
            map_job_ids.append(submit(sbatch, job_name, slurm_opts, cmd))

    #---------------------------------------------------------------------------
    # domain — held until every map job above has completed successfully

    if locals().get('do_domain', False):
        cmd = f'python -m taos.domain {yaml_path} --grid-name {grid_name}'
        submit(sbatch, f'gen_domain_{grid_name}', DOMAIN_SLURM, cmd,
               depends=map_job_ids)

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
