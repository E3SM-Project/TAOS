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
    _resolve_algorithms,
    _resolve_flip_a2o,
    _unified_env_prefix,
    create_maps_lnd,
    create_maps_ocn,
    create_maps_rof,
    create_maps_spa,
)

# ---------------------------------------------------------------------------
# ensure_dir touches the real filesystem; MockConfig roots are fake paths
# that must not be created, so patch it module-wide.

_ensure_dir_patch = patch('taos.maps.ensure_dir')

def setUpModule():
    _ensure_dir_patch.start()

def tearDownModule():
    _ensure_dir_patch.stop()

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
# _resolve_algorithms

class TestResolveAlgorithms(unittest.TestCase):

    _ALL = ['traave', 'trbilin', 'trfv2', 'trintbilin']

    def _cfg(self, **overrides):
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data.update(overrides)
        return cfg

    def test_builtin_default_for_ocn_and_lnd(self):
        cfg = MockConfig()
        self.assertEqual(_resolve_algorithms(cfg, None, 'ocn'), self._ALL)
        self.assertEqual(_resolve_algorithms(cfg, None, 'lnd'), self._ALL)

    def test_builtin_default_for_rof_is_traave_only(self):
        self.assertEqual(_resolve_algorithms(MockConfig(), None, 'rof'), ['traave'])

    def test_flat_config_list_applies_to_every_component(self):
        cfg = self._cfg(**{'maps.algorithms': ['trbilin']})
        for comp in ('ocn', 'lnd', 'rof'):
            self.assertEqual(_resolve_algorithms(cfg, None, comp), ['trbilin'])

    def test_config_mapping_selects_per_component(self):
        cfg = self._cfg(**{'maps.algorithms': {'default': ['trbilin', 'trfv2'],
                                               'rof': ['traave']}})
        self.assertEqual(_resolve_algorithms(cfg, None, 'ocn'), ['trbilin', 'trfv2'])
        self.assertEqual(_resolve_algorithms(cfg, None, 'rof'), ['traave'])

    def test_config_mapping_without_default_falls_back_to_builtin(self):
        cfg = self._cfg(**{'maps.algorithms': {'rof': ['trbilin']}})
        self.assertEqual(_resolve_algorithms(cfg, None, 'ocn'), self._ALL)
        self.assertEqual(_resolve_algorithms(cfg, None, 'rof'), ['trbilin'])

    def test_explicit_override_wins_for_every_component(self):
        cfg = self._cfg(**{'maps.algorithms': {'rof': ['traave']}})
        self.assertEqual(_resolve_algorithms(cfg, ['trfv2'], 'rof'), ['trfv2'])

    def test_accepts_comma_separated_string(self):
        cfg = self._cfg(**{'maps.algorithms': 'traave, trbilin'})
        self.assertEqual(_resolve_algorithms(cfg, None, 'ocn'), ['traave', 'trbilin'])


# ---------------------------------------------------------------------------
# _resolve_flip_a2o

class TestResolveFlipA2o(unittest.TestCase):

    def _cfg(self, **overrides):
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data.update(overrides)
        return cfg

    def test_defaults_to_false_when_unset(self):
        cfg = MockConfig()
        self.assertFalse(_resolve_flip_a2o(cfg, 'ocn'))
        self.assertFalse(_resolve_flip_a2o(cfg, 'lnd'))

    def test_reads_per_component_key(self):
        cfg = self._cfg(**{'grid.lnd_flip_a2o_direction': True})
        self.assertTrue(_resolve_flip_a2o(cfg, 'lnd'))
        self.assertFalse(_resolve_flip_a2o(cfg, 'ocn'))

    def test_accepts_string_values(self):
        for text, expected in [('true', True), ('True', True), ('yes', True),
                               ('1', True), ('false', False), ('no', False)]:
            cfg = self._cfg(**{'grid.ocn_flip_a2o_direction': text})
            self.assertEqual(_resolve_flip_a2o(cfg, 'ocn'), expected, text)


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

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_flip_moves_a2o_to_the_forward_map(self, mock_run, _mock_exists):
        """ocn_flip_a2o_direction moves --a2o from the atm→ocn to the ocn→atm map."""
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data['grid.ocn_flip_a2o_direction'] = True
        create_maps_ocn(cfg)
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            fwd = f'{self._MAPS}/map_oEC60to30v3_to_ne30pg2_{alg}.{self._TS}.nc'
            rev = f'{self._MAPS}/map_ne30pg2_to_oEC60to30v3_{alg}.{self._TS}.nc'
            self.assertIn('--a2o', next(c for c in cmds if fwd in c))
            self.assertNotIn('--a2o', next(c for c in cmds if rev in c))


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

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_flip_moves_a2o_to_the_forward_map(self, mock_run, _mock_exists):
        """The coarse-land-grid case: a pg2 land grid under a refined RRM atm grid.

        lnd_flip_a2o_direction moves --a2o from the atm→lnd to the lnd→atm map.
        """
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data['grid.lnd_flip_a2o_direction'] = True
        create_maps_lnd(cfg)
        cmds = [c.args[0] for c in mock_run.call_args_list]
        for alg in self._ALGORITHMS:
            fwd = f'{self._MAPS}/map_r05_r05_to_ne30pg2_{alg}.{self._TS}.nc'
            rev = f'{self._MAPS}/map_ne30pg2_to_r05_r05_{alg}.{self._TS}.nc'
            self.assertIn('--a2o', next(c for c in cmds if fwd in c))
            self.assertNotIn('--a2o', next(c for c in cmds if rev in c))

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_lnd_flip_does_not_affect_ocn(self, mock_run, _mock_exists):
        """The land switch must not change the ocean map convention."""
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data['grid.lnd_flip_a2o_direction'] = True
        create_maps_ocn(cfg)
        cmds = [c.args[0] for c in mock_run.call_args_list]
        fwd = f'{self._MAPS}/map_oEC60to30v3_to_ne30pg2_traave.{self._TS}.nc'
        rev = f'{self._MAPS}/map_ne30pg2_to_oEC60to30v3_traave.{self._TS}.nc'
        self.assertNotIn('--a2o', next(c for c in cmds if fwd in c))
        self.assertIn('--a2o', next(c for c in cmds if rev in c))


