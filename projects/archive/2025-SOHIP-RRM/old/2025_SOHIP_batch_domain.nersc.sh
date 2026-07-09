#!/bin/bash
#SBATCH --account=m4842
#SBATCH --constraint=cpu
#SBATCH --qos=regular
#SBATCH --job-name=SOHIP_generate_domain
#SBATCH --output=/global/homes/w/whannah/E3SM/logs_slurm/gen_topo_SOHIP_slurm-%x-%j.out
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --mail-type=END,FAIL
#-------------------------------------------------------------------------------
# grid_name=2025-sohip-256x3-ptgnia-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
# grid_name=2025-sohip-256x3-sw-ind-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
# grid_name=2025-sohip-256x3-se-pac-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
# grid_name=2025-sohip-256x3-sc-pac-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
# grid_name=2025-sohip-256x3-eq-ind-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
# grid_name=2025-sohip-256x3-sc-ind-v1; sbatch --job-name=gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM/batch_scripts/2025_SOHIP_domain_batch.sh
#-------------------------------------------------------------------------------
timestamp=20251001

slurm_log_root=/global/homes/w/whannah/E3SM/logs_slurm
# slurm_log_create_grid=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.create_grid.out
# slurm_log_cttrmp_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.cttrmp_topo.out
# slurm_log_smooth_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.smooth_topo.out
# slurm_log_cttsgh_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.cttsgh_topo.out

e3sm_root=/pscratch/sd/w/whannah/tmp_e3sm_src
data_root=/global/cfs/cdirs/m4842/whannah
grid_root=${data_root}/files_grid
maps_root=${data_root}/files_map
domain_root=${data_root}/files_domain

DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata

#-------------------------------------------------------------------------------  
# print some useful things
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------; echo
# echo "   create_grid         = ${create_grid}"
# echo "   cttrmp_topo         = ${cttrmp_topo}"
# echo "   smooth_topo         = ${smooth_topo}"
# echo "   cttsgh_topo         = ${cttsgh_topo}"; echo
echo "   grid_name           = ${grid_name}"; echo
echo "   e3sm_root           = $e3sm_root"
echo "   grid_root           = $grid_root"
echo "   maps_root           = $maps_root"
echo "   domain_root         = $domain_root"
echo "   DIN_LOC_ROOT        = $DIN_LOC_ROOT"; echo
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if [ -z "${grid_name}" ]; then echo -e ${RED}ERROR: grid_name is not defined${NC}; exit ; fi
#-------------------------------------------------------------------------------
# Make sure paths exist
if [ ! -d ${DIN_LOC_ROOT} ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${DIN_LOC_ROOT} ; fi
if [ ! -d ${e3sm_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${e3sm_root} ; fi
if [ ! -d ${grid_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${grid_root} ; fi
if [ ! -d ${maps_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${maps_root} ; fi
if [ ! -d ${domain_root}  ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${domain_root} ; fi
#-------------------------------------------------------------------------------
# ANSI color codes for highlighting terminal output
RED='\033[0;31m' ; GRN='\033[0;32m' CYN='\033[0;36m' ; NC='\033[0m'
# start timer for entire script
start=`date +%s`
# Stop script execution on error
set -e
#-------------------------------------------------------------------------------
echo; echo -e ${GRN} Setting up environment ${NC}; echo
#-------------------------------------------------------------------------------
unified_bin=/global/common/software/e3sm/anaconda_envs/base/envs/e3sm_unified_1.11.1_login/bin
module load python
source activate hiccup_env
# eval $(${e3sm_root}/cime/CIME/Tools/get_case_env)
# ulimit -s unlimited # required for larger grids
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

atm_grid_file=${grid_root}/${grid_name}-pg2_scrip.nc
ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/ICOS10/ocean.ICOS10.scrip.211015.nc
map_file=${maps_root}/map_ICOS10_to_${grid_name}-pg2_traave.${timestamp}.nc

echo atm_file : $atm_grid_file
echo ocn_file : $ocn_grid_file
echo MAP_FILE : $map_file

ncremap -a traave --src_grd=${ocn_grid_file} --dst_grd=${atm_grid_file} --map_file=${map_file}

python ${e3sm_root}/tools/generate_domain_files/generate_domain_files_E3SM.py \
-m ${map_file} -o ICOS10 -l ${grid_name} --date-stamp=${timestamp} --output-root=${domain_root}

#-------------------------------------------------------------------------------
# # Check that files were created
# chk_file1=${domain_root}/domain.ocn.${grid_name}_ICOS10.${timestamp}.nc
# chk_file2=${domain_root}/domain.lnd.${grid_name}_ICOS10.${timestamp}.nc
# if [ ! -f ${map_file} ]; then
#   echo
#   echo -e ${RED} Failed to create map file - Errors ocurred ${NC}
#   echo
# elif [ ! -f ${chk_file1} ]; then
#   echo
#   echo -e ${RED} Failed to create domain file - Errors ocurred ${NC}
#   echo
# fi
#-------------------------------------------------------------------------------
# Indicate overall run time for this script
end=`date +%s`
runtime_sc=$(( end - start ))
runtime_mn=$(( runtime_sc/60 ))
runtime_hr=$(( runtime_mn/60 ))
echo -e    ${CYN} overall runtime: ${NC} ${runtime_sc} seconds / ${runtime_mn} minutes / ${runtime_hr} hours
echo
#-------------------------------------------------------------------------------
