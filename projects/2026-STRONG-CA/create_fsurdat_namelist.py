#!/usr/bin/env python3
import os
#---------------------------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END); os.system(cmd); return
#---------------------------------------------------------------------------------------------------

DIN_LOC_ROOT  = '/global/cfs/cdirs/e3sm/inputdata'
USR_MAPDIR    = '/global/cfs/cdirs/m5277/whannah/2026-STRONG-CA/files_fsurdat'
HGRID_NAME    = f'STRONG-CA-32x5-v1'
YYMMDD        = '20260505'

namelist_file = f'{USR_MAPDIR}/fsurdat_namelist_{HGRID_NAME}'
#---------------------------------------------------------------------------------------------------
def main():
  print()
  print(f'  writing fsurdat namelist data to file: {clr.CYAN}{namelist_file}{clr.END}')
  file = open(namelist_file,'w')
  file.write(namelist_txt)
  file.close()
  print()
  print('  done.')
  print()
#---------------------------------------------------------------------------------------------------
namelist_txt=f'''&elmexp
 nglcec            = 0
 mksrf_fgrid       = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fpft          = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fglacier      = '{USR_MAPDIR}/map_3minx3min_GLOBE-Gardner_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fsoicol       = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fsoiord       = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_furban        = '{USR_MAPDIR}/map_3minx3min_LandScan2004_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fmax          = '{USR_MAPDIR}/map_3x3_USGS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_forganic      = '{USR_MAPDIR}/map_5x5min_ISRIC-WISE_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_flai          = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fharvest      = '{USR_MAPDIR}/map_0.5x0.5_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_flakwat       = '{USR_MAPDIR}/map_3minx3min_MODIS_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fwetlnd       = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fvocef        = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fsoitex       = '{USR_MAPDIR}/map_5x5min_IGBP-GSDP_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_furbtopo      = '{USR_MAPDIR}/map_10x10min_nomask_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_flndtopo      = '{USR_MAPDIR}/map_10x10min_nomask_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fgdp          = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fpeat         = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fabm          = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_ftopostats    = '{USR_MAPDIR}/map_1km-merge-10min_HYDRO1K-merge-nomask_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fvic          = '{USR_MAPDIR}/map_0.9x1.25_GRDC_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fch4          = '{USR_MAPDIR}/map_360x720_cruncep_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fphosphorus   = '{USR_MAPDIR}/map_0.5x0.5_GSDTG2000_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fgrvl         = '{USR_MAPDIR}/map_5x5min_ISRIC-WISE_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fslp10        = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 map_fero          = '{USR_MAPDIR}/map_0.5x0.5_AVHRR_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
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
 map_ftoprad       = '{USR_MAPDIR}/map_0.1x0.1_nomask_to_{HGRID_NAME}_nomask_aave_da_{YYMMDD}.nc'
 fsurdat           = 'surfdata_{HGRID_NAME}_{YYMMDD}.nc'
 fsurlog           = 'surfdata_{HGRID_NAME}_{YYMMDD}.log'
 mksrf_fdynuse     = ' '
 fdyndat           = ' '
 outnc_large_files = .true.

/
'''

#---------------------------------------------------------------------------------------------------
if __name__ == '__main__':
  main()
#---------------------------------------------------------------------------------------------------