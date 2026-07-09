----------------------------------------------------------------------------------------------------

# Checklist

- domain files      DONE
- topo files        ?
- atm srf files     ?
- coupler maps      ?
- fsurdat           ?
- finidat           ?
- xml grid def      ?

----------------------------------------------------------------------------------------------------

# interactive job commands

```shell
salloc --nodes 1 --qos interactive --time 04:00:00 --constraint cpu --account=m4842
```
----------------------------------------------------------------------------------------------------
# Start Here to setup environment
## NERSC
```shell
DATA_ROOT=/global/cfs/cdirs/m4842/whannah
DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
TOPO_ROOT=${DATA_ROOT}/files_topo
GRID_ROOT=${DATA_ROOT}/files_grid
MAPS_ROOT=${DATA_ROOT}/files_map
NE_SRC_TOPO=3000
#-------------------------------------------------------------------------------
# source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh
source activate hiccup_env
eval $(${E3SM_ROOT}/cime/CIME/Tools/get_case_env)
cd ${DATA_ROOT}
#-------------------------------------------------------------------------------
DATESTAMP=20250904
# GRID_NAME=2025-sohip-32x3-patagonia # smaller refined grid for debugging/testing
# GRID_NAME=2025-sohip-256x3-patagonia
# GRID_NAME=2025-sohip-256x3-sw-ind
# GRID_NAME=2025-sohip-256x3-se-pac
# GRID_NAME=2025-sohip-256x3-sc-pac
# GRID_NAME=2025-sohip-256x3-eq-ind
# GRID_NAME=2025-sohip-256x3-sc-ind

GRID_NAME=2025-sohip-256x3-ptgnia-v1
GRID_NAME=2025-sohip-256x3-sw-ind-v1
GRID_NAME=2025-sohip-256x3-se-pac-v1
GRID_NAME=2025-sohip-256x3-sc-pac-v1
GRID_NAME=2025-sohip-256x3-eq-ind-v1
GRID_NAME=2025-sohip-256x3-sc-ind-v1
#-------------------------------------------------------------------------------
echo -e "\n"\
"  DIN_LOC_ROOT : $DIN_LOC_ROOT \n"\
"  E3SM_ROOT    : $E3SM_ROOT \n"\
"  DATA_ROOT    : $DATA_ROOT \n"\
"  TOPO_ROOT    : $TOPO_ROOT \n"\
"  GRID_ROOT    : $GRID_ROOT \n"\
"  MAPS_ROOT    : $MAPS_ROOT \n"\
"\n"\
"  GRID_NAME : ${GRID_NAME} \n ";
#-------------------------------------------------------------------------------
```

```shell
# grid sizes
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-eq-ind-v1-pg2_scrip.nc | grep "grid_size ="
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-ptgnia-v1-pg2_scrip.nc | grep "grid_size ="
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sc-ind-v1-pg2_scrip.nc | grep "grid_size ="
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sc-pac-v1-pg2_scrip.nc | grep "grid_size ="
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-se-pac-v1-pg2_scrip.nc | grep "grid_size ="
ncdump -h /global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sw-ind-v1-pg2_scrip.nc | grep "grid_size ="

eq-ind > 3205680
ptgnia > 2540976
sc-ind > 2670144
sc-pac > 3011616
se-pac > 2670144
sw-ind > 2670144
```

# Create Data Direcotories

```shell
mkdir ${DATA_ROOT}/files_grid
mkdir ${DATA_ROOT}/files_map
mkdir ${DATA_ROOT}/files_domain
mkdir ${DATA_ROOT}/files_topo
mkdir ${DATA_ROOT}/files_fsurdat
mkdir ${DATA_ROOT}/files_atmsrf
mkdir ${DATA_ROOT}/files_init
```

# Grid Parameters

NOTE - falkland grid original designed for SOHIP measurement on `2023-06-14 01:30:00`

