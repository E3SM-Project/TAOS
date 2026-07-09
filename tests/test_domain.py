"""
Unit tests for taos/domain.py.

Tests cover _unified_env_prefix() and create_domain() without touching
the filesystem or running real shell commands. run_cmd and os.path.exists
are mocked throughout.

Run with:
    python -m pytest tests/test_domain.py
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import call, patch


from taos.domain import _unified_env_prefix, create_domain


# ---------------------------------------------------------------------------
# helpers

class MockConfig:
    """Minimal stand-in for taos_config with fixed test values."""

    _data = {
        'paths.unified_src':   '/tools/unified.sh',
        'paths.e3sm_src_root': '/e3sm',
        'grid.name':           'ne30',
        'grid.name_pg2':       'ne30pg2',
        'grid.ocn_name':       'oEC60to30v3',
        'grid.ocn_file':       '/grids/oEC60to30v3_scrip.nc',
        'derived.maps_root':   '/data/maps',
        'derived.domn_root':   '/data/domain',
        'derived.grid_root':   '/data/grids',
        'project.timestamp':   '20260101',
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
# create_domain — map file missing

class TestCreateDomainMapMissing(unittest.TestCase):

    @patch('taos.domain.os.path.exists', return_value=False)
    @patch('taos.domain.run_cmd')
    def test_raises_runtime_error_with_map_path(self, _mock_run, _mock_exists):
        cfg = MockConfig()
        expected_map = (
            '/data/maps/map_oEC60to30v3_to_ne30pg2_traave.20260101.nc'
        )
        with self.assertRaises(RuntimeError) as ctx:
            create_domain(cfg, create_domain_map=False)
        self.assertIn(expected_map, str(ctx.exception))

    @patch('taos.domain.os.path.exists', return_value=False)
    @patch('taos.domain.run_cmd')
    def test_run_cmd_not_called_when_no_map(self, mock_run, _mock_exists):
        with self.assertRaises(RuntimeError):
            create_domain(MockConfig(), create_domain_map=False)
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# create_domain — map file exists, no domain map creation

class TestCreateDomainMapExists(unittest.TestCase):

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_run_cmd_called_once(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=False)
        self.assertEqual(mock_run.call_count, 1)

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_generate_domain_command_contents(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=False)
        cmd = mock_run.call_args.args[0]
        self.assertIn('python', cmd)
        self.assertIn('generate_domain_files_E3SM.py', cmd)
        self.assertIn(' -m ', cmd)
        self.assertIn(' -o oEC60to30v3', cmd)
        self.assertIn(' -l ne30', cmd)
        self.assertIn('--date-stamp=20260101', cmd)
        self.assertIn('--output-root=/data/domain', cmd)


# ---------------------------------------------------------------------------
# create_domain — with domain map creation

class TestCreateDomainWithMapCreation(unittest.TestCase):

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_run_cmd_called_twice(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=True)
        self.assertEqual(mock_run.call_count, 2)

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_first_call_is_ncremap(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=True)
        first_cmd = mock_run.call_args_list[0].args[0]
        self.assertIn('ncremap', first_cmd)
        self.assertIn('--src_grd=', first_cmd)
        self.assertIn('--dst_grd=', first_cmd)
        self.assertIn('--map_file=', first_cmd)

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_second_call_is_generate_domain(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=True)
        second_cmd = mock_run.call_args_list[1].args[0]
        self.assertIn('generate_domain_files_E3SM.py', second_cmd)


# ---------------------------------------------------------------------------
# create_domain — name_pg2 default

class TestCreateDomainNamePg2Default(unittest.TestCase):

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_name_pg2_defaults_to_name_plus_pg2(self, mock_run, _mock_exists):
        cfg = MockConfig()
        cfg._data = dict(cfg._data)
        del cfg._data['grid.name_pg2']
        # Run with create_domain_map=True so the ncremap command (which
        # includes atm_grid_file built from the defaulted atm_grid_name) is
        # emitted, allowing us to verify the 'ne30pg2' default was applied.
        create_domain(cfg, create_domain_map=True)
        ncremap_cmd = mock_run.call_args_list[0].args[0]
        self.assertIn('ne30pg2', ncremap_cmd)


# ---------------------------------------------------------------------------
# create_domain — map filename pattern

class TestCreateDomainMapFilename(unittest.TestCase):

    @patch('taos.domain.os.path.exists', return_value=True)
    @patch('taos.domain.run_cmd')
    def test_map_filename_pattern(self, mock_run, _mock_exists):
        create_domain(MockConfig(), create_domain_map=False)
        cmd = mock_run.call_args.args[0]
        expected_map = (
            'map_oEC60to30v3_to_ne30pg2_traave.20260101.nc'
        )
        self.assertIn(expected_map, cmd)


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
