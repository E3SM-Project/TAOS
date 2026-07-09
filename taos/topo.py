#!/usr/bin/env python3
"""
taos.topo — Topography processing workflow.

Four stages:
  grid         — create np4/pg2/3km SCRIP and MBDA grid files (calls taos.grid).
  remap_topo   — interpolate high-res RLL source topo to the target grid
                 (np4 and pg2) and to the 3km intermediate grid, using MBDA.
  smooth_topo  — apply smoothing to the remapped topo files.
  calc_topo_sgh — compute SGH30 and SGH subgrid-scale orography variance.

Smoothing backend is selected by ``topo.use_python_smooth`` in project.yaml
(default: true).  Set to false to use the original homme_tool path.

Usage
-----
    python -m taos.topo path/to/project.yaml --stage grid
    python -m taos.topo path/to/project.yaml --stage remap
    python -m taos.topo path/to/project.yaml --stage smooth
    python -m taos.topo path/to/project.yaml --stage sgh
    python -m taos.topo path/to/project.yaml --stage smooth,sgh
    python -m taos.topo path/to/project.yaml --stage all
"""
import os
import textwrap
from pathlib import Path

import numpy as np
import xarray as xr

from taos.config import taos_config
from taos.grid import create_grid
from taos import sem
from taos.util import clr, e3sm_env_prefix, print_line, run_cmd, timer

_GRAVITY = 9.80616

# -------------------------------------------------------------------
# internal helpers


def _topo_paths(cfg):
    """Return a dict of all topo (and grid) file paths derived from cfg."""
    grid_name = cfg['grid.name']
    grid_root = cfg['derived.grid_root']
    topo_root = cfg['derived.topo_root']
    timestamp = cfg['project.timestamp']
    np4_name  = cfg.get('grid.name_np4', grid_name + 'np4')
    pg2_name  = cfg.get('grid.name_pg2', grid_name + 'pg2')
    exodus_override = cfg.get('grid.grid_file_exodus', '')
    paths = {
        # grid files (inputs, created by taos.grid)
        'grid_file_np4_mbda': f'{grid_root}/{np4_name}_mbda.nc',
        'grid_file_pg2_mbda': f'{grid_root}/{pg2_name}_mbda.nc',
        'grid_file_3km_mbda': f'{grid_root}/ne3000pg1_mbda.nc',
        'grid_file_exodus':   exodus_override or f'{grid_root}/{grid_name}.g',
        # intermediate topo files
        'topo_file_3km':      f'{topo_root}/tmp_USGS-topo_ne3000.nc',
        'topo_file_1_np4':    f'{topo_root}/tmp_USGS-topo_{grid_name}-np4.nc',
        'topo_file_1_pg2':    f'{topo_root}/tmp_USGS-topo_{grid_name}-pg2.nc',
        'topo_file_2':        f'{topo_root}/tmp_USGS-topo_{grid_name}-np4_smoothedx6t.nc',
        'topo_file_3km_1':    f'{topo_root}/tmp_3km-topo_{grid_name}-np4.nc',
        'topo_file_3km_2':    f'{topo_root}/tmp_3km-topo_{grid_name}-np4_smoothedx6t.nc',
        'topo_file_3km_pg2':  f'{topo_root}/tmp_3km-topo_{grid_name}-pg2.nc',
        # final output topo file
        'topo_file_final':    f'{topo_root}/USGS-topo_{grid_name}-np4_smoothedx6t_{timestamp}.nc',
    }
    homme_tool_root = cfg.get('paths.homme_tool_root', '')
    if homme_tool_root:
        paths['nl_file_smooth'] = f'{homme_tool_root}/input.grd.{grid_name}.nl'
    return paths


# -------------------------------------------------------------------
# remap


