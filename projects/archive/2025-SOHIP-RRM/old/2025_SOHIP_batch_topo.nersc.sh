#!/bin/bash
#SBATCH --account=m4842
#SBATCH --constraint=cpu
#SBATCH --qos=regular
#SBATCH --job-name=SOHIP_generate_topo
#SBATCH --output=/global/homes/w/whannah/E3SM_grid_support/2025-SOHIP-RRM/logs_slurm/gen_topo_SOHIP_slurm-%x-%j.out
#SBATCH --time=6:00:00
#SBATCH --nodes=1
#SBATCH --mail-type=END,FAIL
#-------------------------------------------------------------------------------

# grid_name=2025-sohip-256x3-ptgnia-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
# grid_name=2025-sohip-256x3-sw-ind-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
# grid_name=2025-sohip-256x3-eq-ind-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
# grid_name=2025-sohip-256x3-se-pac-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
# grid_name=2025-sohip-256x3-sc-pac-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
# grid_name=2025-sohip-256x3-sc-ind-v1;sbatch --job-name=gen_topo_$grid_name --export=ALL,grid_name=$grid_name ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh


# export grid_name=2025-sohip-256x3-se-pac-v1; bash ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025_SOHIP_batch_topo.sh
#-------------------------------------------------------------------------------
create_grid=false
cttrmp_topo=false
smooth_topo=false
cttsgh_topo=true
#-------------------------------------------------------------------------------
timestamp=20250904

slurm_log_root=/global/homes/w/whannah/E3SM_grid_support/2025-SOHIP-RRM/logs_slurm
slurm_log_create_grid=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.create_grid.out
slurm_log_cttrmp_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.cttrmp_topo.out
slurm_log_smooth_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.smooth_topo.out
slurm_log_cttsgh_topo=$slurm_log_root/gen_topo_SOHIP_slurm-$SLURM_JOB_NAME-$SLURM_JOB_ID.cttsgh_topo.out

e3sm_root=/pscratch/sd/w/whannah/tmp_e3sm_src

data_root=/global/cfs/cdirs/m4842/whannah

grid_root=${data_root}/files_grid
maps_root=${data_root}/files_map
topo_root=${data_root}/files_topo

DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
homme_tool_root=${e3sm_root}/cmake_homme