```shell
#-------------------------------------------------------------------------------
REFINE_NAME=falkland-v1;BASE_RES=128;REFINE_LVL=3;RLAT1=-55;RLAT2=-35;RLON1=-90;RLON2=-40;LAT_REF=-45;LON_REF=-65;SDIST=3;SITER=20
REFINE_NAME=falkland-v2;BASE_RES=128;REFINE_LVL=3;RLAT1=-55;RLAT2=-35;RLON1=-90;RLON2=-50;LAT_REF=-45;LON_REF=-70;SDIST=3;SITER=20
REFINE_NAME=falkland-v3;BASE_RES=256;REFINE_LVL=3;RLAT1=-55;RLAT2=-42;RLON1=-88;RLON2=-50;LAT_REF=-50;LON_REF=-60;SDIST=3;SITER=20
REFINE_NAME=falkland-v4;BASE_RES=256;REFINE_LVL=3;RLAT1=-55;RLAT2=-42;RLON1=-92;RLON2=-48;LAT_REF=-50;LON_REF=-60;SDIST=3;SITER=20
#-------------------------------------------------------------------------------
sw_ind => south west indian ocean
se_pac => south east pacific ocean
sc_pac => south central pacific ocean
eq_ind => equatorial indian ocean

# BASE_RES=256;REFINE_LVL=3;SDIST=3;SITER=20

### second pass using shorter longitude range - see ~/E3SM/code_grid/2025_SOHIP_generate_RRM_grids.py
# REFINE_NAME=sw_ind;   RLAT1=-55; RLAT2=-42; RLON1=25;   RLON2=65;   LAT_REF=-50; LON_REF=45
# REFINE_NAME=se_pac;   RLAT1=-55; RLAT2=-42; RLON1=-105; RLON2=-75;  LAT_REF=-50; LON_REF=-95
# REFINE_NAME=sc_pac;   RLAT1=-45; RLAT2=-25; RLON1=-155; RLON2=-115; LAT_REF=-35; LON_REF=-135
# REFINE_NAME=eq_ind;   RLAT1=-15; RLAT2=5;   RLON1=60;   RLON2=100;  LAT_REF=-5;  LON_REF=80

#-------------------------------------------------------------------------------
# GRID_NAME=2025-sohip-${BASE_RES}x${REFINE_LVL}_${REFINE_NAME}
# GRID_NAME=2025-sohip-${BASE_RES}x${REFINE_LVL}-${REFINE_NAME}
# echo ${GRID_NAME}

```

# SQuadGen Grid Generation Commands

```shell
SQuadGen --refine_rect ${RLON1},${RLAT1},${RLON2},${RLAT2},${REFINE_LVL} --lon_ref ${LON_REF} --lat_ref ${LAT_REF} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist ${SDIST} --smooth_iter ${SITER} --output ${GRID_ROOT}/${GRID_NAME}.g
GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform
ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc
```

```shell # Unrefined grids for comparison
NE=128
GenerateCSMesh --alt --res ${NE} --file ${GRID_ROOT}/ne${NE}.g
GenerateVolumetricMesh --in ${GRID_ROOT}/ne${NE}.g --out ${GRID_ROOT}/ne${NE}pg2.g --np 2 --uniform
ConvertMeshToSCRIP --in ${GRID_ROOT}/ne${NE}pg2.g --out ${GRID_ROOT}/ne${NE}pg2_scrip.nc
```

----------------------------------------------------------------------------------------------------

# Grid Generation Scripts

```shell # Alternatively we can just use a python script to automate the grid generation
python ~/E3SM/code_grid/2025_SOHIP_generate_RRM_grids.py
```

```shell
# source activate pyn_env
python ~/E3SM/code_grid/plot.grid.scrip.v2.py
# display ~/E3SM/figs_grid/grid.scrip.v2.png
```

----------------------------------------------------------------------------------------------------

# Map Files

