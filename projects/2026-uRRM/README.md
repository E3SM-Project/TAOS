# Micro RRM (uRRM) for Testing

--------------------------------------------------------------------------------

# Grid Creation Notes

The uRRM grid is created by first generating a PNG file with `generate_refinement_image.py` that shades the continental US and builds small buffer zone around it. While previous CONUS and North America RRM grids have used a large buffer away from the coastlines - in this case the base resolution is 13 km (ne256) and we don't feel that a large oceanic buffer is necesssary.

The general grid generation workflow is as follows:

```shell
python 2026-INCITE-CONUS-RRM_generate_refinement_image_ngl.py
# < SQuadGen commands >
```

## SQuadGen commands

The details of the SQuadGen commands are below. If you're running these commands you will likely need to adjust the paths.


```shell
# NERSC paths
# DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
# E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
# DATA_ROOT=/global/cfs/cdirs/e3sm/whannah
# TOPO_ROOT=${DATA_ROOT}/files_topo
# GRID_ROOT=${DATA_ROOT}/files_grid
# MAPS_ROOT=${DATA_ROOT}/files_map

DIN_LOC_ROOT=$(python -m taos.config project.yaml paths.DIN_LOC_ROOT)
E3SM_ROOT=$(python -m taos.config project.yaml paths.e3sm_src_root)
GRID_ROOT=$(python -m taos.config project.yaml derived.grid_root)
MAPS_ROOT=$(python -m taos.config project.yaml derived.maps_root)
TOPO_ROOT=$(python -m taos.config project.yaml derived.topo_root)

echo "DIN_LOC_ROOT : ${DIN_LOC_ROOT}"
echo "E3SM_ROOT    : ${E3SM_ROOT}"
echo "GRID_ROOT    : ${GRID_ROOT}"
echo "MAPS_ROOT    : ${MAPS_ROOT}"
echo "TOPO_ROOT    : ${TOPO_ROOT}"

SDIST=10; SITER=20

BASE_RES=4; REFINE_LVL=3; GRID_NAME=urrm${BASE_RES}x${REFINE_LVL}

REF_IMAGE=${HOME}/E3SM_grid_support/figs_RRM/RRM-png.2025-conus.v1.png

SQuadGen --refine_file ${REF_IMAGE} --resolution ${BASE_RES} --refine_level ${REFINE_LVL} --refine_type LOWCONN --smooth_type SPRING --smooth_dist ${SDIST} --smooth_iter ${SITER} --lon_ref 260 --lat_ref 40 --output ${GRID_ROOT}/${GRID_NAME}.g ; GenerateVolumetricMesh --in ${GRID_ROOT}/${GRID_NAME}.g     --out ${GRID_ROOT}/${GRID_NAME}-pg2.g --np 2 --uniform ; ConvertMeshToSCRIP     --in ${GRID_ROOT}/${GRID_NAME}-pg2.g --out ${GRID_ROOT}/${GRID_NAME}-pg2_scrip.nc; ls -l ${GRID_ROOT}/${GRID_NAME}*
```

--------------------------------------------------------------------------------

# E3SM Source Code Changes Needed to Define Grid

???

--------------------------------------------------------------------------------