"""
taos.config — YAML-based configuration loader for TAOS workflows.

Usage
-----
    from taos import taos_config, taos_config_error

    cfg = taos_config('path/to/project.yaml')
    cfg.validate()                          # raises taos_config_error if anything is missing

    grid_root = cfg['derived.grid_root']
    mbda_path = cfg['paths.mbda_path']
    print(cfg.machine)                      # e.g. "NERSC"

Key design
----------
- A single project.yaml holds all project-specific settings plus optional
  machine-level overrides.
- Machine defaults are loaded from taos/machines.yaml (auto-detected by probing
  known HPC paths; last match wins, mirroring the bash if-chain behavior).
- Merge rule: a project value takes precedence over the machine default ONLY if
  it is non-empty (not None, not "", not a placeholder like "UNSET").
- Derived paths (grid_root, maps_root, etc.) are computed automatically from
  grid_data_root and project.name, mirroring set_project_paths.sh.
"""

import configparser
import copy
import os
import yaml
from pathlib import Path


_MACHINES_YAML = Path(__file__).parent / 'machines.yaml'

# Values treated as "not set" during merge and validation
_BLANK_VALUES = frozenset({'', 'UNSET', 'YYYYMMDD', 'None', 'none', 'null'})


def _is_blank(val) -> bool:
    if val is None:
        return True
    if isinstance(val, str) and val.strip() in _BLANK_VALUES:
        return True
    return False


def _expand(obj):
    """Recursively expand $ENV_VAR and ~ in all string values."""
    if isinstance(obj, str):
        return os.path.expandvars(os.path.expanduser(obj))
    if isinstance(obj, dict):
        return {k: _expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand(v) for v in obj]
    return obj


def _read_cime_mail_user() -> str:
    """Return MAIL_USER from ~/.cime/config, or '' if absent or unset."""
    cime_config = Path.home() / '.cime' / 'config'
    if not cime_config.exists():
        return ''
    parser = configparser.ConfigParser()
    parser.read(cime_config)
    return parser.get('main', 'mail_user', fallback='').strip()


class taos_config_error(ValueError):
    """Raised when the TAOS configuration is invalid or incomplete."""
    pass


def load_machines() -> dict:
    """Return the parsed contents of taos/machines.yaml."""
    return yaml.safe_load(_MACHINES_YAML.read_text())


def detect_machine(machines: dict = None) -> str:
    """
    Auto-detect the HPC machine by probing known paths.

    Checked in document order; last match wins (mirrors the bash if-chain
    in set_machine_paths.sh). Raises taos_config_error if no probe matches.
    """
    if machines is None:
        machines = load_machines()
    detected = None
    for name, mdata in machines.items():
        if name.startswith('_'):
            continue
        probe = (mdata.get('detection') or {}).get('probe_path', '')
        if not probe:
            continue
        expanded = os.path.expandvars(probe)
        # Skip if env var was not expanded (e.g. $SCRATCH unset)
        if expanded.startswith('$'):
            continue
        if os.path.exists(expanded):
            detected = name

    if detected is None:
        raise taos_config_error(
            "Could not auto-detect HPC machine. "
            "Set 'machine: {name: NERSC}' (or LCRC/ALCF/OLCF) in project.yaml."
        )
    return detected


