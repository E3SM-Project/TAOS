#!/usr/bin/env python3
import os, pathlib, taos
from taos import taos_config
#---------------------------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END); os.system(cmd); return
#---------------------------------------------------------------------------------------------------
# usage = '''
# python create_fsurdat_maps.py --grid_root     <grid_root> 
#                               --dst_grid_name <dst_grid_name>
#                               --dst_grid_file <dst_grid_file>
#                               --timestamp     <timestamp>
#                               --batch_acct    <batch_acct>
# Purpose:
#   This script reads a HOMME grid template file and writes out a SCRIP format grid description file of the np4/GLL grid.
    
#   HOMME np4 grid template files are produced by a two step procedure, which first requires running homme_tool, and then this script to convert the output into SCRIP format. This procedure is only needed for np4 files due to their use of vertex data. For cell centered pg2 files, one should instead use TempestRemap to create a grid description file. This is particularly useful when remapping topography data with cube_to_target, which can be much faster than remapping with tools like NCO due to the large size of the input topography data.
# Environment
    
#   This requires libraries such as xarray, which included in the E3SM unified environment:
#   https://e3sm.org/resources/tools/other-tools/e3sm-unified-environment/
#   Otherwise a simple conda environment can be created:
#   conda create --name example_env --channel conda-forge xarray numpy netcdf4
# '''
# from optparse import OptionParser
# parser = OptionParser(usage=usage)
# parser.add_option('--src_file',dest='src_file',default=None,help='Input HOMME grid template file')
# parser.add_option('--dst_file',dest='dst_file',default=None,help='Output scrip grid file')
# (opts, args) = parser.parse_args()
#---------------------------------------------------------------------------------------------------
'''
ncremap -4 -g ${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/SCRIPgrid_0.1x0.1_nomask_c20260731.nc \
    -G ttl='0.1x0.1 degree global uniform latitude-longitude grid'#latlon=1800,3600#lat_typ=uni#lat_drc=s2n#lon_typ=180_wst

ncremap -4 -g ${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/SCRIPgrid_0.01x0.01_nomask_c20260731.nc \
    -G ttl='0.01x0.01 degree global uniform latitude-longitude grid'#latlon=18000,36000#lat_typ=uni#lat_drc=s2n#lon_typ=180_wst
'''
#---------------------------------------------------------------------------------------------------
# The ESMF check runs inside the batch script rather than here, because the
# job no longer inherits this environment - it sources unified_src, and that
# loader picks a different environment on a compute node than on a login node
# (nompi/mpiuni here, MPI-enabled there, keyed off $SLURM_JOB_ID). Checking
# from a login node would therefore reject a job that is going to be fine.
#---------------------------------------------------------------------------------------------------
proj_dir        = pathlib.Path(__file__).parent
taos_cfg        = taos_config(proj_dir / 'project.yaml')

timestamp       = taos_cfg.get('project.timestamp')
host            = taos_cfg.get('machine.name')
unified_src     = taos_cfg.get('paths.unified_src')
account         = taos_cfg.get('slurm.account')
qos             = taos_cfg.get('slurm.qos')
constraint      = taos_cfg.get('slurm.constraint')
mail_user       = taos_cfg.get('slurm.mail_user')
mail_type       = taos_cfg.get('slurm.mail_type')
# machine-specific runtime settings (e.g. UCX transport tuning on OLCF) - empty
# on machines that need none, see slurm.job_env in taos/machines.yaml
job_env         = taos_cfg.job_env_block()

# repo root, so the batch job can import taos.util under whatever python the
# environment it sources provides - taos.util is stdlib-only, so no install
# into that environment is needed
taos_root       = pathlib.Path(taos.__file__).parent.parent

proj_root       = taos_cfg.get('derived.proj_root')
data_root       = taos_cfg.get('derived.data_root')
grid_root       = taos_cfg.get('derived.grid_root')
DIN_LOC_ROOT    = taos_cfg.get('paths.DIN_LOC_ROOT')

