#!/usr/bin/env python3
import os
from taos import taos_config
#---------------------------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END); os.system(cmd); return
#---------------------------------------------------------------------------------------------------
proj_dir        = pathlib.Path(__file__).parent
taos_cfg        = taos_config(proj_dir / 'project.yaml')
timestamp       = taos_cfg.get('project.timestamp')
DIN_LOC_ROOT    = taos_cfg.get('paths.DIN_LOC_ROOT')
data_root       = taos_cfg.get('derived.data_root')
fsurdat_root    = f'{data_root}/files_fsurdat'
dst_grid_name   = f'STRONG-CA-32x5-v1'
namelist_file   = f'{fsurdat_root}/fsurdat_namelist_{dst_grid_name}'
#---------------------------------------------------------------------------------------------------
def main():
  print(f'\n  writing fsurdat namelist data to file: {clr.CYAN}{namelist_file}{clr.END}')
  file = open(namelist_file,'w')
  file.write(namelist_txt)
  file.close()
  print('\n  done.\n')
#---------------------------------------------------------------------------------------------------
namelist_txt=f'''&elmexp
 nglcec            = 0
 mksrf_fgrid       = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fpft          = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fglacier      = '{fsurdat_root}/map_3minx3min_GLOBE-Gardner_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fsoicol       = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fsoiord       = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_furban        = '{fsurdat_root}/map_3minx3min_LandScan2004_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fmax          = '{fsurdat_root}/map_3x3_USGS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_forganic      = '{fsurdat_root}/map_5x5min_ISRIC-WISE_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_flai          = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fharvest      = '{fsurdat_root}/map_0.5x0.5_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_flakwat       = '{fsurdat_root}/map_3minx3min_MODIS_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fwetlnd       = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fvocef        = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fsoitex       = '{fsurdat_root}/map_5x5min_IGBP-GSDP_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_furbtopo      = '{fsurdat_root}/map_10x10min_nomask_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_flndtopo      = '{fsurdat_root}/map_10x10min_nomask_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fgdp          = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fpeat         = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fabm          = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_ftopostats    = '{fsurdat_root}/map_1km-merge-10min_HYDRO1K-merge-nomask_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fvic          = '{fsurdat_root}/map_0.9x1.25_GRDC_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fch4          = '{fsurdat_root}/map_360x720_cruncep_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fphosphorus   = '{fsurdat_root}/map_0.5x0.5_GSDTG2000_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fgrvl         = '{fsurdat_root}/map_5x5min_ISRIC-WISE_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fslp10        = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 map_fero          = '{fsurdat_root}/map_0.5x0.5_AVHRR_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 mksrf_fsoitex     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_soitex.10level.c010119.nc'
 mksrf_forganic    = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_organic_10level_5x5min_ISRIC-WISE-NCSCD_nlev7_c120830.nc'
 mksrf_flakwat     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_LakePnDepth_3x3min_simyr2004_c111116.nc'
 mksrf_fwetlnd     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_lanwat.050425.nc'
 mksrf_fmax        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_fmax_3x3min_USGS_c120911.nc'
 mksrf_fglacier    = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_glacier_3x3min_simyr2000.c120926.nc'
 mksrf_fvocef      = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_vocef_0.5x0.5_simyr2000.c110531.nc'
 mksrf_furbtopo    = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_topo.10min.c080912.nc'
 mksrf_flndtopo    = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/topodata_10min_USGS_071205.nc'
 mksrf_fgdp        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_gdp_0.5x0.5_AVHRR_simyr2000.c130228.nc'
 mksrf_fpeat       = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_peatf_0.5x0.5_AVHRR_simyr2000.c130228.nc'
 mksrf_fabm        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_abm_0.5x0.5_AVHRR_simyr2000.c130201.nc'
 mksrf_ftopostats  = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_topostats_1km-merge-10min_HYDRO1K-merge-nomask_simyr2000.c130402.nc'
 mksrf_fvic        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_vic_0.9x1.25_GRDC_simyr2000.c130307.nc'
 mksrf_fch4        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_ch4inversion_360x720_cruncep_simyr2000.c130322.nc'
 outnc_double      = .true.
 all_urban         = .false.
 no_inlandwet      = .true.
 mksrf_furban      = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_urban_0.05x0.05_simyr2000.c120621.nc'
 mksrf_fphosphorus = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_soilphos_0.5x0.5_simyr1850.c170623.nc'
 mksrf_fgrvl       = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_gravel_10level_5min.c190603.nc'
 mksrf_fslp10      = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_slope_10p_0.5x0.5.c190603.nc'
 mksrf_fero        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_soilero_0.5x0.5.c220523.nc'
 mksrf_fvegtyp     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/LUT_LUH2_HIST_LUH1f_07082020/LUT_LUH2_historical_2015_c07082020.nc'
 mksrf_fsoicol     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/pftlandusedyn.0.5x0.5.simyr1850-2005.c090630/mksrf_soilcol_global_c090324.nc'
 mksrf_fsoiord     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/pftlandusedyn.0.5x0.5.simyr1850-2005.c090630/mksrf_soilord_global_c150313.nc'
 mksrf_flai        = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/pftlandusedyn.0.5x0.5.simyr1850-2005.c090630/mksrf_lai_global_c090506.nc'
 mksrf_ftoprad     = '{DIN_LOC_ROOT}/lnd/clm2/rawdata/mksrf_toprad_0.1x0.1.c231218.nc'
 map_ftoprad       = '{fsurdat_root}/map_0.1x0.1_nomask_to_{dst_grid_name}_nomask_aave_da_{timestamp}.nc'
 fsurdat           = 'surfdata_{dst_grid_name}_{timestamp}.nc'
 fsurlog           = 'surfdata_{dst_grid_name}_{timestamp}.log'
 mksrf_fdynuse     = ' '
 fdyndat           = ' '
 outnc_large_files = .true.

/
'''

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  main()
#---------------------------------------------------------------------------------------------------