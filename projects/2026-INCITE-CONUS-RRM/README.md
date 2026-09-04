# 2026 INCITE: CONUS-RRM

--------------------------------------------------------------------------------

# Grid Creation Notes

The CONUS-RRM grid is created by first generating a PNG file with `generate_refinement_image.py` that shades the continental US and builds small buffer zone around it. While previous CONUS and North America RRM grids have used a large buffer away from the coastlines - in this case the base resolution is 13 km (ne256) and we don't feel that a large oceanic buffer is necesssary.

Note that there are two different scripts to generate the refinement images:

- 2026-INCITE-CONUS-RRM_generate_refinement_image_ngl.py
- 2026-INCITE-CONUS-RRM_generate_refinement_image_mpl.py

The difference between these is that they use different plotting libraries (PyNGL vs matplotlib). The second script was developed later and gives a different shape due to various factors, so the grids generated from either will not be identical despite being mostly similar.

The general grid generation workflow is as follows:

```shell
python 2026-INCITE-CONUS-RRM_generate_refinement_image_ngl.py
# < SQuadGen commands >
```

## SQuadGen commands

The details of the SQuadGen commands are below. If you're running these commands you will likely need to adjust the paths.


```shell

# NERSC paths
DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DATA_ROOT=/global/cfs/cdirs/e3sm/whannah

# LCRC paths
DIN_LOC_ROOT=/lcrc/group/e3sm/data/inputdata
E3SM_ROOT=/lcrc/group/e3sm/ac.whannah/scratch/chrys/tmp_e3sm_src
DATA_ROOT=/lcrc/group/e3sm/ac.whannah

# OLCF paths
DIN_LOC_ROOT=/lustre/orion/cli115/world-shared/e3sm/inputdata
E3SM_ROOT=
DATA_ROOT=/lustre/orion/cli115/world-shared/e3sm/2026-INCITE-CONUS-RRM

TOPO_ROOT=${DATA_ROOT}/files_topo
GRID_ROOT=${DATA_ROOT}/files_grid
MAPS_ROOT=${DATA_ROOT}/files_map

SDIST=10; SITER=20

# smaller versions of the grid for testing
# BASE_RES=128;  REFINE_LVL=2; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}
# BASE_RES=128;  REFINE_LVL=3; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}
# BASE_RES=128;  REFINE_LVL=4; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}

BASE_RES=1024; REFINE_LVL=2; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}
# BASE_RES=1024; REFINE_LVL=3; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}
# BASE_RES=1024; REFINE_LVL=4; GRID_NAME=2025-scream-conus-${BASE_RES}x${REFINE_LVL}

REF_IMAGE=${HOME}/E3SM_grid_support/figs_RRM/RRM-png.2025-conus.v1.png

SQuadGen --refine_file ${REF_IMAGE} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist ${SDIST} --smooth_iter ${SITER} --lon_ref 260 --lat_ref 40 --output ${GRID_ROOT}/${GRID_NAME}.g ; GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform ; ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc; ls -l ${GRID_ROOT}/${GRID_NAME}*
```

## Alt Grid Versions - not used for real experiments

Below are some commands that were used to explore slightly altered versions.

```shell
# alt w/o rotation
BASE_RES=128; REFINE_LVL=2; GRID_NAME=2025-scream-conus-no-rot-${BASE_RES}x${REFINE_LVL}
# BASE_RES=1024;REFINE_LVL=2; GRID_NAME=2025-scream-conus-rect-${BASE_RES}x${REFINE_LVL}
SQuadGen --refine_file ${HOME}/E3SM_grid_support/figs_RRM/RRM-png.2025-conus.v1.png --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist ${SDIST} --smooth_iter ${SITER} --output ${GRID_ROOT}/${GRID_NAME}.g ; GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform ; ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc; ls -l ${GRID_ROOT}/${GRID_NAME}*

# alt rectangule refinement for comparison
# BASE_RES=128; REFINE_LVL=2; GRID_NAME=2025-scream-conus-rect-${BASE_RES}x${REFINE_LVL}
BASE_RES=128; REFINE_LVL=4; GRID_NAME=2025-scream-conus-rect-${BASE_RES}x${REFINE_LVL}
RLAT1=20; RLAT2=50; RLON1=-130; RLON2=-50
SQuadGen --refine_rect ${RLON1},${RLAT1},${RLON2},${RLAT2},${REFINE_LVL} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist ${SDIST} --smooth_iter ${SITER} --lon_ref 260 --lat_ref 40 --output ${GRID_ROOT}/${GRID_NAME}.g ; GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform ; ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc; ls -l ${GRID_ROOT}/${GRID_NAME}*

```

## Unrefined grids for comparison