output_root     = f'{data_root}/files_fsurdat'
src_grid_root   = f'{DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids'

dst_grid_name   = f'STRONG-CA-32x5-v1'
dst_grid_file   = f'{grid_root}/{dst_grid_name}pg2_scrip.nc'

#---------------------------------------------------------------------------------------------------
if not os.path.exists(dst_grid_file): raise FileNotFoundError(f'file not found - dst_grid_file: {dst_grid_file}')
if not os.path.exists(data_root):     raise FileNotFoundError(f'path does not exist - data_root: {data_root}')
if not os.path.exists(grid_root):     raise FileNotFoundError(f'path does not exist - grid_root: {grid_root}')
if not os.path.exists(DIN_LOC_ROOT):  raise FileNotFoundError(f'path does not exist - DIN_LOC_ROOT: {DIN_LOC_ROOT}')
if not os.path.exists(src_grid_root): raise FileNotFoundError(f'path does not exist - src_grid_root: {src_grid_root}')
os.makedirs(output_root, exist_ok=True)
#---------------------------------------------------------------------------------------------------
grid_opt_list = []
def add_grid( **kwargs ):
    case_opts = {}
    for k, val in kwargs.items(): case_opts[k] = val
    grid_opt_list.append(case_opts)
#---------------------------------------------------------------------------------------------------
# build list of source grids

# sbatch_opts => flags for the allocation, emitted on the #SBATCH line
# srun_opts   => flags for the job step; -n is TOTAL tasks, not tasks per node.
# Always set -n explicitly - a bare srun picks up a site-dependent default,
# which on andes silently expanded to 32 duplicate serial ranks.

# std_slurm_opts = {'qos':'regular','time_limit':'1:00:00','sbatch_opts':'--nodes=1','srun_opts':'-n 1'}
# dbg_slurm_opts = {'qos':'debug',  'time_limit':'0:30:00','sbatch_opts':'--nodes=1','srun_opts':'-n 1'}
# big_slurm_opts = {'qos':'regular','time_limit':'2:00:00','sbatch_opts':'--nodes=16 --cpus-per-task=64','srun_opts':'-n 64'}
# xxl_slurm_opts = {'qos':'regular','time_limit':'2:00:00','sbatch_opts':'--nodes=32 --cpus-per-task=64','srun_opts':'-n 128'}
xxl_slurm_opts = {'qos':'regular','time_limit':'2:00:00','sbatch_opts':'--nodes=64 --cpus-per-task=64','srun_opts':'-n 256'}

### OLCF
# std_slurm_opts = {'time_limit':'1:00:00','sbatch_opts':'--nodes=1',                     'srun_opts':'-n 1'}
# # 32 nodes x 16 cpus-per-task => 2 tasks per node on andes' 32-core nodes
# # big_slurm_opts = {'time_limit':'2:00:00','sbatch_opts':'--nodes=32 --cpus-per-task=16','srun_opts':'-n 64'}
# # 48 nodes x 16 cpus-per-task => 2 tasks per node on andes' 32-core nodes
# # big_slurm_opts = {'time_limit':'4:00:00','sbatch_opts':'--nodes=48 --cpus-per-task=16','srun_opts':'-n 96'}
# big_slurm_opts = {'time_limit':'12:00:00','sbatch_opts':'--nodes=64 --cpus-per-task=16','srun_opts':'-n 128'}
# # xxl_slurm_opts = {'time_limit':'4:00:00','sbatch_opts':'--nodes=256 --cpus-per-task=32','srun_opts':'-n 256'} # one task per node on OLCF Andes
# xxl_slurm_opts = {'time_limit':'12:00:00','sbatch_opts':'--nodes=256 --cpus-per-task=32','srun_opts':'-n 256'} # one task per node on OLCF Andes

