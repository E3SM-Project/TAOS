#!/usr/bin/env python
# ==================================================================================================
'''NOTES
DATE=20220727; HR=00
OUT_ROOT=/lustre/orion/cli115/proj-shared/hannah6/TAOS/2026-STRONG-CA/files_init
LOG_FILE=~/TAOS/projects/2026-STRONG-CA/logs_hiccup/log.hiccup.get_hindcast_data.${DATE}.${HR}

nohup python -u ~/HICCUP/get_hindcast_data.ERA5.py --start-date=${DATE} --start-hour=${HR} --output-root=${OUT_ROOT} > ${LOG_FILE} &

YR=2022; python -u ~/HICCUP/get_hindcast_data.NOAA_SSTICE.py --start-year=${YR} --output-root=${OUT_ROOT}

'''
# ==================================================================================================
# from optparse import OptionParser
# parser = OptionParser(usage=None)
# parser.add_option('--dst-horz-grid',dest='dst_horz_grid',default=None,  help='target grid name')
# parser.add_option('--init-date',    dest='init_date',    default=None,  help='intialization date [yyyy-mm-dd]')
# parser.add_option('--init-hour',    dest='init_hour',    default='00',  help='intialization hour [hh]')
# (opts, args) = parser.parse_args()
# # ==================================================================================================
# dst_horz_grid = opts.dst_horz_grid
# init_date     = opts.init_date
# init_hour     = opts.init_hour
# print()
# print(f'Input Arguments:')
# print(f'  dst_horz_grid => {dst_horz_grid}')
# print(f'  init_date     => {init_date}')
# print(f'  init_hour     => {init_hour}')
# print()
# ==================================================================================================
import os
from hiccup import hiccup
# ------------------------------------------------------------------------------
# Logical flags for controlling what this script will do (comment out to disable)
verbose = True            # Global verbosity flag
# unpack_nc_files = True    # unpack data files (convert short to float); NEED TO USE THIS FOR ERA5!!!!
# create_map_file = True    # grid and map file creation
remap_data_horz = True    # horz remap, variable renaming
do_sfc_adjust   = True    # perform surface T and P adjustments
remap_data_vert = True    # vertical remap
do_state_adjust = True    # post vertical interpolation adjustments
combine_files   = True    # combine temporary data files and delete
# create_sst_data = True    # sst/sea ice file creation
# ------------------------------------------------------------------------------

init_date = '2022-07-27' # target => 2022-09-06
init_hour = '00'

# Specify output atmosphere horizontal grid
dst_horz_grid = 'strong-CA-32x5-v1'

# Specify output atmosphere vertical grid 
dst_vert_grid,vert_file_name = 'L128',os.getenv('HOME')+'/HICCUP/files_vert/vert_coord_E3SM_L128.nc'

# specify date of data (and separately specify year for SST/ice files)
init_year = int(init_date.split('-')[0])

# Specify output file paths and names
proj_root = '/lustre/orion/cli115/proj-shared/hannah6/TAOS/2026-STRONG-CA'
data_root = f'{proj_root}/files_init'
topo_root = f'{proj_root}/files_topo'

if not os.path.exists(data_root): os.mkdir(data_root)
output_atm_file_name = f'{data_root}/HICCUP.atm_era5.{init_date}.{init_hour}.{dst_horz_grid}.{dst_vert_grid}.nc'
output_sst_file_name = f'{data_root}/HICCUP.sst_noaa.{init_year}.nc'

# Specify topo file
if dst_horz_grid=='strong-CA-32x5-v1': grid_id='32x5-v1'; topo_file_name=f'{topo_root}/USGS-topo_STRONG-CA-32x5-v1-np4_smoothedx6t_20260505.nc'

# Create data class instance, which includes xarray file dataset objects
# and variable name dictionaries for mapping between naming conventions.
# This also checks input files for required variables
hiccup_data = hiccup.create_hiccup_data(src_data_name='ERA5',target_model='EAMXX',
                                        dst_horz_grid=dst_horz_grid,
                                        dst_vert_grid=dst_vert_grid,
                                        input_file_list=[f'{data_root}/ERA5.atm.{init_date}.{init_hour}.nc',
                                                         f'{data_root}/ERA5.sfc.{init_date}.{init_hour}.nc'],
                                        sstice_name='NOAA',
                                        sst_file=f'{data_root}/sst.day.mean.{init_year}.nc',
                                        ice_file=f'{data_root}/icec.day.mean.{init_year}.nc',
                                        topo_file=topo_file_name,
                                        output_dir=data_root,
                                        grid_dir=f'{data_root}/files_grid',
                                        map_dir=f'{data_root}/files_map',
                                        tmp_dir=f'{data_root}/files_tmp',
                                        verbose=verbose,
                                        check_input_files=True,)

# Print some informative stuff
print('\n  Input Files')
print(f'    input atm files: {hiccup_data.atm_file}')
print(f'    input sfc files: {hiccup_data.sfc_file}')
print(f'    input sst files: {hiccup_data.sst_file}')
print(f'    input ice files: {hiccup_data.ice_file}')
print(f'    input topo file: {hiccup_data.topo_file}')
print('\n  Output files')
print(f'    output atm file: {output_atm_file_name}')
print(f'    output sst file: {output_sst_file_name}')

