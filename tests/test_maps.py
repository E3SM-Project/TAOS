"""
Unit tests for taos/maps.py.

These tests cover pure-Python logic (command-string construction, path checks)
without requiring any HPC tools, SLURM, or real files on disk.
run_cmd() and os.path.exists() are mocked throughout.

Run with:
    python -m pytest tests/test_maps.py
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import call, MagicMock, patch


import taos.maps as maps_mod
from taos.maps import (
    _check_map,
    _ncremap_pair,
    _unified_env_prefix,
    create_maps_lnd,
    create_maps_ocn,
    create_maps_spa,
)

# ---------------------------------------------------------------------------
# helpers

class MockConfig:
    """Minimal stand-in for taos_config with fixed test values."""

    _data = {
        'paths.unified_src':  '/tools/unified.sh',
        'grid.name':          'ne30',
        'grid.name_pg2':      'ne30pg2',
        'grid.ocn_name':      'oEC60to30v3',
        'grid.ocn_file':      '/grids/oEC60to30v3_scrip.nc',
        'grid.lnd_name':      'r05_r05',
        'grid.lnd_file':      '/grids/r05_r05_scrip.nc',
        'grid.spa_name':      'ne30pg2',
        'grid.spa_file':      '/grids/ne30pg2_scrip.nc',
        'derived.maps_root':  '/data/maps',
        'derived.grid_root':  '/data/grids',
        'project.timestamp':  '20260101',
    }

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


# ---------------------------------------------------------------------------
# _unified_env_prefix

class TestUnifiedEnvPrefix(unittest.TestCase):

    def test_returns_source_command(self):
        cfg = MockConfig()
        result = _unified_env_prefix(cfg)
        self.assertEqual(result, 'source /tools/unified.sh')


# ---------------------------------------------------------------------------
# _check_map

class TestCheckMap(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    def test_passes_when_file_exists(self, _mock_exists):
        _check_map('/some/map.nc')  # should not raise

    @patch('os.path.exists', return_value=False)
    def test_raises_when_file_missing(self, _mock_exists):
        with self.assertRaises(RuntimeError) as ctx:
            _check_map('/some/missing.nc')
        self.assertIn('/some/missing.nc', str(ctx.exception))


# ---------------------------------------------------------------------------
# _ncremap_pair

class TestNcremapPair(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_command_without_a2o(self, mock_run, _mock_exists):
        _ncremap_pair(
            env_prefix='source /tools/unified.sh',
            alg='traave',
            src_file='/grids/ocn.nc',
            dst_file='/grids/atm.nc',
            map_file='/maps/map_ocn_to_atm_traave.nc',
        )
        expected = (
            'source /tools/unified.sh &&'
            ' ncremap --alg_typ=traave'
            ' --grd_src="/grids/ocn.nc" --grd_dst="/grids/atm.nc"'
            ' --map_fl="/maps/map_ocn_to_atm_traave.nc"'
        )
        mock_run.assert_called_once_with(expected)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_command_with_a2o_flag(self, mock_run, _mock_exists):
        _ncremap_pair(
            env_prefix='source /tools/unified.sh',
            alg='trbilin',
            src_file='/grids/atm.nc',
            dst_file='/grids/ocn.nc',
            map_file='/maps/map_atm_to_ocn_trbilin.nc',
            a2o=True,
        )
        expected = (
            'source /tools/unified.sh &&'
            ' ncremap --a2o --alg_typ=trbilin'
            ' --grd_src="/grids/atm.nc" --grd_dst="/grids/ocn.nc"'
            ' --map_fl="/maps/map_atm_to_ocn_trbilin.nc"'
        )
        mock_run.assert_called_once_with(expected)

    @patch('os.path.exists', return_value=False)
    @patch('taos.maps.run_cmd')
    def test_raises_when_output_missing(self, _mock_run, _mock_exists):
        with self.assertRaises(RuntimeError):
            _ncremap_pair(
                env_prefix='source /tools/unified.sh',
                alg='traave',
                src_file='/grids/ocn.nc',
                dst_file='/grids/atm.nc',
                map_file='/maps/map.nc',
            )


# ---------------------------------------------------------------------------
# create_maps_ocn

class TestCreateMapsOcn(unittest.TestCase):

    _ALGORITHMS = ['traave', 'trbilin', 'trfv2', 'trintbilin']
    _ENV        = 'source /tools/unified.sh'
    _ATM        = '/data/grids/ne30pg2_scrip.nc'
    _OCN        = '/grids/oEC60to30v3_scrip.nc'
    _MAPS       = '/data/maps'
    _TS         = '20260101'

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_calls_run_cmd_eight_times(self, mock_run, _mock_exists):
        create_maps_ocn(MockConfig())
        # 4 algorithms × 2 directions = 8 ncremap calls
        self.assertEqual(mock_run.call_count, 8)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_all_algorithms_used(self, mock_run, _mock_exists):
        create_maps_ocn(MockConfig())
        all_cmds = ' '.join(c.args[0] for c in mock_run.call_args_list)
        for alg in self._ALGORITHMS:
            self.assertIn(f'--alg_typ={alg}', all_cmds)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_forward_map_filenames(self, mock_run, _mock_exists):
        """ocn → atm maps should not have --a2o flag."""
        create_maps_ocn(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            expected_map = (
                f'{self._MAPS}/map_oEC60to30v3_to_ne30pg2_{alg}.{self._TS}.nc'
            )
            matching = [c for c in cmds if expected_map in c]
            self.assertEqual(len(matching), 1, f'Missing forward map for {alg}')
            self.assertNotIn('--a2o', matching[0])

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_reverse_map_filenames_have_a2o(self, mock_run, _mock_exists):
        """atm → ocn maps should have --a2o flag."""
        create_maps_ocn(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            expected_map = (
                f'{self._MAPS}/map_ne30pg2_to_oEC60to30v3_{alg}.{self._TS}.nc'
            )
            matching = [c for c in cmds if expected_map in c]
            self.assertEqual(len(matching), 1, f'Missing reverse map for {alg}')
            self.assertIn('--a2o', matching[0])

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_name_pg2_defaults_to_name_plus_pg2(self, mock_run, _mock_exists):
        """When name_pg2 is not in config, it should default to <name>pg2."""
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        del cfg._data['grid.name_pg2']
        create_maps_ocn(cfg)
        cmds = ' '.join(c.args[0] for c in mock_run.call_args_list)
        self.assertIn('ne30pg2', cmds)


# ---------------------------------------------------------------------------
# create_maps_lnd

class TestCreateMapsLnd(unittest.TestCase):

    _ALGORITHMS = ['traave', 'trbilin', 'trfv2', 'trintbilin']
    _MAPS = '/data/maps'
    _TS   = '20260101'

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_calls_run_cmd_eight_times(self, mock_run, _mock_exists):
        create_maps_lnd(MockConfig())
        self.assertEqual(mock_run.call_count, 8)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_forward_map_filenames(self, mock_run, _mock_exists):
        """lnd → atm maps should not have --a2o flag."""
        create_maps_lnd(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            expected_map = (
                f'{self._MAPS}/map_r05_r05_to_ne30pg2_{alg}.{self._TS}.nc'
            )
            matching = [c for c in cmds if expected_map in c]
            self.assertEqual(len(matching), 1, f'Missing forward map for {alg}')
            self.assertNotIn('--a2o', matching[0])

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_reverse_map_filenames_have_a2o(self, mock_run, _mock_exists):
        """atm → lnd maps should have --a2o flag."""
        create_maps_lnd(MockConfig())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            expected_map = (
                f'{self._MAPS}/map_ne30pg2_to_r05_r05_{alg}.{self._TS}.nc'
            )
            matching = [c for c in cmds if expected_map in c]
            self.assertEqual(len(matching), 1, f'Missing reverse map for {alg}')
            self.assertIn('--a2o', matching[0])


# ---------------------------------------------------------------------------
# create_maps_spa

class TestCreateMapsSpa(unittest.TestCase):

    _MAPS = '/data/maps'
    _TS   = '20260101'

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_calls_run_cmd_once(self, mock_run, _mock_exists):
        create_maps_spa(MockConfig())
        self.assertEqual(mock_run.call_count, 1)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_uses_traave_algorithm(self, mock_run, _mock_exists):
        create_maps_spa(MockConfig())
        cmd = mock_run.call_args.args[0]
        self.assertIn('--alg_typ=traave', cmd)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_map_filename(self, mock_run, _mock_exists):
        create_maps_spa(MockConfig())
        cmd = mock_run.call_args.args[0]
        expected_map = f'{self._MAPS}/map_ne30pg2_to_ne30pg2_traave.{self._TS}.nc'
        self.assertIn(expected_map, cmd)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_spa_name_defaults_to_ne30pg2(self, mock_run, _mock_exists):
        """When spa_name is absent from config, it should default to ne30pg2."""
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        del cfg._data['grid.spa_name']
        create_maps_spa(cfg)
        cmd = mock_run.call_args.args[0]
        self.assertIn('ne30pg2', cmd)


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