```shell
NE=128
GenerateCSMesh --alt --res ${NE} --file ${GRID_ROOT}/ne${NE}.g
GenerateVolumetricMesh --in ${GRID_ROOT}/ne${NE}.g --out ${GRID_ROOT}/ne${NE}pg2.g --np 2 --uniform
ConvertMeshToSCRIP --in ${GRID_ROOT}/ne${NE}pg2.g --out ${GRID_ROOT}/ne${NE}pg2_scrip.nc
```

--------------------------------------------------------------------------------

# E3SM Source Code Changes Needed to Define Grid

> [!NOTE]
> The entries below are just examples - we will fill in the real entries later

## cime_config/config_grids.xml

### XML grid spec

```xml
    <!--=====================================================================-->
    <!-- INCITE 2026 CONUS-RRM -->
    <model_grid alias="conus1024x2v1pg2_RRSwISC6to18E3r5">
      <grid name="atm">ne0np4_conus1024x2v1.pg2</grid>
      <grid name="lnd">ne0np4_conus1024x2v1.pg2</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r0125</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="conus1024x3v1pg2_RRSwISC6to18E3r5">
      <grid name="atm">ne0np4_conus1024x3v1.pg2</grid>
      <grid name="lnd">ne0np4_conus1024x2v1.pg2</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r0125</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <model_grid alias="conus1024x4v1pg2_RRSwISC6to18E3r5">
      <grid name="atm">ne0np4_conus1024x4v1.pg2</grid>
      <grid name="lnd">ne0np4_conus1024x2v1.pg2</grid>
      <grid name="ocnice">RRSwISC6to18E3r5</grid>
      <grid name="rof">r0125</grid>
      <grid name="glc">null</grid>
      <grid name="wav">null</grid>
      <mask>RRSwISC6to18E3r5</mask>
    </model_grid>
    <!--=====================================================================-->
```

### XML domain spec

```xml
    <!--=====================================================================-->
    <!-- INCITE 2026 CONUS-RRM -->
    <domain name="ne0np4_conus1024x2v1.pg2">
      <nx>31633192</nx>
      <ny>1</ny>
      <!-- <file grid="atm|lnd" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <!-- <file grid="ice|ocn" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.2026-incite-conus-1024x2-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.2026-incite-conus-1024x2-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <desc>conus1024x2v1</desc>
    </domain>
    <domain name="ne0np4_conus1024x3v1.pg2">
      <nx>52070092</nx>
      <ny>1</ny>
      <!-- <file grid="atm|lnd" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <!-- <file grid="ice|ocn" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.2026-incite-conus-1024x3-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.2026-incite-conus-1024x3-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <desc>conus1024x3v1</desc>
    </domain>
    <domain name="ne0np4_conus1024x4v1.pg2">
      <nx>133332960</nx>
      <ny>1</ny>
      <!-- <file grid="atm|lnd" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <!-- <file grid="ice|ocn" mask="RRSwISC6to18E3r5">$DIN_LOC_ROOT/share/domains/</file> -->
      <file grid="atm|lnd" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.2026-incite-conus-1024x3-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <file grid="ice|ocn" mask="RRSwISC6to18E3r5">/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.2026-incite-conus-1024x3-pg2_RRSwISC6to18E3r5.20251121.nc</file>
      <desc>conus1024x4v1</desc>
    </domain>
    <!--=====================================================================-->
```

### XML map spec

