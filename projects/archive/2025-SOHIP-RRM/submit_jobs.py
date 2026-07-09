#!/usr/bin/env python3
import os,subprocess as sp
#-------------------------------------------------------------------------------
home = os.getenv('HOME')
script_root = os.path.realpath(__file__).replace('/submit_jobs.py','')
logs_root = f'{script_root}/logs_slurm'
#-------------------------------------------------------------------------------
def get_env_var(var):
  cmd = f'source {script_root}/set_project.sh>>/dev/null;echo ${var}'
  return sp.run(cmd,shell=True,capture_output=True,text=True,check=True).stdout.replace('\n','')
#-------------------------------------------------------------------------------
proj_root = get_env_var('proj_root')
DIN_LOC_ROOT = get_env_var('DIN_LOC_ROOT')
#-------------------------------------------------------------------------------
class clr:END,RED,GREEN,YELLOW,MAGENTA,CYAN,BOLD = '\033[0m','\033[31m','\033[32m','\033[33m','\033[35m','\033[36m','\033[1m'
def print_line():print(' '*2+'-'*80)
def run_cmd(cmd): print('\n  '+clr.GREEN+cmd+clr.END); os.system(cmd); return
#-------------------------------------------------------------------------------
grid_name_list = []
# grid_name_list.append('2025-sohip-256x3-ptgnia-v1')
# grid_name_list.append('2025-sohip-256x3-sw-ind-v1')
# grid_name_list.append('2025-sohip-256x3-eq-ind-v1')
# grid_name_list.append('2025-sohip-256x3-se-pac-v1')
# grid_name_list.append('2025-sohip-256x3-sc-pac-v1')
# grid_name_list.append('2025-sohip-256x3-sc-ind-v1')

grid_name_list.append('2025-sohip-256x2-ptgnia-v1')
grid_name_list.append('2025-sohip-256x2-sw-ind-v1')
grid_name_list.append('2025-sohip-256x2-eq-ind-v1')
grid_name_list.append('2025-sohip-256x2-se-pac-v1')
grid_name_list.append('2025-sohip-256x2-sc-pac-v1')
grid_name_list.append('2025-sohip-256x2-sc-ind-v1')

#-------------------------------------------------------------------------------
topo_args = ''
topo_args += ' --create_grid'
topo_args += ' --cttrmp_topo'
topo_args += ' --smooth_topo'
topo_args += ' --cttsgh_topo'
#-------------------------------------------------------------------------------
map_args = ''
map_args += f' --create_maps_ocn'
map_args += f' --create_maps_lnd'
#-------------------------------------------------------------------------------
for grid_name in grid_name_list:
  sbatch_common = f'sbatch'
  sbatch_common += f' --export=ALL,proj_root={proj_root}'
  sbatch_common += f',grid_name={grid_name}'
  sbatch_common += f',grid_name_pg2={grid_name}-pg2'
  sbatch_common += f' --output={logs_root}/%x-%j.slurm.main.out'
  sbatch_common += f' --account=e3sm'

  # run_cmd(f'{sbatch_common} --job-name=gen_maps_{grid_name} --time=48:00:00 {home}/E3SM_grid_support/batch_maps.sh {map_args}')
  # run_cmd(f'{sbatch_common} --job-name=gen_domn_{grid_name} --time=6:00:00  {home}/E3SM_grid_support/batch_domain.sh')
  # run_cmd(f'{sbatch_common} --job-name=gen_topo_{grid_name} --time=12:00:00 {home}/E3SM_grid_support/batch_topo.sh {topo_args}')
  run_cmd(f'{sbatch_common} --job-name=gen_topo_{grid_name} --time=12:00:00 {home}/E3SM_grid_support/batch_topo.v2.sh {topo_args}')

#-------------------------------------------------------------------------------
print_line()
# sp.run(['/bin/bash','-i','-c','qjob'],shell=False)
#-------------------------------------------------------------------------------
