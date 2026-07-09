#!/usr/bin/env python3
"""
taos.mbda — Pure-Python disk-averaged remapping (MBDA replacement).

This module provides a numpy/scipy-only reimplementation of the disk-averaged
remap algorithm performed by the compiled ``mbda`` binary, scoped to the
handful of calls that TAOS makes inside ``taos.topo.remap_topo()``.

It is intended for use on machines where the compiled MBDA is not available
(laptops, CI, ALCF, etc.) and for grid/source sizes where a serial Python
implementation is fast enough — see ``plans/python_mbda_replacement.md``
for the design and scope.

Public API
----------
remap(source_lon, source_lat, source_fields, target_lon, target_lat,
      target_area, square_fields=(), alpha=1.0, workers=-1)
    Core in-memory remap.  No I/O.

remap_files(source_path, target_path, output_path, fields,
            square_fields=(), alpha=1.0, dof_var=None,
            lon_var=None, lat_var=None, area_var=None)
    File-in / file-out wrapper matching MBDA's CLI contract.

CLI
---
    python -m taos.mbda --target <mbda_grid.nc> --source <source.nc> \\
                        --output <out.nc> --fields f1[,f2] \\
                        [--square-fields f] [--dof-var grid_size] \\
                        [--alpha 1.0]
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
import netCDF4

try:
    from scipy.spatial import cKDTree
except ImportError as _scipy_err:  # pragma: no cover - scipy is a hard dep
    raise ImportError(
        "taos.mbda requires scipy (for scipy.spatial.cKDTree). "
        "Install scipy into your TAOS environment."
    ) from _scipy_err


_FILL_VALUE = 1.0e36

#-------------------------------------------------------------------------------
# data types


@dataclass
class RemapStats:
    """Summary statistics from a remap() call."""
    n_source: int = 0
    n_target: int = 0
    n_fallback: int = 0           # target cells with empty search disk
    min_neighbors: int = 0        # min non-empty disk count
    max_neighbors: int = 0        # max disk count
    mean_neighbors: float = 0.0
    build_seconds: float = 0.0
    query_seconds: float = 0.0

    def fallback_fraction(self) -> float:
        return self.n_fallback / self.n_target if self.n_target else 0.0


#-------------------------------------------------------------------------------
# coordinate helpers


def _lonlat_to_xyz(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    """Convert lon/lat in degrees to unit-sphere 3-D Cartesian coords."""
    lon = np.deg2rad(np.asarray(lon_deg, dtype=np.float64))
    lat = np.deg2rad(np.asarray(lat_deg, dtype=np.float64))
    clat = np.cos(lat)
    xyz = np.empty(lon.shape + (3,), dtype=np.float64)
    xyz[..., 0] = clat * np.cos(lon)
    xyz[..., 1] = clat * np.sin(lon)
    xyz[..., 2] = np.sin(lat)
    return xyz


def _arc_to_chord(arc_radius: np.ndarray) -> np.ndarray:
    """Convert an arc length on the unit sphere (radians) to a chord length."""
    # chord = 2 sin(arc/2); cap at 2.0 (antipode) to stay a valid chord.
    arc = np.minimum(np.asarray(arc_radius, dtype=np.float64), np.pi)
    return 2.0 * np.sin(arc * 0.5)


#-------------------------------------------------------------------------------
# core remap


def remap(
    source_lon: np.ndarray,
    source_lat: np.ndarray,
    source_fields: Dict[str, np.ndarray],
    target_lon: np.ndarray,
    target_lat: np.ndarray,
    target_area: np.ndarray,
    square_fields: Sequence[str] = (),
    alpha: float = 1.0,
    workers: int = -1,
) -> Tuple[Dict[str, np.ndarray], RemapStats]:
    """
    Disk-averaged remap from a source point cloud to a target point cloud.

    For every target cell i:

      1. Arc radius r_i = alpha * sqrt(area_i / pi)   (radians, on unit sphere)
      2. Chord cutoff d_i = 2 sin(r_i / 2)
      3. Collect source points with chord-distance <= d_i from target_i.
      4. Output field value = arithmetic mean of collected source values.
      5. If no source points lie within the disk, fall back to the single
         nearest source point.

    When a field name appears in ``square_fields``, an additional
    ``<name>_squared`` output field is computed as the mean of the squared
    source values over the same disk.

    Parameters
    ----------
    source_lon, source_lat : 1-D float arrays, degrees
    source_fields          : dict[str, 1-D float array]   same length as source_lon
    target_lon, target_lat : 1-D float arrays, degrees
    target_area            : 1-D float array, steradians
    square_fields          : iterable of field names to also return squared-mean
    alpha                  : search-radius scale factor (MBDA default = 1.0)
    workers                : cKDTree parallel workers (-1 = all cores)

    Returns
    -------
    results : dict[str, np.ndarray]
        Keys include every name in ``source_fields`` and, for each name in
        ``square_fields``, an additional ``<name>_squared`` entry.
    stats   : RemapStats
    """
    source_lon = np.asarray(source_lon, dtype=np.float64).ravel()
    source_lat = np.asarray(source_lat, dtype=np.float64).ravel()
    target_lon = np.asarray(target_lon, dtype=np.float64).ravel()
    target_lat = np.asarray(target_lat, dtype=np.float64).ravel()
    target_area = np.asarray(target_area, dtype=np.float64).ravel()

    if source_lon.shape != source_lat.shape:
        raise ValueError("source_lon and source_lat must have the same shape")
    if target_lon.shape != target_lat.shape != target_area.shape:
        raise ValueError("target_lon/lat/area must all have the same shape")

    n_source = source_lon.size
    n_target = target_lon.size

    square_set = set(square_fields)
    # validate all square_fields exist in source_fields
    missing = square_set - set(source_fields.keys())
    if missing:
        raise KeyError(f"square_fields refer to unknown source fields: {sorted(missing)}")

    # normalise source field arrays
    fields = {}
    for name, arr in source_fields.items():
        arr = np.asarray(arr, dtype=np.float64).ravel()
        if arr.size != n_source:
            raise ValueError(
                f"source field '{name}' has size {arr.size}, expected {n_source}"
            )
        fields[name] = arr

    # build spatial index on source Cartesian coords
    t0 = time.perf_counter()
    src_xyz = _lonlat_to_xyz(source_lon, source_lat)
    tree = cKDTree(src_xyz)
    t_build = time.perf_counter() - t0

    # per-target search radius (chord distance on unit sphere)
    # area is in steradians; r_arc = alpha * sqrt(area/pi) radians
    arc_radius = alpha * np.sqrt(np.maximum(target_area, 0.0) / np.pi)
    chord_cutoff = _arc_to_chord(arc_radius)

    tgt_xyz = _lonlat_to_xyz(target_lon, target_lat)

    # allocate outputs
    results: Dict[str, np.ndarray] = {
        name: np.full(n_target, _FILL_VALUE, dtype=np.float64)
        for name in fields
    }
    for name in square_set:
        results[f"{name}_squared"] = np.full(n_target, _FILL_VALUE, dtype=np.float64)

    # vectorised ball-point query — returns list of neighbour-index arrays
    t0 = time.perf_counter()
    # cKDTree.query_ball_point accepts an array of query points and a matching
    # array of radii (one per point).  This performs the per-target variable-
    # radius search in a single call.
    neighbour_lists = tree.query_ball_point(tgt_xyz, chord_cutoff, workers=workers)
    t_query = time.perf_counter() - t0

    # per-target averaging + fallback
    n_fallback = 0
    counts = np.zeros(n_target, dtype=np.int64)
    for i, idx in enumerate(neighbour_lists):
        if len(idx) == 0:
            # nearest-neighbour fallback (single closest source point)
            _, nn = tree.query(tgt_xyz[i], k=1, workers=workers)
            idx = [int(nn)]
            n_fallback += 1
        counts[i] = len(idx)
        idx_arr = np.asarray(idx, dtype=np.int64)
        for name, arr in fields.items():
            vals = arr[idx_arr]
            results[name][i] = float(vals.mean())
            if name in square_set:
                results[f"{name}_squared"][i] = float((vals * vals).mean())

    stats = RemapStats(
        n_source=n_source,
        n_target=n_target,
        n_fallback=n_fallback,
        min_neighbors=int(counts.min()) if n_target else 0,
        max_neighbors=int(counts.max()) if n_target else 0,
        mean_neighbors=float(counts.mean()) if n_target else 0.0,
        build_seconds=t_build,
        query_seconds=t_query,
    )
    return results, stats


#-------------------------------------------------------------------------------
# source auto-detection


def _detect_source_layout(ds: netCDF4.Dataset,
                          dof_var: Optional[str],
                          lon_var: Optional[str],
                          lat_var: Optional[str]) -> Tuple[str, str, str, str]:
    """
    Pick (layout, lon_name, lat_name, dim_name) for a source NetCDF dataset.

    layout is one of:
      'point1d' — 1-D lon/lat along an arbitrary dimension (e.g. ncol).
      'scrip'   — SCRIP-style: grid_center_lon/lat(grid_size) + grid_area.
      'rll2d'   — 2-D structured: lat(nlat), lon(nlon), fields on (nlat, nlon).
    """
    vars_ = ds.variables

    # 1) Explicit SCRIP request via --dof-var grid_size
    if dof_var == 'grid_size' or (
        lon_var is None and 'grid_center_lon' in vars_ and 'grid_center_lat' in vars_
    ):
        return ('scrip', 'grid_center_lon', 'grid_center_lat', 'grid_size')

    # 2) User-provided names
    if lon_var and lat_var:
        lon = vars_[lon_var]
        if lon.ndim == 1 and ds.variables[lat_var].ndim == 1:
            # could be either point-1d or rll-2d depending on shape relation
            if lon.dimensions == ds.variables[lat_var].dimensions:
                return ('point1d', lon_var, lat_var, lon.dimensions[0])
            return ('rll2d', lon_var, lat_var, '')
        raise ValueError(f"unsupported lon/lat rank for {lon_var}/{lat_var}")

    # 3) Auto-detect: prefer 1-D point cloud (lon(ncol), lat(ncol)),
    #    then fall back to 2-D RLL structured.
    for lname, ltname in (('lon', 'lat'), ('longitude', 'latitude')):
        if lname in vars_ and ltname in vars_:
            lon = vars_[lname]
            lat = vars_[ltname]
            if lon.ndim == 1 and lat.ndim == 1:
                if lon.dimensions == lat.dimensions:
                    return ('point1d', lname, ltname, lon.dimensions[0])
                # different 1-D dims → structured RLL
                return ('rll2d', lname, ltname, '')

    raise ValueError(
        "Could not auto-detect source coordinate layout.  "
        "Pass --lon-var / --lat-var (and optionally --dof-var) explicitly."
    )


def _load_source(source_path, fields, dof_var, lon_var, lat_var, area_var):
    """
    Open a NetCDF source file and return 1-D (lon, lat, {name: field_1d}).

    Handles all three layouts supported by MBDA.
    """
    with netCDF4.Dataset(str(source_path), 'r') as ds:
        layout, lon_name, lat_name, dim_name = _detect_source_layout(
            ds, dof_var, lon_var, lat_var
        )

        if layout in ('point1d', 'scrip'):
            lon = np.asarray(ds.variables[lon_name][:], dtype=np.float64).ravel()
            lat = np.asarray(ds.variables[lat_name][:], dtype=np.float64).ravel()
            out = {}
            for name in fields:
                v = ds.variables[name][:]
                out[name] = np.asarray(v, dtype=np.float64).ravel()
                if out[name].size != lon.size:
                    raise ValueError(
                        f"source field '{name}' size {out[name].size} does not match "
                        f"coordinate size {lon.size}"
                    )
            return lon, lat, out

        # rll2d: expand 1-D lat/lon to 2-D meshgrid, flatten fields
        lon_1d = np.asarray(ds.variables[lon_name][:], dtype=np.float64).ravel()
        lat_1d = np.asarray(ds.variables[lat_name][:], dtype=np.float64).ravel()
        out = {}
        for name in fields:
            v = np.asarray(ds.variables[name][:], dtype=np.float64)
            if v.ndim != 2:
                raise ValueError(
                    f"structured-RLL field '{name}' must be 2-D, got shape {v.shape}"
                )
            # determine axis order by matching dim lengths
            nlat, nlon = lat_1d.size, lon_1d.size
            if v.shape == (nlat, nlon):
                out[name] = v.ravel()
            elif v.shape == (nlon, nlat):
                out[name] = v.T.ravel()
            else:
                raise ValueError(
                    f"field '{name}' shape {v.shape} does not match "
                    f"lat/lon sizes ({nlat}, {nlon})"
                )
        lon2d, lat2d = np.meshgrid(lon_1d, lat_1d)
        return lon2d.ravel(), lat2d.ravel(), out


def _load_target(target_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load an MBDA-format target grid file: ncol dim + lon/lat/area(ncol).

    Returns (lon_deg, lat_deg, area_steradians).
    """
    with netCDF4.Dataset(str(target_path), 'r') as ds:
        vars_ = ds.variables
        if 'lon' in vars_ and 'lat' in vars_ and 'area' in vars_:
            lon = np.asarray(vars_['lon'][:], dtype=np.float64).ravel()
            lat = np.asarray(vars_['lat'][:], dtype=np.float64).ravel()
            area = np.asarray(vars_['area'][:], dtype=np.float64).ravel()
            return lon, lat, area
        # fall back to SCRIP in case someone passes the full SCRIP file
        if ('grid_center_lon' in vars_ and 'grid_center_lat' in vars_
                and 'grid_area' in vars_):
            lon = np.asarray(vars_['grid_center_lon'][:], dtype=np.float64).ravel()
            lat = np.asarray(vars_['grid_center_lat'][:], dtype=np.float64).ravel()
            area = np.asarray(vars_['grid_area'][:], dtype=np.float64).ravel()
            return lon, lat, area
    raise ValueError(
        f"target file {target_path} is missing lon/lat/area or "
        "grid_center_lon/lat + grid_area"
    )


