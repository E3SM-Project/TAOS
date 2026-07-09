#!/usr/bin/env python3
"""
taos.util — Shared utilities for TAOS workflow scripts.
"""
import os
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
# command execution

def e3sm_env_prefix(cfg):
    """Return a bash one-liner that loads the E3SM module environment."""
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