```xml
    <!--=====================================================================-->
    <!-- INCITE 2026 CONUS-RRM  -->
    <!-- 1024x2 - land is on x2 grid, so we only need ocn/rof maps -->
    <gridmap atm_grid="ne0np4_conus1024x2v1.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_traave.20251121.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc</map>
      <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
      <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_conus1024x2v1.pg2" rof_grid="r0125">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_r0125_traave.20251121.nc</map>
      <map name="ATM2ROF_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_r0125_trfv2.20251121.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_r0125_trbilin.20251121.nc</map>
    </gridmap>
    <!-- 1024x3 -->
    <gridmap atm_grid="ne0np4_conus1024x3v1.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_traave.20251121.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_traave.20251121.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_traave.20251121.nc</map>
      <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
      <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_conus1024x3v1.pg2" lnd_grid="ne0np4_conus1024x2v1.pg2">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_conus1024x2v1pg2_traave.20251121.nc</map>
      <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_conus1024x2v1pg2_trfv2.20251121.nc</map>
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_conus1024x2v1pg2_trbilin.20251121.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x2v1pg2_to_conus1024x3v1pg2_traave.20251121.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x2v1pg2_to_conus1024x3v1pg2_traave.20251121.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_conus1024x3v1.pg2" rof_grid="r0125">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_r0125_traave.20251121.nc</map>
      <map name="ATM2ROF_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_r0125_trfv2.20251121.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_r0125_trbilin.20251121.nc</map>
    </gridmap>
    <!-- 1024x4 -->
    <gridmap atm_grid="ne0np4_conus1024x4v1.pg2" ocn_grid="RRSwISC6to18E3r5">
      <map name="ATM2OCN_FMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_RRSwISC6to18E3r5_traave.20251121.nc</map>
      <map name="ATM2OCN_VMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="ATM2OCN_SMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc</map>
      <map name="OCN2ATM_FMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x4v1pg2_traave.20251121.nc</map>
      <map name="OCN2ATM_SMAPNAME"          >cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x4v1pg2_traave.20251121.nc</map>
      <map name="ATM2ICE_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
      <map name="ATM2OCN_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_conus1024x4v1.pg2" lnd_grid="ne0np4_conus1024x2v1.pg2">
      <map name="ATM2LND_FMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_conus1024x2v1pg2_traave.20251121.nc</map>
      <map name="ATM2LND_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_conus1024x2v1pg2_trfv2.20251121.nc</map>
      <map name="ATM2LND_SMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_conus1024x2v1pg2_trbilin.20251121.nc</map>
      <map name="LND2ATM_FMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x2v1pg2_to_conus1024x4v1pg2_traave.20251121.nc</map>
      <map name="LND2ATM_SMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x2v1pg2_to_conus1024x4v1pg2_traave.20251121.nc</map>
    </gridmap>
    <gridmap atm_grid="ne0np4_conus1024x4v1.pg2" rof_grid="r0125">
      <map name="ATM2ROF_FMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_r0125_traave.20251121.nc</map>
      <map name="ATM2ROF_FMAPNAME_NONLINEAR">cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_r0125_trfv2.20251121.nc</map>
      <map name="ATM2ROF_SMAPNAME"          >cpl/gridmaps/conus1024x4v1pg2/map_conus1024x4v1pg2_to_r0125_trbilin.20251121.nc</map>
    </gridmap>
    <!--=====================================================================-->
```

----------------------------------------------------------------------------------------------------

## components/eam/bld/config_files/horiz_grid.xml

```xml
<horiz_grid dyn="se" hgrid="ne0np4_conus1024x2v1.pg2"         ncol="31633192"  csne="0" csnp="4" npg="2" />
<horiz_grid dyn="se" hgrid="ne0np4_conus1024x3v1.pg2"         ncol="52070092"  csne="0" csnp="4" npg="2" />
<horiz_grid dyn="se" hgrid="ne0np4_conus1024x4v1.pg2"         ncol="133332960" csne="0" csnp="4" npg="2" />
```

# Commands for Moving Data

```shell
# these commands were used to copy the map files to the input data directory on NERSC 

# 1024x2
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x2-pg2_to_RRSwISC6to18E3r5_traave.20251121.nc     /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x2-pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc    /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x2-pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc      /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x2-pg2_to_RRSwISC6to18E3r5_trintbilin.20251121.nc /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x2v1pg2/map_conus1024x2v1pg2_to_RRSwISC6to18E3r5_trintbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_ne30pg2_to_2026-incite-conus-1024x2-pg2_traave.20251121.nc              /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x2v1pg2/map_ne30pg2_to_conus1024x2v1pg2_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x2-pg2_traave.20251121.nc     /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x2-pg2_trbilin.20251121.nc    /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_trbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x2-pg2_trfv2.20251121.nc      /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_trfv2.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x2-pg2_trintbilin.20251121.nc /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_trintbilin.20251121.nc
# 1024x3
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x3-pg2_to_RRSwISC6to18E3r5_traave.20251121.nc     /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x3-pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc    /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x3-pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc      /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trfv2.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_2026-incite-conus-1024x3-pg2_to_RRSwISC6to18E3r5_trintbilin.20251121.nc /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x3v1pg2/map_conus1024x3v1pg2_to_RRSwISC6to18E3r5_trintbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_ne30pg2_to_2026-incite-conus-1024x3-pg2_traave.20251121.nc              /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/conus1024x3v1pg2/map_ne30pg2_to_conus1024x3v1pg2_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x3-pg2_traave.20251121.nc     /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_traave.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x3-pg2_trbilin.20251121.nc    /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_trbilin.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x3-pg2_trfv2.20251121.nc      /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_trfv2.20251121.nc
cp /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x3-pg2_trintbilin.20251121.nc /global/cfs/cdirs/e3sm/inputdata/cpl/gridmaps/RRSwISC6to18E3r5/map_RRSwISC6to18E3r5_to_conus1024x3v1pg2_trintbilin.20251121.nc


```
--------------------------------------------------------------------------------