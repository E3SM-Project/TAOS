import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.patches import Rectangle
import cartopy.io.shapereader as shpreader

#-------------------------------------------------------------------------------
# Create the PNG file necessary for Squadgen - refinement area should be white
#-------------------------------------------------------------------------------
class clr:
    END, RED, GREEN, MAGENTA, CYAN = '\033[0m', '\033[31m', '\033[32m', '\033[35m', '\033[36m'

def run_cmd(cmd):
    print('\n' + clr.GREEN + cmd + clr.END)
    os.system(cmd)
    return

#-------------------------------------------------------------------------------

fig_file = '2026-INCITE-CONUS-RRM_refinement_image_mpl.png'

#-------------------------------------------------------------------------------
# Setup figure with high resolution
npix = 4096
dpi = 100
fig_size = npix / dpi

fig = plt.figure(figsize=(fig_size, fig_size), dpi=dpi, facecolor='white')
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

# Set background colors
ax.set_facecolor('black')
fig.patch.set_facecolor('white')

# Set the map boundary (spines) to black
ax.spines['geo'].set_edgecolor('black')
ax.spines['geo'].set_linewidth(1)

# Add ocean and land
ax.add_feature(cfeature.OCEAN, facecolor='black', zorder=0)
ax.add_feature(cfeature.LAND, facecolor='black', zorder=1)

# Add only CONUS states in white (these include the Great Lakes)
shapename = 'admin_1_states_provinces_lakes'
states_shp = shpreader.natural_earth(resolution='10m', category='cultural', name=shapename)

# States to exclude (Alaska, Hawaii, and territories)
exclude_states = ['Alaska', 'Hawaii']

for state in shpreader.Reader(states_shp).records():
    # Filter for only United States, excluding Alaska and Hawaii
    if (state.attributes.get('admin') == 'United States of America' and 
        state.attributes.get('name') not in exclude_states):
        ax.add_geometries([state.geometry], ccrs.PlateCarree(),
                         facecolor='white', edgecolor='none', zorder=2)

# Add Great Lakes in white
lakes_shp = shpreader.natural_earth(resolution='10m', category='physical', name='lakes')

great_lakes = ['Lake Superior', 'Lake Michigan', 'Lake Huron', 'Lake Erie', 'Lake Ontario']

for lake in shpreader.Reader(lakes_shp).records():
    if lake.attributes.get('name') in great_lakes:
        ax.add_geometries([lake.geometry], ccrs.PlateCarree(),
                         facecolor='white', edgecolor='none', zorder=2)

# Overlay black box to hide weird purple region in Flores sea
black_box = Rectangle(
    (100, -15),  # (x, y) lower left corner
    35,          # width
    15,          # height
    facecolor='black',
    edgecolor='none',
    transform=ccrs.PlateCarree(),
    zorder=3
)
ax.add_patch(black_box)

# Set global extent
ax.set_global()

# Remove all ticks and labels
ax.set_xticks([])
ax.set_yticks([])

# Remove margins and save with NO tight bbox to preserve white border
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Save the figure WITHOUT bbox_inches='tight' to keep the white border
plt.savefig(fig_file, 
            dpi=dpi, 
            pad_inches=0,
            facecolor='white',
            edgecolor='none')
plt.close()

#-------------------------------------------------------------------------------
### Post-process with ImageMagick
if os.path.isfile(fig_file):
    # Crop white space from png file
    run_cmd(f'magick convert -trim {fig_file} {fig_file}')
    
    # Apply black border with shave to keep dimensions unchanged
    run_cmd(f'magick convert {fig_file} -shave 5x5 -bordercolor "black" -border 5x5 {fig_file}')
    
    # Expand refined region to create coastal buffer
    run_cmd(f'magick convert {fig_file} -blur 0x10 -fuzz 90% -fill white -opaque white {fig_file}')
else:
    raise FileNotFoundError(f'\n{fig_file} does not exist?!\n')

print()
print(f'  {fig_file}')
print()

#-------------------------------------------------------------------------------