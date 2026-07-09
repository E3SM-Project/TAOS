#!/usr/bin/env python3
"""
taos.grid — Grid file creation workflow.

Generates GLL (np4) and physics (pg2) SCRIP grid files for a target
atmosphere grid, plus the ne3000 (3km) grid files needed for topography
processing.

Usage
-----
    python -m taos.grid path/to/project.yaml
"""
import os
import textwrap
from pathlib import Path

import netCDF4
import numpy as np

from taos import sem
from taos.config import taos_config
from taos.util import clr, e3sm_env_prefix, print_line, run_cmd, timer

# -------------------------------------------------------------------
# internal helpers


def _grid_paths(cfg):
    """Return a dict of all grid file paths derived from cfg."""
    grid_name = cfg['grid.name']
    grid_root = cfg['derived.grid_root']
    homme_tool_root = cfg.get('paths.homme_tool_root', '')
    np4_name = cfg.get('grid.name_np4', grid_name + 'np4')
    pg2_name = cfg.get('grid.name_pg2', grid_name + 'pg2')
    exodus_override = cfg.get('grid.grid_file_exodus', '')
    return {
        'grid_file_exodus':     exodus_override or f'{grid_root}/{grid_name}.g',
        'grid_file_np4_scrip':  f'{grid_root}/{np4_name}_scrip.nc',
        'grid_file_np4_mbda':   f'{grid_root}/{np4_name}_mbda.nc',
        'grid_file_pg2_scrip':  f'{grid_root}/{pg2_name}_scrip.nc',
        'grid_file_pg2_mbda':   f'{grid_root}/{pg2_name}_mbda.nc',
        'grid_file_3km_exodus': f'{grid_root}/ne3000.g',
        'grid_file_3km_scrip':  f'{grid_root}/ne3000pg1_scrip.nc',
        'grid_file_3km_mbda':   f'{grid_root}/ne3000pg1_mbda.nc',
        'grid_template_file':   f'{homme_tool_root}/{grid_name}_ne0np4_tmp1.nc',
        'nl_file':              f'{homme_tool_root}/input.grd.{grid_name}.nl',
    }


def _compute_np4_scrip_fields(coords, connect):
    """
    Compute all field arrays needed for an np4 SCRIP grid file.

    CV corners are assembled from all adjacent elements per node, producing an
    8-corner polygon that accurately covers the full control-volume boundary.
    Interior nodes use 4 unique corners (slots 4-7 repeat the last); edge nodes
    use 6; mesh-corner nodes use all 8.

    Parameters
    ----------
    coords  : ndarray, shape (nnodes, 3)
    connect : ndarray, shape (nelems, 4), dtype int

    Returns
    -------
    lon        : ndarray, shape (ncol,)     center longitude, degrees [0, 360)
    lat        : ndarray, shape (ncol,)     center latitude,  degrees [−90, 90]
    area       : ndarray, shape (ncol,)     control volume area, steradians
    corner_lon : ndarray, shape (ncol, 8)   CV corner longitudes, degrees
    corner_lat : ndarray, shape (ncol, 8)   CV corner latitudes, degrees
    """
    metdet, _, _, _                      = sem.element_metric(coords, connect)
    unique_xyz, inverse_idx, _           = sem.unique_gll_nodes(coords, connect)
    ncol                                 = len(unique_xyz)

    area = sem.gll_node_areas(metdet, inverse_idx, ncol)

    lon = np.degrees(np.arctan2(unique_xyz[:, 1], unique_xyz[:, 0])) % 360.0
    lat = np.degrees(np.arcsin(np.clip(unique_xyz[:, 2], -1.0, 1.0)))

    # corner_lon, corner_lat = sem.cv_corners_assembled(coords, connect)
    corner_lon, corner_lat = sem.cv_corners_assembled_numba(coords, connect)

    return lon, lat, area, corner_lon, corner_lat


