"""
Unit tests for taos/grid.py.

These tests cover pure-Python logic (command-string construction, path checks)
without requiring any HPC tools, SLURM, or real files on disk.
run_cmd() and os.path.exists() are mocked throughout.

The np4 SCRIP generation tests use the same synthetic ne=1 cube-sphere mesh
as tests/test_sem.py — 6 elements, 8 nodes, 56 unique GLL nodes.

Run with:
    python -m pytest tests/test_grid.py
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, MagicMock, patch

import netCDF4
import numpy as np

from taos.grid import (
    _compute_np4_scrip_fields,
    _create_np4_scrip,
    _grid_paths,
    _write_mbda,
    _write_scrip,
    create_grid,
)

# ---------------------------------------------------------------------------
# synthetic ne=1 cube-sphere mesh fixture (shared with test_sem.py)

_S3 = 1.0 / np.sqrt(3.0)

_NE1_COORDS = _S3 * np.array([
    [-1, -1, -1],  # 0
    [ 1, -1, -1],  # 1
    [ 1,  1, -1],  # 2
    [-1,  1, -1],  # 3
    [-1, -1,  1],  # 4
    [ 1, -1,  1],  # 5
    [ 1,  1,  1],  # 6
    [-1,  1,  1],  # 7
], dtype=float)

_NE1_CONNECT = np.array([
    [0, 1, 2, 3],  # −z face
    [4, 5, 6, 7],  # +z face
    [0, 1, 5, 4],  # −y face
    [3, 2, 6, 7],  # +y face
    [0, 3, 7, 4],  # −x face
    [1, 2, 6, 5],  # +x face
])

# ---------------------------------------------------------------------------
# _compute_np4_scrip_fields


class TestComputeNp4ScripFields(unittest.TestCase):

    def setUp(self):
        self.lon, self.lat, self.area, self.corner_lon, self.corner_lat = \
            _compute_np4_scrip_fields(_NE1_COORDS, _NE1_CONNECT)

    def test_ncol(self):
        # ne=1, np=4: ncol = 6*1^2*(4-1)^2 + 2 = 56
        self.assertEqual(len(self.lon), 56)

    def test_shapes(self):
        self.assertEqual(self.lon.shape,        (56,))
        self.assertEqual(self.lat.shape,        (56,))
        self.assertEqual(self.area.shape,       (56,))
        self.assertEqual(self.corner_lon.shape, (56, 8))
        self.assertEqual(self.corner_lat.shape, (56, 8))

    def test_lon_range(self):
        self.assertTrue(np.all(self.lon >= 0.0))
        self.assertTrue(np.all(self.lon < 360.0))

    def test_lat_range(self):
        self.assertTrue(np.all(self.lat >= -90.0))
        self.assertTrue(np.all(self.lat <=  90.0))

    def test_corner_lon_range(self):
        self.assertTrue(np.all(self.corner_lon >= 0.0))
        self.assertTrue(np.all(self.corner_lon < 360.0))

    def test_corner_lat_range(self):
        self.assertTrue(np.all(self.corner_lat >= -90.0))
        self.assertTrue(np.all(self.corner_lat <=  90.0))

    def test_area_positive(self):
        self.assertTrue(np.all(self.area > 0))

    def test_total_area_near_4pi(self):
        np.testing.assert_allclose(np.sum(self.area), 4 * np.pi, rtol=0.05)


# ---------------------------------------------------------------------------
# _write_scrip


class TestWriteScrip(unittest.TestCase):

    def setUp(self):
        self.lon        = np.array([10.0, 90.0])
        self.lat        = np.array([-30.0, 45.0])
        self.area       = np.array([0.5, 1.5])
        self.corner_lon = np.zeros((2, 4))
        self.corner_lat = np.zeros((2, 4))

    def test_scrip_variables_present(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/scrip.nc'
            _write_scrip(path, self.lon, self.lat, self.area,
                         self.corner_lon, self.corner_lat)
            with netCDF4.Dataset(path) as nc:
                for var in ('grid_dims', 'grid_center_lat', 'grid_center_lon',
                            'grid_imask', 'grid_area',
                            'grid_corner_lat', 'grid_corner_lon'):
                    self.assertIn(var, nc.variables, f'{var} missing from SCRIP file')

    def test_scrip_dimensions(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/scrip.nc'
            _write_scrip(path, self.lon, self.lat, self.area,
                         self.corner_lon, self.corner_lat)
            with netCDF4.Dataset(path) as nc:
                self.assertEqual(len(nc.dimensions['grid_size']),    2)
                self.assertEqual(len(nc.dimensions['grid_corners']), 4)  # driven by input shape
                self.assertEqual(len(nc.dimensions['grid_rank']),    1)
                np.testing.assert_array_equal(nc.variables['grid_dims'][:], [2])

    def test_scrip_center_values(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/scrip.nc'
            _write_scrip(path, self.lon, self.lat, self.area,
                         self.corner_lon, self.corner_lat)
            with netCDF4.Dataset(path) as nc:
                np.testing.assert_allclose(nc.variables['grid_center_lon'][:], self.lon)
                np.testing.assert_allclose(nc.variables['grid_center_lat'][:], self.lat)
                np.testing.assert_allclose(nc.variables['grid_area'][:],       self.area)

    def test_scrip_imask_all_ones(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/scrip.nc'
            _write_scrip(path, self.lon, self.lat, self.area,
                         self.corner_lon, self.corner_lat)
            with netCDF4.Dataset(path) as nc:
                np.testing.assert_array_equal(nc.variables['grid_imask'][:], [1, 1])


# ---------------------------------------------------------------------------
# _write_mbda


class TestWriteMbda(unittest.TestCase):

    def setUp(self):
        self.lon  = np.array([10.0, 90.0])
        self.lat  = np.array([-30.0, 45.0])
        self.area = np.array([0.5, 1.5])

    def test_mbda_variables_present(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/mbda.nc'
            _write_mbda(path, self.lon, self.lat, self.area)
            with netCDF4.Dataset(path) as nc:
                for var in ('lon', 'lat', 'area'):
                    self.assertIn(var, nc.variables, f'{var} missing from MBDA file')
                self.assertIn('ncol', nc.dimensions)

    def test_mbda_dimension_size(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/mbda.nc'
            _write_mbda(path, self.lon, self.lat, self.area)
            with netCDF4.Dataset(path) as nc:
                self.assertEqual(len(nc.dimensions['ncol']), 2)

    def test_mbda_values(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/mbda.nc'
            _write_mbda(path, self.lon, self.lat, self.area)
            with netCDF4.Dataset(path) as nc:
                np.testing.assert_allclose(nc.variables['lon'][:],  self.lon)
                np.testing.assert_allclose(nc.variables['lat'][:],  self.lat)
                np.testing.assert_allclose(nc.variables['area'][:], self.area)

    def test_mbda_format_is_cdf5(self):
        with tempfile.TemporaryDirectory() as d:
            path = f'{d}/mbda.nc'
            _write_mbda(path, self.lon, self.lat, self.area)
            with netCDF4.Dataset(path) as nc:
                self.assertEqual(nc.data_model, 'NETCDF3_64BIT_DATA')


# ---------------------------------------------------------------------------
# helpers

class MockConfig:
    """Stand-in for taos_config that uses the legacy homme_tool np4 path."""

    _data = {
        'grid.name':              'ne30',
        'derived.grid_root':      '/data/grids',
        'paths.homme_tool_root':  '/homme',
        'paths.unified_bin':      '/unified/bin',
        'paths.e3sm_src_root':    '/e3sm',
        'grid.homme_np4_scrip':   True,     # exercise the legacy homme path
    }

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


class MockConfigPython:
    """Stand-in for taos_config that uses the default Python np4 path."""

    _data = {
        'grid.name':            'ne30',
        'derived.grid_root':    '/data/grids',
        'paths.unified_bin':    '/unified/bin',
        'paths.e3sm_src_root':  '/e3sm',
        # no 'paths.homme_tool_root' — not needed for Python path
        # no 'grid.homme_np4_scrip' — defaults to False (Python path)
    }

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


# ---------------------------------------------------------------------------
# _grid_paths

class TestGridPaths(unittest.TestCase):

    def setUp(self):
        self.p = _grid_paths(MockConfig())

    def test_grid_file_exodus(self):
        self.assertEqual(self.p['grid_file_exodus'], '/data/grids/ne30.g')

    def test_grid_file_np4_scrip(self):
        self.assertEqual(self.p['grid_file_np4_scrip'], '/data/grids/ne30np4_scrip.nc')

    def test_grid_file_np4_mbda(self):
        self.assertEqual(self.p['grid_file_np4_mbda'], '/data/grids/ne30np4_mbda.nc')

    def test_grid_file_pg2_scrip(self):
        self.assertEqual(self.p['grid_file_pg2_scrip'], '/data/grids/ne30pg2_scrip.nc')

    def test_grid_file_pg2_mbda(self):
        self.assertEqual(self.p['grid_file_pg2_mbda'], '/data/grids/ne30pg2_mbda.nc')

    def test_grid_file_3km_exodus(self):
        self.assertEqual(self.p['grid_file_3km_exodus'], '/data/grids/ne3000.g')

    def test_grid_file_3km_scrip(self):
        self.assertEqual(self.p['grid_file_3km_scrip'], '/data/grids/ne3000pg1_scrip.nc')

    def test_grid_file_3km_mbda(self):
        self.assertEqual(self.p['grid_file_3km_mbda'], '/data/grids/ne3000pg1_mbda.nc')

    def test_grid_template_file(self):
        self.assertEqual(self.p['grid_template_file'], '/homme/ne30_ne0np4_tmp1.nc')

    def test_nl_file(self):
        self.assertEqual(self.p['nl_file'], '/homme/input.grd.ne30.nl')


# ---------------------------------------------------------------------------
# create_grid — main command tests
#
# Default scenario: no stale template (exists[0]=False), all outputs succeed,
# 3km_mbda already present (skip creation).
#   exists call order:
#     [0] grid_template_file  — stale check        → False (no rm)
#     [1] grid_template_file  — success check       → True
#     [2] grid_file_np4_mbda  — success check       → True
#     [3] grid_file_pg2_mbda  — success check       → True
#     [4] grid_file_3km_mbda  — already-exists check → True (skip)

class TestCreateGridCommands(unittest.TestCase):

    _DEFAULT_EXISTS = [False, True, True, True, True]

    def _run(self, exists_side_effect=None):
        """Execute create_grid with mocked run_cmd and os.path.exists."""
        if exists_side_effect is None:
            exists_side_effect = list(self._DEFAULT_EXISTS)
        with patch('taos.grid.run_cmd') as mock_run, \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            create_grid(MockConfig())
        return mock_run

    def _all_cmds(self, mock_run):
        return [c.args[0] for c in mock_run.call_args_list]

    # ------------------------------------------------------------------
    # homme_tool invocation

    def test_homme_tool_command(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        matching = [c for c in cmds if 'srun' in c and 'homme_tool' in c]
        self.assertEqual(len(matching), 1)
        nl_file = _grid_paths(MockConfig())['nl_file']
        self.assertIn(nl_file, matching[0])

    # ------------------------------------------------------------------
    # HOMME2SCRIP conversion

    def test_homme2scrip_command(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        matching = [c for c in cmds if 'HOMME2SCRIP.py' in c]
        self.assertEqual(len(matching), 1)
        self.assertIn('--src_file', matching[0])
        self.assertIn('--dst_file', matching[0])

    # ------------------------------------------------------------------
    # np4 MBDA file creation

    def test_np4_mbda_commands(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        p = _grid_paths(MockConfig())
        ncap2_cmds = [c for c in cmds
                      if 'ncap2' in c and p['grid_file_np4_scrip'] in c]
        self.assertEqual(len(ncap2_cmds), 1)
        ncrename_cmds = [c for c in cmds
                         if 'ncrename' in c and p['grid_file_np4_mbda'] in c]
        self.assertEqual(len(ncrename_cmds), 1)

    # ------------------------------------------------------------------
    # PG2 exodus and SCRIP

    def test_pg2_commands(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        vol_cmds = [c for c in cmds if 'GenerateVolumetricMesh' in c]
        self.assertEqual(len(vol_cmds), 1)
        scrip_cmds = [c for c in cmds if 'ConvertMeshToSCRIP' in c]
        self.assertEqual(len(scrip_cmds), 1)

    # ------------------------------------------------------------------
    # PG2 MBDA file creation

    def test_pg2_mbda_commands(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        p = _grid_paths(MockConfig())
        ncap2_cmds = [c for c in cmds
                      if 'ncap2' in c and p['grid_file_pg2_scrip'] in c]
        self.assertEqual(len(ncap2_cmds), 1)
        ncrename_cmds = [c for c in cmds
                         if 'ncrename' in c and p['grid_file_pg2_mbda'] in c]
        self.assertEqual(len(ncrename_cmds), 1)

    # ------------------------------------------------------------------
    # 3km grid skipped when already present

    def test_3km_skipped_when_exists(self):
        mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        self.assertFalse(any('GenerateCSMesh' in c for c in cmds))

    # ------------------------------------------------------------------
    # stale template removal

    def test_stale_template_removed(self):
        # First call for grid_template_file → True (stale file present)
        exists_side_effect = [True, True, True, True, True]
        with patch('taos.grid.run_cmd') as mock_run, \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            create_grid(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        rm_cmds = [c for c in cmds if c.startswith('rm ')]
        self.assertEqual(len(rm_cmds), 1)
        self.assertIn(_grid_paths(MockConfig())['grid_template_file'], rm_cmds[0])

    # ------------------------------------------------------------------
    # RuntimeError when homme_tool output missing

    def test_raises_when_homme_tool_fails(self):
        # exists[1] (grid_template_file success check) → False
        exists_side_effect = [False, False, True, True, True]
        with patch('taos.grid.run_cmd'), \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            with self.assertRaises(RuntimeError) as ctx:
                create_grid(MockConfig())
        self.assertIn('homme_tool', str(ctx.exception))

    # ------------------------------------------------------------------
    # RuntimeError when np4 MBDA file missing

    def test_raises_when_np4_mbda_missing(self):
        # exists[2] (np4_mbda success check) → False
        exists_side_effect = [False, True, False, True, True]
        with patch('taos.grid.run_cmd'), \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            with self.assertRaises(RuntimeError) as ctx:
                create_grid(MockConfig())
        self.assertIn('np4', str(ctx.exception))

    # ------------------------------------------------------------------
    # RuntimeError when pg2 MBDA file missing

    def test_raises_when_pg2_mbda_missing(self):
        # exists[3] (pg2_mbda success check) → False
        exists_side_effect = [False, True, True, False, True]
        with patch('taos.grid.run_cmd'), \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            with self.assertRaises(RuntimeError) as ctx:
                create_grid(MockConfig())
        self.assertIn('pg2', str(ctx.exception))

    # ------------------------------------------------------------------
    # 3km grid created when missing
    #   exists call order with 3km creation path:
    #     [0] grid_template_file  — stale check        → False
    #     [1] grid_template_file  — success check       → True
    #     [2] grid_file_np4_mbda  — success check       → True
    #     [3] grid_file_pg2_mbda  — success check       → True
    #     [4] grid_file_3km_mbda  — already-exists check → False (create)
    #     [5] grid_file_3km_exodus — success check      → True
    #     [6] grid_file_3km_scrip  — success check      → True

    def test_3km_created_when_missing(self):
        exists_side_effect = [False, True, True, True, False, True, True]
        with patch('taos.grid.run_cmd') as mock_run, \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect), \
             patch('pathlib.Path.write_text'):
            create_grid(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertTrue(any('GenerateCSMesh' in c for c in cmds))

    # ------------------------------------------------------------------
    # namelist written correctly

    def test_namelist_written(self):
        captured = {}

        def fake_write_text(self_path, content):
            captured['content'] = content

        with patch('taos.grid.run_cmd'), \
             patch('taos.grid.os.path.exists', side_effect=list(self._DEFAULT_EXISTS)), \
             patch('pathlib.Path.write_text', fake_write_text):
            create_grid(MockConfig())

        self.assertIn('content', captured)
        nl = captured['content']
        self.assertIn('mesh_file', nl)
        self.assertIn('grid_template_tool', nl)
        self.assertIn('ne30_', nl)


# ---------------------------------------------------------------------------
# create_grid — Python np4 path (default)
#
# With no 'grid.homme_np4_scrip' key (or set to False), create_grid calls
# _create_np4_scrip instead of homme_tool.  _create_np4_scrip is mocked so
# no real Exodus file is needed.
#
# os.path.exists call order (Python path):
#   [0] grid_file_np4_mbda  — success check       → True
#   [1] grid_file_pg2_mbda  — success check       → True
#   [2] grid_file_3km_mbda  — already-exists check → True (skip)

class TestCreateGridPythonPath(unittest.TestCase):

    _DEFAULT_EXISTS = [True, True, True]

    def _run(self, exists_side_effect=None):
        if exists_side_effect is None:
            exists_side_effect = list(self._DEFAULT_EXISTS)
        with patch('taos.grid._create_np4_scrip') as mock_scrip, \
             patch('taos.grid.run_cmd') as mock_run, \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect):
            create_grid(MockConfigPython())
        return mock_scrip, mock_run

    def _all_cmds(self, mock_run):
        return [c.args[0] for c in mock_run.call_args_list]

    # ------------------------------------------------------------------
    # _create_np4_scrip is called with the correct paths

    def test_create_np4_scrip_called(self):
        mock_scrip, _ = self._run()
        mock_scrip.assert_called_once()
        args = mock_scrip.call_args.args
        p = _grid_paths(MockConfigPython())
        self.assertEqual(args[0], p['grid_file_exodus'])
        self.assertEqual(args[1], p['grid_file_np4_scrip'])
        self.assertEqual(args[2], p['grid_file_np4_mbda'])

    # ------------------------------------------------------------------
    # homme_tool and HOMME2SCRIP are not invoked

    def test_no_homme_tool(self):
        _, mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        self.assertFalse(any('homme_tool' in c for c in cmds))

    def test_no_homme2scrip(self):
        _, mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        self.assertFalse(any('HOMME2SCRIP' in c for c in cmds))

    def test_no_ncap2_for_np4(self):
        _, mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        p = _grid_paths(MockConfigPython())
        np4_ncap2 = [c for c in cmds if 'ncap2' in c and p['grid_file_np4_scrip'] in c]
        self.assertEqual(len(np4_ncap2), 0)

    # ------------------------------------------------------------------
    # PG2 and 3km steps are unchanged

    def test_pg2_commands_present(self):
        _, mock_run = self._run()
        cmds = self._all_cmds(mock_run)
        self.assertTrue(any('GenerateVolumetricMesh' in c for c in cmds))
        self.assertTrue(any('ConvertMeshToSCRIP'      in c for c in cmds))

    def test_raises_when_np4_mbda_missing(self):
        exists_side_effect = [False, True, True]
        with patch('taos.grid._create_np4_scrip'), \
             patch('taos.grid.run_cmd'), \
             patch('taos.grid.os.path.exists', side_effect=exists_side_effect):
            with self.assertRaises(RuntimeError) as ctx:
                create_grid(MockConfigPython())
        self.assertIn('np4', str(ctx.exception))


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
