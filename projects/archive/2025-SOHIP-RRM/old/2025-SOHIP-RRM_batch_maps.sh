#!/bin/bash
#SBATCH --account=e3sm
###SBATCH --job-name=SOHIP_gen_maps
###SBATCH --output=/home/ac.whannah/E3SM_grid_support/2025-SOHIP-RRM/logs_slurm/%x-%j.slurm.out
#SBATCH --time=48:00:00
#SBATCH --nodes=1
#SBATCH --mail-user=hannah6@llnl.gov
#SBATCH --mail-type=END,FAIL
#-------------------------------------------------------------------------------
# grid_name=2025-sohip-256x3-ptgnia-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
# grid_name=2025-sohip-256x3-sw-ind-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
# grid_name=2025-sohip-256x3-se-pac-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
# grid_name=2025-sohip-256x3-sc-pac-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
# grid_name=2025-sohip-256x3-eq-ind-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
# grid_name=2025-sohip-256x3-sc-ind-v1; sbatch --job-name=gen_maps_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_maps.lcrc.sh
#-------------------------------------------------------------------------------
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${SCRIPT_DIR}/set_project.sh
start=`date +%s` # start timer for entire script
set -e  # Stop script execution on error
#-------------------------------------------------------------------------------
create_maps_ocn=true
create_maps_lnd=true
#-------------------------------------------------------------------------------
# NERSC
# home=/global/homes/w/whannah
# # data_root=/global/cfs/cdirs/e3sm/whannah
# data_root=/global/cfs/cdirs/m4842/whannah
# DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
#-------------------------------------------------------------------------------
# LCRC
home=/home/ac.whannah
data_root=/lcrc/group/e3sm/ac.whannah/scratch/chrys/SOHIP
DIN_LOC_ROOT=/lcrc/group/e3sm/data/inputdata
#-------------------------------------------------------------------------------
timestamp=20251006

slurm_log_create_maps_ocn=$slurm_log_root/$SLURM_JOB_NAME-$SLURM_JOB_ID.slurm.create_maps_ocn.out
slurm_log_create_maps_lnd=$slurm_log_root/$SLURM_JOB_NAME-$SLURM_JOB_ID.slurm.create_maps_lnd.out

# atm_grid_name=ne${NE}pg2
atm_grid_name=${grid_name}-pg2
lnd_grid_name=r025
ocn_grid_name=RRSwISC6to18E3r5

atm_grid_file=${grid_root}/${atm_grid_name}_scrip.nc