#-------------------------------------------------------------------------------
# file I/O wrapper


def remap_files(
    source_path,
    target_path,
    output_path,
    fields: Sequence[str],
    square_fields: Sequence[str] = (),
    alpha: float = 1.0,
    dof_var: Optional[str] = None,
    lon_var: Optional[str] = None,
    lat_var: Optional[str] = None,
    area_var: Optional[str] = None,
    workers: int = -1,
    verbose: bool = True,
) -> RemapStats:
    """
    File-in / file-out equivalent of the compiled MBDA command line.

    Writes output to ``output_path`` as a CDF5 NetCDF file with dimension
    ``ncol`` and variables ``lon``, ``lat``, ``area`` (copied from the target
    MBDA file) plus every requested field (and its ``_squared`` partner for
    each ``square_fields`` entry).  ``_FillValue = 1.e+36`` is set on each
    output field to match MBDA.

    Returns the ``RemapStats`` for the remap call.
    """
    source_path = os.fspath(source_path)
    target_path = os.fspath(target_path)
    output_path = os.fspath(output_path)
    fields = list(fields)
    square_fields = list(square_fields)

    if verbose:
        print(f"  [taos.mbda] source: {source_path}")
        print(f"  [taos.mbda] target: {target_path}")
        print(f"  [taos.mbda] output: {output_path}")
        print(f"  [taos.mbda] fields: {fields}   squared: {square_fields}")

    # load source + target
    src_lon, src_lat, src_fields = _load_source(
        source_path, fields, dof_var, lon_var, lat_var, area_var
    )
    tgt_lon, tgt_lat, tgt_area = _load_target(target_path)

    if verbose:
        print(f"  [taos.mbda] source points: {src_lon.size:,}")
        print(f"  [taos.mbda] target cells : {tgt_lon.size:,}")

    # core remap
    results, stats = remap(
        src_lon, src_lat, src_fields,
        tgt_lon, tgt_lat, tgt_area,
        square_fields=square_fields,
        alpha=alpha,
        workers=workers,
    )

    if verbose:
        print(f"  [taos.mbda] tree build  : {stats.build_seconds:.2f} s")
        print(f"  [taos.mbda] ball query  : {stats.query_seconds:.2f} s")
        print(f"  [taos.mbda] neighbours/cell: "
              f"min={stats.min_neighbors} mean={stats.mean_neighbors:.1f} "
              f"max={stats.max_neighbors}")
        if stats.n_fallback:
            frac = stats.fallback_fraction() * 100.0
            msg = (f"  [taos.mbda] WARNING: {stats.n_fallback}/{stats.n_target} "
                   f"target cells ({frac:.2f}%) had empty search disks and used "
                   f"nearest-neighbour fallback")
            if frac > 1.0:
                msg += " — consider increasing alpha or using a denser source."
            print(msg)

    # write output (CDF5 to match _write_mbda in taos.grid)
    ncol = tgt_lon.size
    with netCDF4.Dataset(output_path, 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('ncol', ncol)
        nc.history = 'created by taos.mbda (Python MBDA replacement)'

        v = nc.createVariable('lon', 'f8', ('ncol',))
        v.units = 'degrees_east'
        v[:] = tgt_lon

        v = nc.createVariable('lat', 'f8', ('ncol',))
        v.units = 'degrees_north'
        v[:] = tgt_lat

        v = nc.createVariable('area', 'f8', ('ncol',))
        v.units = 'radians^2'
        v[:] = tgt_area

        for name in fields:
            v = nc.createVariable(name, 'f8', ('ncol',),
                                  fill_value=_FILL_VALUE)
            v[:] = results[name]
        for name in square_fields:
            sq_name = f'{name}_squared'
            v = nc.createVariable(sq_name, 'f8', ('ncol',),
                                  fill_value=_FILL_VALUE)
            v[:] = results[sq_name]

    return stats


#-------------------------------------------------------------------------------
# CLI


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='python -m taos.mbda',
        description='Pure-Python disk-averaged remap (MBDA replacement).',
    )
    p.add_argument('--source', required=True, help='source NetCDF file')
    p.add_argument('--target', required=True, help='target MBDA-format grid file')
    p.add_argument('--output', required=True, help='output NetCDF file')
    p.add_argument('--fields', required=True,
                   help='comma-separated list of source field names')
    p.add_argument('--square-fields', default='',
                   help='comma-separated list of fields to also emit as <f>_squared')
    p.add_argument('--alpha', type=float, default=1.0,
                   help='search-radius scale factor (default 1.0)')
    p.add_argument('--dof-var', default=None,
                   help='source coordinate dimension selector (e.g. grid_size for SCRIP)')
    p.add_argument('--lon-var', default=None, help='source longitude variable name')
    p.add_argument('--lat-var', default=None, help='source latitude variable name')
    p.add_argument('--area-var', default=None,
                   help='source area variable name (accepted for CLI compat; unused)')
    p.add_argument('--workers', type=int, default=-1,
                   help='cKDTree worker count (-1 = all cores)')
    p.add_argument('--quiet', action='store_true', help='suppress progress output')
    return p


def main(argv=None) -> int:
    args = _build_argparser().parse_args(argv)
    fields = [f for f in args.fields.split(',') if f]
    square_fields = [f for f in args.square_fields.split(',') if f]
    remap_files(
        source_path=args.source,
        target_path=args.target,
        output_path=args.output,
        fields=fields,
        square_fields=square_fields,
        alpha=args.alpha,
        dof_var=args.dof_var,
        lon_var=args.lon_var,
        lat_var=args.lat_var,
        area_var=args.area_var,
        workers=args.workers,
        verbose=not args.quiet,
    )
    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
