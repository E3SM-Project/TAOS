"""
Unit tests for taos/util.py.

Tests cover print_line(), run_cmd(), and get_env_var() without touching
the filesystem or spawning real subprocesses. subprocess.run and
os.path.exists are mocked throughout.

Run with:
    python -m pytest tests/test_util.py
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import subprocess as sp


from taos.util import cime_env_ok, e3sm_env_prefix, ensure_dir, get_env_var, print_line, run_cmd


# ---------------------------------------------------------------------------
# print_line

class TestPrintLine(unittest.TestCase):

    @patch('builtins.print')
    def test_default_width(self, mock_print):
        print_line()
        mock_print.assert_called_once_with('  ' + '-' * 80)

    @patch('builtins.print')
    def test_custom_width(self, mock_print):
        print_line(width=40)
        mock_print.assert_called_once_with('  ' + '-' * 40)


# ---------------------------------------------------------------------------
# run_cmd

class TestRunCmd(unittest.TestCase):

    @patch('taos.util.sp.run')
    def test_calls_subprocess_with_correct_args(self, mock_run):
        run_cmd('echo hello')
        mock_run.assert_called_once_with(
            'echo hello',
            shell=True,
            check=True,
            executable='/bin/bash',
            cwd=None,
        )

    @patch('taos.util.sp.run', side_effect=sp.CalledProcessError(1, 'bad_cmd'))
    def test_propagates_called_process_error(self, _mock_run):
        with self.assertRaises(sp.CalledProcessError):
            run_cmd('bad_cmd')


# ---------------------------------------------------------------------------
# ensure_dir

class TestEnsureDir(unittest.TestCase):

    def test_creates_nested_directories(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'a/b/c'
            ensure_dir(str(target))
            self.assertTrue(target.is_dir())

    def test_noop_on_existing_directory(self):
        with tempfile.TemporaryDirectory() as d:
            ensure_dir(d)  # must not raise
            self.assertTrue(Path(d).is_dir())

    def test_noop_on_empty_path(self):
        ensure_dir('')  # must not raise or create anything


# ---------------------------------------------------------------------------
# e3sm_env_prefix

class _EnvMockCfg:
    def __init__(self, e3sm_src_root='/e3sm'):
        self._cfg = {'paths.e3sm_src_root': e3sm_src_root}

    def __getitem__(self, key):
        return self._cfg[key]


class TestE3smEnvPrefix(unittest.TestCase):

    def test_returns_eval_command(self):
        with patch('taos.util.cime_env_ok', return_value=True):
            result = e3sm_env_prefix(_EnvMockCfg())
        self.assertEqual(
            result,
            'eval $(/e3sm/cime/CIME/Tools/get_case_env) 2>/dev/null',
        )

    def test_noop_when_cime_env_unavailable(self):
        with patch('taos.util.cime_env_ok', return_value=False):
            self.assertEqual(e3sm_env_prefix(_EnvMockCfg()), 'true')


# ---------------------------------------------------------------------------
# cime_env_ok

class TestCimeEnvOk(unittest.TestCase):

    def test_false_when_src_root_empty(self):
        self.assertFalse(cime_env_ok(_EnvMockCfg(e3sm_src_root='')))

    def test_false_when_tool_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(cime_env_ok(_EnvMockCfg(e3sm_src_root=d)))

    def test_true_when_tool_produces_env(self):
        with tempfile.TemporaryDirectory() as d:
            tool = Path(d) / 'cime/CIME/Tools/get_case_env'
            tool.parent.mkdir(parents=True)
            tool.write_text('#!/bin/bash\necho "export FOO=1"\n')
            tool.chmod(0o755)
            self.assertTrue(cime_env_ok(_EnvMockCfg(e3sm_src_root=d)))

    def test_false_when_tool_fails(self):
        with tempfile.TemporaryDirectory() as d:
            tool = Path(d) / 'cime/CIME/Tools/get_case_env'
            tool.parent.mkdir(parents=True)
            tool.write_text('#!/bin/bash\nexit 1\n')
            tool.chmod(0o755)
            self.assertFalse(cime_env_ok(_EnvMockCfg(e3sm_src_root=d)))

    def test_result_is_cached(self):
        with tempfile.TemporaryDirectory() as d:
            tool = Path(d) / 'cime/CIME/Tools/get_case_env'
            tool.parent.mkdir(parents=True)
            tool.write_text('#!/bin/bash\necho "export FOO=1"\n')
            tool.chmod(0o755)
            self.assertTrue(cime_env_ok(_EnvMockCfg(e3sm_src_root=d)))
            # second call must hit the cache, not re-probe the (now removed) tool
            tool.unlink()
            self.assertTrue(cime_env_ok(_EnvMockCfg(e3sm_src_root=d)))


# ---------------------------------------------------------------------------
# get_env_var

class TestGetEnvVar(unittest.TestCase):

    @patch('taos.util.os.path.exists', return_value=False)
    def test_raises_file_not_found_when_config_missing(self, _mock_exists):
        with self.assertRaises(FileNotFoundError) as ctx:
            get_env_var('/nonexistent/config.sh', 'MY_VAR')
        self.assertIn('/nonexistent/config.sh', str(ctx.exception))

    @patch('taos.util.sp.run')
    @patch('taos.util.os.path.exists', return_value=True)
    def test_raises_value_error_when_stdout_empty(self, _mock_exists, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = '\n'
        mock_run.return_value = mock_result
        with self.assertRaises(ValueError) as ctx:
            get_env_var('/some/config.sh', 'EMPTY_VAR')
        self.assertIn('EMPTY_VAR', str(ctx.exception))

    @patch('taos.util.sp.run')
    @patch('taos.util.os.path.exists', return_value=True)
    def test_returns_value_when_stdout_nonempty(self, _mock_exists, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = '/some/path/value\n'
        mock_run.return_value = mock_result
        result = get_env_var('/some/config.sh', 'MY_VAR')
        self.assertEqual(result, '/some/path/value')


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