def remap_topo(cfg, force_new_3km_data=False):
    """
    Remap source topography to the target np4 and pg2 grids using MBDA.

    Also remaps to the 3km (ne3000) intermediate grid if it doesn't exist
    (or if force_new_3km_data is True).

    Parameters
    ----------
    cfg : taos_config
    force_new_3km_data : bool
        If True, delete and recreate the 3km topo file even if it exists.
    """
    with timer.time('remap_topo'):
        # -------------------------------------------------------------------
        # resolve paths
        # mbda_path may be empty — in that case fall back to the pure-Python
        # disk-averaged remap in taos.mbda (see plans/python_mbda_replacement.md).
        # topo.use_python_mbda (or per-grid grid.use_python_mbda) forces the
        # Python path even when mbda_path is set — useful for quick login-node
        # tests since the compiled MBDA currently has issues on login nodes.
        mbda_path    = cfg.get('paths.mbda_path', '')
        unified_bin  = cfg['paths.unified_bin']
        topo_file_src = cfg['paths.topo_file_src']
        env_prefix   = e3sm_env_prefix(cfg)
        p            = _topo_paths(cfg)

        force_python = cfg.get('grid.use_python_mbda',
                               cfg.get('topo.use_python_mbda', False))
        if isinstance(force_python, str):
            force_python = force_python.lower() not in ('false', '0', 'no', '')
        use_python_mbda = force_python or not mbda_path
        if use_python_mbda:
            # lazy import so that taos.topo can still be imported on machines
            # where scipy isn't installed but the compiled MBDA is.
            from taos import mbda as _py_mbda

        def _run_remap(source, target, output, fields, square_fields=(),
                       dof_var=None, label='remap'):
            """Dispatch a single remap call to compiled MBDA or the Python fallback."""
            if use_python_mbda:
                with timer.time(label + ' [python]'):
                    _py_mbda.remap_files(
                        source_path=source,
                        target_path=target,
                        output_path=output,
                        fields=list(fields),
                        square_fields=list(square_fields),
                        dof_var=dof_var,
                    )
                return
            sq_flag = f' --square-fields {",".join(square_fields)}' if square_fields else ''
            dof_flag = f' --dof-var {dof_var}' if dof_var else ''
            cmd = (f'{env_prefix} &&'
                   f' {mbda_path}'
                   f' --target {target}'
                   f' --source {source}'
                   f' --output {output}'
                   f'{dof_flag}'
                   f' --fields {",".join(fields)}'
                   f'{sq_flag}')
            with timer.time(label):
                run_cmd(cmd)

        if force_new_3km_data and os.path.exists(p['topo_file_3km']):
            run_cmd(f'rm {p["topo_file_3km"]}')

        create_new_3km = not os.path.exists(p['topo_file_3km'])

        # -------------------------------------------------------------------
        # remap source → np4
        print_line()
        print(f'\n  {clr.CYAN}Remapping source topo to np4 grid{clr.END}')
        _run_remap(source=topo_file_src,
                   target=p['grid_file_np4_mbda'],
                   output=p['topo_file_1_np4'],
                   fields=['htopo'],
                   label='remap: MBDA source → np4')
        if not os.path.exists(p['topo_file_1_np4']):
            raise RuntimeError(f'Remapped np4 topo creation FAILED: {p["topo_file_1_np4"]}')

        with timer.time('remap: ncrename np4 htopo→PHIS'):
            run_cmd(f'{unified_bin}/ncrename -O -v htopo,PHIS {p["topo_file_1_np4"]} {p["topo_file_1_np4"]}')
        with timer.time('remap: ncap2 np4 PHIS*gravity'):
            run_cmd(f'{unified_bin}/ncap2 -O -s "PHIS=PHIS*{_GRAVITY}" {p["topo_file_1_np4"]} {p["topo_file_1_np4"]}')

        # -------------------------------------------------------------------
        # remap source → pg2 (with squared field for variance)
        print_line()
        print(f'\n  {clr.CYAN}Remapping source topo to pg2 grid{clr.END}')
        _run_remap(source=topo_file_src,
                   target=p['grid_file_pg2_mbda'],
                   output=p['topo_file_1_pg2'],
                   fields=['htopo'], square_fields=['htopo'],
                   label='remap: MBDA source → pg2')
        if not os.path.exists(p['topo_file_1_pg2']):
            raise RuntimeError(f'Remapped pg2 topo creation FAILED: {p["topo_file_1_pg2"]}')

        with timer.time('remap: ncrename pg2 htopo→PHIS'):
            run_cmd(f'{unified_bin}/ncrename -O -v htopo,PHIS -v htopo_squared,PHIS_squared'
                    f' {p["topo_file_1_pg2"]} {p["topo_file_1_pg2"]}')
        with timer.time('remap: ncap2 pg2 PHIS*gravity'):
            run_cmd(f'{unified_bin}/ncap2 -O'
                    f' -s "PHIS=PHIS*{_GRAVITY}; PHIS_squared=PHIS_squared*{_GRAVITY}*{_GRAVITY}"'
                    f' {p["topo_file_1_pg2"]} {p["topo_file_1_pg2"]}')

        # -------------------------------------------------------------------
        # remap source → 3km grid (skipped if file already exists)
        # Call 3 is out of scope for the Python fallback (9M target cells vs
        # a multi-hundred-million-point source) — see plans/python_mbda_replacement.md.
        if create_new_3km:
            if use_python_mbda:
                raise RuntimeError(
                    "Creating the 3km intermediate topo file requires the compiled "
                    "MBDA binary: the 9M-target × high-res-source remap is out of "
                    "scope for the pure-Python fallback. Either set paths.mbda_path "
                    "in your project.yaml, reuse an existing "
                    f"{p['topo_file_3km']} file, or provide a pre-computed substitute."
                )
            print_line()
            print(f'\n  {clr.CYAN}Creating 3km topo file with MBDA{clr.END}')
            _run_remap(source=topo_file_src,
                       target=p['grid_file_3km_mbda'],
                       output=p['topo_file_3km'],
                       fields=['htopo'], square_fields=['htopo'],
                       dof_var='grid_size',
                       label='remap: MBDA source → 3km')
            if not os.path.exists(p['topo_file_3km']):
                raise RuntimeError(f'3km topo file creation FAILED: {p["topo_file_3km"]}')

            with timer.time('remap: ncap2 3km derive PHIS/VAR30'):
                run_cmd(f'{unified_bin}/ncap2 -v -O'
                        f' -s "PHIS=htopo*{_GRAVITY}; VAR30=(htopo_squared-(htopo*htopo))*{_GRAVITY}*{_GRAVITY}; lat=lat; lon=lon"'
                        f' {p["topo_file_3km"]} {p["topo_file_3km"]}')
        else:
            print(f'\n  {clr.CYAN}Skipping 3km topo file creation (already exists){clr.END}')

        # -------------------------------------------------------------------
        # remap 3km → np4 and pg2 (needed for SGH calc)
        print_line()
        print(f'\n  {clr.CYAN}Mapping 3km topo to np4 with MBDA{clr.END}')
        _run_remap(source=p['topo_file_3km'],
                   target=p['grid_file_np4_mbda'],
                   output=p['topo_file_3km_1'],
                   fields=['PHIS'], square_fields=['PHIS'],
                   label='remap: MBDA 3km → np4')
        if not os.path.exists(p['topo_file_3km_1']):
            raise RuntimeError(f'3km→np4 remapped topo creation FAILED: {p["topo_file_3km_1"]}')

        print_line()
        print(f'\n  {clr.CYAN}Mapping 3km topo to pg2 with MBDA{clr.END}')
        _run_remap(source=p['topo_file_3km'],
                   target=p['grid_file_pg2_mbda'],
                   output=p['topo_file_3km_pg2'],
                   fields=['PHIS', 'VAR30'], square_fields=['PHIS'],
                   label='remap: MBDA 3km → pg2')
        if not os.path.exists(p['topo_file_3km_pg2']):
            raise RuntimeError(f'3km→pg2 remapped topo creation FAILED: {p["topo_file_3km_pg2"]}')