# ---------------------------------------------------------------------------
# create_maps_rof

class TestCreateMapsRof(unittest.TestCase):

    _MAPS = '/data/maps'
    _TS   = '20260101'
    _FWD  = f'{_MAPS}/map_r05_r05_to_r0125_traave.{_TS}.nc'   # lnd -> rof
    _REV  = f'{_MAPS}/map_r0125_to_r05_r05_traave.{_TS}.nc'   # rof -> lnd

    def _cfg(self, **overrides):
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        cfg._data.update({
            'grid.rof_name': 'r0125',
            'grid.rof_file': '/grids/MOSART_global_8th_scrip.nc',
        })
        cfg._data.update(overrides)
        return cfg

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_skips_when_no_river_grid(self, mock_run, _mock_exists):
        """No rof_file means no river maps and no error — the common case."""
        create_maps_rof(MockConfig())
        mock_run.assert_not_called()

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_defaults_to_traave_only(self, mock_run, _mock_exists):
        """River maps default to the conservative algorithm alone."""
        create_maps_rof(self._cfg())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertEqual(len(cmds), 2)
        for cmd in cmds:
            self.assertIn('--alg_typ=traave', cmd)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_pairs_river_with_land_not_atm(self, mock_run, _mock_exists):
        """The river grid pairs with the land grid; the atm grid is not involved."""
        create_maps_rof(self._cfg())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertTrue(any(self._FWD in c for c in cmds), cmds)
        self.assertTrue(any(self._REV in c for c in cmds), cmds)
        for cmd in cmds:
            self.assertNotIn('ne30pg2', cmd)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_a2o_on_lnd_to_rof_by_default(self, mock_run, _mock_exists):
        create_maps_rof(self._cfg())
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertIn('--a2o', next(c for c in cmds if self._FWD in c))
        self.assertNotIn('--a2o', next(c for c in cmds if self._REV in c))

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_flip_moves_a2o_to_rof_to_lnd(self, mock_run, _mock_exists):
        """The coarse-river-grid case, e.g. r0125 under a high-res land grid."""
        cfg = self._cfg(**{'grid.rof_flip_a2o_direction': True})
        create_maps_rof(cfg)
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertNotIn('--a2o', next(c for c in cmds if self._FWD in c))
        self.assertIn('--a2o', next(c for c in cmds if self._REV in c))

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_explicit_algorithms_override_the_default(self, mock_run, _mock_exists):
        create_maps_rof(self._cfg(), algorithms=['traave', 'trbilin'])
        cmds = [c.args[0] for c in mock_run.call_args_list]
        self.assertEqual(len(cmds), 4)

    @patch('os.path.exists', return_value=True)
    @patch('taos.maps.run_cmd')
    def test_raises_when_land_grid_missing(self, _mock_run, _mock_exists):
        cfg = self._cfg()
        del cfg._data['grid.lnd_file']
        with self.assertRaises(RuntimeError) as ctx:
            create_maps_rof(cfg)
        self.assertIn('land grid', str(ctx.exception))


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
