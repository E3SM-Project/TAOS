import matplotlib
# matplotlib.use('Agg')
import os, subprocess as sp, numpy as np, xarray as xr, dask, copy, string, cmocean, glob, uxarray as ux
import cartopy.crs as ccrs; import matplotlib.pyplot as plt; import matplotlib.colors as mcolors
import hapy
#-------------------------------------------------------------------------------
file_list,name_list = [],[]
scrip_file_list = []
def add_file(file,name=None,scrip_file=None):
   file_list.append(file)
   name_list.append(name)
   scrip_file_list.append(scrip_file)
#-------------------------------------------------------------------------------
var,lev_list,var_str = [],[],[]
htype_list = []
def add_var(var_name,lev=0,s=None,htype=None): 
   var.append(var_name); lev_list.append(lev); 
   if s is None:
      var_str.append(var_name)
   else:
      var_str.append(s)
   htype_list.append(htype)
# ------------------------------------------------------------------------------
# Output path
fig_file = 'figs/topo.png'
#-------------------------------------------------------------------------------

# grid_root = '/lcrc/group/e3sm/ac.whannah/scratch/chrys/E3SM_grid_support/2026-ne30-test/files_grid'
# topo_root1 = '/lcrc/group/e3sm/data/inputdata/atm/cam/topo'
# topo_root2 = '/lcrc/group/e3sm/ac.whannah/scratch/chrys/E3SM_grid_support/2026-ne30-test/files_topo'

# grid_root = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/2026-ne30-test/files_grid'
grid_root = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid'
topo_root1 = '/global/cfs/cdirs/e3sm/inputdata/atm/cam/topo'
# topo_root2 = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/2026-ne30-test/files_topo/'
topo_root2 = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_topo'

# scrip_file = f'{grid_root}/ne30np4_scrip.nc'

# scrip_file = f'{grid_root}/ne30pg2_scrip.nc'
# add_file(f'{topo_root1}/USGS-gtopo30_ne30np4pg2_x6t-SGH.c20210614.nc',name='default ne30 topo')
# # add_file(f'{topo_root2}/USGS-topo_ne30-np4_smoothedx6t_20260204-nc.nc',name='bash+NCO SGH workflow')
# # add_file(f'{topo_root2}/USGS-topo_ne30-np4_smoothedx6t_20260204-py.nc',name='python SGH workflow')
# add_file(f'{topo_root2}/USGS-topo_ne30-np4_smoothedx6t_20260403.nc',name='new workflow')



# scrip_file = f'{topo_root2}/../files_grid/ne3000pg1_scrip.nc'
# topo_root1 = f'{topo_root1}/../hrtopo'
# add_file(f'{topo_root1}/USGS-topo-cube3000.nc',  name='ne3000 old')
# add_file(f'{topo_root2}/tmp_USGS-topo_ne3000.nc',name='ne3000 new')

# scrip_file = f'{grid_root}/ne30pg2_scrip.nc'
# add_file(f'{topo_root2}/tmp_USGS-topo_ne30-pg2.nc',name='SRC=>ne30pg2  tmp_USGS-topo_ne30-pg2.nc')
# add_file(f'{topo_root2}/tmp_3km-topo_ne30-pg2.nc',name='3km=>ne30pg2  tmp_3km-topo_ne30-pg2.nc')
# # add_file(f'{topo_root2}/tmp_3km-topo_ne30-pg2.old.nc',name='3km=>ne30pg2  tmp_3km-topo_ne30-pg2.old.nc')

# add_file(f'{topo_root2}/USGS-topo_ne30-np4_smoothedx6t_20260204-nc.nc',name='bash+NCO topo')

# topo_root = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_topo'
# scrip_file = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid/ne30np4_scrip.nc'
# add_file(f'{topo_root}/USGS-topo_ne30-hm-np4_smoothedx6t_20260403.nc',name='ne30-hm')#,scrip_file=grid_file)
# add_file(f'{topo_root}/USGS-topo_ne30-py-np4_smoothedx6t_20260403.nc',name='ne30-py')#,scrip_file=grid_file)

