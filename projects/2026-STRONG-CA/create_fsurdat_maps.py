#!/usr/bin/env python3
import os
#---------------------------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END); os.system(cmd); return
#---------------------------------------------------------------------------------------------------
# usage = '''
# python create_fsurdat_maps.py --grid_root     <grid_root> 
#                               --dst_grid_name <dst_grid_name>
#                               --dst_grid_file <dst_grid_file>
#                               --datestamp     <datestamp>
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
# # Make sure E3SM unified env is activated
# E3SMU_SCRIPT = os.getenv('E3SMU_SCRIPT')
# if E3SMU_SCRIPT is None:
#     raise ValueError('ERROR - This tool requires the E3SM unified environement to active')
#---------------------------------------------------------------------------------------------------

allocation = 'm5277'
datestamp  = 20260505

proj_root = '/global/homes/w/whannah/E3SM_grid_support/projects/2026-STRONG'

grid_root = '/global/cfs/cdirs/m5277/whannah/2026-STRONG-CA/files_grid'
maps_root = '/global/cfs/cdirs/m5277/whannah/2026-STRONG-CA/files_fsurdat'

src_grid_root='/global/cfs/cdirs/e3sm/inputdata/lnd/clm2/mappingdata/grids'

dst_grid_name = f'STRONG-CA-32x5-v1'
dst_grid_file = f'{grid_root}/{dst_grid_name}-pg2_scrip.nc'

#---------------------------------------------------------------------------------------------------
grid_opt_list = []
def add_grid( **kwargs ):
    case_opts = {}
    for k, val in kwargs.items(): case_opts[k] = val
    grid_opt_list.append(case_opts)
#---------------------------------------------------------------------------------------------------
# build list of source grids

std_slurm_opts = {'qos':'regular','time_limit':'1:00:00','num_nodes':1}
# dbg_slurm_opts = {'qos':'debug',  'time_limit':'0:30:00','num_nodes':1}
big_slurm_opts = {'qos':'regular','time_limit':'2:00:00','num_nodes':32,'cpus_per_task':16}