# -------------------------------------------------------------------
# smooth


def smooth_topo(cfg):
    """
    Apply smoothing to the remapped topography files.

    The backend is chosen by ``topo.use_python_smooth`` in project.yaml
    (default: true):

    - true  — pure Python SEM tensor hyperviscosity (no homme_tool required)
    - false — original homme_tool topo_pgn_to_smoothed via srun

    Both produce identical output files for the next stage.  The homme_tool
    path requires ``paths.homme_tool_root`` to be set and an active E3SM
    module environment.

    Parameters
    ----------
    cfg : taos_config
    """
    # per-grid override takes precedence over project-wide topo: setting
    use_python = cfg.get('grid.use_python_smooth',
                         cfg.get('topo.use_python_smooth', True))
    if isinstance(use_python, str):
        use_python = use_python.lower() not in ('false', '0', 'no')

    if use_python:
        _smooth_topo_python(cfg)
    else:
        _smooth_topo_homme(cfg)


def _smooth_topo_python(cfg):
    """Python SEM tensor hyperviscosity smoothing (no homme_tool required)."""
    with timer.time('smooth_topo'):
        p = _topo_paths(cfg)

        # -------------------------------------------------------------------
        # precompute SEM geometry from the Exodus mesh (shared by both runs)
        print_line()
        print(f'\n  {clr.CYAN}Loading Exodus mesh for SEM geometry{clr.END}')
        with timer.time('smooth: load Exodus geometry'):
            coords, connect = sem.read_exodus(p['grid_file_exodus'])
            _, metdet, _, D_mat = sem.element_metric(coords, connect)
            _, inverse_idx, _ = sem.unique_gll_nodes(coords, connect)
            ncol = int(np.max(inverse_idx)) + 1
            del coords, connect

        def _smooth_file(input_path, output_path, label):
            with timer.time(label):
                with xr.open_dataset(input_path) as ds_in:
                    phis = ds_in['PHIS'].values.flatten()
                phis_smooth = sem.smooth_phis(phis, metdet, inverse_idx, ncol,
                                              D_mat)
                del phis
                ds_out = xr.Dataset({
                    'PHIS':   xr.DataArray(phis_smooth, dims=['ncol'],
                                           attrs={'units': 'm2 s-2'}),
                    'PHIS_d': xr.DataArray(phis_smooth, dims=['ncol'],
                                           attrs={'units': 'm2 s-2'}),
                })
                ds_out.to_netcdf(output_path)
                ds_out.close()
            print(f'\n  {clr.GREEN}Smoothing SUCCESSFUL:{clr.END} {output_path}')

        # -------------------------------------------------------------------
        # smooth source topo
        print_line()
        print(f'\n  {clr.CYAN}Smoothing source topo (np4) — Python{clr.END}')
        _smooth_file(p['topo_file_1_np4'], p['topo_file_2'], 'smooth: Python source np4')

        # -------------------------------------------------------------------
        # smooth 3km topo
        print_line()
        print(f'\n  {clr.CYAN}Smoothing 3km topo (np4) — Python{clr.END}')
        _smooth_file(p['topo_file_3km_1'], p['topo_file_3km_2'], 'smooth: Python 3km np4')


