# ROF Map Generation Notes

```shell


# # OLCF - doesn't work because of MOAB/mpi/pmix issue
# # export SLURM_MPI_TYPE=pmix # pmix isn't available
# micromamba activate taos_env
# GRID_ROOT=/lustre/orion/cli115/world-shared/e3sm/2026-INCITE-CONUS-RRM/files_grid
# MAP_ROOT=/lustre/orion/cli115/world-shared/e3sm/2026-INCITE-CONUS-RRM/files_map

# NERSC
salloc --nodes 1 --qos interactive --time 4:00:00 --constraint cpu --account=e3sm

conda activate taos_env
GRID_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid
MAP_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map
TMP_ROOT=/pscratch/sd/w/whannah/tmp_data

LND_FILE=2026-incite-conus-1024x2-pg2_scrip.nc
ROF_FILE=MOSART_global_8th.scrip.20180211c.nc

cp ${GRID_ROOT}/${LND_FILE} ${TMP_ROOT}/${LND_FILE}
cp ${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/${ROF_FILE} ${TMP_ROOT}/${ROF_FILE}

LND_GRID=${TMP_ROOT}/${LND_FILE}
ROF_GRID=${TMP_ROOT}/${ROF_FILE}

# ROF_FILE1=MOSART_global_8th.scrip.20180211c.nc
# ROF_FILE2=MOSART_global_8th.scrip.20180211c.cdf5.nc
# ncks -5 ${DIN_LOC_ROOT}/${ROF_FILE1} ${TMP_ROOT}/${ROF_FILE2}

# MAP_FILE_LND2ROF=map_conus1024x2v1pg2_to_r0125_traave.20260810.nc
# MAP_FILE_ROF2LND=map_r0125_to_conus1024x2v1pg2_traave.20260810.nc

# time ncremap --mpi_nbr=16 -a traave --src_grd=${LND_GRID} --dst_grd=${ROF_GRID} --map_file=${TMP_ROOT}/${MAP_FILE_LND2ROF} --tmp_drc=${TMP_ROOT}

MAP_FILE_LND2ROF=map_conus1024x2v1pg2_to_r0125_traave.20260810.nc
time ncremap -a traave --src_grd=${LND_GRID} --dst_grd=${ROF_GRID} --map_file=${TMP_ROOT}/${MAP_FILE_LND2ROF} --tmp_drc=${TMP_ROOT}

MAP_FILE_LND2ROF=map_conus1024x2v1pg2_to_r0125_esmfaave.20260810.nc
time ncremap -a esmfaave --wgt_cmd='srun -n 32 ESMF_RegridWeightGen' --src_grd=${LND_GRID} --dst_grd=${ROF_GRID} --map_file=${TMP_ROOT}/${MAP_FILE_LND2ROF} --tmp_drc=${TMP_ROOT}

# srun -n 8 ESMF_RegridWeightGen -s "/pscratch/sd/w/whannah/tmp_data/2026-incite-conus-1024x2-pg2_scrip.nc" -d "/pscratch/sd/w/whannah/tmp_data/MOSART_global_8th.scrip.20180211c.nc" -w "/pscratch/sd/w/whannah/tmp_data/map_conus1024x2v1pg2_to_r0125_esmfaave.20260810.nc" --method conserve --no_log --ignore_unmapped --ignore_degenerate

cp ${TMP_ROOT}/${MAP_FILE_LND2ROF} ${MAP_ROOT}/${MAP_FILE_LND2ROF}

```