```shell


OCN_GRID=/lcrc/group/e3sm/data/inputdata/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
ATM_GRID=/lcrc/group/e3sm/ac.whannah/scratch/chrys/SOHIP/files_grid/2025-sohip-256x3-ptgnia-v1-pg2_scrip.nc

OCN_NAME=RRSwISC6to18E3r5
ATM_NAME=2025-sohip-256x3-ptgnia-v1-pg2

DATE=20251006

MAP_ROOT=

ncremap --alg_typ=traave           --grd_src="${OCN_GRID}" --grd_dst="${ATM_GRID}" --map_fl="${MAP_ROOT}/map_${OCN_NAME}_to_${ATM_NAME}_traave.${DATE}.nc"
ncremap --alg_typ=trbilin          --grd_src="${OCN_GRID}" --grd_dst="${ATM_GRID}" --map_fl="${MAP_ROOT}/map_${OCN_NAME}_to_${ATM_NAME}_trbilin.${DATE}.nc"
ncremap --alg_typ=trfv2            --grd_src="${OCN_GRID}" --grd_dst="${ATM_GRID}" --map_fl="${MAP_ROOT}/map_${OCN_NAME}_to_${ATM_NAME}_trfv2.${DATE}.nc"
ncremap --alg_typ=trintbilin       --grd_src="${OCN_GRID}" --grd_dst="${ATM_GRID}" --map_fl="${MAP_ROOT}/map_${OCN_NAME}_to_${ATM_NAME}_trintbilin.${DATE}.nc"
ncremap --a2o --alg_typ=traave     --grd_src="${ATM_GRID}" --grd_dst="${OCN_GRID}" --map_fl="${MAP_ROOT}/map_${ATM_NAME}_to_${OCN_NAME}_traave.${DATE}.nc"
ncremap --a2o --alg_typ=trbilin    --grd_src="${ATM_GRID}" --grd_dst="${OCN_GRID}" --map_fl="${MAP_ROOT}/map_${ATM_NAME}_to_${OCN_NAME}_trbilin.${DATE}.nc"
ncremap --a2o --alg_typ=trfv2      --grd_src="${ATM_GRID}" --grd_dst="${OCN_GRID}" --map_fl="${MAP_ROOT}/map_${ATM_NAME}_to_${OCN_NAME}_trfv2.${DATE}.nc"
ncremap --a2o --alg_typ=trintbilin --grd_src="${ATM_GRID}" --grd_dst="${OCN_GRID}" --map_fl="${MAP_ROOT}/map_${ATM_NAME}_to_${OCN_NAME}_trintbilin.${DATE}.nc"

```

----------------------------------------------------------------------------------------------------

# Domain files

```shell

atm_grid_file=${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc
ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/ICOS10/ocean.ICOS10.scrip.211015.nc
MAP_FILE=${MAPS_ROOT}/map_ICOS10_to_${GRID_NAME}-pg2_traave.${DATESTAMP}.nc
echo atm_file : $atm_grid_file ; echo ocn_file : $ocn_grid_file ; echo MAP_FILE : $MAP_FILE

# ls -l $atm_grid_file ; ls -l $ocn_grid_file ; ls -l $MAP_FILE

ncremap -a traave --src_grd=${ocn_grid_file} --dst_grd=${atm_grid_file} --map_file=${MAP_FILE}
# nohup time ncremap -a traave --src_grd=${ocn_grid_file} --dst_grd=${atm_grid_file} --map_file=${MAP_FILE} > log.domain_map.${GRID_NAME}.out & 

python ${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py -m ${MAP_FILE} -o ICOS10 -l ${GRID_NAME} --date-stamp=${DATESTAMP} --output-root=${DATA_ROOT}/files_domain
```

----------------------------------------------------------------------------------------------------

# Topography

## Build `homme_tool`

```shell
# mkdir -p ${E3SM_ROOT}/cmake_homme
cd ${E3SM_ROOT}/cmake_homme

eval $( ${E3SM_ROOT}/cime/CIME/Tools/get_case_env )

mach_file=${E3SM_ROOT}/components/homme/cmake/machineFiles/pm-cpu.cmake

cmake -C ${mach_file}  \
-DBUILD_HOMME_WITHOUT_PIOLIBRARY=OFF \
-DPREQX_PLEV=26  \
${E3SM_ROOT}/components/homme

make -j4 homme_tool

```

