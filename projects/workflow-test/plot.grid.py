#!/usr/bin/env python3
"""
plot.grid.py  —  Plot E3SM SCRIP grid files with matplotlib + cartopy.

Shade modes
-----------
  'area'   shade each cell by approximate grid spacing [km]
  'topo'   shade each cell by surface elevation [m] from a topo file
  'lines'  draw cell outlines only, no fill

Edit the "User configuration" section below, then run:
    python plot.grid.py
"""
# --------------------------------------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------------------------------------
import os, numpy as np, xarray as xr
import matplotlib as mpl, matplotlib.pyplot as plt
import matplotlib.collections as mcollections
import matplotlib.colors as mcolors
import cartopy.crs as ccrs, cartopy.feature as cfeature
import cmocean
# --------------------------------------------------------------------------------------------------
class tclr: END,RED,GRN,MGN,CYN,YLW = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m','\033[33m'
# --------------------------------------------------------------------------------------------------
# User configuration — edit this section
# --------------------------------------------------------------------------------------------------
home = os.getenv('HOME')

grids = []

def add_grid(file, name, clat=0, clon=0, topo_file=None, markers=None):
    """
    Register a SCRIP grid for plotting.

    Parameters
    ----------
    file       : str   — path to SCRIP .nc grid file
    name       : str   — label shown in the subplot title
    clat, clon : float — center of the orthographic view
    topo_file  : str or None — topo .nc file; used when shade_mode='topo'
    markers    : list of (lat, lon) tuples to overlay as markers, or None
    """
    grids.append(dict(file=file, name=name, clat=clat, clon=clon,
                      topo_file=topo_file, markers=markers or []))

# ------------------------------------------------------------------------------
# Output path
fig_file = 'figs/grid.png'
# ------------------------------------------------------------------------------
# Add grids here
grid_root = '/global/cfs/cdirs/m4310/whannah/files_grid'
topo_root = '/global/cfs/cdirs/e3sm/inputdata/atm/cam/topo'
# add_grid(f'{grid_root}/ne30pg2_scrip.nc',  'ne30',  clat=38, clon=-120)#, topo_file=f'{topo_root}/USGS-topo_ne30np4_smoothedx6t_20250513.nc')
# add_grid(f'{grid_root}/scrip_ne120pg2.nc', 'ne120', clat=38, clon=-120)#, topo_file=f'{topo_root}/USGS-gtopo30_ne120np4pg2_x6t_20230404.nc')

grid_root = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid'
# add_grid(f'{grid_root}/ne16pg2_scrip.nc', 'ne16')#, clat=40, clon=260)
# add_grid(f'{grid_root}/RRM-test-16x2-pg2_scrip.nc', 'RRM-test-16x2')#, clat=40, clon=260)

# add_grid(f'{grid_root}/RRM-test-32x1-pg2_scrip.nc', 'RRM-test-32x1')#, clat=40, clon=260)
# add_grid(f'{grid_root}/RRM-test-32x1-hmpg2_scrip.nc', 'RRM-test-32x1-hm')#, clat=40, clon=260)

add_grid(f'{grid_root}/RRM-test-2x7-pg2_scrip.nc', 'RRM-test-2x7')#, clat=40, clon=260)
add_grid(f'{grid_root}/RRM-test-4x6-pg2_scrip.nc', 'RRM-test-4x6')#, clat=40, clon=260)

# add_grid(f'{grid_root}/ne4-pynp4_scrip.nc', 'ne4-py np4')#, clat=40, clon=260)
# add_grid(f'{grid_root}/ne4-hmnp4_scrip.nc', 'ne4-hm np4')#, clat=40, clon=260)

# ------------------------------------------------------------------------------
# Shade mode: 'area', 'topo', or 'lines'
shade_mode = 'lines'

# Color scale for 'area' mode — approximate grid spacing [km]
dx_min = 3.0
dx_max = 150.0
dx_log = True        # log color scale (recommended for RRM grids)

# Color scale for 'topo' mode — surface elevation [m]
topo_min = -500
topo_max = 4800

# Half-width/height of the zoomed view [degrees]
half_w = 50
half_h = 30

# Panel layout and figure size [inches per panel]
num_plot_col = 1#len(grids)
panel_w      = 5.5
panel_h      = 5.5

# --------------------------------------------------------------------------------------------------
# Colormaps
# --------------------------------------------------------------------------------------------------
CMAP_AREA = cmocean.cm.curl
CMAP_TOPO = mpl.colormaps['terrain']

# --------------------------------------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------------------------------------
RE = 6.37122e6   # radius of earth [m]

# ------------------------------------------------------------------------------
# Load SCRIP grid variables from a NetCDF file
def load_scrip(path):
    ds = xr.open_dataset(path)
    return dict(
        clat   = ds['grid_center_lat'].values,
        clon   = ds['grid_center_lon'].values,
        vlat   = ds['grid_corner_lat'].values,   # (ncells, nvertices)
        vlon   = ds['grid_corner_lon'].values,
        area   = ds['grid_area'].values,          # steradians
        ncells = len(ds['grid_area']),
    )

# ------------------------------------------------------------------------------
# Compute approximate grid spacing [km] from SCRIP area [steradians]
def approx_dx(area):
    return np.sqrt(area) * RE / 1e3

# ------------------------------------------------------------------------------
# Load surface elevation [m] from an E3SM topo file
def load_topo(path):
    ds = xr.open_dataset(path)
    if 'PHIS' in ds:
        return ds['PHIS'].values.squeeze() / 9.81   # geopotential → elevation [m]
    if 'terr' in ds:
        return ds['terr'].values.squeeze()
    raise ValueError(f"No recognized topo variable (PHIS or terr) in {path}")

# ------------------------------------------------------------------------------
# Normalize longitudes from 0..360 to -180..180
def norm_lon(lon):
    return np.where(lon > 180.0, lon - 360.0, lon)

# ------------------------------------------------------------------------------
# Project SCRIP corner vertices into the native coordinate system of `proj`.
# Returns x, y of shape (ncells, nvertices) and a boolean visibility mask
# (True = all corners project without NaN).
def transform_verts(vlat, vlon, proj, src_crs):
    ncells, nv = vlat.shape
    xyz = proj.transform_points(src_crs, vlon.ravel(), vlat.ravel())
    x = xyz[:, 0].reshape(ncells, nv)
    y = xyz[:, 1].reshape(ncells, nv)
    vis = ~np.any(np.isnan(x) | np.isnan(y), axis=1)
    return x, y, vis

# --------------------------------------------------------------------------------------------------
# Build figure
# --------------------------------------------------------------------------------------------------
num_grids = len(grids)
num_rows  = int(np.ceil(num_grids / num_plot_col))
src_crs   = ccrs.PlateCarree()

fig = plt.figure(figsize=(panel_w * num_plot_col, panel_h * num_rows))

for idx, g in enumerate(grids):

    print(f'  {tclr.GRN}{g["name"]:20}{tclr.END}  {tclr.YLW}{g["file"]}{tclr.END}')

    # --------------------------------------------------------------------------

    proj = ccrs.PlateCarree()
    ax   = fig.add_subplot(num_rows, num_plot_col, idx + 1, projection=proj)

    ax.set_global()

    clon, clat = g['clon'], g['clat']
    # ax.set_extent(
    #     [clon - half_w, clon + half_w, clat - half_h, clat + half_h],
    #     crs=src_crs,
    # )

    # --------------------------------------------------------------------------
    # Load grid data and determine fill color data + colormap
    sc     = load_scrip(g['file'])
    ncells = sc['ncells']
    dx     = approx_dx(sc['area'])
    # --------------------------------------------------------------------------
    print(f'    ncells : {ncells}')
    print(f'    dx     : {np.min(dx):6.2f} - {np.max(dx):6.2f} km')
    # --------------------------------------------------------------------------
    if shade_mode == 'topo':
        if g['topo_file'] is None:
            raise ValueError(f"shade_mode='topo' requires topo_file for grid '{g['name']}'")
        fill_data   = load_topo(g['topo_file'])
        cmap        = CMAP_TOPO
        norm        = mcolors.Normalize(vmin=topo_min, vmax=topo_max)
        cbar_label  = 'Elevation [m]'
        do_fill     = True
        coast_color = 'white'

    elif shade_mode == 'area':
        fill_data   = dx
        cmap        = CMAP_AREA
        norm        = (mcolors.LogNorm(vmin=dx_min, vmax=dx_max) if dx_log
                       else mcolors.Normalize(vmin=dx_min, vmax=dx_max))
        cbar_label  = 'Approx. grid spacing [km]'
        do_fill     = True
        coast_color = 'white'

    else:   # 'lines'
        fill_data   = None
        cmap        = None
        norm        = None
        cbar_label  = None
        do_fill     = False
        coast_color = '#333333'

    # --------------------------------------------------------------------------
    # Background features (land/ocean base layer for 'lines' mode)
    if not do_fill:
        ax.add_feature(cfeature.OCEAN, facecolor='#cde4f0', zorder=0)
        ax.add_feature(cfeature.LAND,  facecolor='#e8e8e8', zorder=0)

    # --------------------------------------------------------------------------
    # Normalize corner and center longitudes from 0..360 to -180..180.
    # E3SM SCRIP files store longitudes in 0..360; PlateCarree expects -180..180.
    vlon_norm = norm_lon(sc['vlon'])
    cclon     = norm_lon(sc['clon'])
    cclat     = sc['clat']

    # --------------------------------------------------------------------------
    # Transform normalized corner vertices to projected coordinates
    x, y, vis = transform_verts(sc['vlat'], vlon_norm, proj, src_crs)

    # --------------------------------------------------------------------------
    # Keep cells whose center falls within the zoomed view extent, padded by
    # one approximate cell-width so partially visible edge cells are included.
    # set_extent handles the visual clipping.
    dx_deg  = dx.max() / 111.0   # rough cell size in degrees (1 deg ~ 111 km)
    pad     = dx_deg * 1.5
    # in_view = (
    #     (cclat >= clat - half_h - pad) & (cclat <= clat + half_h + pad) &
    #     (cclon >= clon - half_w - pad) & (cclon <= clon + half_w + pad)
    # )
    # vis = vis & in_view

    # --------------------------------------------------------------------------
    # Exclude cells that straddle the antimeridian (vertex lon range > 180 deg)
    vlon_range  = vlon_norm.max(axis=1) - vlon_norm.min(axis=1)
    not_wrapped = vlon_range < 180.0
    vis = vis & not_wrapped

    # --------------------------------------------------------------------------
    # Build PolyCollection from visible cells
    verts = np.stack([x[vis], y[vis]], axis=-1)   # (nvis, nvertices, 2)

    if do_fill:
        col = mcollections.PolyCollection(
            verts,
            array=fill_data[vis],
            cmap=cmap,
            norm=norm,
            linewidths=0,
            edgecolors='none',
            zorder=2,
        )
    else:
        col = mcollections.PolyCollection(
            verts,
            facecolors='none',
            edgecolors='#444444',
            linewidths=0.3,
            zorder=2,
        )
    ax.add_collection(col)

    # --------------------------------------------------------------------------
    # Coastlines and state borders
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor=coast_color, zorder=3)
    ax.add_feature(cfeature.STATES,    linewidth=0.4, edgecolor=coast_color, zorder=3)

    # --------------------------------------------------------------------------
    # Optional markers (list of (lat, lon) tuples)
    for (mlat, mlon) in g['markers']:
        ax.plot(mlon, mlat, 'r^', markersize=6, transform=src_crs, zorder=5)

    # --------------------------------------------------------------------------
    # Per-panel colorbar
    if do_fill:
        cb = fig.colorbar(col, ax=ax, orientation='horizontal',
                          fraction=0.04, pad=0.02, shrink=0.85)
        cb.set_label(cbar_label, fontsize=8)
        cb.ax.tick_params(labelsize=7)

    # --------------------------------------------------------------------------
    # Subplot title
    ax.set_title(f"{g['name']}   ({ncells:,} cells,  "
                 f"dx {dx.min():.1f}–{dx.max():.1f} km)", fontsize=9)

# --------------------------------------------------------------------------------------------------
# Save figure
# --------------------------------------------------------------------------------------------------
os.makedirs(os.path.dirname(fig_file), exist_ok=True)
fig.tight_layout()
fig.savefig(fig_file, dpi=200, bbox_inches='tight')
print(f'\n{fig_file}\n')