```shell
# NERSC

GRID_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid
MAP_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map
TMP_ROOT=/pscratch/sd/w/whannah/tmp_data

LND_FILE=2026-incite-conus-1024x2-pg2_scrip.cdf5.nc
ROF_FILE=MOSART_global_8th.scrip.20180211c.nc

# cp ${GRID_ROOT}/${LND_FILE} ${TMP_ROOT}/${LND_FILE}
# cp ${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/${ROF_FILE} ${TMP_ROOT}/${ROF_FILE}

LND_GRID=${TMP_ROOT}/${LND_FILE}
ROF_GRID=${TMP_ROOT}/${ROF_FILE}

# MAP_FILE_LND2ROF=map_conus1024x2v1pg2_to_r0125_esmfaave.20260812.nc

# sbatch -A e3sm -C cpu -q regular -N 8 -t 06:00:00 -J gen_map_lnd2rof_esmf --wrap="source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh && ncremap --dbg_lvl=1 -a esmfaave --mpi_pfx='srun -n 32' --src_grd=$LND_GRID --dst_grd=$ROF_GRID --map_file=$TMP_ROOT/$MAP_FILE_LND2ROF --tmp_drc=$TMP_ROOT" --mail-type=END,FAIL --mail-user=hannah6@llnl.gov --output=logs_batch/%x_%j

MAP_FILE_LND2ROF=map_conus1024x2v1pg2_to_r0125_traave.20260814.nc

sbatch -A e3sm -C cpu -q regular -N 4 -t 06:00:00 -J gen_map_lnd2rof_mbtr --wrap="source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh && srun -n 128 mbtempest --type 5 --load $LND_GRID --load $ROF_GRID --weights --file $TMP_ROOT/$MAP_FILE_LND2ROF" --mail-type=END,FAIL --mail-user=hannah6@llnl.gov --output=logs_batch/%x_%j
```

```shell
# mbtempest options for coupler maps
trfv2    => --order 2 --order 2
trbilin  => --fvmethod bilin
intbilin => --fvmethod intbilin
```

## Reproducer for mbtempest problems

```shell
# NERSC

# cp ${GRID_ROOT}/${LND_FILE} ${TMP_ROOT}/${LND_FILE}
# cp ${DIN_LOC_ROOT}/lnd/clm2/mappingdata/grids/${ROF_FILE} ${TMP_ROOT}/${ROF_FILE}

LND_FILE_OLD=2026-incite-conus-128x2-pg2_scrip.nc
LND_FILE_NEW=2026-incite-conus-128x2-pg2_scrip.nc3.nc
# ncks --fl_fmt=64bit_offset ${TMP_ROOT}/${LND_FILE_OLD} ${TMP_ROOT}/${LND_FILE_NEW}
# ncks --fl_fmt=64bit_offset ${TMP_ROOT}/${ROF_FILE_OLD} ${TMP_ROOT}/${ROF_FILE_NEW}

LND_FILE=$LND_FILE_NEW
# ROF_FILE=$ROF_FILE_NEW



GRID_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid
MAP_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map
TMP_ROOT=/pscratch/sd/w/whannah/tmp_data

LND_FILE=2026-incite-conus-128x2-pg2_scrip.nc3.nc
ROF_FILE=MOSART_global_8th.scrip.20180211c.nc

LND_GRID=${TMP_ROOT}/${LND_FILE}
ROF_GRID=${TMP_ROOT}/${ROF_FILE}

MAP_FILE_LND2ROF=map_conus128x2v1pg2_to_r0125_traave.20260812.nc

# sbatch -A e3sm -C cpu -q regular -N 1 -t 06:00:00 -J gen_map_lnd2rof_mbtr --wrap="source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh && ncremap --dbg_lvl=1 -a traave --mpi_nbr=8 --src_grd=$LND_GRID --dst_grd=$ROF_GRID --map_file=$TMP_ROOT/$MAP_FILE_LND2ROF --tmp_drc=$TMP_ROOT" --mail-type=END,FAIL --mail-user=hannah6@llnl.gov --output=logs_batch/%x_%j

# disable optimization
sbatch -A e3sm -C cpu -q regular -N 1 -t 06:00:00 -J gen_map_lnd2rof_mbtr --wrap="source /global/common/software/e3sm/anaconda_envs/load_latest_e3sm_unified_pm-cpu.sh && export MPICH_SHARED_MEM_COLL_OPT=0 && ncremap --dbg_lvl=1 -a traave --mpi_nbr=8 --src_grd=$LND_GRID --dst_grd=$ROF_GRID --map_file=$TMP_ROOT/$MAP_FILE_LND2ROF --tmp_drc=$TMP_ROOT" --mail-type=END,FAIL --mail-user=hannah6@llnl.gov --output=logs_batch/%x_%j

```