def _smooth_topo_homme(cfg):
    """homme_tool topo_pgn_to_smoothed smoothing (requires homme_tool_root + srun)."""
    with timer.time('smooth_topo'):
        # -------------------------------------------------------------------
        # resolve paths
        homme_tool_root = cfg['paths.homme_tool_root']
        env_prefix      = e3sm_env_prefix(cfg)
        p               = _topo_paths(cfg)

        def _run_smooth(input_file, output_file, label):
            nl_content = textwrap.dedent(f"""\
                &ctl_nl
                ne = 0
                mesh_file = "{p['grid_file_exodus']}"
                smooth_phis_p2filt = 0
                smooth_phis_numcycle = 6
                smooth_phis_nudt = 4e-16
                hypervis_scaling = 2
                se_ftype = 2
                /
                &vert_nl
                /
                &analysis_nl
                tool = 'topo_pgn_to_smoothed'
                infilenames = '{input_file}', '{output_file}'
                output_type='netcdf4p'
                /
                """)
            Path(p['nl_file_smooth']).write_text(nl_content)

            cmd = (f'cd {homme_tool_root} && {env_prefix} &&'
                   f' srun -c 32 -N $SLURM_NNODES {homme_tool_root}/src/tool/homme_tool < {p["nl_file_smooth"]}')
            with timer.time(label):
                run_cmd(cmd)

            # homme_tool appends "1.nc" to the output prefix
            produced = f'{output_file}1.nc'
            if not os.path.exists(produced):
                raise RuntimeError(f'homme_tool smoothing FAILED: {produced}')
            run_cmd(f'mv {produced} {output_file}')
            print(f'\n  {clr.GREEN}Smoothing SUCCESSFUL:{clr.END} {output_file}')

        # -------------------------------------------------------------------
        # smooth source topo
        print_line()
        print(f'\n  {clr.CYAN}Smoothing source topo (np4) — homme_tool{clr.END}')
        _run_smooth(p['topo_file_1_np4'], p['topo_file_2'], 'smooth: homme_tool source np4')

        # -------------------------------------------------------------------
        # smooth 3km topo
        print_line()
        print(f'\n  {clr.CYAN}Smoothing 3km topo (np4) — homme_tool{clr.END}')
        _run_smooth(p['topo_file_3km_1'], p['topo_file_3km_2'], 'smooth: homme_tool 3km np4')


