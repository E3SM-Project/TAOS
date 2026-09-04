# Domain File Problems

July 2, 2026 - Ben ran into trouble with the domain files we created for the x2 grid. Here's the log file message:

```
 5642:  inconsistency between land fraction and sea ice fraction
 5642:  n=          449  fracl=   0.63371414333061638       fraci=    0.0000000000000000       sum=   0.63371414333061638
 5642:  ERROR: (seq_domain_check)  inconsistency between land fraction and sea ice fraction
```

I tried re-creating the domain file with the commands below, but the file doesn't appear to be any different.

```shell
E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DOMAIN_TOOL=${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc
OUTPUT_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain
DATESTAMP=20260618

python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT}
```

Ben eventually got a mono-grid configuration to work (everything on `conus1024x2v1`), but we worry the domain file problem will just come back in the x3 case, which might force us to use three different mono-grids. The main problem there is that we don't want to create multipel land datasets.

Mark pointed out that we should try modifying the default `fminval` parameter - default is 1e-8

```shell
/pscratch/sd/w/whannah/tmp_e3sm_src/tools/generate_domain_files/generate_domain_files_E3SM.py

E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DOMAIN_TOOL=${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc
OUTPUT_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain
DATESTAMP=20260702

python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT} --fminval=1e-12

mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.fminval_1e-12.nc
mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.fminval_1e-12.nc

python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT} --fminval=1e-4
mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.fminval_1e-4.nc
mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260702.fminval_1e-4.nc
```

Another idea we had was to try using a different MPAS grid... but which one?

```shell
# GRID_OCN=/global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
GRID_OCN=???
du /global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
du /global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/ICOS10/ocean.ICOS10.scrip.211015.nc
GRID_ATM=/global/cfs/cdirs/e3sm/whannah/files_grid/2025-scream-conus-1024x2-pg2_scrip.nc
MAP_FILE=/global/cfs/cdirs/e3sm/tccleve/CONUS2025/files_map/map_RRSwISC6to18E3r5_to_2025-scream-conus-1024x2-pg2_traave.20251121.nc
TMP_PATH=/global/cfs/cdirs/e3sm/tccleve/CONUS2025/tmp

ncremap -5 --alg_typ=traave --grd_src=${GRID_OCN} --grd_dst=${GRID_ATM} --map_fl=${MAP_FILE} --drc_tmp=${TMP_PATH}

E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DOMAIN_TOOL=${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc
OUTPUT_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain
DATESTAMP=20260618

python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT}
```

Another idea is that `--set-omask` flag in the domain tool might fix the problem

```shell
E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DOMAIN_TOOL=${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.20251121.nc
OUTPUT_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain
DATESTAMP=20260710

python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT} --set-omask


F1=${OUTPUT_ROOT}/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.${DATESTAMP}.nc
F2=${OUTPUT_ROOT}/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.${DATESTAMP}.set-omask.nc
echo mv ${F1} ${F2}
mv ${F1} ${F2}

F1=${OUTPUT_ROOT}/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.${DATESTAMP}.nc
F2=${OUTPUT_ROOT}/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.${DATESTAMP}.set-omask.nc
echo mv ${F1} ${F2}
mv ${F1} ${F2}

```

perhaps we need to use the "mask" version of the ocean grid?

```shell
DATESTAMP=20260721

# GRID_OCN=/global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.nomask.scrip.20240327.nc
GRID_OCN=/global/cfs/cdirs/e3sm/inputdata/ocn/mpas-o/RRSwISC6to18E3r5/ocean.RRSwISC6to18E3r5.mask.scrip.20240327.nc
GRID_ATM=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_grid/2026-incite-conus-1024x2-pg2_scrip.nc
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_conus1024x2v1pg2_traave.${DATESTAMP}.nc
TMP_PATH=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_tmp

time ncremap -5 --alg_typ=traave --grd_src=${GRID_OCN} --grd_dst=${GRID_ATM} --map_fl=${MAP_FILE} --drc_tmp=${TMP_PATH}

E3SM_ROOT=/pscratch/sd/w/whannah/tmp_e3sm_src
DOMAIN_TOOL=${E3SM_ROOT}/tools/generate_domain_files/generate_domain_files_E3SM.py
MAP_FILE=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_map/map_RRSwISC6to18E3r5_to_2026-incite-conus-1024x2-pg2_traave.20260610.nc
OUTPUT_ROOT=/global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain


python ${DOMAIN_TOOL} -m ${MAP_FILE} -o RRSwISC6to18E3r5 -l conus-1024x2-pg2 --date-stamp=${DATESTAMP} --output-root=${OUTPUT_ROOT}

mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260721.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.ocn.conus-1024x2-pg2_RRSwISC6to18E3r5.20260721.mask-version.nc
mv /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260721.nc /global/cfs/cdirs/e3sm/2026-INCITE-CONUS-RRM/files_domain/domain.lnd.conus-1024x2-pg2_RRSwISC6to18E3r5.20260721.mask-version.nc
```