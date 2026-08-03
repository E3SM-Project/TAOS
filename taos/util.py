#!/usr/bin/env python3
"""
taos.util — Shared utilities for TAOS workflow scripts.
"""
import os
import re
import shutil
import subprocess as sp
import sys
from contextlib import contextmanager
from time import perf_counter

# Ensure stdout is line-buffered so print output appears before stderr
# (tracebacks) when both are redirected to the same file (e.g. SLURM logs).
sys.stdout.reconfigure(line_buffering=True)

# -------------------------------------------------------------------
# terminal color codes
class clr:
    END     = '\033[0m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    BOLD    = '\033[1m'

# -------------------------------------------------------------------
# output helpers
def print_line(width=80):
    print('  ' + '-' * width)

# -------------------------------------------------------------------
# filesystem helpers

def ensure_dir(path):
    """Create a directory (and parents) if it doesn't already exist.

    Workflow stages write into derived output roots (files_topo, files_map,
    etc.) that nothing else creates — external tools like mbda fail with
    confusing errors when the parent directory is missing.
    """
    if path:
        os.makedirs(path, exist_ok=True)


# -------------------------------------------------------------------
# command execution

# Cache get_case_env usability per tool path — probing it spawns CIME once,
# which is slow, and the answer cannot change within a single process.
_cime_env_cache = {}

def cime_env_ok(cfg):
    """Return True if CIME's get_case_env exists and produces a usable env.

    False on machines E3SM doesn't support (e.g. OLCF Andes, where
    get_case_env exists but fails machine detection at runtime) or when
    the cime submodule isn't initialized.
    """
    e3sm_src = cfg['paths.e3sm_src_root']
    tool = f'{e3sm_src}/cime/CIME/Tools/get_case_env' if e3sm_src else ''
    if tool not in _cime_env_cache:
        ok = bool(tool) and os.path.exists(tool)
        reason = 'not found (cime submodule initialized?)'
        if ok:
            result = sp.run(tool, shell=True, capture_output=True, text=True,
                            executable='/bin/bash')
            ok = result.returncode == 0 and bool(result.stdout.strip())
            reason = 'failed — machine not supported by E3SM?'
        if not ok:
            print(f'\n  {clr.YELLOW}NOTE: get_case_env {reason}'
                  f'\n  ({tool})'
                  f'\n  Proceeding without the CIME case env — conda-built'
                  f' tools (mbda, TempestRemap, NCO) do not need it.{clr.END}')
        _cime_env_cache[tool] = ok
    return _cime_env_cache[tool]


def esmf_comm(exe):
    """Return the MPI backend ESMF was built with, or '' if undetermined.

    ESMF records this as ``ESMF_COMM`` in esmf.mk — 'mpiuni' means the serial
    stub (no real MPI), anything else ('mpich', 'openmpi', 'intelmpi', ...)
    means a genuine MPI build. esmf.mk is located via $ESMFMKFILE, which conda
    activation sets, falling back to <prefix>/lib/esmf.mk next to the binary.

    When esmf.mk cannot be found, falls back to checking whether the binary
    links an MPI library. That fallback can only confirm MPI, never rule it
    out (a statically linked build shows no libmpi), so it returns '' rather
    than 'mpiuni' when it finds nothing.
    """
    mk = os.environ.get('ESMFMKFILE', '')
    if not (mk and os.path.exists(mk)):
        mk = os.path.join(os.path.dirname(os.path.dirname(exe)), 'lib', 'esmf.mk')
    if os.path.exists(mk):
        try:
            text = open(mk).read()
        except OSError:
            text = ''
        # the '# ESMF_COMM: <value>' summary comment, else the -D compile flag
        for pattern in (r'^#\s*ESMF_COMM:\s*(\S+)', r'-DESMF_COMM=(\w+)'):
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1)
    # esmf.mk unavailable - MPI libs in the link line still prove a real build
    try:
        ldd = sp.run(['ldd', exe], capture_output=True, text=True, timeout=30)
        if re.search(r'\blibmpi\w*\.so', ldd.stdout):
            return 'mpi (from ldd)'
    except (OSError, sp.SubprocessError):
        pass
    return ''


def check_esmf_rwg(quiet=False):
    """Verify ESMF_RegridWeightGen is on PATH and built with real MPI.

    Returns the resolved path to the tool. Raises RuntimeError if it is
    missing, or if ESMF was built with ESMF_COMM=mpiuni — the serial stub,
    which makes every rank of a parallel launch run the same serial regrid
    in the same directory, racing on ESMF's .esmf.nc temp mesh file and
    dying with a confusing NetCDF "Unable to open existing file" error.

    Prints a warning but does not raise when the build cannot be identified,
    since a false block is worse than an unverified pass.

    Worth running before generating batch scripts: sbatch exports the current
    environment by default, so the ESMF found here is the one the job uses.
    """
    exe = shutil.which('ESMF_RegridWeightGen')
    if exe is None:
        raise RuntimeError(
            'ESMF_RegridWeightGen not found on $PATH.\n'
            '  Activate an environment providing an MPI-enabled ESMF, e.g.\n'
            '  the E3SM unified environment or a conda env built with\n'
            "  'esmf=*=mpi_*' (the 'nompi_*' builds will not work).")

    comm = esmf_comm(exe)
    if comm == 'mpiuni':
        raise RuntimeError(
            f'ESMF_RegridWeightGen is built without MPI (ESMF_COMM=mpiuni).\n'
            f'  {exe}\n'
            '  This build ignores the rank count and runs serially, so a\n'
            '  parallel launch produces N identical serial jobs that corrupt\n'
            "  each other's temp files. Install or load an ESMF built with\n"
            "  real MPI (conda: 'esmf=*=mpi_*', not 'nompi_*').")

    if not comm:
        print(f'\n  {clr.YELLOW}NOTE: could not determine the MPI backend of'
              f'\n  {exe}'
              f'\n  (no esmf.mk found via $ESMFMKFILE or ../lib, and no MPI'
              f' library in its link line).'
              f'\n  Proceeding, but verify it is not an mpiuni build.{clr.END}')
    elif not quiet:
        print(f'  {clr.GREEN}ESMF_RegridWeightGen{clr.END}  '
              f'[ESMF_COMM={comm}]  {clr.CYAN}{exe}{clr.END}')
    return exe


