import os, numpy as np, xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import hapy
home = os.getenv('HOME')
#-------------------------------------------------------------------------------
# Grid registration
#-------------------------------------------------------------------------------
opt_list = []
def add_grid(file_path, **kwargs):
    case_opts = {'file': file_path}
    for k, val in kwargs.items():
        case_opts[k] = val
    opt_list.append(case_opts)
#-------------------------------------------------------------------------------

add_grid(f'{home}/HICCUP/files_vert/L80_for_E3SMv3.nc',                n='L80 EAMv3 default',d=0,c='gray')
add_grid(f'{home}/HICCUP/files_vert/vert_coord_E3SM_L128.nc',          n='L128 default',d=0,c='black'  )
# add_grid(f'{home}/E3SM/vert_grid_files/SCREAM_L128_v3.0_c20251112.nc', n='L128 v3.0',c='red')
add_grid(f'{home}/E3SM/vert_grid_files/SCREAM_L128_v3.1_c20251112.nc', n='L128 v3.1',c='green')
add_grid(f'{home}/E3SM/vert_grid_files/SCREAM_L128_v3.2_c20251112.nc', n='L128 v3.2',c='blue')
add_grid(f'{home}/E3SM/vert_grid_files/SCREAM_L128_v3.3_c20251112.nc', n='L128 v3.3',c='magenta')


print()
for opts in opt_list: print(opts['file'])
print()

#-------------------------------------------------------------------------------
# Settings
#-------------------------------------------------------------------------------
fig_file        = os.path.join('vertical_grid_spacing.png')
print_table     = False
use_height      = True   # use height (km) for Y-axis; else use pressure (hPa)
add_zoomed_plot = True
zoom_top_idx    = -30    # index cutoff for zoomed panel

#-------------------------------------------------------------------------------
# simple routine to print simple statistics
#-------------------------------------------------------------------------------
def print_stat(x, name='(no name)', unit='', fmt='f', stat='naxh', indent=' '*2, compact=True):
    """ Print min, avg, max, std, and shape of input """
    fmt = {'f':'%.4f', 'e':'%e', 'g':'%g'}.get(fmt, fmt)
    ops = {'h': ('shp', lambda v: str(v.shape)),
           'a': ('avg', lambda v: fmt % v.mean()),
           'n': ('min', lambda v: fmt % v.min()),
           'x': ('max', lambda v: fmt % v.max()),
           's': ('std', lambda v: fmt % v.std())}
    unit = f'[{unit}]' if unit else ''
    head = f'{indent}{name:{12 if compact else len(name)}} {unit}'
    body = [f'   {lbl}: {fn(x)}' for lbl, fn in (ops[c] for c in stat if c in ops)]
    msg = head+''.join(body) if compact else '\n'.join([head]+[indent+b for b in body])
    print(msg)
    return msg
#-------------------------------------------------------------------------------
# Assign unique colors to any grid that didn't specify one
#-------------------------------------------------------------------------------
def _gen_unique_colors(n_colors):
    """Return n visually distinct colors using HSV spacing."""
    return [mcolors.hsv_to_rgb((i / n_colors, 0.85, 0.80)) for i in range(n_colors)]

_uncolored = [i for i, o in enumerate(opt_list) if 'c' not in o]
_palette   = _gen_unique_colors(len(_uncolored))
for idx, palette_color in zip(_uncolored, _palette):
    opt_list[idx]['c'] = palette_color

#-------------------------------------------------------------------------------
# Print table
#-------------------------------------------------------------------------------
if print_table:
    mlev_list_tbl, zlev_list_tbl = [], []
    for opts in opt_list:
        ds   = xr.open_dataset(opts['file'])
        mlev = ds['hyai'].values * 1000 + ds['hybi'].values * 1000
        zlev = np.log(mlev / 1e3) * -6740.
        mlev_list_tbl.append(mlev)
        zlev_list_tbl.append(zlev)

    max_len = max(len(m) for m in mlev_list_tbl)
    for k in range(max_len):
        k2  = max_len - k - 1
        msg = f'{k:3}  ({k2:3}) '
        for g, (mlev, zlev) in enumerate(zip(mlev_list_tbl, zlev_list_tbl)):
            if k < len(mlev):
                msg += f'     {mlev[k]:8.2f} mb   {zlev[k]:8.1f} m'
        print(msg)

#-------------------------------------------------------------------------------
# Load data
#-------------------------------------------------------------------------------
mlev_list = []
dlev_list = []

