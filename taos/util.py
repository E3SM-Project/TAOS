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


# Install prefixes where a bundled-MPI check makes no sense — a system
# package naturally keeps its libraries alongside the binaries it ships.
_SYSTEM_PREFIXES = ('/', '/usr', '/usr/local', '/opt', '/lib', '/lib64')


def linked_libs(exe, pattern):
    """Return {soname: resolved path} for linked libraries matching pattern.

    Returns {} when ldd cannot report anything (not found, static binary,
    timeout), so an empty result means 'unknown', never 'none linked'.
    """
    try:
        ldd = sp.run(['ldd', exe], capture_output=True, text=True, timeout=30)
    except (OSError, sp.SubprocessError):
        return {}
    matches = re.findall(r'^\s*(\S+)\s+=>\s+(/\S+)', ldd.stdout, re.MULTILINE)
    return {soname: path for soname, path in matches if re.search(pattern, soname)}


def bundled_mpi_libs(exe):
    """Return {soname: path} for MPI libraries shipped inside exe's own prefix.

    A conda/pixi environment that installs its own mpich or openmpi alongside
    ESMF is the signature of an MPI that srun cannot launch — those builds
    carry no PMI client, so each rank ends up in a private MPI_COMM_WORLD of
    size 1. An ESMF linked against a site MPI resolves libmpi outside its own
    prefix (e.g. /opt/cray/pe/mpich/...) and returns {} here.

    Returns {} for binaries installed under a system prefix, where sharing a
    prefix with libmpi carries no such implication.
    """
    exe_path = os.path.realpath(exe)
    prefix = os.path.dirname(os.path.dirname(exe_path))
    if prefix in _SYSTEM_PREFIXES:
        return {}
    return {soname: path for soname, path in linked_libs(exe, r'^libmpi').items()
            if os.path.realpath(path).startswith(prefix + os.sep)}


def esmf_comm(exe):
    """Return the MPI backend ESMF was built with, or '' if undetermined.

    ESMF records this as ``ESMF_COMM`` in esmf.mk — 'mpiuni' means the serial
    stub (no real MPI), anything else ('mpich', 'openmpi', 'intelmpi', ...)
    means a genuine MPI build.

    The esmf.mk beside the binary wins over $ESMFMKFILE, because the two can
    describe different installs: E3SM-unified puts an MPI-enabled ESMF from
    its spack view on $PATH while exporting an $ESMFMKFILE from its pixi env,
    where ESMF is nompi. Trusting the variable there reports a good build as
    mpiuni. $ESMFMKFILE is still consulted last, for layouts that keep
    esmf.mk somewhere other than <prefix>/lib.

    When esmf.mk cannot be found, falls back to checking whether the binary
    links an MPI library. That fallback can only confirm MPI, never rule it
    out (a statically linked build shows no libmpi), so it returns '' rather
    than 'mpiuni' when it finds nothing.
    """
    # both the as-given path and its realpath - a package manager may expose
    # the tool through a symlink farm whose lib/ is populated the same way
    candidates = [os.path.join(os.path.dirname(os.path.dirname(path)), 'lib', 'esmf.mk')
                  for path in (exe, os.path.realpath(exe))]
    candidates.append(os.environ.get('ESMFMKFILE', ''))
    for mk in candidates:
        if not (mk and os.path.exists(mk)):
            continue
        try:
            text = open(mk).read()
        except OSError:
            continue
        # the '# ESMF_COMM: <value>' summary comment, else the -D compile flag
        for pattern in (r'^#\s*ESMF_COMM:\s*(\S+)', r'-DESMF_COMM=(\w+)'):
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                return match.group(1)
    # esmf.mk unavailable - MPI libs in the link line still prove a real build
    if linked_libs(exe, r'^libmpi'):
        return 'mpi (from ldd)'
    return ''


def check_esmf_rwg(quiet=False):
    """Verify ESMF_RegridWeightGen is on PATH and launchable by the job step.

    Returns the resolved path to the tool. Raises RuntimeError when it is
    missing, when ESMF was built with ESMF_COMM=mpiuni, or when the build
    bundles its own MPI on a machine whose jobs run under srun. All three
    fail the same way: every rank of a parallel launch runs the same serial
    regrid in the same directory, racing on ESMF's .esmf.nc temp mesh file.

    mpiuni dies quickly with a confusing NetCDF "Unable to open existing
    file" error. The bundled-MPI case is nastier — nothing errors, the ranks
    just grind against each other until the job hits its wall clock, so a
    map that takes 30 minutes on a site MPI can burn 3 hours and produce
    nothing. The giveaway in the log is ESMF's "Starting weight generation"
    banner appearing once per rank instead of once per job.

    Prints a warning but does not raise when the build cannot be identified,
    since a false block is worse than an unverified pass. Set
    TAOS_SKIP_ESMF_MPI_CHECK=1 to bypass the bundled-MPI check when the
    launch is known to work (e.g. mpirun rather than srun).

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

    # ESMF_COMM only says an MPI was linked, not that srun can launch it. A
    # conda/pixi env that ships its own mpich reports ESMF_COMM=mpich and
    # still gives every rank a private communicator, because those builds
    # carry no PMI client for Slurm to hand a job step to. Only flag it where
    # srun is the launcher — the same build driven by its own mpirun is fine.
    bundled = bundled_mpi_libs(exe)
    if bundled and shutil.which('srun') and not os.environ.get('TAOS_SKIP_ESMF_MPI_CHECK'):
        pmi = linked_libs(exe, r'^libpmi|^libpals')
        pmi_note = ('links no PMI client' if not pmi else
                    'links ' + ', '.join(sorted(pmi)))
        raise RuntimeError(
            f'ESMF_RegridWeightGen bundles its own MPI (ESMF_COMM={comm}) and\n'
            f'  cannot be launched in parallel by srun on this machine.\n'
            f'  {exe}\n'
            + ''.join(f'  {soname} -> {path}\n' for soname, path in sorted(bundled.items()))
            + f'  It {pmi_note}, so each rank initializes a private\n'
            '  MPI_COMM_WORLD of size 1 and redundantly runs the whole regrid.\n'
            '  The job does not fail — it silently runs N racing serial copies\n'
            '  until it hits the wall clock.\n'
            '  Load a site-MPI ESMF instead (its libmpi should resolve outside\n'
            '  the install prefix, e.g. /opt/cray/pe/mpich/...); the E3SM\n'
            '  unified environment provides one. Set TAOS_SKIP_ESMF_MPI_CHECK=1\n'
            '  to bypass this check if the launch is known to work.')

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
