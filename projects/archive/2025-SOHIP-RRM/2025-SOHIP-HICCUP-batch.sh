#!/bin/bash
#SBATCH --constraint=cpu
#SBATCH --account=m4842
#SBATCH --qos=regular
###SBATCH --time=24:00:00
#SBATCH --time=6:00:00
#SBATCH --nodes=1
#SBATCH -J HICCUP_SOHIP-L256
#SBATCH -o /global/homes/w/whannah/E3SM_grid_support/2025-SOHIP-RRM/logs_hiccup/slurm-%x-%j.out
#SBATCH --mail-user=hannah6@llnl.gov
#SBATCH --mail-type=END,FAIL
# ------------------------------------------------------------------------------
# To run this batch script, use the command below:
# sbatch user_scripts/2025-SOHIP-batch.sh
# ------------------------------------------------------------------------------
# to set the output grid from the command line:
# NE=120 ; sbatch --job-name=hiccup_ne$NE --output=logs_slurm/slurm-%x-%j.out --export=NE=$NE ./run_hiccup_batch.rhea.sh
# ------------------------------------------------------------------------------

# HGRID=2025-sohip-256x2-ptgnia-v1; IDATE=2023-06-13; HR=19; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-sw-ind-v1; IDATE=2023-06-12; HR=06; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-se-pac-v1; IDATE=2023-06-12; HR=16; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-sc-pac-v1; IDATE=2023-06-14; HR=15; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-eq-ind-v1; IDATE=2023-06-19; HR=09; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-eq-ind-v1; IDATE=2023-06-21; HR=02; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x2-sc-ind-v1; IDATE=2023-06-21; HR=09; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh

# HGRID=2025-sohip-256x3-ptgnia-v1; IDATE=2023-06-13; HR=19; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-sw-ind-v1; IDATE=2023-06-12; HR=06; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-se-pac-v1; IDATE=2023-06-12; HR=16; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-sc-pac-v1; IDATE=2023-06-14; HR=15; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-eq-ind-v1; IDATE=2023-06-19; HR=09; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-eq-ind-v1; IDATE=2023-06-21; HR=02; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh
# HGRID=2025-sohip-256x3-sc-ind-v1; IDATE=2023-06-21; HR=09; sbatch --job-name=HICCUP_SOHIP_${HGRID}_${IDATE} --export=ALL,HGRID=${HGRID},IDATE=${IDATE},HR=${HR} ~/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-batch.sh

# ------------------------------------------------------------------------------

ulimit -s unlimited

source activate hiccup_env

# python -u ${HOME}/HICCUP/user_scripts/2025-SOHIP-create_IC_from_ERA5-NOAA.py
# python -u ${HOME}/E3SM_grid_support/2025-SOHIP-HICCUP-create_IC_from_ERA5-NOAA.py

python -u ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-create_IC_from_ERA5-NOAA.py --dst-horz-grid=${HGRID} --init-date=${IDATE} --init-hour=${HR}

### commands for manually rerunning last step to clean up attributes
# python -u ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-create_IC_from_ERA5-NOAA.py --dst-horz-grid=2025-sohip-256x3-eq-ind-v1 --init-date=2023-06-19 --init-hour=09
# python -u ${HOME}/E3SM_grid_support/2025-SOHIP-RRM/2025-SOHIP-HICCUP-create_IC_from_ERA5-NOAA.py --dst-horz-grid=2025-sohip-256x3-eq-ind-v1 --init-date=2023-06-21 --init-hour=02


# ------------------------------------------------------------------------------