# Get dict of temporary files for each variable
# file_dict = hiccup_data.get_multifile_dict() # this uses the current time down to the seconds in UTC as a default
file_dict = hiccup_data.get_multifile_dict(timestamp=f'{grid_id}-{init_date}')

# ------------------------------------------------------------------------------
# Make sure files are "unpacked" (may take awhile, so only do it if you need to)
if 'unpack_nc_files' not in locals(): unpack_nc_files = False
if unpack_nc_files:

    hiccup_data.unpack_data_files()

# ------------------------------------------------------------------------------
# Create grid and mapping files
if 'create_map_file' not in locals(): create_map_file = False
if create_map_file :

    # # Create grid description files needed for the mapping file
    # hiccup_data.create_src_grid_file()
    # hiccup_data.create_dst_grid_file()

    grid_root = '/global/cfs/cdirs/m4842/whannah/files_grid'
    hiccup_data.dst_grid_file = f'{grid_root}/{dst_horz_grid}.g'
    # if dst_horz_grid=='2025-sohip-256x3-eq-ind-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-eq-ind-v1.g'
    # if dst_horz_grid=='2025-sohip-256x3-ptgnia-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-ptgnia-v1.g'
    # if dst_horz_grid=='2025-sohip-256x3-sc-ind-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-sc-ind-v1.g'
    # if dst_horz_grid=='2025-sohip-256x3-sc-pac-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-sc-pac-v1.g'
    # if dst_horz_grid=='2025-sohip-256x3-se-pac-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-se-pac-v1.g'
    # if dst_horz_grid=='2025-sohip-256x3-sw-ind-v1': hiccup_data.dst_grid_file = f'{grid_root}/2025-sohip-256x3-sw-ind-v1.g'

    # Create mapping file
    hiccup_data.create_map_file()

# ------------------------------------------------------------------------------
# perform multi-file horizontal remap
if 'remap_data_horz' not in locals(): remap_data_horz = False
if remap_data_horz :

    # Horizontally regrid the data
    hiccup_data.remap_horizontal_multifile(file_dict)

    # Rename variables to match what the model expects
    hiccup_data.rename_vars_multifile(file_dict=file_dict)

    # Add time/date information
    hiccup_data.add_time_date_variables_multifile(file_dict=file_dict)

# ------------------------------------------------------------------------------
# Do surface adjustments
if 'do_sfc_adjust' not in locals(): do_sfc_adjust = False
if do_sfc_adjust:

    hiccup_data.surface_adjustment_multifile(file_dict=file_dict,
                                             adj_TS=False,adj_PS=True)

# ------------------------------------------------------------------------------
# Vertically remap the data
if 'remap_data_vert' not in locals(): remap_data_vert = False
if remap_data_vert :

    hiccup_data.remap_vertical_multifile(file_dict=file_dict
                                        ,vert_file_name=vert_file_name)

# ------------------------------------------------------------------------------
# Perform final state adjustments on interpolated data and add additional data
if 'do_state_adjust' not in locals(): do_state_adjust = False
if do_state_adjust :

    hiccup_data.atmos_state_adjustment_multifile(file_dict=file_dict)

# ------------------------------------------------------------------------------
# Combine files
if 'combine_files' not in locals(): combine_files = False
if combine_files :

    # Combine and delete temporary files
    hiccup_data.combine_files(file_dict=file_dict,
                              delete_files=False,
                              use_single_precision=True,
                              output_file_name=output_atm_file_name)

    # Clean up the global attributes of the file
    hiccup_data.clean_global_attributes(file_name=output_atm_file_name)

# ------------------------------------------------------------------------------
# Create SST/sea ice file
if 'create_sst_data' not in locals(): create_sst_data = False
if create_sst_data :

    # create grid and mapping files
    overwrite = False
    hiccup_data.sstice_create_src_grid_file(force_overwrite=overwrite)
    hiccup_data.sstice_create_dst_grid_file(force_overwrite=overwrite, output_grid_spacing=0.25)
    hiccup_data.sstice_create_map_file(force_overwrite=overwrite)

    # Remap the sst/ice data after time slicing and combining (if necessary)
    hiccup_data.sstice_slice_and_remap(output_file_name=output_sst_file_name,
                                       time_slice_method='use_all',
                                       atm_file=output_atm_file_name)

    # Rename the variables and remove unnecessary variables and attributes
    hiccup_data.sstice_rename_vars(output_file_name=output_sst_file_name)

    # Adjust final SST/ice data to fill in missing values and limit ice fraction
    hiccup_data.sstice_adjustments(output_file_name=output_sst_file_name)

# ------------------------------------------------------------------------------
# Print final output file names

print()
print(f'output_atm_file_name: {output_atm_file_name}')
print(f'output_sst_file_name: {output_sst_file_name}')
print()

# Print summary of timer info
hiccup_data.print_timer_summary()

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------