for opts in opt_list:
    ds    = xr.open_dataset(opts['file'])
    mlev  = ds['hyam'].values * 1000 + ds['hybm'].values * 1000
    ilev  = ds['hyai'].values * 1000 + ds['hybi'].values * 1000

    ilevz = np.log(ilev / 1e3) * -6740.         # interface heights [m]
    mlevz = np.log(mlev / 1e3) * -6740. / 1e3   # midpoint heights  [km]

    lbl = opts.get('n', opts['file'])
    hapy.print_stat(mlev,  name=lbl+' mlev', stat='nxh', indent='    ', compact=True)
    hapy.print_stat(mlevz, name=lbl+' zlev', stat='nxh', indent='    ', compact=True)

    dlevz = np.array([ilevz[k] - ilevz[k+1] for k in range(len(mlev))])

    if use_height:
        mlev_list.append(mlevz)
    else:
        mlev_list.append(mlev)
    dlev_list.append(dlevz)

#-------------------------------------------------------------------------------
# Create figure
#-------------------------------------------------------------------------------
lw        = 1.8
ms        = 4
n_panels  = 2 if add_zoomed_plot else 1
fig, axes = plt.subplots(1, n_panels, figsize=(5 * n_panels, 8), sharey=False)
if n_panels == 1:
    axes = [axes]

ax1 = axes[0]
ax2 = axes[1] if add_zoomed_plot else None

ylabel = 'Approx. Height [km]'  if use_height else 'Approx. Pressure [hPa]'
xlabel = 'Grid Spacing [m]'

for ax in axes:
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.tick_params(direction='in', which='both')

# ---- Axis limits ----
# dlev_min  = min(np.nanmin(d)              for d in dlev_list)
dlev_min  = 0.
dlev_max  = max(np.nanmax(d)              for d in dlev_list)
mlev_min  = min(np.nanmin(m)              for m in mlev_list)
mlev_max  = max(np.nanmax(m)              for m in mlev_list)
dlev_max2 = max(np.nanmax(d[zoom_top_idx:]) for d in dlev_list)
mlev_min2 = min(np.nanmin(m[zoom_top_idx:]) for m in mlev_list)
mlev_max2 = max(np.nanmax(m[zoom_top_idx:]) for m in mlev_list)

x_pad = (dlev_max - dlev_min) * 0.05
ax1.set_xlim(dlev_min, dlev_max + x_pad)
# ax1.set_ylim(mlev_min, mlev_max + (mlev_max - mlev_min) * 0.05)

if use_height:
    ax1.set_ylim(mlev_min, mlev_max + (mlev_max - mlev_min) * 0.15)
else:
    ax1.set_ylim(mlev_min * 0.5, mlev_max + (mlev_max - mlev_min) * 0.05)

if ax2 is not None:
    x_pad2 = (dlev_max2 - dlev_min) * 0.05
    y_pad2 = (mlev_max2 - mlev_min2) * 0.05
    # ax2.set_xlim(dlev_min, dlev_max2 + x_pad2)
    # ax2.set_ylim(mlev_min2, mlev_max2)# + y_pad2)
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0, 3)# + y_pad2)

# Pressure axis: invert and log scale
if not use_height:
    for ax in axes:
        ax.invert_yaxis()
    ax1.set_yscale('log')

# ---- Plot lines ----
handles = []
for opts, mlev, dlev in zip(opt_list, mlev_list, dlev_list):
    label = opts.get('n', opts['file'])
    color = opts['c']
    ls    = opts['ls'] if 'ls' in opts else 'solid'
    # ls    = '--' if opts.get('d', 0) else '-'

    line, = ax1.plot(dlev, mlev, color=color, linestyle=ls,
                     linewidth=lw, marker='o', markersize=ms, label=label)
    ax1.plot(dlev[0], mlev[0], marker='_', color=color, markersize=30,   # <-- top marker
                markeredgecolor='black', markeredgewidth=0.5, zorder=5)
    handles.append(line)

    if ax2 is not None:
        ax2.plot(dlev, mlev, color=color, linestyle=ls,
                 linewidth=lw, marker='o', markersize=ms)

# ---- Legend ----
ax1.legend(handles=handles, fontsize=8, loc='upper left',
           framealpha=0.85, edgecolor='gray')

# ---- Titles ----
ax1.set_title('Full Column', fontsize=11)
if ax2 is not None:
    ax2.set_title('Lower Troposphere (zoomed)', fontsize=11)

plt.tight_layout()
os.makedirs(os.path.dirname(fig_file), exist_ok=True)
plt.savefig(fig_file, dpi=150, bbox_inches='tight')
print(f'\n{fig_file.replace(home+"/E3SM/","")}\n')
plt.close()