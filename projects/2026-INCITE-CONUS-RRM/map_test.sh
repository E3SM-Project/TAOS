#!/bin/bash
#SBATCH --constraint=cpu
#SBATCH --account=m2637
#SBATCH --qos=regular
#SBATCH --time=8:00:00
#SBATCH --nodes=64
###SBATCH --time=1:00:00
###SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --exclusive
#SBATCH --mem=0
#SBATCH --job-name=esmfbilin_map_test
#SBATCH --output=esmfbilin_map_test.log
#SBATCH --mail-user=hannah6@llnl.gov
#SBATCH --mail-type=END,FAIL

source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh

# esmf_wgt_cmd="srun -n 512 ESMF_RegridWeightGen --pnetcdf"
# --wgt_cmd=${esmf_wgt_cmd}

SRC_GRID=/global/cfs/projectdirs/m3312/whannah/HICCUP/scrip_ERA5_721x1440.nc
DST_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid
DST_GRID=${DST_ROOT}/2026-incite-conus-1024x2-np4_scrip.nc
MAP_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map
MAP_FILE=${MAP_ROOT}/map_ERA5-721x1440_to_2026-incite-conus-1024x2-pg2_esmfbilin.20260303.nc
cmd="ncremap  -a esmfbilin --mpi_nbr=512 --src_grd=${SRC_GRID} --dst_grd=${DST_GRID} --map_file=${MAP_FILE}"


# SRC_GRID=/global/cfs/projectdirs/m3312/whannah/HICCUP/scrip_ERA5_721x1440.nc
# DST_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid
# MAP_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map
# # DST_GRID=${DST_ROOT}/2026s-incite-conus-128x2-np4_scrip.nc
# # MAP_FILE=${MAP_ROOT}/map_ERA5-721x1440_to_2026-incite-conus-128x2-pg2_esmfbilin.20260303.nc
# DST_GRID=${DST_ROOT}/ne30pg2_scrip.nc
# MAP_FILE=${MAP_ROOT}/map_ERA5-721x1440_to_ne30pg2_esmfbilin.20260303.nc
# cmd="ncremap  -a esmfbilin --mpi_nbr=16 --src_grd=${SRC_GRID} --dst_grd=${DST_GRID} --map_file=${MAP_FILE}"

echo "  $cmd" ; echo; eval "$cmd"

if [ ! -f ${MAP_FILE} ]; then echo;echo -e "${RED}  map file creation FAILED:${NC} ${MAP_FILE}"; echo; exit 1; fi
if [   -f ${MAP_FILE} ]; then echo;echo -e "${GRN}  map file creation SUCCESSFUL:${NC} ${MAP_FILE}"; echo; fi