# Workflow Testing

This project is a place to validate and stress test the TAOS workflow.

--------------------------------------------------------------------------------

# Grid Generation

```shell
GRID_ROOT=/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/2026-workflow-test/files_grid
unified_bin=/global/common/software/e3sm/anaconda_envs/e3smu_1_12_0/pm-cpu/conda/envs/e3sm_unified_1.12.0_login/bin

# for NE in 30 120 256; do
# for NE in 512 1024 2048; do
for NE in 16; do
    ${unified_bin}/GenerateCSMesh --alt --res ${NE} --file ${GRID_ROOT}/ne${NE}.g
    ${unified_bin}/GenerateVolumetricMesh --in ${GRID_ROOT}/ne${NE}.g --out ${GRID_ROOT}/ne${NE}pg2.g --np 2 --uniform
    ${unified_bin}/ConvertMeshToSCRIP --in ${GRID_ROOT}/ne${NE}pg2.g --out ${GRID_ROOT}/ne${NE}pg2_scrip.nc
done
```

An RRM is useful for testing the smoothing and SGH calculations

```shell
# us rectangular region for refinement
GRID_ROOT=/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid
unified_bin=/global/common/software/e3sm/anaconda_envs/e3smu_1_12_0/pm-cpu/conda/envs/e3sm_unified_1.12.0_login/bin
# BASE_RES=16; REFINE_LVL=2
# BASE_RES=32; REFINE_LVL=2
BASE_RES=32; REFINE_LVL=1
GRID_NAME=RRM-test-${BASE_RES}x${REFINE_LVL}
# RLAT1=20; RLAT2=50; RLON1=-130; RLON2=-50 # cover entire conus region
RLAT1=38; RLAT2=39; RLON1=-108; RLON2=-107 # smaller region just for testing
${unified_bin}/SQuadGen --refine_rect ${RLON1},${RLAT1},${RLON2},${RLAT2},${REFINE_LVL} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist 10 --smooth_iter 20 --lon_ref -107.5 --lat_ref 38.5 --output ${GRID_ROOT}/${GRID_NAME}.g
cd ${GRID_ROOT}
# ${unified_bin}/GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform
# ${unified_bin}/ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc
${unified_bin}/GenerateVolumetricMesh --in ${GRID_NAME}.g     --out ${GRID_NAME}-pg2.g --np 2 --uniform
${unified_bin}/ConvertMeshToSCRIP     --in ${GRID_NAME}-pg2.g --out ${GRID_NAME}-pg2_scrip.nc
ls -l ${GRID_ROOT}/${GRID_NAME}*
cd ~/E3SM_grid_support/projects/workflow-test
```

special RRM for new testing paradigm

```shell
# us rectangular region for refinement
GRID_ROOT=/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid
unified_bin=/global/common/software/e3sm/anaconda_envs/e3smu_1_12_0/pm-cpu/conda/envs/e3sm_unified_1.12.0_login/bin
BASE_RES=4; REFINE_LVL=6
GRID_NAME=RRM-test-${BASE_RES}x${REFINE_LVL}
RLAT1=20; RLAT2=21; RLON1=-104; RLON2=-103
${unified_bin}/SQuadGen --refine_rect ${RLON1},${RLAT1},${RLON2},${RLAT2},${REFINE_LVL} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist 10 --smooth_iter 20 --lon_ref -103.5 --lat_ref 20.5 --output ${GRID_ROOT}/${GRID_NAME}.g
# ${unified_bin}/GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform
# ${unified_bin}/ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc
cd ${GRID_ROOT}
${unified_bin}/GenerateVolumetricMesh --in ${GRID_NAME}.g     --out ${GRID_NAME}-pg2.g --np 2 --uniform
${unified_bin}/ConvertMeshToSCRIP     --in ${GRID_NAME}-pg2.g --out ${GRID_NAME}-pg2_scrip.nc
ls -l ${GRID_ROOT}/${GRID_NAME}*
cd ~/E3SM_grid_support/projects/workflow-test
```
--------------------------------------------------------------------------------