# -------------------------------------------------------------------
# SGH computation (pure Python / xarray)


def _compute_variance(phis, phis_smoothed, phis_squared):
    """Compute variance: E[(X - X_smooth)^2] = X_sq + X_smooth^2 - 2*X_smooth*X."""
    return phis_squared + (phis_smoothed ** 2) - (2 * phis_smoothed * phis)


def _get_np4_phis(ds, np4_ncol):
    """Return the np4-sized PHIS from ds, normalized to dim 'ncol'.

    Handles legacy files where np4 data lives on 'ncol_d' and pg2 data occupies
    'ncol', as well as current files where np4 data is on 'ncol'.  Tries PHIS
    first, then PHIS_d (same values; written by older smooth-stage code).
    """
    for varname in ('PHIS', 'PHIS_d'):
        if varname not in ds:
            continue
        da = ds[varname]
        if da.sizes.get('ncol') == np4_ncol:
            return da
        if da.sizes.get('ncol_d') == np4_ncol:
            return da.rename({'ncol_d': 'ncol'})
    raise ValueError(f'No np4 PHIS (ncol={np4_ncol}) found; dims={dict(ds.dims)}')


def calc_topo_sgh(cfg):
    """
    Compute SGH30 and SGH subgrid-scale orography variance and write
    the final topography output file.

    SGH30  = sqrt(min(VAR2, VAR30)) / g
    SGH    = sqrt(VAR_3km) / g

    Parameters
    ----------
    cfg : taos_config
    """
    with timer.time('calc_topo_sgh'):
        p = _topo_paths(cfg)

        # -------------------------------------------------------------------
        # load input datasets
        print_line()
        print(f'\n  {clr.CYAN}Computing SGH30{clr.END}')

        ds_3km    = xr.open_dataset(p['topo_file_3km_pg2'])
        ds_1_pg2  = xr.open_dataset(p['topo_file_1_pg2'])
        ds_2      = xr.open_dataset(p['topo_file_2'])
        ds_3km_1  = xr.open_dataset(p['topo_file_3km_1'])
        ds_3km_2  = xr.open_dataset(p['topo_file_3km_2'])
        ds_1_np4  = xr.open_dataset(p['topo_file_1_np4'])

        # ds_1_np4 is a pure np4 file, so its column dim size is the
        # canonical np4 ncol used to disambiguate np4 vs pg2 in ds_2.
        np4_ncol = ds_1_np4.sizes.get('ncol', ds_1_np4.sizes.get('ncol_d'))

        try:
            # ---------------------------------------------------------------
            # SGH30 & SGH computation
            with timer.time('sgh: compute SGH30 + SGH'):
                phis_smoothed = ds_2['PHIS']
                phis          = ds_1_pg2['PHIS']
                phis_squared  = ds_1_pg2['PHIS_squared']
                var2          = phis_squared - phis * phis
                var30         = ds_3km['VAR30']
                var_min       = xr.where(var30 < var2, var30, var2)
                var_min       = xr.where(var_min > 0, var_min, 0)
                sgh30         = np.sqrt(var_min) / _GRAVITY

                ds_out = xr.Dataset({'SGH30': sgh30})
                ds_out['SGH30'].attrs['units']     = 'm'
                ds_out['SGH30'].attrs['long_name'] = 'standard deviation of source elevation from 3km cube'
                del var2, var30, var_min

                # -----------------------------------------------------------
                # SGH
                print(f'\n  {clr.CYAN}Computing SGH{clr.END}')

                phis_3km         = ds_3km['PHIS']
                phis_3km_squared = ds_3km['PHIS_squared']
                var_3km          = phis_3km_squared - phis_3km * phis_3km
                var_3km          = xr.where(var_3km > 0, var_3km, 0)
                sgh              = np.sqrt(var_3km) / _GRAVITY

                ds_out['SGH'] = sgh
                ds_out['SGH'].attrs['units']     = 'm'
                ds_out['SGH'].attrs['long_name'] = 'standard deviation of 3km cubed-sphere elevation'
                del var_3km

            # ---------------------------------------------------------------
            # add coordinate and smoothed PHIS fields
            print(f'\n  {clr.CYAN}Adding coordinate and smoothed PHIS fields{clr.END}')

            if 'lon' in ds_1_pg2 and 'lat' in ds_1_pg2:
                ds_out['lon'] = ds_1_pg2['lon']
                ds_out['lat'] = ds_1_pg2['lat']

            for coord in ('lon', 'lat'):
                if coord in ds_1_np4:
                    var = ds_1_np4[coord].reset_coords(drop=True) if coord in ds_1_np4.coords else ds_1_np4[coord]
                    if 'ncol' in var.dims:
                        var = var.rename({'ncol': 'ncol_d'})
                    ds_out[f'{coord}_d'] = var

            if 'PHIS' in ds_2 or 'PHIS_d' in ds_2:
                phis_np4_2       = _get_np4_phis(ds_2, np4_ncol).rename({'ncol': 'ncol_d'})
                ds_out['PHIS']   = ds_1_pg2['PHIS']
                ds_out['PHIS_d'] = phis_np4_2

        finally:
            # always close inputs, even if computation fails
            for ds in (ds_3km, ds_1_pg2, ds_2, ds_3km_1, ds_3km_2, ds_1_np4):
                ds.close()

        # -------------------------------------------------------------------
        # write output
        print(f'\n  {clr.CYAN}Writing output: {p["topo_file_final"]}{clr.END}')
        with timer.time('sgh: write output file'):
            encoding = {var: {'zlib': True, 'complevel': 1} for var in ds_out.data_vars}
            ds_out.to_netcdf(p['topo_file_final'], encoding=encoding)
        ds_out.close()

        print(f'\n  {clr.GREEN}SGH calculation SUCCESSFUL:{clr.END} {p["topo_file_final"]}')
        print('\n  The following temporary files can be deleted:')
        topo_root = cfg['derived.topo_root']
        for f in Path(topo_root).glob('tmp_*'):
            print(f'    {f}')


