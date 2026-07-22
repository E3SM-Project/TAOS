"""
Unit tests for taos/mbda.py — pure-Python disk-averaged remap.

These tests are analytical / self-contained: they synthesise small
point-cloud sources and target grids and verify algebraic properties.
An optional integration test against the compiled MBDA binary is
skipped automatically when the binary is unavailable.

Run with:
    python -m pytest tests/test_mbda.py -v
"""
import os
import shutil
import tempfile
import unittest

import numpy as np
import netCDF4

from taos.mbda import (
    RemapStats,
    _arc_to_chord,
    _lonlat_to_xyz,
    remap,
    remap_files,
)


#-------------------------------------------------------------------------------
# helpers


def _fibonacci_sphere(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (lon_deg, lat_deg) for an approximately equi-area point set."""
    i = np.arange(n, dtype=np.float64) + 0.5
    phi = np.arccos(1.0 - 2.0 * i / n)              # colatitude
    theta = np.pi * (1.0 + 5.0 ** 0.5) * i          # golden-angle longitude
    lat = 90.0 - np.rad2deg(phi)
    lon = (np.rad2deg(theta) % 360.0) - 180.0
    return lon, lat


def _write_target_mbda(path, lon, lat, area):
    with netCDF4.Dataset(path, 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('ncol', lon.size)
        nc.createVariable('lon', 'f8', ('ncol',))[:] = lon
        nc.createVariable('lat', 'f8', ('ncol',))[:] = lat
        nc.createVariable('area', 'f8', ('ncol',))[:] = area


def _write_point_source(path, lon, lat, fields: dict):
    with netCDF4.Dataset(path, 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('ncol', lon.size)
        nc.createVariable('lon', 'f8', ('ncol',))[:] = lon
        nc.createVariable('lat', 'f8', ('ncol',))[:] = lat
        for name, arr in fields.items():
            nc.createVariable(name, 'f8', ('ncol',))[:] = arr


def _write_scrip_source(path, lon, lat, fields: dict):
    with netCDF4.Dataset(path, 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('grid_size', lon.size)
        nc.createVariable('grid_center_lon', 'f8', ('grid_size',))[:] = lon
        nc.createVariable('grid_center_lat', 'f8', ('grid_size',))[:] = lat
        nc.createVariable('grid_area', 'f8', ('grid_size',))[:] = \
            np.full(lon.size, 4.0 * np.pi / lon.size)
        for name, arr in fields.items():
            nc.createVariable(name, 'f8', ('grid_size',))[:] = arr


def _write_rll_source(path, lon_1d, lat_1d, fields_2d: dict):
    with netCDF4.Dataset(path, 'w', format='NETCDF3_64BIT_DATA') as nc:
        nc.createDimension('lon', lon_1d.size)
        nc.createDimension('lat', lat_1d.size)
        nc.createVariable('lon', 'f8', ('lon',))[:] = lon_1d
        nc.createVariable('lat', 'f8', ('lat',))[:] = lat_1d
        for name, arr in fields_2d.items():
            nc.createVariable(name, 'f8', ('lat', 'lon'))[:] = arr


#-------------------------------------------------------------------------------
# coordinate helpers


class TestCoordinateHelpers(unittest.TestCase):

    def test_xyz_unit_length(self):
        lon = np.array([0.0, 90.0, -45.0, 180.0])
        lat = np.array([0.0, 0.0, 30.0, -60.0])
        xyz = _lonlat_to_xyz(lon, lat)
        self.assertEqual(xyz.shape, (4, 3))
        norms = np.linalg.norm(xyz, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-14)

    def test_xyz_poles_and_equator(self):
        xyz = _lonlat_to_xyz(np.array([0.0, 0.0, 0.0]),
                             np.array([0.0, 90.0, -90.0]))
        np.testing.assert_allclose(xyz[0], [1.0, 0.0, 0.0], atol=1e-14)
        np.testing.assert_allclose(xyz[1], [0.0, 0.0, 1.0], atol=1e-14)
        np.testing.assert_allclose(xyz[2], [0.0, 0.0, -1.0], atol=1e-14)

    def test_arc_to_chord(self):
        # arc 0 → chord 0
        # arc π/2 → chord √2
        # arc π → chord 2 (antipode)
        arcs = np.array([0.0, np.pi / 2, np.pi])
        chords = _arc_to_chord(arcs)
        np.testing.assert_allclose(chords, [0.0, np.sqrt(2.0), 2.0], atol=1e-14)

    def test_arc_to_chord_capped(self):
        # values beyond pi should cap at chord = 2
        self.assertAlmostEqual(float(_arc_to_chord(np.array([2 * np.pi]))[0]), 2.0)


#-------------------------------------------------------------------------------
# core remap


class TestRemapCore(unittest.TestCase):

    def setUp(self):
        # 5k quasi-uniform sources, ~200 target cells
        self.src_lon, self.src_lat = _fibonacci_sphere(5000)
        self.tgt_lon, self.tgt_lat = _fibonacci_sphere(200)
        # each target covers area = 4π / N steradians
        self.tgt_area = np.full(self.tgt_lon.size, 4.0 * np.pi / self.tgt_lon.size)

    def test_constant_source_preserved(self):
        """A constant source field must give a constant output."""
        f = np.full(self.src_lon.size, 42.5)
        results, stats = remap(
            self.src_lon, self.src_lat, {'htopo': f},
            self.tgt_lon, self.tgt_lat, self.tgt_area,
            alpha=1.5,
        )
        self.assertEqual(stats.n_fallback, 0)
        np.testing.assert_allclose(results['htopo'], 42.5, atol=1e-12)

    def test_variance_non_negative(self):
        """mean(f^2) - mean(f)^2 >= 0 for all target cells."""
        rng = np.random.default_rng(0)
        f = rng.normal(100.0, 30.0, size=self.src_lon.size)
        results, _ = remap(
            self.src_lon, self.src_lat, {'htopo': f},
            self.tgt_lon, self.tgt_lat, self.tgt_area,
            square_fields=('htopo',),
            alpha=1.5,
        )
        var = results['htopo_squared'] - results['htopo'] ** 2
        self.assertTrue(np.all(var >= -1e-10),
                        f"negative variance: min={var.min()}")

    def test_squared_matches_manual_mean(self):
        """For a single large target, the squared field should equal the
        arithmetic mean of f^2 over the source points inside the disk."""
        # one target covering the whole sphere
        tgt_lon = np.array([0.0])
        tgt_lat = np.array([0.0])
        tgt_area = np.array([4.0 * np.pi])  # full sphere
        rng = np.random.default_rng(1)
        f = rng.uniform(-10.0, 10.0, size=self.src_lon.size)
        results, stats = remap(
            self.src_lon, self.src_lat, {'v': f},
            tgt_lon, tgt_lat, tgt_area,
            square_fields=('v',),
            alpha=2.0,
        )
        self.assertEqual(stats.n_fallback, 0)
        self.assertAlmostEqual(results['v'][0], float(f.mean()), places=12)
        self.assertAlmostEqual(results['v_squared'][0],
                               float((f * f).mean()), places=10)

    def test_empty_disk_triggers_fallback(self):
        """Tiny area with a sparse source → fallback to nearest neighbour."""
        src_lon = np.array([0.0, 180.0])
        src_lat = np.array([0.0, 0.0])
        f = np.array([1.0, -7.0])
        # target near (1,0) with an area so small no points fit in the disk
        tgt_lon = np.array([1.0])
        tgt_lat = np.array([0.0])
        tgt_area = np.array([1e-12])  # radius ~5.6e-7 rad → chord tiny
        results, stats = remap(
            src_lon, src_lat, {'f': f},
            tgt_lon, tgt_lat, tgt_area,
        )
        self.assertEqual(stats.n_fallback, 1)
        # nearest source is (0,0) with value 1.0
        self.assertAlmostEqual(results['f'][0], 1.0, places=12)

    def test_unknown_square_field_raises(self):
        f = np.zeros(self.src_lon.size)
        with self.assertRaises(KeyError):
            remap(self.src_lon, self.src_lat, {'f': f},
                  self.tgt_lon, self.tgt_lat, self.tgt_area,
                  square_fields=('missing',))

    def test_mismatched_field_size_raises(self):
        f = np.zeros(self.src_lon.size - 1)
        with self.assertRaises(ValueError):
            remap(self.src_lon, self.src_lat, {'f': f},
                  self.tgt_lon, self.tgt_lat, self.tgt_area)


#-------------------------------------------------------------------------------
# source auto-detection + file I/O


class TestRemapFiles(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='taos_mbda_test_')
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

        # small quasi-uniform target
        tlon, tlat = _fibonacci_sphere(50)
        tarea = np.full(50, 4.0 * np.pi / 50)
        self.target = os.path.join(self.tmpdir, 'target.nc')
        _write_target_mbda(self.target, tlon, tlat, tarea)
        self.target_lon = tlon
        self.target_lat = tlat

    def _check_output(self, path, fields, square_fields):
        with netCDF4.Dataset(path, 'r') as nc:
            self.assertEqual(nc.dimensions['ncol'].size, self.target_lon.size)
            self.assertIn('lon', nc.variables)
            self.assertIn('lat', nc.variables)
            self.assertIn('area', nc.variables)
            for f in fields:
                self.assertIn(f, nc.variables)
                self.assertEqual(nc.variables[f].shape, (self.target_lon.size,))
            for f in square_fields:
                self.assertIn(f + '_squared', nc.variables)

    def test_point1d_source(self):
        slon, slat = _fibonacci_sphere(2000)
        src = os.path.join(self.tmpdir, 'src_point.nc')
        _write_point_source(src, slon, slat, {'htopo': np.full(slon.size, 3.14)})
        out = os.path.join(self.tmpdir, 'out_point.nc')
        remap_files(src, self.target, out, fields=['htopo'], verbose=False)
        self._check_output(out, ['htopo'], [])
        with netCDF4.Dataset(out) as nc:
            np.testing.assert_allclose(nc.variables['htopo'][:], 3.14, atol=1e-12)

    def test_scrip_source_dof_var(self):
        slon, slat = _fibonacci_sphere(2000)
        src = os.path.join(self.tmpdir, 'src_scrip.nc')
        _write_scrip_source(src, slon, slat, {'htopo': np.full(slon.size, -1.0)})
        out = os.path.join(self.tmpdir, 'out_scrip.nc')
        remap_files(src, self.target, out, fields=['htopo'],
                    square_fields=['htopo'], dof_var='grid_size', verbose=False)
        self._check_output(out, ['htopo'], ['htopo'])
        with netCDF4.Dataset(out) as nc:
            np.testing.assert_allclose(nc.variables['htopo'][:], -1.0, atol=1e-12)
            np.testing.assert_allclose(nc.variables['htopo_squared'][:], 1.0,
                                       atol=1e-12)

    def test_rll2d_source(self):
        # regular 2-D lat-lon grid (72x36) with a field = latitude
        lon_1d = np.linspace(-180.0, 175.0, 72)
        lat_1d = np.linspace(-87.5, 87.5, 36)
        lat_2d = np.broadcast_to(lat_1d[:, None], (36, 72)).copy()
        src = os.path.join(self.tmpdir, 'src_rll.nc')
        _write_rll_source(src, lon_1d, lat_1d, {'elev': lat_2d})
        out = os.path.join(self.tmpdir, 'out_rll.nc')
        remap_files(src, self.target, out, fields=['elev'], verbose=False)
        self._check_output(out, ['elev'], [])
        with netCDF4.Dataset(out) as nc:
            # averaged source "elev = lat" should approximately track target lat
            elev = nc.variables['elev'][:]
            self.assertEqual(elev.shape, (self.target_lon.size,))
            # loose bound: within ±6° given the coarse RLL grid
            self.assertTrue(np.all(np.abs(elev - self.target_lat) < 6.0),
                            f"max deviation {np.max(np.abs(elev - self.target_lat))}")

    def test_fill_value_attr_written(self):
        slon, slat = _fibonacci_sphere(1000)
        src = os.path.join(self.tmpdir, 'src_fv.nc')
        _write_point_source(src, slon, slat, {'htopo': np.ones(slon.size)})
        out = os.path.join(self.tmpdir, 'out_fv.nc')
        remap_files(src, self.target, out, fields=['htopo'], verbose=False)
        with netCDF4.Dataset(out) as nc:
            self.assertAlmostEqual(float(nc.variables['htopo']._FillValue), 1e36)


#-------------------------------------------------------------------------------
# optional comparison against the compiled MBDA binary


def _find_mbda_bin() -> str:
    """Locate the compiled MBDA binary for the integration test.

    TAOS_TEST_MBDA_PATH takes precedence; otherwise fall back to the
    auto-detected machine's mbda_path from taos/machines.yaml. Returns
    '' when neither yields a usable path (test is skipped).
    """
    path = os.environ.get('TAOS_TEST_MBDA_PATH', '')
    if path:
        return path
    try:
        from taos.config import detect_machine, load_machines
        machines = load_machines()
        machine = detect_machine(machines)
        default = machines[machine].get('paths', {}).get('mbda_path', '') or ''
        return os.path.expandvars(os.path.expanduser(default))
    except Exception:
        return ''


_MBDA_BIN = _find_mbda_bin()


@unittest.skipIf(not _MBDA_BIN or not os.path.isfile(_MBDA_BIN),
                 "compiled MBDA binary not available "
                 "(set TAOS_TEST_MBDA_PATH or machines.yaml mbda_path to enable)")
class TestAgainstCompiledMBDA(unittest.TestCase):
    """
    Integration check — only runs when TAOS_TEST_MBDA_PATH points at a
    real ``mbda`` executable.  Compares Python remap output against
    compiled MBDA on a small point cloud.
    """

    def test_small_comparison(self):  # pragma: no cover - HPC-only
        import subprocess as sp
        tmpdir = tempfile.mkdtemp(prefix='taos_mbda_compare_')
        self.addCleanup(shutil.rmtree, tmpdir, ignore_errors=True)

        slon, slat = _fibonacci_sphere(20000)
        rng = np.random.default_rng(42)
        f = rng.normal(500.0, 200.0, size=slon.size)
        src = os.path.join(tmpdir, 'src.nc')
        _write_scrip_source(src, slon, slat, {'htopo': f})

        tlon, tlat = _fibonacci_sphere(100)
        tarea = np.full(100, 4.0 * np.pi / 100)
        tgt = os.path.join(tmpdir, 'tgt.nc')
        _write_target_mbda(tgt, tlon, tlat, tarea)

        py_out = os.path.join(tmpdir, 'py.nc')
        cc_out = os.path.join(tmpdir, 'cc.nc')

        remap_files(src, tgt, py_out, fields=['htopo'],
                    square_fields=['htopo'], dof_var='grid_size', verbose=False)
        # Note: no --dof-var here — mbda applies it to the TARGET mesh
        # dimension (default 'ncol'), not the source; the SCRIP source
        # layout is auto-detected. PNETCDF_HINTS pins the classic MPI-IO
        # driver: PnetCDF 1.15.0's new GIO Lustre driver SIGFPEs on open
        # (observed on OLCF Andes, July 2026).
        env = dict(os.environ)
        env.setdefault('PNETCDF_HINTS', 'nc_driver=mpiio')
        sp.run([_MBDA_BIN, '--target', tgt, '--source', src, '--output', cc_out,
                '--fields', 'htopo', '--square-fields', 'htopo'],
               check=True, env=env)

        with netCDF4.Dataset(py_out) as py, netCDF4.Dataset(cc_out) as cc:
            py_f = py.variables['htopo'][:]
            cc_f = cc.variables['htopo'][:]
            py_sq = py.variables['htopo_squared'][:]
            cc_sq = cc.variables['htopo_squared'][:]
        # allow O(1e-10) rel diff for summation order
        self.assertLess(np.max(np.abs(py_f - cc_f) / (np.abs(cc_f) + 1.0)), 1e-10)
        self.assertLess(np.max(np.abs(py_sq - cc_sq) / (np.abs(cc_sq) + 1.0)), 1e-8)


if __name__ == '__main__':
    unittest.main()