```shell
# clean up previous homme_tool build
git clean -f 
rm -rf CMakeFiles/ src/preqx/CMakeFiles/ src/preqx_acc/CMakeFiles/ src/sweqx/CMakeFiles/ src/theta-l/CMakeFiles/ src/tool/CMakeFiles/ test/unit_tests/CMakeFiles/ utils/csm_share/CMakeFiles/
rm -rf ${E3SM_ROOT}/cime
rm -rf ${E3SM_ROOT}/externals/scorpio
git submodule sync ; git submodule update --init --recursive
git status
```

## Build `cube_to_target`

```shell
# build cube_to_target
cd ${E3SM_ROOT}/components/eam/tools/topo_tool/cube_to_target
# eval $( ${E3SM_ROOT}/cime/CIME/Tools/get_case_env )
make clean
make FC=gfortran
```

## Generate np4 scrip grid file for cube_to_target

```shell

# salloc --nodes 1 --qos interactive --time 01:00:00 --constraint cpu --account=m4842

source activate hiccup_env
eval $( ${E3SM_ROOT}/cime/CIME/Tools/get_case_env )
ulimit -s unlimited # required for larger grids

cd ${E3SM_ROOT}/cmake_homme

rm -f ${E3SM_ROOT}/cmake_homme/input.nl
cat > ${E3SM_ROOT}/cmake_homme/input.nl <<EOF
&ctl_nl
ne = 0
mesh_file = "${GRID_ROOT}/${GRID_NAME}.g"
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

srun -n 4 ${E3SM_ROOT}/cmake_homme/src/tool/homme_tool < ${E3SM_ROOT}/cmake_homme/input.nl

python ${E3SM_ROOT}/components/homme/test/tool/python/HOMME2SCRIP.py  --src_file ne0np4_tmp1.nc --dst_file ${GRID_ROOT}/${GRID_NAME}-np4_scrip.nc

```

## Create map with ncremap

```shell
map_file_src_to_np4=${MAPS_ROOT}/map_ne${NE_SRC_TOPO}pg1_to_${atm_grid_name}np4_fv2se_flx.${DATESTAMP}.nc

# Create map from source to target np4
time ncremap ${MAP_ARGS} -a fv2se_flx \
  --src_grd=${GRID_ROOT}/scrip_ne${NE_SRC_TOPO}pg1.nc \
  --dst_grd=${GRID_ROOT}/${atm_grid_name}.g \
  --map_file=${map_file_src_to_np4} \
  --tmp_dir=${MAPS_ROOT}
```

## Remap topo with cube_to_target

```shell
# remap topo with cube_to_target
cd ${DATA_ROOT}
${E3SM_ROOT}/components/eam/tools/topo_tool/cube_to_target/cube_to_target \
  --target-grid ${GRID_ROOT}/${GRID_NAME}-np4_scrip.nc \
  --input-topography ${DIN_LOC_ROOT}/atm/cam/hrtopo/USGS-topo-cube${NE_SRC_TOPO}.nc \
  --output-topography ${TOPO_ROOT}/tmp_USGS-topo_${GRID_NAME}-np4.nc

```

## Smooth remapped topo with homme_tool

```shell
# Apply Smoothing

# increase stack size - required for larger grids
ulimit -s unlimited

cd ${E3SM_ROOT}/cmake_homme

topo_file_1=${TOPO_ROOT}/tmp_USGS-topo_${GRID_NAME}-np4.nc
topo_file_2=${TOPO_ROOT}/tmp_USGS-topo_${GRID_NAME}-np4_smoothedx6t.nc

# Create namelist file for HOMME
cat <<EOF > input.nl
&ctl_nl
mesh_file = "${GRID_ROOT}/${GRID_NAME}.g"
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
srun -n 4 ${E3SM_ROOT}/cmake_homme/src/tool/homme_tool < input.nl

mv ${topo_file_2}1.nc ${topo_file_2}

```

## Calculate SGH with cube_to_target