# add_grid(id='00', **std_slurm_opts, name='0.5x0.5_AVHRR',                       file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_AVHRR_c110228.nc' )
# add_grid(id='01', **std_slurm_opts, name='0.5x0.5_MODIS',                       file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_MODIS_c110228.nc' )
# add_grid(id='02', **std_slurm_opts, name='3minx3min_LandScan2004',              file=f'{src_grid_root}/SCRIPgrid_3minx3min_LandScan2004_c120517.nc' )
# add_grid(id='03', **std_slurm_opts, name='3minx3min_MODIS',                     file=f'{src_grid_root}/SCRIPgrid_3minx3min_MODIS_c110915.nc' )
# add_grid(id='04', **std_slurm_opts, name='3x3_USGS',                            file=f'{src_grid_root}/SCRIPgrid_3x3_USGS_c120912.nc' )
# add_grid(id='05', **std_slurm_opts, name='5x5min_nomask',                       file=f'{src_grid_root}/SCRIPgrid_5x5min_nomask_c110530.nc' )
# add_grid(id='06', **std_slurm_opts, name='5x5min_IGBP-GSDP',                    file=f'{src_grid_root}/SCRIPgrid_5x5min_IGBP-GSDP_c110228.nc' )
# add_grid(id='07', **std_slurm_opts, name='5x5min_ISRIC-WISE',                   file=f'{src_grid_root}/SCRIPgrid_5x5min_ISRIC-WISE_c111114.nc' )
# add_grid(id='08', **std_slurm_opts, name='10x10min_nomask',                     file=f'{src_grid_root}/SCRIPgrid_10x10min_nomask_c110228.nc' )
# add_grid(id='09', **std_slurm_opts, name='10x10min_IGBPmergeICESatGIS',         file=f'{src_grid_root}/SCRIPgrid_10x10min_IGBPmergeICESatGIS_c110818.nc' )
# add_grid(id='10', **std_slurm_opts, name='3minx3min_GLOBE-Gardner',             file=f'{src_grid_root}/SCRIPgrid_3minx3min_GLOBE-Gardner_c120922.nc' )
# add_grid(id='11', **std_slurm_opts, name='3minx3min_GLOBE-Gardner-mergeGIS',    file=f'{src_grid_root}/SCRIPgrid_3minx3min_GLOBE-Gardner-mergeGIS_c120922.nc' )
# add_grid(id='12', **std_slurm_opts, name='0.9x1.25_GRDC',                       file=f'{src_grid_root}/SCRIPgrid_0.9x1.25_GRDC_c130307.nc' )
# add_grid(id='13', **std_slurm_opts, name='360x720_cruncep',                     file=f'{src_grid_root}/SCRIPgrid_360x720_cruncep_c120830.nc' )
add_grid(id='14', **xxl_slurm_opts, name='1km-merge-10min_HYDRO1K-merge-nomask',file=f'{src_grid_root}/SCRIPgrid_1km-merge-10min_HYDRO1K-merge-nomask_c20200415.nc' )
# add_grid(id='15', **std_slurm_opts, name='0.5x0.5_GSDTG2000',                   file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_GSDTG2000_c240125.nc' )

# add_grid(id='16', **std_slurm_opts, name='0.1x0.1_nomask',                      file=f'{src_grid_root}/SCRIPgrid_0.1x0.1_nomask_c110712.nc' )
# add_grid(id='17', **xxl_slurm_opts, name='0.01x0.01_nomask',                    file=f'{src_grid_root}/SCRIPgrid_0.01x0.01_nomask_c250510.nc' )

# add_grid(id='16', **std_slurm_opts, name='0.1x0.1_nomask',                      file=f'{src_grid_root}/SCRIPgrid_0.1x0.1_nomask_c20260731.nc' ) # newer versions created at OLCF when PM was down
# add_grid(id='17', **xxl_slurm_opts, name='0.01x0.01_nomask',                    file=f'{src_grid_root}/SCRIPgrid_0.01x0.01_nomask_c20260731.nc' ) # newer versions created at OLCF when PM was down

