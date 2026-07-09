#!/usr/bin/env python
import os,glob,subprocess as sp
#---------------------------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END) ; os.system(cmd); return
#-------------------------------------------------------------------------------
nersc_data_root = '/global/cfs/cdirs/m4842/whannah'
lcrc_data_root = '/lcrc/group/e3sm/ac.whannah/scratch/chrys/SOHIP'
data_root = None
if os.path.exists(nersc_data_root): data_root = nersc_data_root
if os.path.exists(lcrc_data_root): data_root = lcrc_data_root
if data_root is None: raise ValueError('root path not found!')
#-------------------------------------------------------------------------------

grid_list = []
grid_list.append('2025-sohip-256x3-ptgnia-v1')
grid_list.append('2025-sohip-256x3-sw-ind-v1')
grid_list.append('2025-sohip-256x3-se-pac-v1')
grid_list.append('2025-sohip-256x3-sc-pac-v1')
grid_list.append('2025-sohip-256x3-eq-ind-v1')
grid_list.append('2025-sohip-256x3-sc-ind-v1')

file_type_list = []
# file_type_list.append('grid')
file_type_list.append('map')
# file_type_list.append('domain')
# file_type_list.append('topo')
# file_type_list.append('fsurdat')
# file_type_list.append('atmsrf')
# file_type_list.append('init')



#-------------------------------------------------------------------------------
for grid_name in grid_list:
  print('-'*80)
  print(f'  grid_name: {clr.CYAN}{grid_name}{clr.END}')
  for file_type in file_type_list:
    file_path = f'{data_root}/files_{file_type}/*{grid_name}*'
    print(' '*4+f'Checking file type: {clr.GREEN}{file_type}{clr.END}')
    file_list = sorted(glob.glob(file_path))
    if len(file_list)>0:
      for f in file_list: print(' '*6+f)
    else:
      print(' '*6+f'{clr.RED}no files found{clr.END}')
  print()
  