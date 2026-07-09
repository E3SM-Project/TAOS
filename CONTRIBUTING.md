# Contributing to TAOS

This document describes the internal architecture of TAOS and the conventions
used in this repository. It is intended for developers extending the tool or
contributing changes. For user-facing documentation on running the workflow,
see the [README](README.md).

## Running Tests

```shell
python -m pytest tests/ -v                   # all tests
python -m pytest tests/test_config.py -v     # single file
```

Tests use `unittest.mock.patch` to stub `taos.config._MACHINES_YAML` and
filesystem probes, so no HPC environment is required to run them.

## Running Individual Pipeline Stages

The typical entry point is `run_workflow.py` inside a project directory, which
submits the configured SLURM jobs. For testing or re-running a single stage,
each stage can also be invoked directly as a Python module against a
`project.yaml`:

```shell
python -m taos.grid   path/to/project.yaml
python -m taos.topo   path/to/project.yaml --stage all   # or remap|smooth|sgh
python -m taos.maps   path/to/project.yaml --create-maps-ocn --create-maps-lnd
python -m taos.domain path/to/project.yaml
```

Helper scripts in each project directory:

```shell
python check_config.py   # print all resolved config values
python check_paths.py    # color-coded check of which paths exist on disk
python check_grids.py    # color-coded check of grid/topo/map file existence
```

## Architecture

### `taos/` Package

The core Python package. All workflow logic lives here:

- **`config.py`** — `taos_config` class: loads `project.yaml`, merges with
  `machines.yaml` defaults, validates, and exposes values via dot-notation
  (`cfg['derived.grid_root']`). Also defines `taos_config_error`.
- **`grid.py`** — `create_grid()`: produces np4 and pg2 SCRIP/MBDA grid files
  from the Exodus mesh.
- **`topo.py`** — `remap_topo()`, `smooth_topo()`, `calc_topo_sgh()`: the
  three-stage topography pipeline (MBDA remap, smoothing, SGH variance
  calculation).
- **`maps.py`** — `create_maps_ocn()`, `create_maps_lnd()`, `create_maps_spa()`:
  atmosphere↔ocean/land/SPA coupling maps via `ncremap`/TempestRemap.
- **`domain.py`** — `create_domain()`: E3SM domain files via
  `generate_domain_files_E3SM.py` from the E3SM source tree.
- **`mbda.py`** — pure-Python disk-averaged remap built on
  `scipy.spatial.cKDTree`; used when a compiled `mbda` binary is not available.
- **`sem.py`** — pure-Python SEM tensor hyperviscosity smoothing and SCRIP/MBDA
  grid file generation; the default replacement for `homme_tool`.
- **`util.py`** — `clr` (terminal colors), `print_line()`, `run_cmd()`.
- **`machines.yaml`** — per-machine path and SLURM defaults (NERSC, LCRC, ALCF,
  OLCF). Auto-detected by probing known filesystem paths; last match wins.

### `taos_config` Key Details

```python
from taos import taos_config, taos_config_error

cfg = taos_config('path/to/project.yaml')   # or taos_config.from_project_dir(dir)
cfg.validate()                              # raises taos_config_error listing all missing fields
cfg['derived.grid_root']                    # dot-notation; raises KeyError if blank
cfg.get('paths.mbda_path', '')              # dot-notation with default
cfg.to_env_dict()                           # flat dict of legacy bash variable names
```

Merge rule: `project.yaml` values win over machine defaults only if non-blank
(not `None`, `""`, `"UNSET"`, `"YYYYMMDD"`, etc.). Derived paths (`grid_root`,
`maps_root`, `topo_root`, `init_root`, `domn_root`) are computed from
`grid_data_root + project.name`. Logs go in `<proj_dir>/logs_batch/` and
`<proj_dir>/logs_hiccup/`.

### Workflow Pipeline Sequence

1. **Create grid** (`taos.grid`) — np4 GLL and pg2 physics SCRIP/MBDA grid
   files, plus ne3000 (3km) files for topography processing.
2. **Remap topo** (`taos.topo --stage remap`) — MBDA interpolates high-res RLL
   source topography to target np4, pg2, and 3km grids.
3. **Smooth topo** (`taos.topo --stage smooth`) — applies smoothing (native
   `taos.sem`, or `homme_tool` if configured).
4. **Calc SGH** (`taos.topo --stage sgh`) — subgrid-scale orography variance
   computed from the 3km intermediate files.
5. **Maps** (`taos.maps`) — atmosphere↔ocean, atmosphere↔land, SPA coupling
   maps.
6. **Domain** (`taos.domain`) — E3SM domain files.

### Grid Types

- **Uniform cube-sphere** — `ne${NE}` (spectral element, np4), `ne${NE}pg2`
  (physics grid, 2×2 GLL points).
- **Regionally Refined Mesh (RRM)** — generated with SQuadGen; uses a refinement
  image or rectangle spec.

### Data Formats

- **Exodus II (`.g`)** — native mesh format.
- **SCRIP (`.nc`)** — NetCDF used by coupling/remapping tools.
- **MBDA (`.nc`, cdf5)** — reduced SCRIP with `lon`, `lat`, `area` only; `ncol`
  dimension.

### Project Directory Layout

```
projects/
  template/          ← copy this to start a new project
    project.yaml     ← all configuration (machine auto-detected)
    run_workflow.py  ← edit to select which stages/grids to run
    check_config.py
    check_paths.py
    check_grids.py
  <year>-<name>/     ← your own projects
```

## Code Style

### Python comment separators

Always separate section dividers from descriptive comments. Use a dashed line
followed by the description on its own line:

```python
#-------------------------------------------------------------------------------
# section description here
```

Section dividers should end at column 80. Never embed text inside the dashes
(e.g. `# ---- description ----`).