topo_root  = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_topo'
# scrip_file = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid/RRM-test-32x1-hmnp4_scrip.nc'
scrip_file = '/global/cfs/cdirs/e3sm/whannah/E3SM_grid_support/workflow-test/files_grid/RRM-test-32x1-hmpg2_scrip.nc'

# add_file(f'{topo_root}/tmp_USGS-topo_RRM-test-32x1-hm-np4.nc',name='RRM-test-32x1-hm')
# add_file(f'{topo_root}/tmp_USGS-topo_RRM-test-32x1-py-np4.nc',name='RRM-test-32x1-py')
# add_var('PHIS')

# add_file(f'{topo_root}/tmp_USGS-topo_RRM-test-32x1-hm-np4_smoothedx6t.nc',name='RRM-test-32x1-hm')
# add_file(f'{topo_root}/tmp_USGS-topo_RRM-test-32x1-py-np4_smoothedx6t.nc',name='RRM-test-32x1-py')
# add_var('PHIS_d')

add_file(f'{topo_root}/USGS-topo_RRM-test-32x1-hm-np4_smoothedx6t_20260403.nc',name='RRM-test-32x1-py')#,scrip_file=grid_file)
add_file(f'{topo_root}/USGS-topo_RRM-test-32x1-py-np4_smoothedx6t_20260403.nc',name='RRM-test-32x1-py')#,scrip_file=grid_file)

# scrip_file = f'compare_np4/ne30_np4_scrip_homme.nc'
# scrip_file = f'compare_np4/ne30_np4_scrip_python.nc'
# add_file('compare_np4/ne30_np4_scrip_homme.nc',name='ne30_np4_scrip_homme',scrip_file='compare_np4/ne30_np4_scrip_homme.nc')
# add_file('compare_np4/ne30_np4_scrip_python.nc',name='ne30_np4_scrip_python',scrip_file='compare_np4/ne30_np4_scrip_python.nc')

# scrip_file='compare_np4/ne4_np4_scrip_homme.nc'
# # scrip_file='compare_np4/ne4_np4_scrip_python.nc'
# add_file('compare_np4/ne4_np4_scrip_homme.nc', name='ne4_np4_scrip_homme', scrip_file='compare_np4/ne4_np4_scrip_homme.nc')
# add_file('compare_np4/ne4_np4_scrip_python.nc',name='ne4_np4_scrip_python',scrip_file='compare_np4/ne4_np4_scrip_python.nc')

#-------------------------------------------------------------------------------

# add_var('PHIS')
# add_var('PHIS_d')
# add_var('SGH')
add_var('SGH30')

# add_var('grid_area')


#-------------------------------------------------------------------------------

# plot_diff = False
add_diff  = True

print_stats          = True
var_x_case           = True

# num_plot_col         = 1#len(var)

use_common_label_bar = False

if 'use_snapshot' not in locals(): use_snapshot,ss_t = False,-1

#---------------------------------------------------------------------------------------------------
num_var = len(var)
num_file = len(file_list)
if 'plot_diff' not in locals(): plot_diff = False
if 'add_diff'  not in locals(): add_diff = False
#---------------------------------------------------------------------------------------------------
# set up figure objects
subplot_kwargs = {}
subplot_kwargs['projection'] = ccrs.Robinson(central_longitude=180)
# subplot_kwargs['projection'] = ccrs.PlateCarree(central_longitude=180)
# lat_min, lat_max = -90, -60
# subplot_kwargs['projection'] = ccrs.Orthographic(central_latitude=-85)

fdx,fdy=12,6
if add_diff:
   (d1,d2) = (num_var,num_file+1) if var_x_case else (num_file+1,num_var)
   figsize = (fdx*num_file+1,fdy*num_var) if var_x_case else (fdx*num_var,fdy*num_file+1)