def _write_scrip(path, lon, lat, area, corner_lon, corner_lat):
    """
    Write a SCRIP-format grid file.

    Parameters
    ----------
    path       : str or Path
    lon, lat   : ndarray, shape (ncol,)   center positions, degrees
    area       : ndarray, shape (ncol,)   control volume areas, steradians
    corner_lon : ndarray, shape (ncol, N) CV corner longitudes, degrees
    corner_lat : ndarray, shape (ncol, N) CV corner latitudes, degrees
    """
    ncol    = len(lon)
    ncorner = corner_lon.shape[1]
    with netCDF4.Dataset(str(path), 'w') as nc:
        nc.createDimension('grid_size',    ncol)
        nc.createDimension('grid_corners', ncorner)
        nc.createDimension('grid_rank',    1)

        v = nc.createVariable('grid_area', 'f8', ('grid_size',))
        v.units = 'radians^2'
        v[:] = area

        v = nc.createVariable('grid_corner_lat', 'f8', ('grid_size', 'grid_corners'))
        v.units = 'degrees'
        v[:] = corner_lat

        v = nc.createVariable('grid_corner_lon', 'f8', ('grid_size', 'grid_corners'))
        v.units = 'degrees'
        v[:] = corner_lon

        v = nc.createVariable('grid_center_lat', 'f8', ('grid_size',))
        v.units = 'degrees'
        v[:] = lat

        v = nc.createVariable('grid_center_lon', 'f8', ('grid_size',))
        v.units = 'degrees'
        v[:] = lon

        v = nc.createVariable('grid_imask', 'i4', ('grid_size',))
        v.units = 'unitless'
        v[:] = np.ones(ncol, dtype='i4')

        v = nc.createVariable('grid_dims', 'i4', ('grid_rank',))
        v[:] = [ncol]


