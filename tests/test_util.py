"""
Unit tests for taos/util.py.

Tests cover print_line(), run_cmd(), and get_env_var() without touching
the filesystem or spawning real subprocesses. subprocess.run and
os.path.exists are mocked throughout.

Run with:
    python -m pytest tests/test_util.py
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import subprocess as sp


from taos.util import (check_esmf_rwg, cime_env_ok, e3sm_env_prefix, ensure_dir,
                       esmf_comm, get_env_var, print_line, run_cmd)


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
# esmf_comm

class TestEsmfComm(unittest.TestCase):

    @staticmethod
    def _make_install(root, name, comm):
        """Create <root>/<name>/{bin,lib} holding an esmf.mk declaring comm."""
        prefix = Path(root) / name
        (prefix / 'bin').mkdir(parents=True)
        (prefix / 'lib').mkdir(parents=True)
        exe = prefix / 'bin' / 'ESMF_RegridWeightGen'
        exe.touch()
        (prefix / 'lib' / 'esmf.mk').write_text(f'# ESMF_COMM: {comm}\n')
        return exe

    def test_prefers_esmf_mk_beside_the_binary_over_the_env_var(self):
        # E3SM-unified puts an MPI build on $PATH but exports an $ESMFMKFILE
        # from a separate nompi env - trusting the variable reported the good
        # build as mpiuni and aborted jobs that would have run fine
        with tempfile.TemporaryDirectory() as d:
            exe = self._make_install(d, 'spack_view', 'mpi')
            other = self._make_install(d, 'pixi_env', 'mpiuni')
            with patch.dict('os.environ',
                            {'ESMFMKFILE': str(other.parent.parent / 'lib' / 'esmf.mk')}):
                self.assertEqual(esmf_comm(str(exe)), 'mpi')

    def test_falls_back_to_env_var_when_prefix_has_no_esmf_mk(self):
        with tempfile.TemporaryDirectory() as d:
            other = self._make_install(d, 'elsewhere', 'openmpi')
            bare = Path(d) / 'bare' / 'bin'
            bare.mkdir(parents=True)
            exe = bare / 'ESMF_RegridWeightGen'
            exe.touch()
            with patch.dict('os.environ',
                            {'ESMFMKFILE': str(other.parent.parent / 'lib' / 'esmf.mk')}):
                self.assertEqual(esmf_comm(str(exe)), 'openmpi')


# ---------------------------------------------------------------------------
# check_esmf_rwg

def _ldd_stdout(*entries):
    """Build fake ldd output from 'soname => path' strings."""
    return ''.join(f'\t{entry} (0x00007f0000000000)\n' for entry in entries)


# a conda env shipping its own mpich - libmpi resolves inside the prefix
_CONDA_LDD = _ldd_stdout(
    'libmpifort.so.12 => /home/u/envs/taos_env/bin/../lib/libmpifort.so.12',
    'libmpi.so.12 => /home/u/envs/taos_env/bin/../lib/libmpi.so.12',
    'libnetcdf.so.19 => /home/u/envs/taos_env/lib/libnetcdf.so.19')

# a site-MPI build - libmpi resolves outside the prefix, and PMI is linked
_CRAY_LDD = _ldd_stdout(
    'libmpi_gnu_123.so.12 => /opt/cray/pe/mpich/9.0.1/ofi/gnu/12.3/lib/libmpi_gnu_123.so.12',
    'libpmi.so.0 => /opt/cray/pe/lib64/libpmi.so.0',
    'libpmi2.so.0 => /opt/cray/pe/lib64/libpmi2.so.0')


class TestCheckEsmfRwg(unittest.TestCase):

    def setUp(self):
        # neutralize a real TAOS_SKIP_ESMF_MPI_CHECK in the developer's shell
        patcher = patch.dict('os.environ', {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop('TAOS_SKIP_ESMF_MPI_CHECK', None)

    def _run(self, exe, ldd_stdout, comm, has_srun=True):
        """Invoke check_esmf_rwg against a mocked tool path and link line."""
        def which(name):
            if name == 'ESMF_RegridWeightGen':
                return exe
            return '/usr/bin/srun' if has_srun else None
        with patch('taos.util.shutil.which', side_effect=which), \
             patch('taos.util.esmf_comm', return_value=comm), \
             patch('taos.util.sp.run', return_value=MagicMock(stdout=ldd_stdout)):
            return check_esmf_rwg(quiet=True)

    def test_raises_when_build_bundles_its_own_mpi(self):
        with self.assertRaises(RuntimeError) as ctx:
            self._run('/home/u/envs/taos_env/bin/ESMF_RegridWeightGen',
                      _CONDA_LDD, 'mpich')
        msg = str(ctx.exception)
        self.assertIn('bundles its own MPI', msg)
        self.assertIn('libmpi.so.12', msg)
        self.assertIn('links no PMI client', msg)

    def test_passes_for_site_mpi_build(self):
        exe = '/soft/spack/opt/esmf-8.9.1/bin/ESMF_RegridWeightGen'
        self.assertEqual(self._run(exe, _CRAY_LDD, 'mpi'), exe)

    def test_passes_when_srun_is_not_the_launcher(self):
        # the same bundled build driven by its own mpirun works fine
        exe = '/home/u/envs/taos_env/bin/ESMF_RegridWeightGen'
        self.assertEqual(self._run(exe, _CONDA_LDD, 'mpich', has_srun=False), exe)

    def test_env_var_bypasses_the_bundled_mpi_check(self):
        os.environ['TAOS_SKIP_ESMF_MPI_CHECK'] = '1'
        exe = '/home/u/envs/taos_env/bin/ESMF_RegridWeightGen'
        self.assertEqual(self._run(exe, _CONDA_LDD, 'mpich'), exe)

    def test_mpiuni_still_raises_before_the_bundled_check(self):
        with self.assertRaises(RuntimeError) as ctx:
            self._run('/home/u/envs/taos_env/bin/ESMF_RegridWeightGen',
                      _CONDA_LDD, 'mpiuni')
        self.assertIn('mpiuni', str(ctx.exception))

    def test_system_prefix_is_not_treated_as_bundled(self):
        exe = '/usr/bin/ESMF_RegridWeightGen'
        ldd = _ldd_stdout('libmpi.so.12 => /usr/lib64/libmpi.so.12')
        self.assertEqual(self._run(exe, ldd, 'mpich'), exe)


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