```shell
# Calculate SGH and topo shape parameters

topo_file_0=${DIN_LOC_ROOT}/atm/cam/hrtopo/USGS-topo-cube${NE_SRC_TOPO}.nc
topo_file_2=${TOPO_ROOT}/tmp_USGS-topo_${GRID_NAME}-np4_smoothedx6t.nc
topo_file_3=${TOPO_ROOT}/USGS-topo_${GRID_NAME}-np4_smoothedx6t_${DATESTAMP}.nc

# Compute SGH with cube_to_target
${E3SM_ROOT}/components/eam/tools/topo_tool/cube_to_target/cube_to_target \
  --target-grid ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc \
  --input-topography ${topo_file_0} \
  --smoothed-topography ${topo_file_2} \
  --output-topography ${topo_file_3} \
  --add-oro-shape

# Append the GLL phi_s data to the output
ncks -A ${topo_file_2} ${topo_file_3}

```

----------------------------------------------------------------------------------------------------

# XML grid definition

## cime_config/config_grids.xml

### grid definition

```xml
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <!-- ******************************************************************* -->
    <!-- ne0np4_sohip-256x3-eq-ind -->
    <!-- ne0np4_sohip-256x3-ptgnia -->
    <!-- ne0np4_sohip-256x3-sc-ind -->
    <!-- ne0np4_sohip-256x3-sc-pac -->
    <!-- ne0np4_sohip-256x3-se-pac -->
    <!-- ne0np4_sohip-256x3-sw-ind -->
    <model_grid alias="2025-sohip-256x3-eq-ind-v1">
      <grid name="atm">ne0np4_sohip-256x3-eq-ind.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="2025-sohip-256x3-ptgnia-v1">
      <grid name="atm">ne0np4_sohip-256x3-ptgnia.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="2025-sohip-256x3-sc-ind-v1">
      <grid name="atm">ne0np4_sohip-256x3-sc-ind.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="2025-sohip-256x3-sc-pac-v1">
      <grid name="atm">ne0np4_sohip-256x3-sc-pac.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="2025-sohip-256x3-se-pac-v1">
      <grid name="atm">ne0np4_sohip-256x3-se-pac.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="2025-sohip-256x3-sw-ind-v1">
      <grid name="atm">ne0np4_sohip-256x3-sw-ind.pg2</grid>
      <grid name="lnd">r025</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r025</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <!-- ******************************************************************* -->
    <!-- ******************************************************************* -->
```

### domain specs

```xml
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <!-- ******************************************************************* -->
    <domain name="ne0np4_sohip-256x3-ptgnia.pg2">
      <nx>2540976</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-ptgnia-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-ptgnia-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <domain name="ne0np4_sohip-256x3-sw-ind.pg2">
      <nx>2670144</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-sw-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-sw-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <domain name="ne0np4_sohip-256x3-se-pac.pg2">
      <nx>2670144</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-se-pac-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-se-pac-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <domain name="ne0np4_sohip-256x3-sc-pac.pg2">
      <nx>3011616</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-sc-pac-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-sc-pac-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <domain name="ne0np4_sohip-256x3-eq-ind.pg2">
      <nx>3205680</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-eq-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-eq-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <domain name="ne0np4_sohip-256x3-sc-ind.pg2">
      <nx>2670144</nx>
      <ny>1</ny>
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.lnd.2025-sohip-256x3-sc-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/m4842/whannah/files_domain/domain.ocn.2025-sohip-256x3-sc-ind-v1_RRSwISC6to18E3r5.20251006.nc</file>
    </domain>
    <!-- ******************************************************************* -->
    <!-- ******************************************************************* -->
```

### map specs

