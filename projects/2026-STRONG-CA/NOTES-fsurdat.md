
----------------------------------------------------------------------------------------------------

# Create maps

This script will launch a series of jobs - one for each map.

```shell
python create_fsurdat_maps.py
```

----------------------------------------------------------------------------------------------------

# Create namelist for `mksurfdata_map`

## python script

This script will generate the namelist. Note that it is not equivalent to the old perl script, so use caution.

```shell
create_fsurdat_namelist.py
```

## older perl script

```shell
DIN_LOC_ROOT=/global/cfs/cdirs/e3sm/inputdata
RES=0.5x0.5

YR=1850-2015
./mksurfdata.pl -res $RES -years $YR -d -dinlc $DIN_LOC_ROOT
mv namelist namelist.$RES.$YR

YR=2015-2100
RCP=3-7.0
./mksurfdata.pl -res $RES -years $YR -rcp $RCP -d -dinlc $DIN_LOC_ROOT
mv namelist namelist.$RES.$YR.$RCP
```

----------------------------------------------------------------------------------------------------

# Build `mksurfdata_map`

```shell
e3sm_src_root=/pscratch/sd/w/whannah/tmp_e3sm_src

# Setup environment (should work on any E3SM-supported machine)
eval $(${e3sm_src_root}/cime/CIME/Tools/get_case_env)
# ${e3sm_src_root}/cime/CIME/scripts/configure --macros-format Makefile --mpilib mpi-serial
# source .env_mach_specific.sh

# Build mksurfdata_map
cd ${e3sm_src_root}/components/elm/tools/mksurfdata_map/src

# I thought I needed to swithc ifort => ifx - but I can do that via USER_FC
# sed -i  's/ifort/ifx/' Makefile.common

make clean
INC_NETCDF="`nf-config --includedir`" LIB_NETCDF="`nc-config --libdir`" USER_FC="ifx" USER_LDFLAGS="-L`nc-config --libdir` -lnetcdf -lnetcdff" make

USER_LDFLAGS="`nf-config --flibs`  -lnetcdf -lnetcdff"


# USER_FC="`nf-config --fc`"  \ <= this yeilds "ftn" and does not work
```

----------------------------------------------------------------------------------------------------

# Generate fsurdat

Start a single node interactive job.

```shell
salloc --nodes 1 --qos interactive --time 01:00:00 --constraint cpu --account=m5277
```

run `mksurfdata_map` with the namelist generated above

```shell
cd ~/E3SM_grid_support/projects/2026-STRONG
e3sm_src_root=/pscratch/sd/w/whannah/tmp_e3sm_src
NAMELIST=/global/cfs/cdirs/m5277/whannah/2026-STRONG-CA/files_fsurdat/fsurdat_namelist_STRONG-CA-32x5-v2
eval $(${e3sm_src_root}/cime/CIME/Tools/get_case_env)
cd /global/cfs/cdirs/m5277/whannah/2026-STRONG-CA
srun -n 1 ${e3sm_src_root}/components/elm/tools/mksurfdata_map/mksurfdata_map < $NAMELIST
```

----------------------------------------------------------------------------------------------------
