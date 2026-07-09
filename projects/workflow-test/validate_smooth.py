"""
Validate smooth_phis against the homme_tool reference output for ne30.

Usage:
    python validate_smooth.py

Compares the Python smooth_phis implementation against the homme_tool
topo_pgn_to_smoothed reference output already on disk.
"""
import sys, numpy as np, xarray as xr

sys.path.insert(0, '/global/u1/w/whannah/E3SM_grid_support')

from taos import taos_config
from taos import sem

#-------------------------------------------------------------------------------
# resolve paths from project config

cfg = taos_config.from_project_dir('/global/u1/w/whannah/E3SM_grid_support/projects/2026-workflow-test')
cfg = cfg.for_grid('ne30')

from taos.topo import _topo_paths
p = _topo_paths(cfg)

exodus_path = p['grid_file_exodus']
input_path  = p['topo_file_1_np4']
# ref_path    = p['topo_file_2']         # homme_tool smoothed output
ref_path    = '/global/cfs/cdirs/e3sm/inputdata/atm/cam/topo/USGS-gtopo30_ne30np4pg2_x6t-SGH.c20210614.nc'

print(f'Exodus:  {exodus_path}')
print(f'Input:   {input_path}')
print(f'Ref:     {ref_path}')
print()

#-------------------------------------------------------------------------------
# load geometry

print('Loading Exodus geometry...')
coords, connect   = sem.read_exodus(exodus_path)
_, metdet, _, D_mat = sem.element_metric(coords, connect)
_, inverse_idx, _ = sem.unique_gll_nodes(coords, connect)
ncol = int(np.max(inverse_idx)) + 1
print(f'  nelems={metdet.shape[0]}  ncol={ncol}')

#-------------------------------------------------------------------------------
# load input and reference

ds_in  = xr.open_dataset(input_path)
ds_ref = xr.open_dataset(ref_path)

phis_in  = ds_in['PHIS'].values.flatten()
# homme_tool output has PHIS (pg2, 21600 nodes) and PHIS_d (np4, 48602 nodes)
phis_ref = ds_ref['PHIS_d'].values.flatten()

print(f'Input  PHIS: min={phis_in.min():.4g}  max={phis_in.max():.4g}')
print(f'Ref    PHIS: min={phis_ref.min():.4g}  max={phis_ref.max():.4g}')

#-------------------------------------------------------------------------------
# run Python smoother

print('\nRunning smooth_phis (numcycle=6, nudt=4e-16)...')
phis_py = sem.smooth_phis(phis_in, metdet, inverse_idx, ncol, D_mat,
                         numcycle=6, nudt=4e-16)
print(f'Python PHIS: min={phis_py.min():.4g}  max={phis_py.max():.4g}')

#-------------------------------------------------------------------------------
# compare

diff    = phis_py - phis_ref
abs_err = np.abs(diff)
scale   = np.maximum(np.abs(phis_ref), 1.0)
rel_err = abs_err / scale

print()
print('--- Comparison ---')
print(f'  Max absolute error : {abs_err.max():.3e}')
print(f'  Mean absolute error: {abs_err.mean():.3e}')
print(f'  Max relative error : {rel_err.max():.3e}  (normalized by max(|ref|, 1))')
print(f'  Mean relative error: {rel_err.mean():.3e}')

threshold = 1e-8
n_exceed = np.sum(rel_err > threshold)
print()
if n_exceed == 0:
    print(f'PASS: all {ncol} nodes within relative tolerance {threshold:.0e}')
else:
    frac = n_exceed / ncol
    print(f'WARNING: {n_exceed}/{ncol} nodes ({frac:.1%}) exceed relative tolerance {threshold:.0e}')

ds_in.close()
ds_ref.close()