```xml
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <!-- ******************************************************************* -->
    <!-- ne0np4_sohip-256x3-eq-ind -->
    <gridmap atm_grid="ne0np4_sohip-256x3-eq-ind.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-eq-ind.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-eq-ind.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-eq-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- 2025-sohip-256x3-ptgnia -->
    <gridmap atm_grid="ne0np4_sohip-256x3-ptgnia.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-ptgnia.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-ptgnia.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-ptgnia-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- 2025-sohip-256x3-sc-ind -->
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-ind.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-ind.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-ind.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- 2025-sohip-256x3-sc-pac -->
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-pac.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-pac.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sc-pac.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sc-pac-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- 2025-sohip-256x3-se-pac -->
    <gridmap atm_grid="ne0np4_sohip-256x3-se-pac.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-se-pac.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-se-pac.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-se-pac-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- 2025-sohip-256x3-sw-ind -->
    <gridmap atm_grid="ne0np4_sohip-256x3-sw-ind.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_RRSwISC6to18E3r5_traave.20251006.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_RRSwISC6to18E3r5_trbilin.20251006.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_RRSwISC6to18E3r5_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc</map>
      <!-- <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
      <!-- <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_RRSwISC6to18E3r5_trfvnp2.20251006.nc</map> -->
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sw-ind.pg2" lnd_grid="r025">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <!-- <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_r025_trfvnp2.20251006.nc</map> -->
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_r025_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_sohip-256x3-sw-ind.pg2" rof_grid="r025">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_r025_traave.20251006.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/2025-SOHIP/map_2025-sohip-256x3-sw-ind-v1-pg2_to_r025_trbilin.20251006.nc</map>
    </gridmap>
    <!-- ******************************************************************* -->
    <!-- ******************************************************************* -->
```

```shell
# copy tr maps
reg=eq-ind; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
reg=ptgnia; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
reg=sc-ind; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
reg=sc-pac; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
reg=se-pac; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
reg=sw-ind; cp /global/cfs/cdirs/m4842/whannah/files_map/*${reg}*_tr[ab]* /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/2025-SOHIP/
```


## components/eam/bld/config_files/horiz_grid.xml

```xml
<!-- 2025 SOHIP grids -->
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-eq-ind" ncol="3205680" csne="0" csnp="4" npg="0" />
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-ptgnia" ncol="2540976" csne="0" csnp="4" npg="0" />
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-sc-ind" ncol="2670144" csne="0" csnp="4" npg="0" />
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-sc-pac" ncol="3011616" csne="0" csnp="4" npg="0" />
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-se-pac" ncol="2670144" csne="0" csnp="4" npg="0" />
<horiz_grid dyn="se" hgrid="ne0np4_sohip-256x3-sw-ind" ncol="2670144" csne="0" csnp="4" npg="0" />
```

## components/eamxx/cime_config/namelist_defaults_eamxx.xml

```shell

# DATA_ROOT=/global/cfs/cdirs/m4842/whannah
# GRID_ROOT=${DATA_ROOT}/files_grid
# MAPS_ROOT=${DATA_ROOT}/files_map
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-eq-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-ptgnia-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sc-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sc-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-se-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc
# ncremap --alg_typ=intbilin_se2fv --grd_src=${HOME}/grids/ne30.g  --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sw-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc


DATA_ROOT=/global/cfs/cdirs/m4842/whannah
GRID_ROOT=${DATA_ROOT}/files_grid
MAPS_ROOT=${DATA_ROOT}/files_map
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-eq-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-eq-ind-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-ptgnia-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-ptgnia-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-sc-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-sc-ind-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-sc-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-sc-pac-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-se-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-se-pac-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x2-sw-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x2-sw-ind-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-eq-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-ptgnia-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sc-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sc-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-se-pac-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc
ncremap --alg_typ=traave --grd_src=${HOME}/grids/ne30pg2_scrip.nc --grd_dst=${GRID_ROOT}/2025-sohip-256x3-sw-ind-v1-pg2_scrip.nc --map_fl=${MAPS_ROOT}/map_ne30pg2_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc

```