# /lcrc/group/e3sm/data/inputdata/share/meshes/rof/SCRIPgrid_0.25x0.25_nomask_c200309.nc
# /global/cfs/cdirs/e3sm/inputdata/share/meshes/rof/SCRIPgrid_0.25x0.25_nomask_c200309.nc
lnd_grid_file=${DIN_LOC_ROOT}/share/meshes/rof/SCRIPgrid_0.25x0.25_nomask_c200309.nc
ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
# ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.mask.scrip.20240327.nc
rof_grid_file=${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/SCRIPgrid_0.25x0.25_nomask_c200309.nc

# alg_list_arg="--alg_lst=esmfaave,esmfbilin,ncoaave,ncoidw,traave,trbilin,trfv2,trintbilin" # default
alg_list_arg="--alg_lst=traave,trbilin,trfv2,trintbilin"

#---------------------------------------------------------------------------------------------------  
# print some useful things
echo --------------------------------------------------------------------------------
# echo "   NE                  = ${NE}"; echo
echo "   grid_name           = ${grid_name}"; echo
echo --------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
# if [ -z "${NE}" ]; then echo -e ${RED}ERROR: NE is not defined${NC}; exit ; fi
if [ -z "${grid_name}" ]; then echo -e ${RED}ERROR: grid_name is not defined${NC}; exit ; fi
#-------------------------------------------------------------------------------
echo; echo -e ${GRN} Setting up environment ${NC}; echo
#-------------------------------------------------------------------------------
source ${unified_src}
# eval $(${e3sm_src_root}/cime/CIME/Tools/get_case_env)
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
# #---------------------------------------------------------------------------------------------------
# if $create_maps_ocn; then
#   echo
#   echo -e ${GRN} Creating ocn map files with TempestRemap ${NC} $slurm_log_create_maps
#   echo
#   cd ${maps_root}
#   cmd="time ncremap -P mwf ${alg_list_arg} -s ${ocn_grid_file} -g ${atm_grid_file} --nm_src=${ocn_grid_name} --nm_dst=${atm_grid_name} --dt_sng=${timestamp} >> ${slurm_log_create_maps_ocn} 2>&1 "
#   echo $cmd ; echo
#   eval "$cmd"
#   #-----------------------------------------------------------------------------
#   # Check that map files were created
#   chk_file1=${maps_root}/map_${atm_grid_name}_to_${ocn_grid_name}_trintbilin.${timestamp}.nc
#   if [ ! -f ${chk_file1} ]; then
#     echo
#     echo -e ${RED} Failed to create ocn map files - Errors ocurred ${NC}
#     echo
#   fi
#   #-----------------------------------------------------------------------------
# else
#   echo
#   echo -e ${CYN} Skipping ocn map generation ${NC}
#   echo
# fi
# #---------------------------------------------------------------------------------------------------
# if $create_maps_lnd; then
#   echo
#   echo -e ${GRN} Creating lnd map files with TempestRemap ${NC} $slurm_log_create_maps
#   echo
#   cd ${maps_root}
#   cmd="time ncremap -P mwf ${alg_list_arg} -s ${lnd_grid_file} -g ${atm_grid_file} --nm_src=${lnd_grid_name} --nm_dst=${atm_grid_name} --dt_sng=${timestamp} >> ${slurm_log_create_maps_lnd} 2>&1 "
#   echo $cmd ; echo
#   eval "$cmd"
#   #-----------------------------------------------------------------------------
#   # Check that map files were created
#   chk_file1=${maps_root}/map_${atm_grid_name}_to_${lnd_grid_name}_trintbilin.${timestamp}.nc
#   if [ ! -f ${chk_file1} ]; then
#     echo
#     echo -e ${RED} Failed to create lnd map files - Errors ocurred ${NC}
#     echo
#   fi
#   #-----------------------------------------------------------------------------
# else
#   echo
#   echo -e ${CYN} Skipping lnd map generation ${NC}
#   echo
# fi
#---------------------------------------------------------------------------------------------------
# The command below are the same commands called by "ncremap -P mwf"
#---------------------------------------------------------------------------------------------------
if $create_maps_ocn; then
  echo; echo -e ${GRN} Creating ocn map files with TempestRemap ${NC} $slurm_log_create_maps; echo
  cd ${maps_root}

  map1=${maps_root}/map_${ocn_grid_name}_to_${atm_grid_name}_traave.${timestamp}.nc
  map2=${maps_root}/map_${ocn_grid_name}_to_${atm_grid_name}_trbilin.${timestamp}.nc
  map3=${maps_root}/map_${ocn_grid_name}_to_${atm_grid_name}_trfv2.${timestamp}.nc
  map4=${maps_root}/map_${ocn_grid_name}_to_${atm_grid_name}_trintbilin.${timestamp}.nc
  map5=${maps_root}/map_${atm_grid_name}_to_${ocn_grid_name}_traave.${timestamp}.nc
  map6=${maps_root}/map_${atm_grid_name}_to_${ocn_grid_name}_trbilin.${timestamp}.nc
  map7=${maps_root}/map_${atm_grid_name}_to_${ocn_grid_name}_trfv2.${timestamp}.nc
  map8=${maps_root}/map_${atm_grid_name}_to_${ocn_grid_name}_trintbilin.${timestamp}.nc

  cmd1='ncremap --alg_typ=traave           --grd_src="${ocn_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map1}" '
  cmd2='ncremap --alg_typ=trbilin          --grd_src="${ocn_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map2}" '
  cmd3='ncremap --alg_typ=trfv2            --grd_src="${ocn_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map3}" '
  cmd4='ncremap --alg_typ=trintbilin       --grd_src="${ocn_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map4}" '
  cmd5='ncremap --a2o --alg_typ=traave     --grd_src="${atm_grid_file}" --grd_dst="${ocn_grid_file}" --map_fl="${map5}" '
  cmd6='ncremap --a2o --alg_typ=trbilin    --grd_src="${atm_grid_file}" --grd_dst="${ocn_grid_file}" --map_fl="${map6}" '
  cmd7='ncremap --a2o --alg_typ=trfv2      --grd_src="${atm_grid_file}" --grd_dst="${ocn_grid_file}" --map_fl="${map7}" '
  cmd8='ncremap --a2o --alg_typ=trintbilin --grd_src="${atm_grid_file}" --grd_dst="${ocn_grid_file}" --map_fl="${map8}" '

  echo; echo $cmd1 ; echo; eval "$cmd1"; if [ ! -f ${map1} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map1}; echo; exit 1; fi
  echo; echo $cmd2 ; echo; eval "$cmd2"; if [ ! -f ${map2} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map2}; echo; exit 1; fi
  echo; echo $cmd3 ; echo; eval "$cmd3"; if [ ! -f ${map3} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map3}; echo; exit 1; fi
  echo; echo $cmd4 ; echo; eval "$cmd4"; if [ ! -f ${map4} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map4}; echo; exit 1; fi
  echo; echo $cmd5 ; echo; eval "$cmd5"; if [ ! -f ${map5} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map5}; echo; exit 1; fi
  echo; echo $cmd6 ; echo; eval "$cmd6"; if [ ! -f ${map6} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map6}; echo; exit 1; fi
  echo; echo $cmd7 ; echo; eval "$cmd7"; if [ ! -f ${map7} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map7}; echo; exit 1; fi
  echo; echo $cmd8 ; echo; eval "$cmd8"; if [ ! -f ${map8} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map8}; echo; exit 1; fi
  #-----------------------------------------------------------------------------
  # # Check that map files were created
  # if [ ! -f ${map1} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map1}; echo; exit 1; fi
  # if [ ! -f ${map2} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map2}; echo; exit 1; fi
  # if [ ! -f ${map3} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map3}; echo; exit 1; fi
  # if [ ! -f ${map4} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map4}; echo; exit 1; fi
  # if [ ! -f ${map5} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map5}; echo; exit 1; fi
  # if [ ! -f ${map6} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map6}; echo; exit 1; fi
  # if [ ! -f ${map7} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map7}; echo; exit 1; fi
  # if [ ! -f ${map8} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map8}; echo; exit 1; fi
  #-----------------------------------------------------------------------------
else
  echo; echo -e ${CYN} Skipping ocn map generation ${NC}; echo
fi
#---------------------------------------------------------------------------------------------------
if $create_maps_lnd; then
  echo; echo -e ${GRN} Creating lnd map files with TempestRemap ${NC} $slurm_log_create_maps; echo
  cd ${maps_root}

  map1=${maps_root}/map_${lnd_grid_name}_to_${atm_grid_name}_traave.${timestamp}.nc
  map2=${maps_root}/map_${lnd_grid_name}_to_${atm_grid_name}_trbilin.${timestamp}.nc
  map3=${maps_root}/map_${lnd_grid_name}_to_${atm_grid_name}_trfv2.${timestamp}.nc
  map4=${maps_root}/map_${lnd_grid_name}_to_${atm_grid_name}_trintbilin.${timestamp}.nc
  map5=${maps_root}/map_${atm_grid_name}_to_${lnd_grid_name}_traave.${timestamp}.nc
  map6=${maps_root}/map_${atm_grid_name}_to_${lnd_grid_name}_trbilin.${timestamp}.nc
  map7=${maps_root}/map_${atm_grid_name}_to_${lnd_grid_name}_trfv2.${timestamp}.nc
  map8=${maps_root}/map_${atm_grid_name}_to_${lnd_grid_name}_trintbilin.${timestamp}.nc
  
  cmd1='ncremap --alg_typ=traave           --grd_src="${lnd_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map1}" '
  cmd2='ncremap --alg_typ=trbilin          --grd_src="${lnd_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map2}" '
  cmd3='ncremap --alg_typ=trfv2            --grd_src="${lnd_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map3}" '
  cmd4='ncremap --alg_typ=trintbilin       --grd_src="${lnd_grid_file}" --grd_dst="${atm_grid_file}" --map_fl="${map4}" '
  cmd5='ncremap --a2o --alg_typ=traave     --grd_src="${atm_grid_file}" --grd_dst="${lnd_grid_file}" --map_fl="${map5}" '
  cmd6='ncremap --a2o --alg_typ=trbilin    --grd_src="${atm_grid_file}" --grd_dst="${lnd_grid_file}" --map_fl="${map6}" '
  cmd7='ncremap --a2o --alg_typ=trfv2      --grd_src="${atm_grid_file}" --grd_dst="${lnd_grid_file}" --map_fl="${map7}" '
  cmd8='ncremap --a2o --alg_typ=trintbilin --grd_src="${atm_grid_file}" --grd_dst="${lnd_grid_file}" --map_fl="${map8}" '

  echo; echo $cmd1 ; echo; eval "$cmd1"; if [ ! -f ${map1} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map1}; echo; exit 1; fi
  echo; echo $cmd2 ; echo; eval "$cmd2"; if [ ! -f ${map2} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map2}; echo; exit 1; fi
  echo; echo $cmd3 ; echo; eval "$cmd3"; if [ ! -f ${map3} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map3}; echo; exit 1; fi
  echo; echo $cmd4 ; echo; eval "$cmd4"; if [ ! -f ${map4} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map4}; echo; exit 1; fi
  echo; echo $cmd5 ; echo; eval "$cmd5"; if [ ! -f ${map5} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map5}; echo; exit 1; fi
  echo; echo $cmd6 ; echo; eval "$cmd6"; if [ ! -f ${map6} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map6}; echo; exit 1; fi
  echo; echo $cmd7 ; echo; eval "$cmd7"; if [ ! -f ${map7} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map7}; echo; exit 1; fi
  echo; echo $cmd8 ; echo; eval "$cmd8"; if [ ! -f ${map8} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map8}; echo; exit 1; fi
  #-----------------------------------------------------------------------------
  # # Check that map files were created
  # if [ ! -f ${map1} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map1}; echo; exit 1; fi
  # if [ ! -f ${map2} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map2}; echo; exit 1; fi
  # if [ ! -f ${map3} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map3}; echo; exit 1; fi
  # if [ ! -f ${map4} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map4}; echo; exit 1; fi
  # if [ ! -f ${map5} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map5}; echo; exit 1; fi
  # if [ ! -f ${map6} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map6}; echo; exit 1; fi
  # if [ ! -f ${map7} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map7}; echo; exit 1; fi
  # if [ ! -f ${map8} ]; then echo; echo -e ${RED} Failed to create map file: ${NC} ${map8}; echo; exit 1; fi
  #-----------------------------------------------------------------------------
else
  echo; echo -e ${CYN} Skipping lnd map generation ${NC}; echo
fi
#---------------------------------------------------------------------------------------------------
# Indicate overall run time for this script
end=`date +%s`
runtime_sc=$(( end - start ))
runtime_mn=$(( runtime_sc/60 ))
runtime_hr=$(( runtime_mn/60 ))
echo -e    ${CYN} overall runtime: ${NC} ${runtime_sc} seconds / ${runtime_mn} minutes / ${runtime_hr} hours
echo
#-------------------------------------------------------------------------------