#-------------------------------------------------------------------------------
# Specify topo file names - including temporary files that will be deleted
topo_file_0=${DIN_LOC_ROOT}/atm/cam/hrtopo/USGS-topo-cube3000.nc
# NE_SRC=3000 ; topo_file_0=${DIN_LOC_ROOT}/atm/cam/hrtopo/USGS-topo-cube${NE_SRC}.nc
topo_file_1=${topo_root}/tmp_USGS-topo_${grid_name}-np4.nc
topo_file_2=${topo_root}/tmp_USGS-topo_${grid_name}-np4_smoothedx6t.nc
topo_file_3=${topo_root}/USGS-topo_${grid_name}-np4_smoothedx6t_${timestamp}.nc
#-------------------------------------------------------------------------------  
# print some useful things
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------; echo
echo "   create_grid         = ${create_grid}"
echo "   cttrmp_topo         = ${cttrmp_topo}"
echo "   smooth_topo         = ${smooth_topo}"
echo "   cttsgh_topo         = ${cttsgh_topo}"; echo
echo "   grid_name           = ${grid_name}"; echo
echo "   e3sm_root           = $e3sm_root"
echo "   grid_root           = $grid_root"
echo "   maps_root           = $maps_root"
echo "   topo_root           = $topo_root"
echo "   DIN_LOC_ROOT        = $DIN_LOC_ROOT"; echo
echo "   topo_file_0         = $topo_file_0"
echo "   topo_file_1         = $topo_file_1"
echo "   topo_file_2         = $topo_file_2"
echo "   topo_file_3         = $topo_file_3"; echo
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
#---------------------------------------------------------------------------
# if [ -z "${NE_SRC}" ]; then echo -e ${RED}ERROR: NE_SRC is not defined${NC}; exit ; fi
# if [ -z "${NE_DST}" ]; then echo -e ${RED}ERROR: NE_DST is not defined${NC}; exit ; fi
if [ -z "${grid_name}" ]; then echo -e ${RED}ERROR: grid_name is not defined${NC}; exit ; fi
#---------------------------------------------------------------------------
# Make sure paths exist
mkdir -p ${grid_root} ${maps_root} ${topo_root}
if [ ! -d ${DIN_LOC_ROOT} ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${DIN_LOC_ROOT} ; fi
if [ ! -d ${e3sm_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${e3sm_root} ; fi
if [ ! -d ${grid_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${grid_root} ; fi
if [ ! -d ${maps_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${maps_root} ; fi
if [ ! -d ${topo_root}    ]; then echo -e ${RED}ERROR directory does not exist:${NC} ${topo_root} ; fi
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
# unified_bin=/global/common/software/e3sm/anaconda_envs/base/envs/e3sm_unified_1.11.1_login/bin
module load python
source activate hiccup_env
eval $(${e3sm_root}/cime/CIME/Tools/get_case_env)
ulimit -s unlimited # required for larger grids
echo --------------------------------------------------------------------------------
echo --------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
# set -x # echo commands
#*******************************************************************************
#*******************************************************************************
#*******************************************************************************
# Generate GLL SCRIP grid file for target topo grid
if $create_grid; then
  echo
  echo -e ${GRN} Creating np4 grid file with homme_tool ${NC} $slurm_log_create_grid
  echo
  cd ${e3sm_root}/cmake_homme

  rm -f ${e3sm_root}/cmake_homme/input.nl
  cat > ${e3sm_root}/cmake_homme/input.nl <<EOF
&ctl_nl
ne = 0
mesh_file = "${grid_root}/${grid_name}.g"
/
&vert_nl    
/
&analysis_nl
tool = 'grid_template_tool'
output_dir = "./"
output_timeunits=1
output_frequency=1
output_varnames1='area','corners','cv_lat','cv_lon'
output_type='netcdf'    
io_stride = 1
/
EOF

  srun -n 4 ${e3sm_root}/cmake_homme/src/tool/homme_tool < ${e3sm_root}/cmake_homme/input.nl >> $slurm_log_create_grid 2>&1

  # use python utility for format conversion
  # ${unified_bin}/python ${e3sm_root}/components/homme/test/tool/python/HOMME2SCRIP.py  \
  python ${e3sm_root}/components/homme/test/tool/python/HOMME2SCRIP.py  \
          --src_file ${homme_tool_root}/ne0np4_tmp1.nc \
          --dst_file ${grid_root}/${grid_name}-np4_scrip.nc >> $slurm_log_create_grid 2>&1
else
  echo
  echo -e ${CYN} Skipping grid generation ${NC}
  echo
fi
#-------------------------------------------------------------------------------
chk_file=${grid_root}/${grid_name}-np4_scrip.nc
if [ ! -f ${chk_file} ]; then
  echo; echo -e ${RED} Failed to create file: ${NC} ${chk_file} ; exit; echo;
else
  echo; echo -e ${GRN} Successfully created file: ${NC} ${chk_file} ; echo;
fi
#-------------------------------------------------------------------------------
# echo ; echo Successfully finished homme_tool grid generation ; echo
# exit
#*******************************************************************************
#*******************************************************************************
#*******************************************************************************
# Remap to target grid with cube_to_target
if $cttrmp_topo; then
  echo
  echo -e ${GRN} Remapping topogaphy with cube_to_target ${NC} $slurm_log_cttrmp_topo
  echo
  ${e3sm_root}/components/eam/tools/topo_tool/cube_to_target/cube_to_target \
    --target-grid ${grid_root}/${grid_name}-np4_scrip.nc \
    --input-topography ${topo_file_0} \
    --output-topography ${topo_file_1} >> $slurm_log_cttrmp_topo 2>&1
else
  echo
  echo -e ${CYN} Skipping remapping ${NC}
  echo
fi
#-------------------------------------------------------------------------------
chk_file=${topo_file_1}
if [ ! -f ${chk_file} ]; then
  echo; echo -e ${RED} Failed to create file: ${NC} ${chk_file} ; exit; echo;
else
  echo; echo -e ${GRN} Successfully created file: ${NC} ${chk_file} ; echo;
fi
#*******************************************************************************
#*******************************************************************************
#*******************************************************************************
# Apply Smoothing with homme_tool
if $smooth_topo; then
  echo
  echo -e ${GRN} Smoothing topogaphy with homme_tool ${NC} $slurm_log_smooth_topo
  echo
  cd ${homme_tool_root}
  # Create namelist file for HOMME
  rm -f ${homme_tool_root}/input.nl
  cat > ${homme_tool_root}/input.nl <<EOF
&ctl_nl
mesh_file = "${grid_root}/${grid_name}.g"
smooth_phis_p2filt = 0
smooth_phis_numcycle = 6 ! v2/v3 uses 12/6 for more/less smoothing
smooth_phis_nudt = 4e-16
hypervis_scaling = 2
se_ftype = 2 ! actually output NPHYS; overloaded use of ftype
/
&vert_nl
/
&analysis_nl
tool = 'topo_pgn_to_smoothed'
infilenames = '${topo_file_1}', '${topo_file_2}'
/
EOF
  # run homme_tool for topography smoothing
  srun -n 8 ${homme_tool_root}/src/tool/homme_tool < ${homme_tool_root}/input.nl >> $slurm_log_smooth_topo 2>&1
  # rename output file to remove "1.nc" suffix
  mv ${topo_file_2}1.nc ${topo_file_2}
else
  echo
  echo -e ${CYN} Skipping smoothing ${NC}
  echo
fi
#-------------------------------------------------------------------------------
chk_file=${topo_file_2}
if [ ! -f ${chk_file} ]; then
  echo; echo -e ${RED} Failed to create file: ${NC} ${chk_file} ; exit; echo;
else
  echo; echo -e ${GRN} Successfully created file: ${NC} ${chk_file} ; echo;
fi
#*******************************************************************************
#*******************************************************************************
#*******************************************************************************
# Compute SGH with cube_to_target
if $cttsgh_topo; then
  echo
  echo -e ${GRN} Calculating SGH with cube_to_target ${NC} $slurm_log_cttsgh_topo
  echo
  ${e3sm_root}/components/eam/tools/topo_tool/cube_to_target/cube_to_target \
    --target-grid ${grid_root}/${grid_name}-pg2_scrip.nc \
    --input-topography ${topo_file_0} \
    --smoothed-topography ${topo_file_2} \
    --output-topography ${topo_file_3} >> $slurm_log_cttsgh_topo 2>&1
    # --add-oro-shape >> $slurm_log_cttsgh_topo 2>&1
  #-----------------------------------------------------------------------------
  # convert to 64-bit data format to avoid problems in next step
  echo
  echo -e ${GRN} Converting smoothed topo file to 64-bit data format ${NC} $slurm_log_cttsgh_topo
  echo

  cmd="ncks -5 ${topo_file_2} ${topo_file_2}.tmp"
  echo $cmd ; echo
  
  eval "$cmd"
  
  cmd="mv ${topo_file_2}.tmp ${topo_file_2}"
  echo $cmd ; echo

  eval "$cmd"

  cmd="ncks -5 ${topo_file_3} ${topo_file_3}.tmp"
  echo $cmd ; echo

  eval "$cmd"
  
  cmd="mv ${topo_file_3}.tmp ${topo_file_3}"
  echo $cmd ; echo

  eval "$cmd"
  #-----------------------------------------------------------------------------
  # Append the GLL phi_s data to the output
  ### source {unified_src} # this is problematic - just use unified_bin
  # cmd="${unified_bin}/ncks -5 -A ${topo_file_2} ${topo_file_3} >> $slurm_log_cttsgh_topo 2>&1"
  echo
  echo -e ${GRN} Appending GLL phi_s data to the smoothed topo file ${NC} $slurm_log_cttsgh_topo
  echo

  cmd="ncks -A ${topo_file_2} ${topo_file_3} >> $slurm_log_cttsgh_topo 2>&1"
  echo $cmd ; echo

  eval "$cmd"
else
  echo
  echo -e ${CYN} Skipping SGH calculation ${NC}
  echo
fi
#-------------------------------------------------------------------------------
#*******************************************************************************
# # Clean up Temporary Files
# rm ${topo_root}/tmp_USGS-topo_ne${NE_DST}*
#-------------------------------------------------------------------------------
# set +x # stop echoing commands
#-------------------------------------------------------------------------------
# Check that final topo output file was created
if [ ! -f ${topo_file_3} ]; then
  echo
  echo -e ${RED} Failed to create topography file - Errors ocurred ${NC}
  echo
else
  echo
  echo -e ${GRN} Sucessfully created new topography file  ${NC}
  echo -e $topo_file_3
  echo
fi
#-------------------------------------------------------------------------------
# Indicate overall run time for this script
end=`date +%s`
runtime_sc=$(( end - start ))
runtime_mn=$(( runtime_sc/60 ))
runtime_hr=$(( runtime_mn/60 ))
echo -e    ${CYN} overall runtime: ${NC} ${runtime_sc} seconds / ${runtime_mn} minutes / ${runtime_hr} hours
echo
#-------------------------------------------------------------------------------