# -------------------------------------------------------------------
# entry point


if __name__ == '__main__':
    import argparse

    _VALID_STAGES = ('grid', 'remap', 'smooth', 'sgh', 'all')

    def _parse_stages(value):
        stages = [s.strip() for s in value.split(',')]
        for s in stages:
            if s not in _VALID_STAGES:
                raise argparse.ArgumentTypeError(
                    f"invalid stage: {s!r} (choose from {', '.join(_VALID_STAGES)})")
        return stages

    parser = argparse.ArgumentParser(description='Run a TAOS topography stage.')
    parser.add_argument('project_yaml', help='Path to project.yaml')
    parser.add_argument('--stage', type=_parse_stages, default=['all'],
                        help='Comma-separated stages to run: '
                             'grid,remap,smooth,sgh,all (default: all)')
    parser.add_argument('--force-new-3km-data', action='store_true',
                        help='Force recreation of the 3km topo file')
    parser.add_argument('--grid-name', default=None,
                        help='Grid name to process (selects from grids: list; default: base grid:)')
    args = parser.parse_args()

    cfg = taos_config(args.project_yaml)
    if args.grid_name:
        cfg = cfg.for_grid(args.grid_name)
    cfg.validate()

    run_all = 'all' in args.stage
    timer.start_total()
    if run_all or 'grid' in args.stage:
        create_grid(cfg)
    if run_all or 'remap' in args.stage:
        remap_topo(cfg, force_new_3km_data=args.force_new_3km_data)
    if run_all or 'smooth' in args.stage:
        smooth_topo(cfg)
    if run_all or 'sgh' in args.stage:
        calc_topo_sgh(cfg)
    timer.summary()