#---------------------------------------------------------------------------------------------------
def get_batch_script_text( opts, tmp_root ):
    global account, output_root, dst_grid_name, dst_grid_file
    src_grid_file = opts['file']
    src_grid_name = opts['name']
    map_file = f'{output_root}/map_{src_grid_name}_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
    # map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --64bit_offset'
    map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --netcdf4'
    # allow grids to override slurm job defaults
    # qos                 = opts.get('qos',                   'regular')
    time_limit          = opts.get('time_limit',            '01:00:00')
    sbatch_opts         = opts.get('sbatch_opts',           '--nodes=1')
    srun_opts           = opts.get('srun_opts',             '-n 1')
    slurm_mach_specific_opts = ''
    slurm_mach_specific_opts += (f'\n#SBATCH --qos={qos}'                if qos is not None else '')
    slurm_mach_specific_opts += (f'\n#SBATCH --constraint={constraint}'  if constraint is not None else '')
    # bash, not sh - the unified loader sourced below refuses to run without
    # $BASH_VERSION, and it is only bash here by virtue of /bin/sh being a
    # symlink to it
    return f'''#!/bin/bash
#SBATCH --account={account} {slurm_mach_specific_opts}
#SBATCH --output={proj_root}/logs_slurm/slurm-%x-%j.out
#SBATCH --time={time_limit}
#SBATCH {sbatch_opts}
#SBATCH --mail-user={mail_user}
#SBATCH --mail-type={mail_type}
cd {tmp_root}
source {unified_src}
# # verify the ESMF resolved here can actually be launched in parallel by srun.
# # The job's environment is what matters, not the one this script was written
# # from, so this has to run after the source above and before the srun below.
# PYTHONPATH={taos_root} python3 -c 'from taos.util import check_esmf_rwg; check_esmf_rwg()' || exit 1
{job_env}srun {srun_opts} ESMF_RegridWeightGen {map_opts} -s {src_grid_file} -d {dst_grid_file}  -w {map_file}
'''

#---------------------------------------------------------------------------------------------------
def human_readable_size(path):
    size = os.path.getsize(path)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        unit_str = unit
        if unit=='GB': unit_str += '*'
        if unit=='TB': unit_str += '*'
        if size < 1024: return f"{size:6.1f} {unit_str}"
        size /= 1024
#---------------------------------------------------------------------------------------------------
# loop through source grids to print summary and grid file sizes
indent = ' '*2
print(f'\n{indent}Source Grid Files:')
for n,opts in enumerate(grid_opt_list):
    src_grid_file = opts['file']
    print(f'{indent}  {human_readable_size(src_grid_file):12}  {clr.CYAN}{src_grid_file}{clr.END}')
# exit()
#---------------------------------------------------------------------------------------------------
# loop through source grids and build a batch script to create the map
for n,opts in enumerate(grid_opt_list):
    src_grid_id   = opts['id']
    # src_grid_name = opts['name']
    # src_grid_file = opts['file']
    # map_file = f'{output_root}/map_{src_grid_name}_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
    # map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --64bit_offset'
    #-----------------------------------------------------------------------------
    # create to a dedicated tmp directory for each grid to avoid overwriting logs and temp files
    tmp_root = f'{output_root}/esmf_tmp_{src_grid_id}'
    os.makedirs(tmp_root, exist_ok=True)
    batch_script_text = get_batch_script_text(opts,tmp_root)
    #-----------------------------------------------------------------------------
    # Write the batch script
    batch_script_path = f'{output_root}/generate_fsurdat_map_{dst_grid_name}_{src_grid_id}.sh'
    file = open(batch_script_path,'w')
    file.write(batch_script_text)
    file.close()
    #-----------------------------------------------------------------------------
    # Submit the batch job
    job_name = f'generate_fsurdat_map_{dst_grid_name}_{src_grid_id}'
    cmd = f'sbatch --job-name={job_name}  {batch_script_path}'
    print(cmd)
    run_cmd(cmd)
print()
#---------------------------------------------------------------------------------------------------