def e3sm_env_prefix(cfg):
    """Return a bash one-liner that loads the E3SM module environment.

    Returns a no-op ('true') when the CIME env is unavailable — see
    cime_env_ok(). Code paths that genuinely require the CIME env
    (homme_tool) must guard with cime_env_ok() and fail loudly instead.
    """
    if not cime_env_ok(cfg):
        return 'true'
    e3sm_src = cfg['paths.e3sm_src_root']
    return f'eval $({e3sm_src}/cime/CIME/Tools/get_case_env) 2>/dev/null'


def run_cmd(cmd: str, cwd: str = None) -> None:
    """Execute a shell command, printing it first and raising on failure."""
    print(f'\n  {clr.GREEN}{cmd}{clr.END}')
    try:
        sp.run(cmd, shell=True, check=True, executable='/bin/bash', cwd=cwd)
    except sp.CalledProcessError as e:
        import signal
        sig_name = ''
        if e.returncode < 0:
            try:
                sig_name = f' ({signal.Signals(-e.returncode).name})'
            except (ValueError, AttributeError):
                pass
        cwd_msg = f'\n  cwd : {cwd}' if cwd else ''
        print(f'\n  {clr.RED}{"─" * 70}', file=sys.stderr)
        print(f'  run_cmd failed with exit code {e.returncode}{sig_name}', file=sys.stderr)
        print(f'  cmd : {cmd}{cwd_msg}', file=sys.stderr)
        print(f'  {"─" * 70}{clr.END}', file=sys.stderr)
        raise

# -------------------------------------------------------------------
# timing

class TaosTimer:
    """
    Lightweight stage/sub-stage timer for TAOS workflow scripts.

    Usage
    -----
    Import the module-level singleton and wrap any block you want timed:

        from taos.util import timer

        timer.start_total()            # call once at the top of __main__

        with timer.time('my label'):
            run_cmd(some_cmd)

        timer.summary()                # call once at the bottom of __main__

    Each timer prints its result immediately on exit (visible in batch logs
    even if the job is killed before summary() is reached), and summary()
    prints a consolidated recap plus the total elapsed time.
    """

    _LABEL_WIDTH = 55

    def __init__(self):
        self._entries = []
        self._total_start = None

    def start_total(self):
        """Record the start time for the overall total."""
        self._total_start = perf_counter()

    @contextmanager
    def time(self, label):
        """Context manager: time a block, print result immediately, record for summary."""
        t0 = perf_counter()
        yield
        self._record(label, perf_counter() - t0)

    def _format_elapsed(self, elapsed):
        s = f'{elapsed:10.1f} sec'
        if elapsed > 60:
            s += f'  ({elapsed / 60:5.1f} min)'
        return s

    def _record(self, label, elapsed, print_msg=True):
        msg = f'{label:{self._LABEL_WIDTH}}  elapsed time: {self._format_elapsed(elapsed)}'
        if print_msg:
            print(f'\n  {clr.YELLOW}{msg}{clr.END}')
        self._entries.append(msg)
        return msg

    def summary(self):
        """Print all accumulated timer results plus the overall total."""
        if not self._entries and self._total_start is None:
            return
        print(f'\n  {"─" * 80}')
        print(f'  TAOS timer summary:')
        for msg in self._entries:
            print(f'    {msg}')
        if self._total_start is not None:
            total_elapsed = perf_counter() - self._total_start
            total_msg = (f'{"Total":{self._LABEL_WIDTH}}'
                         f'  elapsed time: {self._format_elapsed(total_elapsed)}')
            print(f'    {clr.YELLOW}{total_msg}{clr.END}')
        print(f'  {"─" * 80}\n')


# Module-level singleton — shared across all taos modules in a single process.
timer = TaosTimer()


# -------------------------------------------------------------------
# legacy: read env var from a bash config script
def get_env_var(project_config_path, var):
    """Source a bash config script and return the value of an env var.

    Deprecated: use taos_config instead. Kept for backward compatibility
    with projects that haven't yet migrated to project.yaml.
    """
    if not os.path.exists(project_config_path):
        raise FileNotFoundError(f'Configuration script not found: {project_config_path}')
    cmd = f'source {project_config_path} >> /dev/null; echo ${var}'
    result = sp.run(cmd, shell=True, capture_output=True, text=True, check=True)
    value = result.stdout.strip()
    if not value:
        raise ValueError(f"Environment variable '{var}' is empty or not set in {project_config_path}")
    return value