def _write_mbda(path, lon, lat, area):
    """
    Write an MBDA-format grid file (reduced SCRIP, CDF5).

    Parameters
    ----------
    path     : str or Path
    lon, lat : ndarray, shape (ncol,)  in degrees
    area     : ndarray, shape (ncol,)  in steradians
    """
    ncol = len(lon)
    with netCDF4.Dataset(str(path), 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('ncol', ncol)

        v = nc.createVariable('lon', 'f8', ('ncol',))
        v.units = 'degrees_east'
        v[:] = lon

        v = nc.createVariable('lat', 'f8', ('ncol',))
        v.units = 'degrees_north'
        v[:] = lat

        v = nc.createVariable('area', 'f8', ('ncol',))
        v.units = 'radians^2'
        v[:] = area


def _create_np4_scrip(exodus_path, scrip_path, mbda_path):
    """
    Create np4 SCRIP and MBDA grid files from an Exodus II mesh.

    Parameters
    ----------
    exodus_path : str or Path
    scrip_path  : str or Path
    mbda_path   : str or Path
    """
    coords, connect = sem.read_exodus(exodus_path)
    lon, lat, area, corner_lon, corner_lat = _compute_np4_scrip_fields(coords, connect)
    _write_scrip(scrip_path, lon, lat, area, corner_lon, corner_lat)
    _write_mbda(mbda_path, lon, lat, area)


# -------------------------------------------------------------------
# public API


def create_grid(cfg):
    """
    Create GLL and physics grid files for the target atmosphere grid.

    np4 SCRIP and MBDA generation uses a pure Python implementation by default.
    Set ``grid.homme_np4_scrip: true`` in project.yaml to revert to the legacy
    homme_tool grid_template_tool + HOMME2SCRIP.py path.

    Prerequisites
    -------------
    The target grid Exodus II file (``<grid_root>/<grid_name>.g``, or the path
    set by ``grid.grid_file_exodus``) must already exist before calling this
    function.  For uniform grids it can be generated with GenerateCSMesh; for
    RRM grids it is produced by SQuadGen.

    Steps
    -----
    1. Generate np4 SCRIP and MBDA grid files (pure-Python path by default;
       homme_tool grid_template_tool + HOMME2SCRIP.py if
       ``grid.homme_np4_scrip: true``).
    2. Create pg2 exodus file from the target exodus via GenerateVolumetricMesh.
    3. Convert pg2 exodus to SCRIP format via ConvertMeshToSCRIP.
    4. Convert pg2 SCRIP to MBDA format via ncap2 + ncrename.
    5. Create ne3000 (3km) grid files if they do not already exist:
       GenerateCSMesh → ConvertMeshToSCRIP → ncap2.

    Parameters
    ----------
    cfg : taos_config
        Loaded and validated project configuration.
    """
    # -------------------------------------------------------------------
    # resolve common paths
    grid_name     = cfg['grid.name']
    unified_bin   = cfg['paths.unified_bin']
    e3sm_src_root = cfg['paths.e3sm_src_root']
    env_prefix    = e3sm_env_prefix(cfg)
    p             = _grid_paths(cfg)

    use_homme_np4 = cfg.get('grid.homme_np4_scrip', False)

    with timer.time('create_grid'):
        # -------------------------------------------------------------------
        # np4 SCRIP and MBDA
        if use_homme_np4:
            homme_tool_root = cfg['paths.homme_tool_root']

            # clear any stale homme_tool grid template file
            if os.path.exists(p['grid_template_file']):
                run_cmd(f'rm {p["grid_template_file"]}')

            # write namelist for homme_tool grid template generation
            nl_content = textwrap.dedent(f"""\
                &ctl_nl
                ne = 0
                mesh_file = "{p['grid_file_exodus']}"
                /
                &vert_nl
                /
                &analysis_nl
                output_dir = "{homme_tool_root}/"
                output_prefix="{grid_name}_"
                tool = 'grid_template_tool'
                output_timeunits=1
                output_frequency=1
                output_varnames1='area','corners','cv_lat','cv_lon'
                output_type='netcdf4p'
                io_stride = 1
                /
                """)
            Path(p['nl_file']).write_text(nl_content)

            # run homme_tool to create np4 grid template
            cmd = (f'cd {homme_tool_root} && {env_prefix} &&'
                   f' srun -c 32 -N $SLURM_NNODES {homme_tool_root}/src/tool/homme_tool < {p["nl_file"]}')
            with timer.time('grid: homme_tool np4 template'):
                run_cmd(cmd)

            if not os.path.exists(p['grid_template_file']):
                raise RuntimeError(f'homme_tool grid file creation FAILED: {p["grid_template_file"]}')
            print(f'\n  {clr.GREEN}homme_tool grid file creation SUCCESSFUL:{clr.END} {p["grid_template_file"]}')

            # convert np4 template to SCRIP format
            homme2scrip = f'{e3sm_src_root}/components/homme/test/tool/python/HOMME2SCRIP.py'
            cmd = (f'{env_prefix} &&'
                   f' {unified_bin}/python {homme2scrip}'
                   f' --src_file {p["grid_template_file"]}'
                   f' --dst_file {p["grid_file_np4_scrip"]}')
            with timer.time('grid: HOMME2SCRIP np4'):
                run_cmd(cmd)

            # create MBDA-format np4 grid file (reduced SCRIP, cdf5)
            cmd = (f'{unified_bin}/ncap2 -v -5 -O'
                   f' -s "lon=grid_center_lon;lat=grid_center_lat;area=grid_area"'
                   f' {p["grid_file_np4_scrip"]} {p["grid_file_np4_mbda"]}')
            with timer.time('grid: ncap2 np4 SCRIP→MBDA'):
                run_cmd(cmd)
            with timer.time('grid: ncrename np4 grid_size→ncol'):
                run_cmd(f'{unified_bin}/ncrename -d grid_size,ncol {p["grid_file_np4_mbda"]}')
        else:
            with timer.time('grid: Python np4 SCRIP+MBDA'):
                _create_np4_scrip(p['grid_file_exodus'],
                                  p['grid_file_np4_scrip'],
                                  p['grid_file_np4_mbda'])

        if not os.path.exists(p['grid_file_np4_mbda']):
            raise RuntimeError(f'MBDA np4 grid file creation FAILED: {p["grid_file_np4_mbda"]}')
        print(f'\n  {clr.GREEN}MBDA np4 grid file creation SUCCESSFUL:{clr.END} {p["grid_file_np4_mbda"]}')

        # -------------------------------------------------------------------
        # TempestRemap command will throw an error with long absolute paths,
        # so these two commands use relative paths via cwd=grid_root.

        grid_root = cfg['derived.grid_root']

        grid_file_exodus_rel    = p['grid_file_exodus'].replace(f'{grid_root}/','')
        grid_file_pg2_mbda_rel  = p['grid_file_pg2_mbda'].replace(f'{grid_root}/','')
        grid_file_pg2_scrip_rel = p['grid_file_pg2_scrip'].replace(f'{grid_root}/','')

        # create PG2 exodus file
        cmd = (f'{env_prefix} &&'
               f' {unified_bin}/GenerateVolumetricMesh'
               f' --in {grid_file_exodus_rel} --out {grid_file_pg2_mbda_rel} --np 2 --uniform')
        with timer.time('grid: GenerateVolumetricMesh pg2'):
            run_cmd(cmd, cwd=grid_root)

        # convert PG2 exodus to SCRIP
        cmd = (f'{env_prefix} &&'
               f' {unified_bin}/ConvertMeshToSCRIP'
               f' --in {grid_file_pg2_mbda_rel} --out {grid_file_pg2_scrip_rel}')
        with timer.time('grid: ConvertMeshToSCRIP pg2'):
            run_cmd(cmd, cwd=grid_root)

        # -------------------------------------------------------------------
        # create MBDA-format pg2 grid file
        cmd = (f'{unified_bin}/ncap2 -v -5 -O'
               f' -s "lon=grid_center_lon;lat=grid_center_lat;area=grid_area"'
               f' {p["grid_file_pg2_scrip"]} {p["grid_file_pg2_mbda"]}')
        with timer.time('grid: ncap2 pg2 SCRIP→MBDA'):
            run_cmd(cmd)
        with timer.time('grid: ncrename pg2 grid_size→ncol'):
            run_cmd(f'{unified_bin}/ncrename -d grid_size,ncol {p["grid_file_pg2_mbda"]}')

        if not os.path.exists(p['grid_file_pg2_mbda']):
            raise RuntimeError(f'MBDA pg2 grid file creation FAILED: {p["grid_file_pg2_mbda"]}')
        print(f'\n  {clr.GREEN}MBDA pg2 grid file creation SUCCESSFUL:{clr.END} {p["grid_file_pg2_mbda"]}')

        # -------------------------------------------------------------------
        # create 3km (ne3000) grid files if they don't already exist
        if not os.path.exists(p['grid_file_3km_mbda']):
            print_line()
            print(f'\n  {clr.CYAN}Creating 3km (ne3000) grid files{clr.END}')

            cmd = (f'{env_prefix} &&'
                   f' {unified_bin}/GenerateCSMesh --alt --res 3000 --file {p["grid_file_3km_exodus"]}')
            with timer.time('grid: GenerateCSMesh 3km'):
                run_cmd(cmd)
            if not os.path.exists(p['grid_file_3km_exodus']):
                raise RuntimeError(f'3km exodus file creation FAILED: {p["grid_file_3km_exodus"]}')

            cmd = (f'{env_prefix} &&'
                   f' {unified_bin}/ConvertMeshToSCRIP'
                   f' --in {p["grid_file_3km_exodus"]} --out {p["grid_file_3km_scrip"]}')
            with timer.time('grid: ConvertMeshToSCRIP 3km'):
                run_cmd(cmd)
            if not os.path.exists(p['grid_file_3km_scrip']):
                raise RuntimeError(f'3km SCRIP file creation FAILED: {p["grid_file_3km_scrip"]}')

            cmd = (f'{unified_bin}/ncap2 -v -5 -O'
                   f' -s "lon=grid_center_lon;lat=grid_center_lat;area=grid_area"'
                   f' {p["grid_file_3km_scrip"]} {p["grid_file_3km_mbda"]}')
            with timer.time('grid: ncap2 3km SCRIP→MBDA'):
                run_cmd(cmd)
        else:
            print(f'\n  {clr.CYAN}Skipping 3km grid file creation (already exists){clr.END}')


# -------------------------------------------------------------------
# entry point


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create grid files for a TAOS project.')
    parser.add_argument('project_yaml', help='Path to project.yaml')
    parser.add_argument('--grid-name', default=None,
                        help='Grid name to process (selects from grids: list; default: base grid:)')
    args = parser.parse_args()
    cfg = taos_config(args.project_yaml)
    if args.grid_name:
        cfg = cfg.for_grid(args.grid_name)
    cfg.validate()
    timer.start_total()
    create_grid(cfg)
    timer.summary()