add_grid(id='00', **std_slurm_opts, name='0.5x0.5_AVHRR',                       file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_AVHRR_c110228.nc' )
add_grid(id='01', **std_slurm_opts, name='0.5x0.5_MODIS',                       file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_MODIS_c110228.nc' )
add_grid(id='02', **std_slurm_opts, name='3minx3min_LandScan2004',              file=f'{src_grid_root}/SCRIPgrid_3minx3min_LandScan2004_c120517.nc' )
add_grid(id='03', **std_slurm_opts, name='3minx3min_MODIS',                     file=f'{src_grid_root}/SCRIPgrid_3minx3min_MODIS_c110915.nc' )
add_grid(id='04', **std_slurm_opts, name='3x3_USGS',                            file=f'{src_grid_root}/SCRIPgrid_3x3_USGS_c120912.nc' )
add_grid(id='05', **std_slurm_opts, name='5x5min_nomask',                       file=f'{src_grid_root}/SCRIPgrid_5x5min_nomask_c110530.nc' )
add_grid(id='06', **std_slurm_opts, name='5x5min_IGBP-GSDP',                    file=f'{src_grid_root}/SCRIPgrid_5x5min_IGBP-GSDP_c110228.nc' )
add_grid(id='07', **std_slurm_opts, name='5x5min_ISRIC-WISE',                   file=f'{src_grid_root}/SCRIPgrid_5x5min_ISRIC-WISE_c111114.nc' )
add_grid(id='08', **std_slurm_opts, name='10x10min_nomask',                     file=f'{src_grid_root}/SCRIPgrid_10x10min_nomask_c110228.nc' )
add_grid(id='09', **std_slurm_opts, name='10x10min_IGBPmergeICESatGIS',         file=f'{src_grid_root}/SCRIPgrid_10x10min_IGBPmergeICESatGIS_c110818.nc' )
add_grid(id='10', **std_slurm_opts, name='3minx3min_GLOBE-Gardner',             file=f'{src_grid_root}/SCRIPgrid_3minx3min_GLOBE-Gardner_c120922.nc' )
add_grid(id='11', **std_slurm_opts, name='3minx3min_GLOBE-Gardner-mergeGIS',    file=f'{src_grid_root}/SCRIPgrid_3minx3min_GLOBE-Gardner-mergeGIS_c120922.nc' )
add_grid(id='12', **std_slurm_opts, name='0.9x1.25_GRDC',                       file=f'{src_grid_root}/SCRIPgrid_0.9x1.25_GRDC_c130307.nc' )
add_grid(id='13', **std_slurm_opts, name='360x720_cruncep',                     file=f'{src_grid_root}/SCRIPgrid_360x720_cruncep_c120830.nc' )
add_grid(id='14', **big_slurm_opts, name='1km-merge-10min_HYDRO1K-merge-nomask',file=f'{src_grid_root}/SCRIPgrid_1km-merge-10min_HYDRO1K-merge-nomask_c20200415.nc' )
add_grid(id='15', **std_slurm_opts, name='0.5x0.5_GSDTG2000',                   file=f'{src_grid_root}/SCRIPgrid_0.5x0.5_GSDTG2000_c240125.nc' )
add_grid(id='16', **std_slurm_opts, name='0.1x0.1_nomask',                      file=f'{src_grid_root}/SCRIPgrid_0.1x0.1_nomask_c110712.nc' )
add_grid(id='17', **big_slurm_opts, name='0.01x0.01_nomask',                    file=f'{src_grid_root}/SCRIPgrid_0.01x0.01_nomask_c250510.nc' )

#---------------------------------------------------------------------------------------------------
def get_host():
    host = None
    if os.path.exists('/global/cfs'): host = 'nersc'
    if os.path.exists('/lcrc')      : host = 'lcrc'
    if host is None: raise ValueError('ERROR: supported host not found')
    return host
#---------------------------------------------------------------------------------------------------
def get_unified_source():
    host = get_host()
    unified_source = None
    if host=='nersc': unified_source = '/global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh'
    if host=='lcrc' : unified_source = '/lcrc/soft/climate/e3sm-unified/load_latest_e3sm_unified_chrysalis.sh'
    if unified_source is None: raise ValueError('ERROR: path for E3SM unified environment not found')
    return unified_source
#---------------------------------------------------------------------------------------------------
def get_batch_script_text( opts ):
    global allocation, maps_root, dst_grid_name, dst_grid_file
    src_grid_id   = opts['id']
    src_grid_file = opts['file']
    src_grid_name = opts['name']
    map_file = f'{maps_root}/map_{src_grid_name}_to_{dst_grid_name}_nomask_aave_da_{datestamp}.nc'
    # map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --64bit_offset'
    map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --netcdf4'
    # create to a dedicated tmp directory for each grid to avoid overwriting logs and temp files
    tmp_root = f'{maps_root}/esmf_tmp_{src_grid_id}'
    os.makedirs(tmp_root, exist_ok=True)
    # allow grids to override slurm job defaults
    qos                 = opts.get('qos',                   'regular')
    time_limit          = opts.get('time_limit',            '01:00:00')
    num_nodes           = opts.get('num_nodes',             1)
    cpus_per_task       = opts.get('cpus_per_task',         1)
    # num_tasks_per_node  = opts.get('num_tasks_per_node',    64)
    return f'''#!/bin/sh
#SBATCH --account={allocation}
#SBATCH --constraint=cpu
#SBATCH --qos={qos}
#SBATCH --output={proj_root}/logs_slurm/slurm-%x-%j.out
#SBATCH --time={time_limit}
#SBATCH --nodes={num_nodes}
#SBATCH --cpus-per-task={cpus_per_task}
#SBATCH --mail-type=END,FAIL
cd {tmp_root}
source {get_unified_source()}
srun ESMF_RegridWeightGen {map_opts} -s {src_grid_file} -d {dst_grid_file}  -w {map_file} 
'''
# --ntasks=64
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
    # map_file = f'{maps_root}/map_{src_grid_name}_to_{dst_grid_name}_nomask_aave_da_{datestamp}.nc'
    # map_opts = f'-m conserve --ignore_unmapped --src_type SCRIP --dst_type SCRIP --64bit_offset'
    #-----------------------------------------------------------------------------
    # Write the batch script
    batch_script_path = f'{maps_root}/generate_fsurdat_map_{dst_grid_name}_{src_grid_id}.sh'
    file = open(batch_script_path,'w')
    # file.write(get_batch_script_text(map_opts,src_grid_file,dst_grid_file,map_file))
    file.write(get_batch_script_text(opts))
    file.close()
    #-----------------------------------------------------------------------------
    # Submit the batch job
    job_name = f'generate_fsurdat_map_{dst_grid_name}_{src_grid_id}'
    cmd = f'sbatch --job-name={job_name}  {batch_script_path}'
    run_cmd(cmd)
print()
#---------------------------------------------------------------------------------------------------