```xml
    <!-- <filename hgrid="ne0np4_CAx32v1" nlev="128">${DIN_LOC_ROOT}/atm/scream/init/screami_CAx32v1np4L128_hiccup-era5-20150101_041823.ncpdq.nc</filename> -->
    <!-- ******************************************************************* -->  
    <!-- 2025 SOHIP -->
    <filename hgrid="ne0np4_sohip-256x3-eq-ind" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <filename hgrid="ne0np4_sohip-256x3-ptgnia" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <filename hgrid="ne0np4_sohip-256x3-sc-ind" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <filename hgrid="ne0np4_sohip-256x3-sc-pac" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <filename hgrid="ne0np4_sohip-256x3-se-pac" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <filename hgrid="ne0np4_sohip-256x3-sw-ind" nlev="256">/global/cfs/cdirs/m4842/whannah/files_init/</filename>
    <!-- ******************************************************************* -->

    <!-- <spa_remap_file hgrid="ne0np4_CAx32v1">${DIN_LOC_ROOT}/atm/scream/maps/map_ne30np4_to_CAx32v1pg2_intbilin_se2fv_20230420.nc</spa_remap_file> -->
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-eq-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-ptgnia">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-sc-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-sc-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-se-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- <spa_remap_file hgrid="ne0np4_sohip-256x3-sw-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30np4_to_2025-sohip-256x3-ptgnia-v1-pg2_intbilin_se2fv.20251006.nc</spa_remap_file> -->
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP 256x2-->
    <spa_remap_file hgrid="ne0np4_sohip-256x2-eq-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-eq-ind-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x2-ptgnia">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-ptgnia-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x2-sc-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-sc-ind-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x2-sc-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-sc-pac-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x2-se-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-se-pac-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x2-sw-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x2-sw-ind-v1-pg2_traave.20251006.nc</spa_remap_file>
    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP 256x3-->
    <spa_remap_file hgrid="ne0np4_sohip-256x3-eq-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-eq-ind-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x3-ptgnia">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-ptgnia-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x3-sc-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-sc-ind-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x3-sc-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-sc-pac-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x3-se-pac">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-se-pac-v1-pg2_traave.20251006.nc</spa_remap_file>
    <spa_remap_file hgrid="ne0np4_sohip-256x3-sw-ind">/global/cfs/cdirs/m4842/whannah/files_map/map_ne30pg2_to_2025-sohip-256x3-sw-ind-v1-pg2_traave.20251006.nc</spa_remap_file>

    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <topography_filename hgrid="ne0np4_sohip-256x3-eq-ind">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-eq-ind-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <topography_filename hgrid="ne0np4_sohip-256x3-ptgnia">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-ptgnia-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <topography_filename hgrid="ne0np4_sohip-256x3-sc-ind">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-sc-ind-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <topography_filename hgrid="ne0np4_sohip-256x3-sc-pac">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-sc-pac-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <topography_filename hgrid="ne0np4_sohip-256x3-se-pac">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-se-pac-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <topography_filename hgrid="ne0np4_sohip-256x3-sw-ind">/global/cfs/cdirs/m4842/whannah/files_topo/USGS-topo_2025-sohip-256x3-sw-ind-v1-np4_smoothedx6t_20251006.nc</topography_filename>
    <!-- ******************************************************************* -->


    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <rad_frequency hgrid="ne0np4_sohip-256x3*">3</rad_frequency>
    <!-- ******************************************************************* -->


    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <!-- mac_aero_mic -->
    <number_of_subcycles hgrid="ne0np4_sohip-256x3*">1</number_of_subcycles>
    <!-- ******************************************************************* -->


    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <nc hgrid="ne0np4_sohip-256x3*">0.0</nc>
    <ni hgrid="ne0np4_sohip-256x3*">0.0</ni>
    <!-- ******************************************************************* -->


    <!-- ******************************************************************* -->
    <!-- 2025 SOHIP -->
    <se_ne     hgrid="ne0np4_sohip-256x3*">0</se_ne>
    <!-- <se_tstep  hgrid="ne0np4_sohip-256x3*" constraints="gt 0">4.1666666666</se_tstep> -->
    <!-- settings for 60 sec physics time step -->
    <se_tstep                          hgrid="ne0np4_sohip-256x2*" constraints="gt 0">7.5</se_tstep>
    <dt_remap_factor                   hgrid="ne0np4_sohip-256x2*">2</dt_remap_factor>
    <dt_tracer_factor                  hgrid="ne0np4_sohip-256x2*">8</dt_tracer_factor>
    <hypervis_subcycle_q               hgrid="ne0np4_sohip-256x2*">8</hypervis_subcycle_q>
    <semi_lagrange_trajectory_nsubstep hgrid="ne0np4_sohip-256x2*">2</semi_lagrange_trajectory_nsubstep>
    <!-- settings for 30 sec physics time step -->
    <se_tstep                          hgrid="ne0np4_sohip-256x3*" constraints="gt 0">3.75</se_tstep>
    <dt_remap_factor                   hgrid="ne0np4_sohip-256x3*">2</dt_remap_factor>
    <dt_tracer_factor                  hgrid="ne0np4_sohip-256x3*">8</dt_tracer_factor>
    <hypervis_subcycle_q               hgrid="ne0np4_sohip-256x3*">8</hypervis_subcycle_q>
    <semi_lagrange_trajectory_nsubstep hgrid="ne0np4_sohip-256x3*">2</semi_lagrange_trajectory_nsubstep>

    <nu_top    hgrid="ne0np4_sohip-256x3*">1.0e4</nu_top>
    <mesh_file hgrid="ne0np4_sohip-256x3-eq-ind">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-eq-ind-v1.g</mesh_file>
    <mesh_file hgrid="ne0np4_sohip-256x3-ptgnia">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-ptgnia-v1.g</mesh_file>
    <mesh_file hgrid="ne0np4_sohip-256x3-sc-ind">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sc-ind-v1.g</mesh_file>
    <mesh_file hgrid="ne0np4_sohip-256x3-sc-pac">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sc-pac-v1.g</mesh_file>
    <mesh_file hgrid="ne0np4_sohip-256x3-se-pac">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-se-pac-v1.g</mesh_file>
    <mesh_file hgrid="ne0np4_sohip-256x3-sw-ind">/global/cfs/cdirs/m4842/whannah/files_grid/2025-sohip-256x3-sw-ind-v1.g</mesh_file>
    <!-- ******************************************************************* -->

<!-- <ncdata dyn="se"     hgrid="ne18np4"  nlev="80"  ic_ymd="101" >atm/cam/inic/homme/eami_mam4_Linoz_ne30np4_L80_c20231010.nc</ncdata> -->
<!-- <bnd_topo            hgrid="ne18np4" npg="2">atm/cam/topo/USGS-topo_ne18np4_smoothedx6t_20250205.nc</bnd_topo> -->
<!-- <drydep_srf_file     hgrid="ne18np4" npg="2">atm/cam/chem/trop_mam/atm_srf_ne18pg2-pg2_20240205.nc</drydep_srf_file> -->
<!-- <se_tstep            hgrid="ne18np4" dyn_target="theta-l"> 300 </se_tstep> -->
<!-- <dt_remap_factor     hgrid="ne18np4" dyn_target="theta-l"> 2 </dt_remap_factor> -->
<!-- <dt_tracer_factor    hgrid="ne18np4" dyn_target="theta-l"> 6 </dt_tracer_factor> -->
<!-- <hypervis_subcycle_q hgrid="ne18np4" dyn_target="theta-l"> 6 </hypervis_subcycle_q> -->
<!-- <nu_top              hgrid="ne18np4" dyn_target="theta-l"> 2.5e5 </nu_top> -->
```

### components/elm/bld/namelist_files/namelist_defaults.xml

```xml
<!-- <fsurdat hgrid="ne0np4-2024-nimbus-iraq-128x8.pg2"   sim_year="2010" use_crop=".false." >/global/cfs/cdirs/m2637/jsgoodni/surfdata_Saomai2006ne128x8pg2_simyr2006_c240105.nc</fsurdat> -->
<fsurdat hgrid="ne0np4_sohip-256x3-eq-ind" sim_year="2010" use_crop=".false.">???</fsurdat>
<fsurdat hgrid="ne0np4_sohip-256x3-ptgnia" sim_year="2010" use_crop=".false.">???</fsurdat>
<fsurdat hgrid="ne0np4_sohip-256x3-sc-ind" sim_year="2010" use_crop=".false.">???</fsurdat>
<fsurdat hgrid="ne0np4_sohip-256x3-sc-pac" sim_year="2010" use_crop=".false.">???</fsurdat>
<fsurdat hgrid="ne0np4_sohip-256x3-se-pac" sim_year="2010" use_crop=".false.">???</fsurdat>
<fsurdat hgrid="ne0np4_sohip-256x3-sw-ind" sim_year="2010" use_crop=".false.">???</fsurdat>
```

----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