else:
   (d1,d2) = (num_var,num_file) if var_x_case else (num_file,num_var)
   figsize = (fdx*num_file,fdy*num_var) if var_x_case else (fdx*num_var,fdy*num_file)

title_fontsize,lable_fontsize = 16,16

fig, axs = plt.subplots(d1,d2, subplot_kw=subplot_kwargs, figsize=figsize, squeeze=False )

#---------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------
for v in range(num_var):
   hapy.print_line()
   print(' '*2+'var: '+hapy.tclr.MAGENTA+var[v]+hapy.tclr.END)
   print()
   data_list = []
   glb_avg_list = []
   lat_list,lon_list = [],[]
   grid_ds_list = []
   if 'lev_list' in locals(): lev = lev_list[v]
   for f in range(num_file):
      print(' '*4+'file: '+hapy.tclr.GREEN+file_list[f]+hapy.tclr.END)
      #-------------------------------------------------------------------------
      # scrip_file = scrip_file_list[f]
      #-------------------------------------------------------------------------
      # ds = ux.open_dataset(scrip_file, file_list[f])

      grid_ds = xr.open_dataset(scrip_file)
      ds      = xr.open_dataset(file_list[f])
      #-------------------------------------------------------------------------
      # compare datasets
      if False:
         print()
         print(ds)
         print()
         # if f==0: continue
         # if f==1: exit()
      #-------------------------------------------------------------------------
      if var[v]=='PHIS' and 'terr' in ds:
         data = ds['terr']*9.81
      else:
         data = ds[var[v]]
      #-------------------------------------------------------------------------
      # print(); print(data)
      #-------------------------------------------------------------------------
      # compare coordinates
      if False:
         npts = 10
         print(' '*6+f'lat / lon [:{npts}]:')
         for i in range(npts):
            # cell centers
            lat_val = ds.grid_center_lat[i].values[0]
            lon_val = ds.grid_center_lon[i].values[0]
            area = ds.grid_area[i].values[0]
            print(' '*8+f'{lat_val:10.4f}  / {lon_val:10.4f}    {area}')
            # # cell corners
            # for j in range(4):
            #    lat_val = ds.grid_corner_lat[i].values[0][j]
            #    lon_val = ds.grid_corner_lon[i].values[0][j]
            #    print(' '*8+f'{lat_val:10.4f}  / {lon_val:10.4f}')
         if f==0: continue
         if f==1: exit()
      #-------------------------------------------------------------------------
      # # check polar points
      # if True:
      #    for i in range(len(data)):
      #       # lat_val = ds.grid_center_lat[i].values[0]
      #       # lon_val = ds.grid_center_lon[i].values[0]
      #       # area = ds.grid_area[i].values[0]
      #       # print(' '*8+f'{lat_val:10.4f}  / {lon_val:10.4f}    {area}')
      #       for j in range(len(ds.grid_corners)):
      #          lat_val = ds.grid_corner_lat[i].values[0][j]
      #          lon_val = ds.grid_corner_lon[i].values[0][j]
      #          if lat_val>89:
      #             print(' '*8+f'i: {i:6}    {lat_val:10.4f}  / {lon_val:10.4f}')
      #    if f==0: continue
      #    if f==1: exit()
      #-------------------------------------------------------------------------
      if print_stats: hapy.print_stat(data,name=var[v],stat='naxsh',indent='    ',compact=True,fmt='e')
      #-------------------------------------------------------------------------
      if 'ncol_d' in data.dims: data = data.rename({'ncol_d':'ncol'})
      # print()
      # print(data)
      # print()
      # print(grid_ds)
      # print()
      # exit()
      data_list.append( data )
      grid_ds_list.append(grid_ds)
      #-------------------------------------------------------------------------
      # # save baseline for diff map
      # if plot_diff and f==0: data_baseline = data.copy()
   #----------------------------------------------------------------------------
   # calculate common limits for consistent contour levels
   data_min = np.min([np.nanmin(d) for d in data_list])
   data_max = np.max([np.nanmax(d) for d in data_list])
   if plot_diff or add_diff:
      tmp_data = copy.deepcopy(data_list)
      for f in range(num_file): tmp_data[f] = data_list[f] - data_list[0]
      # diff_data_max = np.max([np.nanmax(d) for d in tmp_data])
      # diff_data_min = np.min([np.nanmin(d) for d in tmp_data])
      diff_data_max = np.max([np.nanmax(np.absolute(d)) for d in tmp_data])
      diff_data_min = -1*diff_data_max
   if plot_diff and not add_diff:
      for f in range(num_file):
         if f>0:
            data_list[f] = data_list[f] - data_list[0]
   if add_diff and not plot_diff:
      diff = copy.deepcopy(data_list[1])
      diff = diff - data_list[0]
      hapy.print_stat(diff,name=f'{var[v]} diff',stat='naxsh',indent='    ',compact=True,fmt='e')
   #----------------------------------------------------------------------------
   # set color bar levels
   clev = None
   # if var[v]=='': clev = np.logspace( -5, -1, num=40)
   # if var[v]=='': clev = np.linspace( 800e2, 1020e2, num=40)
   # if var[v]=='': clev = np.arange(600e2,1040e2+2e2,10e2)
   # if var[v]=='PHIS': clev = np.linspace( 0, 5000e1, num=100)
   #----------------------------------------------------------------------------
   # set color map
   cmap = 'viridis'
   # cmap = cmocean.cm.rain
   #----------------------------------------------------------------------------
   num_file_alt = (num_file+1) if add_diff else num_file
   for f in range(num_file_alt):
      img_kwargs = {}
      img_kwargs['origin'] = 'lower'
      img_kwargs['cmap']   = cmap

      if var[v]=='PHIS': img_kwargs['vmin'],img_kwargs['vmax'] = 0,5000e1

      # if plot_diff and f>0:
      #    img_kwargs['cmap'] = cmocean.cm.balance
      #    img_kwargs['vmin'] = diff_data_min
      #    img_kwargs['vmax'] = diff_data_max
      #    clev = None

      ax = axs[v,f] if var_x_case else axs[f,v]
      ax.coastlines(linewidth=0.2,edgecolor='white')
      ax.set_global()

      if add_diff and f==num_file:
         img_kwargs['cmap'] = cmocean.cm.balance
         # if var[v]=='PHIS': img_kwargs['vmin'],img_kwargs['vmax'] = -1000e1,1000e1
         img_kwargs['vmin'],img_kwargs['vmax'] = diff_data_min,diff_data_max
         clev = None
         ax.set_title('diff',      fontsize=title_fontsize, loc='left')
         ax.set_title(var_str[v],  fontsize=title_fontsize, loc='right')
         # raster = diff.to_raster(ax=ax)
         raster = hapy.to_raster(diff, grid_ds_list[f-1], ax)
      else:
         ax.set_title(name_list[f],fontsize=title_fontsize, loc='left')
         ax.set_title(var_str[v],  fontsize=title_fontsize, loc='right')
         # raster = data_list[f].to_raster(ax=ax)
         raster = hapy.to_raster(data_list[f], grid_ds_list[f], ax)

      if clev is not None: img_kwargs['norm'] = mcolors.BoundaryNorm(clev, ncolors=256)
      img = ax.imshow(raster, extent=ax.get_xlim() + ax.get_ylim(), **img_kwargs)

      cbar = fig.colorbar(img, ax=ax, fraction=0.02, orientation='vertical')
      cbar.ax.tick_params(labelsize=lable_fontsize)

#---------------------------------------------------------------------------------------------------
# Finalize plot
# fig.savefig(fig_file, dpi=100, bbox_inches='tight')
# fig.savefig(fig_file, dpi=200, bbox_inches='tight')
fig.savefig(fig_file, dpi=1000, bbox_inches='tight')
plt.close(fig)

print(f'\n{fig_file}\n')

#---------------------------------------------------------------------------------------------------
