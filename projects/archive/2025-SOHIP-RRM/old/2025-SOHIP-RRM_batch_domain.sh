#!/bin/bash
#-------------------------------------------------------------------------------
# chrysalis
#SBATCH --account=e3sm
###SBATCH --job-name=SOHIP_gen_domain
###SBATCH --output=/home/ac.whannah/E3SM_grid_support/2025-SOHIP-RRM/logs_slurm/SOHIP_gen_domain_%x_%j.slurm.out
#SBATCH --time=6:00:00
#SBATCH --nodes=1
#SBATCH --mail-user=hannah6@llnl.gov
#SBATCH --mail-type=END,FAIL
#-------------------------------------------------------------------------------
# grid_name=2025-sohip-256x3-ptgnia-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
# grid_name=2025-sohip-256x3-sw-ind-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
# grid_name=2025-sohip-256x3-se-pac-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
# grid_name=2025-sohip-256x3-sc-pac-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
# grid_name=2025-sohip-256x3-eq-ind-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
# grid_name=2025-sohip-256x3-sc-ind-v1; sbatch --job-name=SOHIP_gen_domain_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_domain.lcrc.sh
#-------------------------------------------------------------------------------
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${SCRIPT_DIR}/set_project.sh
start=`date +%s` # start timer for entire script
set -e  # Stop script execution on error
#-------------------------------------------------------------------------------
timestamp=20251006

#-------------------------------------------------------------------------------  
# print some useful things
echo --------------------------------------------------------------------------------
echo "   grid_name           = ${grid_name}"; echo
echo --------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if [ -z "${grid_name}" ]; then echo -e ${RED}ERROR: grid_name is not defined${NC}; exit ; fi
#-------------------------------------------------------------------------------
echo; echo -e ${GRN} Setting up environment ${NC}; echo
#-------------------------------------------------------------------------------
# unified_bin=/lcrc/soft/climate/e3sm-unified/base/envs/e3sm_unified_1.11.1_login/bin
# source ${home}/.bashrc
# source activate hiccup_env
source ${unified_src}
# eval $(${e3sm_src_root}/cime/CIME/Tools/get_case_env)
# ulimit -s unlimited # required for larger grids
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
#-------------------------------------------------------------------------------

# atm_grid_file=${grid_root}/${grid_name}-pg2_scrip.nc
# ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/ICOS10/ocean.ICOS10.scrip.211015.nc
# map_file=${maps_root}/map_ICOS10_to_${grid_name}-pg2_traave.${timestamp}.nc

atm_grid_file=${grid_root}/${grid_name}-pg2_scrip.nc
ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
map_file=${maps_root}/map_RRSwISC6to18E3r5_to_${grid_name}-pg2_traave.${timestamp}.nc

echo
echo atm_file : $atm_grid_file
echo ocn_file : $ocn_grid_file
echo map_file : $map_file
echo

# ncremap -a traave --src_grd=${ocn_grid_file} --dst_grd=${atm_grid_file} --map_file=${map_file}

domn_tool=${e3sm_src_root}/tools/generate_domain_files/generate_domain_files_E3SM.py
cmd="python ${domn_tool} -m ${map_file} -o RRSwISC6to18E3r5 -l ${grid_name} --date-stamp=${timestamp} --output-root=${domn_root}"

echo $cmd ; echo
eval "$cmd"

#-------------------------------------------------------------------------------
# # Check that files were created
# chk_file1=${domn_root}/domain.ocn.${grid_name}_ICOS10.${timestamp}.nc
# chk_file2=${domn_root}/domain.lnd.${grid_name}_ICOS10.${timestamp}.nc
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
