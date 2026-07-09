import os, numpy as np, xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
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
grid_root = '/global/cfs/cdirs/e3sm/whannah/files_vert'

add_grid(f'{grid_root}/SCREAM_L128_v3.1_c20251112_alpha_1.0_pm_100.nc', n='L128 v3.1 alpha=1.0 pm=100', c='black')
add_grid(f'{grid_root}/SCREAM_L128_v3.1_c20251112_alpha_1.5_pm_100.nc', n='L128 v3.1 alpha=1.5 pm=100', c='red')
add_grid(f'{grid_root}/SCREAM_L128_v3.1_c20251112_alpha_2.0_pm_100.nc', n='L128 v3.1 alpha=2.0 pm=100', c='green')
add_grid(f'{grid_root}/SCREAM_L128_v3.1_c20251112_alpha_2.5_pm_100.nc', n='L128 v3.1 alpha=2.5 pm=100', c='blue')
add_grid(f'{grid_root}/SCREAM_L128_v3.1_c20251112_alpha_3.0_pm_100.nc', n='L128 v3.1 alpha=3.0 pm=100', c='purple')

#-------------------------------------------------------------------------------
# Settings
#-------------------------------------------------------------------------------
fig_file    = os.path.join('vertical_hybrid_coeffs.png')
print_table = True

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
    ilev_list_tbl = []
    zlev_list_tbl = []
    hyai_list = []
    hybi_list = []
    for opts in opt_list:
        ds   = xr.open_dataset(opts['file'])
        hyai = ds['hyai']
        hybi = ds['hybi']
        ilev = ds['hyai'].values * 1000 + ds['hybi'].values * 1000
        zlev = np.log(ilev / 1e3) * -6740.
        # dz = np.diff(z)
        ilev_list_tbl.append(ilev)
        zlev_list_tbl.append(zlev)
        hyai_list.append(hyai)
        hybi_list.append(hybi)

    max_len = max(len(m) for m in ilev_list_tbl)
    for k in range(max_len):
        k2  = max_len - k - 1
        msg = f'{k:3}  ({k2:3}) '
        zip_list = zip(ilev_list_tbl, zlev_list_tbl, hyai_list, hybi_list)
        for g, (ilev, zlev, hyai, hybi) in enumerate(zip_list):
            if k < len(ilev):
                msg += ' '*6
                msg += f'  {ilev[k]:8.2f} mb   {zlev[k]:8.1f} m'
                msg += f'  a/b: {hyai[k]:6.4f} / {hybi[k]:6.4f}'
                msg += f'  a+b: {(hyai[k]+hybi[k]):6.4f}'
        print(msg)
# exit()
#-------------------------------------------------------------------------------
# Load data
#-------------------------------------------------------------------------------
data_list = []

for opts in opt_list:
    ds   = xr.open_dataset(opts['file'])
    # hyam = ds['hyam'].values
    # hybm = ds['hybm'].values
    hyai = ds['hyai'].values
    hybi = ds['hybi'].values
    lev  = hyai*1e3 + hybi*1e3
    lbl  = opts.get('n', opts['file'])
    # hapy.print_stat(hyam, name=lbl+' hyam', stat='nxh', indent='    ', compact=True)
    # hapy.print_stat(hybm, name=lbl+' hybm', stat='nxh', indent='    ', compact=True)
    hapy.print_stat(hyai, name=lbl+' hyai', stat='nxh', indent='    ', compact=True)
    hapy.print_stat(hybi, name=lbl+' hybi', stat='nxh', indent='    ', compact=True)
    # data_list.append({'hyam': hyam, 'hybm': hybm, 'lev': lev})
    data_list.append({'hyai': hyai, 'hybi': hybi, 'lev': lev})

#-------------------------------------------------------------------------------
# Create figure
#-------------------------------------------------------------------------------
lw = 1.8
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 6))

def _add_legends(ax):
    handles = ax._hyai_handles
    leg1 = ax.legend(handles=handles, fontsize=8, loc='upper left',
                     framealpha=0.85, edgecolor='gray')
    ax.add_artist(leg1)
    style_handles = [
        Line2D([0], [0], color='gray', linestyle='solid',  linewidth=lw, label='hyai'),
        Line2D([0], [0], color='gray', linestyle='dashed', linewidth=lw, label='hybi'),
    ]
    ax.legend(handles=style_handles, fontsize=8, loc='upper right',
              framealpha=0.85, edgecolor='gray')

# ---- Panel 1 ----
ax.set_xlabel('Hybrid Coefficient', fontsize=11)
ax.set_ylabel('Level [hPa]', fontsize=11)
ax.tick_params(direction='in', which='both')
ax.set_yscale('log')
ax.invert_yaxis()
ax._hyai_handles = []

for opts, data in zip(opt_list, data_list):
    label = opts.get('n', opts['file'])
    color = opts['c']
    lev   = data['lev']
    hyai  = data['hyai']
    hybi  = data['hybi']
    line, = ax.plot(hyai, lev, color=color, linestyle='solid',  linewidth=lw, label=label)
    ax.plot(        hybi, lev, color=color, linestyle='dashed', linewidth=lw)
    ax._hyai_handles.append(line)

ax.set_title('Hybrid Coefficients vs Level', fontsize=11)
_add_legends(ax)

# ---- Panel 2 (normalized) ----
ax2.set_xlabel('Normalized Hybrid Coefficient', fontsize=11)
ax2.set_ylabel('Normalized Level', fontsize=11)
ax2.tick_params(direction='in', which='both')
ax2.invert_yaxis()
ax2._hyai_handles = []

for opts, data in zip(opt_list, data_list):
    label = opts.get('n', opts['file'])
    color = opts['c']
    hyai  = data['hyai'].copy()
    hybi  = data['hybi'].copy()
    lev   = data['lev'].copy()
    denom = hyai + hybi
    hyai  = hyai / denom
    hybi  = hybi / denom
    lev   = lev  / np.max(lev)
    line, = ax2.plot(hyai, lev, color=color, linestyle='solid',  linewidth=lw, label=label)
    ax2.plot(         hybi, lev, color=color, linestyle='dashed', linewidth=lw)
    ax2._hyai_handles.append(line)

ax2.set_title('Normalized Hybrid Coefficients vs Level', fontsize=11)
_add_legends(ax2)

plt.tight_layout()
os.makedirs(os.path.dirname(fig_file), exist_ok=True)
plt.savefig(fig_file, dpi=150, bbox_inches='tight')
print(f'\n{fig_file.replace(home+"/E3SM/","")}\n')
plt.close()
