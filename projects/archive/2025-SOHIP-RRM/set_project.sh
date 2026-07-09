#!/bin/bash
#-------------------------------------------------------------------------------
export proj=2025-SOHIP-RRM
export timestamp=20251006
#-------------------------------------------------------------------------------
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source ${SCRIPT_DIR}/../set_machine_paths.sh
source ${SCRIPT_DIR}/../set_project_paths.sh
#-------------------------------------------------------------------------------
export lnd_grid_name=r025
export rof_grid_name=r025
export ocn_grid_name=RRSwISC6to18E3r5
export lnd_grid_file=${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/SCRIPgrid_0.25x0.25_nomask_c200309.nc
export rof_grid_file=${DIN_LOC_ROOT}/share/meshes/rof/SCRIPgrid_0.25x0.25_nomask_c200309.nc
export ocn_grid_file=${DIN_LOC_ROOT}/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
#-------------------------------------------------------------------------------
