import os
#---------------------------------------------------------------------------------------------------
class tcolor: END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
#---------------------------------------------------------------------------------------------------
def run_cmd(cmd,suppress_output=False):
  if suppress_output : cmd = cmd + ' > /dev/null'
  msg = tcolor.GREEN + cmd + tcolor.END ; print(f'\n{msg}')
  os.system(cmd); return
#---------------------------------------------------------------------------------------------------
opt_list = []
def add_grid( **kwargs ):
  grid_opts = {}
  for k, val in kwargs.items(): grid_opts[k] = val
  opt_list.append(grid_opts)
#---------------------------------------------------------------------------------------------------

# add_grid(region='patagonia', base_res=32, lat_ref=-50, lon_ref=-60, rlat1=-55, rlat2=-42, rlon1=-92,  rlon2=-48 )

# add_grid(region='patagonia', base_res=256, lat_ref=-50, lon_ref=-60, rlat1=-55, rlat2=-42, rlon1=-92,  rlon2=-48 )
# add_grid(region='sw-ind',    base_res=256, dy=10, dx=20, lat_ref=-50, lon_ref=40 )
# add_grid(region='se-pac',    base_res=256, dy=10, dx=20, lat_ref=-50, lon_ref=-100 )
# add_grid(region='sc-pac',    base_res=256, dy=10, dx=20, lat_ref=-35, lon_ref=-135 )
# add_grid(region='sc-ind',    base_res=256, dy=10, dx=20, lat_ref=-50,  lon_ref=65 )
# add_grid(region='eq-ind',    base_res=256, dy=10, dx=20, lat_ref= -5,  lon_ref=75 ) # v1
# add_grid(region='eq-ind-v2', base_res=256, dy=10, dx=18, lat_ref= -5,  lon_ref=75 ) # v2


add_grid(region='ptgnia-v1',base_res=256, lat_ref=-50, lon_ref=-60, rlat1=-55, rlat2=-42, rlon1=-92,  rlon2=-48 )
add_grid(region='sw-ind-v1',base_res=256, dy=10, dx=20, lat_ref=-50, lon_ref=40 )
add_grid(region='se-pac-v1',base_res=256, dy=10, dx=20, lat_ref=-50, lon_ref=-100 )
add_grid(region='sc-pac-v1',base_res=256, dy=10, dx=20, lat_ref=-35, lon_ref=-135 )
add_grid(region='eq-ind-v1',base_res=256, dy=10, dx=18, lat_ref= -5, lon_ref=75 )
add_grid(region='sc-ind-v1',base_res=256, dy=10, dx=20, lat_ref=-50, lon_ref=65 )

# GRID_ROOT = '/global/cfs/cdirs/m4842/whannah/files_grid'
GRID_ROOT = '/lcrc/group/e3sm/ac.whannah/scratch/chrys/E3SM_grid_support/2025-SOHIP-RRM/files_grid'

#---------------------------------------------------------------------------------------------------
def main(opts):
  global GRID_ROOT

  # BASE_RES=256
  BASE_RES=opts['base_res']
  
  # REFINE_LVL=3
  REFINE_LVL=2
  SDIST=3
  SITER=20

  REFINE_NAME = opts['region']

  LAT_REF = opts['lat_ref']
  LON_REF = opts['lon_ref']

  if 'dy' in opts:
    RLAT1 = opts['lat_ref'] - opts['dy']
    RLAT2 = opts['lat_ref'] + opts['dy']

  if 'dx' in opts:
    RLON1 = opts['lon_ref'] - opts['dx']
    RLON2 = opts['lon_ref'] + opts['dx']

  if 'rlat1' in opts: RLAT1 = opts['rlat1']
  if 'rlat2' in opts: RLAT2 = opts['rlat2']
  if 'rlon1' in opts: RLON1 = opts['rlon1']
  if 'rlon2' in opts: RLON2 = opts['rlon2']

  GRID_NAME = f'2025-sohip-{BASE_RES}x{REFINE_LVL}-{REFINE_NAME}'

  #-----------------------------------------------------------------------------
  # print()
  # print('-'*120)
  print()
  # print(f'  GRID_ROOT : {GRID_ROOT}')
  print(f'  GRID_NAME : {GRID_NAME}')
  # print(f'  BASE_RES  : {BASE_RES}')
  # print(f'  REFINE_LVL: {REFINE_LVL}')
  # print(f'  SDIST     : {SDIST}')
  # print(f'  SITER     : {SITER}')
  # print(f'  LAT_REF   : {LAT_REF}')
  # print(f'  LON_REF   : {LON_REF}')
  print(f'  RLAT1     : {RLAT1}')
  print(f'  RLAT2     : {RLAT2}')
  print(f'  RLON1     : {RLON1}')
  print(f'  RLON2     : {RLON2}')
  # print()
  # exit()
  return
  #-----------------------------------------------------------------------------

  cmd = f'SQuadGen'
  cmd+= f' --refine_rect {RLON1},{RLAT1},{RLON2},{RLAT2},{REFINE_LVL}'
  cmd+= f' --lon_ref {LON_REF} --lat_ref {LAT_REF} --resolution {BASE_RES}'
  cmd+= f' --refine_level {REFINE_LVL} --refine_type LOWCONN'
  cmd+= f' --smooth_type SPRING --smooth_dist {SDIST} --smooth_iter {SITER}'
  cmd+= f' --output {GRID_ROOT}/{GRID_NAME}.g'
  run_cmd(cmd)

  run_cmd(f'GenerateVolumetricMesh --in {GRID_ROOT}/{GRID_NAME}.g     --out {GRID_ROOT}/{GRID_NAME}-pg2.g --np 2 --uniform')
  run_cmd(f'ConvertMeshToSCRIP     --in {GRID_ROOT}/{GRID_NAME}-pg2.g --out {GRID_ROOT}/{GRID_NAME}-pg2_scrip.nc')

  print()
#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  for n in range(len(opt_list)):
    main( opt_list[n] )
#---------------------------------------------------------------------------------------------------