class taos_config:
    """
    Loads, merges, and validates a TAOS project configuration.

    Parameters
    ----------
    project_yaml_path : str or Path
        Path to the project.yaml file.

    Attributes
    ----------
    machine : str
        Detected or specified machine name (e.g. "NERSC", "LCRC").
    paths : dict
        Merged machine + project path values, env-vars expanded.
    slurm : dict
        Merged machine + project SLURM settings, env-vars expanded.
    project : dict
        Project identity fields (name, timestamp).
    grid : dict
        Grid configuration fields (name, ...).
    derived : dict
        Auto-populated paths derived from grid_data_root and project.name.
    """

    def __init__(self, project_yaml_path):
        self._proj_yaml_path = Path(project_yaml_path).resolve()
        if not self._proj_yaml_path.exists():
            raise FileNotFoundError(
                f"Project config not found: {self._proj_yaml_path}\n"
                f"Copy template-proj-yaml/project.yaml to your project directory and fill it in."
            )
        self.proj_dir = self._proj_yaml_path.parent

        # Load machine definitions
        self._machines = load_machines()

        # Load project YAML
        self._raw = yaml.safe_load(self._proj_yaml_path.read_text()) or {}

        # Detect machine (from project.yaml override or auto-detection)
        self.machine = self._detect_machine()

        # Merge machine defaults with project overrides
        self.paths  = _expand(self._merge_section('paths'))
        self.slurm  = _expand(self._merge_section('slurm'))

        # Project and grid sections come directly from the project YAML.
        # Grid values may reference path vars like ${DIN_LOC_ROOT} or derived
        # keys like ${grid_root}, which are not in the system env — see
        # _expand_grid_vars for the temporary-injection expansion.
        self.project = dict(self._raw.get('project', {}))
        self.grid = self._expand_grid_vars(dict(self._raw.get('grid', {})))

        # Apply per-user path/slurm overrides from users: section
        _current_user = os.environ.get('USER', '')
        _user_section = (self._raw.get('users') or {}).get(_current_user) or {}
        if _user_section:
            for k, v in (_user_section.get('paths') or {}).items():
                if not _is_blank(v):
                    self.paths[k] = os.path.expandvars(os.path.expanduser(str(v)))
            for k, v in (_user_section.get('slurm') or {}).items():
                if not _is_blank(v):
                    self.slurm[k] = str(v)

        # Post-process: derive homme_tool_root if not explicitly set
        if _is_blank(self.paths.get('homme_tool_root')):
            e3sm = self.paths.get('e3sm_src_root', '')
            if e3sm:
                self.paths['homme_tool_root'] = f'{e3sm}/cmake_homme'

        # Post-process: derive mail_user from ~/.cime/config if not explicitly set
        if _is_blank(self.slurm.get('mail_user')):
            cime_mail = _read_cime_mail_user()
            if cime_mail:
                self.slurm['mail_user'] = cime_mail

        # Compute derived paths (mirrors set_project_paths.sh)
        self.derived = self._compute_derived()

        # Re-expand the base grid section now that derived keys (e.g.
        # ${grid_root}) are available, so grid values may reference them too.
        self.grid = self._expand_grid_vars(self.grid)

    # ------------------------------------------------------------------
    # Alternate constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_project_yaml(cls, path) -> 'taos_config':
        return cls(path)

    @classmethod
    def from_project_dir(cls, project_dir) -> 'taos_config':
        return cls(Path(project_dir) / 'project.yaml')

    # ------------------------------------------------------------------
    # Config-var expansion
    # ------------------------------------------------------------------

    def _expand_grid_vars(self, obj):
        """Expand ``$ENV_VAR``, ``~``, and TAOS config vars in *obj*.

        In addition to real environment variables, this resolves path keys
        (``self.paths``, e.g. ``${DIN_LOC_ROOT}``) and derived keys
        (``self.derived``, e.g. ``${grid_root}``) by temporarily injecting
        them into the environment for the duration of the expansion. Derived
        keys are only available after ``self.derived`` is populated; before
        then only path keys are injected.
        """
        extra = {}
        extra.update({k: v for k, v in self.paths.items() if v})
        extra.update({k: v for k, v in getattr(self, 'derived', {}).items() if v})
        _saved = {k: os.environ.get(k) for k in extra}
        os.environ.update(extra)
        try:
            return _expand(obj)
        finally:
            for k, old in _saved.items():
                if old is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old

    # ------------------------------------------------------------------
    # Multi-grid iteration
    # ------------------------------------------------------------------

    def iter_grids(self):
        """Yield one taos_config variant per entry in the 'grids:' list.

        Each entry is merged over the base 'grid:' section — a non-blank
        entry value overrides the base; a blank value defers to it.

        If 'grids:' is absent, yields self unchanged (single-grid fallback
        so existing single-grid project.yaml files need no changes).
        """
        raw_grids = self._raw.get('grids')
        if not raw_grids:
            yield self
            return
        # Grid entries may reference path vars like ${grid_data_root} or
        # derived roots like ${grid_root}; _expand_grid_vars injects them for
        # expansion, mirroring how __init__ expands the base grid: section.
        for entry in raw_grids:
            merged = dict(self.grid)
            for k, v in self._expand_grid_vars(entry or {}).items():
                if not _is_blank(v):
                    merged[k] = v
            variant = copy.copy(self)
            variant.grid = merged
            yield variant

    def for_grid(self, name: str) -> 'taos_config':
        """Return the config variant whose grid.name matches *name*.

        Raises KeyError if no matching grid is found.
        """
        for variant in self.iter_grids():
            if variant.grid.get('name') == name:
                return variant
        raise KeyError(
            f"Grid '{name}' not found in project config. "
            f"Check the grids: list in your project.yaml."
        )

    # ------------------------------------------------------------------
    # Key access
    # ------------------------------------------------------------------

    def __getitem__(self, dot_key: str) -> str:
        """Access a config value by dot-notation key, e.g. cfg['derived.grid_root']."""
        val = self._get_by_dot(dot_key)
        if _is_blank(val):
            raise KeyError(f"Config key '{dot_key}' is not set or empty.")
        return val

    def get(self, dot_key: str, default=None):
        """Like __getitem__ but returns default instead of raising."""
        val = self._get_by_dot(dot_key)
        return default if _is_blank(val) else val

    def _get_by_dot(self, dot_key: str):
        section, _, rest = dot_key.partition('.')
        store = {
            'paths':   self.paths,
            'slurm':   self.slurm,
            'project': self.project,
            'grid':    self.grid,
            'derived': self.derived,
            'machine': {'name': self.machine},
            'topo':    self._raw.get('topo', {}),
            'maps':    self._raw.get('maps', {}),
        }
        if section not in store:
            return None
        if not rest:
            return store[section]
        d = store[section]
        for part in rest.split('.'):
            if not isinstance(d, dict):
                return None
            d = d.get(part)
        return d

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, required_keys: list = None) -> None:
        """
        Check that all required config keys are non-empty.

        Collects ALL missing values before raising, so the user sees
        everything wrong in a single error message.

        Parameters
        ----------
        required_keys : list of dot-notation strings, optional
            Defaults to the _required_keys list in machines.yaml plus
            project.name, project.timestamp, and grid.name.

        Raises
        ------
        taos_config_error
            Lists every missing key. Never raises multiple exceptions.
        """
        if required_keys is None:
            required_keys = self._default_required_keys()

        missing = [k for k in required_keys if _is_blank(self._get_by_dot(k))]

        if missing:
            lines = '\n'.join(f'  - {k}' for k in missing)
            n = len(missing)
            raise taos_config_error(
                f"{n} required config value{'s are' if n != 1 else ' is'} missing or unset:\n{lines}"
            )

    def _default_required_keys(self) -> list:
        req = self._machines.get('_required_keys', {})
        keys = []
        for section, field_list in req.items():
            for field in field_list:
                keys.append(f'{section}.{field}')
        keys += ['project.name', 'project.timestamp', 'grid.name']
        return keys

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def as_dict(self) -> dict:
        """
        Return all resolved values as a flat dict with dot-notation keys.
        Useful for string formatting or debug inspection.
        """
        result = {'machine.name': self.machine}
        for section, d in [('paths', self.paths), ('slurm', self.slurm),
                            ('project', self.project), ('grid', self.grid),
                            ('derived', self.derived)]:
            for k, v in d.items():
                result[f'{section}.{k}'] = str(v) if v is not None else ''
        return result

    def to_env_dict(self) -> dict:
        """
        Return a flat dict of legacy bash variable names for backward
        compatibility with existing batch scripts that still use env vars.

        Variable naming conventions mirror set_machine_paths.sh and
        set_project_paths.sh exactly:
          paths.grid_data_root  -> grid_data_root
          slurm.mail_user       -> taos_slurm_mail_user
          project.name          -> proj  (and also 'name')
          project.timestamp     -> timestamp
          machine.name          -> taos_host
        """
        env = {}
        env.update({k: v for k, v in self.paths.items()   if v})
        env.update({k: v for k, v in self.derived.items() if v})
        env.update({k: v for k, v in self.project.items() if v})
        env.update({f'taos_slurm_{k}': v for k, v in self.slurm.items() if v})
        env['taos_host'] = self.machine
        if 'name' in self.project:
            env['proj'] = self.project['name']
        if 'name' in self.grid:
            env['grid_name'] = self.grid['name']
        return {k: str(v) for k, v in env.items()}

    # ------------------------------------------------------------------
    # Internal: machine detection
    # ------------------------------------------------------------------

    def _detect_machine(self) -> str:
        # Allow explicit override in project.yaml under machine.name
        override = (self._raw.get('machine') or {}).get('name', '')
        if not _is_blank(override):
            valid = [k for k in self._machines if not k.startswith('_')]
            if override not in valid:
                raise taos_config_error(
                    f"Unknown machine '{override}' in project.yaml. "
                    f"Valid options: {valid}"
                )
            return override

        # Auto-detect by probing known paths (last match wins, same as bash)
        return detect_machine(self._machines)

    # ------------------------------------------------------------------
    # Internal: merging
    # ------------------------------------------------------------------

    def _merge_section(self, section: str) -> dict:
        """
        Merge machine defaults with project overrides for one section.
        Project value wins only if it is non-blank.
        """
        machine_data  = dict(self._machines.get(self.machine, {}).get(section, {}))
        project_data  = dict(self._raw.get(section, {}))

        result = dict(machine_data)
        for key, val in project_data.items():
            if not _is_blank(val):
                result[key] = val
        return result

    # ------------------------------------------------------------------
    # Internal: derived paths
    # ------------------------------------------------------------------

    def _compute_derived(self) -> dict:
        """
        Compute paths that are not set directly but follow from
        grid_data_root + project.name — mirrors set_project_paths.sh.

        Note: slurm_log_root and hiccup_log_root use proj_dir (the code
        directory containing project.yaml), not data_root — matching the
        existing bash convention where logs live with the scripts.
        """
        proj_name       = self.project.get('name', '')
        grid_data_root  = self.paths.get('grid_data_root', '')

        if not _is_blank(proj_name) and not _is_blank(grid_data_root):
            data_root = f'{grid_data_root}/{proj_name}'
        else:
            data_root = ''

        return {
            'proj_root':       str(self.proj_dir),
            'data_root':       data_root,
            'grid_root':       f'{data_root}/files_grid'   if data_root else '',
            'maps_root':       f'{data_root}/files_map'    if data_root else '',
            'topo_root':       f'{data_root}/files_topo'   if data_root else '',
            'init_root':       f'{data_root}/files_init'   if data_root else '',
            'domn_root':       f'{data_root}/files_domain' if data_root else '',
            'slurm_log_root':  str(self.proj_dir / 'logs_batch'),
            'hiccup_log_root': str(self.proj_dir / 'logs_hiccup'),
        }
