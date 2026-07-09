import os, ngl, numpy as np, xarray as xr
#-------------------------------------------------------------------------------
# Create the PNG file necessary for Squadgen - refinment area should be white
# export PYNGL_RANGS=~/.conda/envs/pyn_env/lib/ncarg/database/rangs
#-------------------------------------------------------------------------------
class clr:END,RED,GREEN,MAGENTA,CYAN = '\033[0m','\033[31m','\033[32m','\033[35m','\033[36m'
def run_cmd(cmd): print('\n'+clr.GREEN+cmd+clr.END) ; os.system(cmd); return
#-------------------------------------------------------------------------------

fig_file,fig_type = f'2026-INCITE-CONUS-RRM_refinement_image_ngl','png'

#-------------------------------------------------------------------------------
wkres = ngl.Resources()
npix = 4096; wkres.wkWidth,wkres.wkHeight=npix,npix
wkres.wkForegroundColor = 'black'#np.array([1.,1.,1.])*-1
wkres.wkBackgroundColor = 'white'#np.array([1.,1.,1.])*-1

wks = ngl.open_wks(fig_type,fig_file,wkres)

res = ngl.Resources()
res.nglDraw               = False
res.nglFrame              = False
res.tmXTOn                = False
res.tmXBOn                = False
res.tmYLOn                = False
res.tmYROn                = False

res.mpGridAndLimbOn       = False
res.mpPerimOn             = False
res.mpOutlineOn           = False

res.mpPerimOn             = True
res.mpPerimLineColor      = 'black'

# res.mpDataBaseVersion = 'MediumRes' # LowRes / MediumRes / HighRes # doesn't work when filling along political boundaries

# res.mpOutlineOn           = True
# res.mpOutlineBoundarySets = 'Geophysical'
# res.mpGeophysicalLineColor  = 'white'

# res.mpOutlineBoundarySets = 'NoBoundaries'
# res.lbLabelBarOn          = False
# res.cnFillPalette         = "gsdtol"
# res.cnFillPalette         = clr
# res.tfPolyDrawOrder = 'PreDraw'

res.mpFillOn              = True
res.mpInlandWaterFillColor= 'black'#'Background'
res.mpOceanFillColor      = 'black'#'Background'
res.mpLandFillColor       = 'black'#'Background'

res.mpOutlineBoundarySets = 'National'
res.mpFillAreaSpecifiers  = ['AllUSStates']
res.mpSpecifiedFillColors = ['white'] # white / green


#-------------------------------------------------------------------------------

plot = ngl.map(wks,res)
# plot = ngl.contour_map(wks,data,res)

# res.mpSpecifiedFillColors = ['green'] # white / green
# ngl.overlay(plot, ngl.map(wks,res))

# overlay black box to hide weird puple region in Flores sea
pgres = ngl.Resources()
pgres.nglDraw,pgres.nglFrame = False,False
pgres.gsFillColor = 'black'
ulx,uly = 100,0
lrx,lry = 135,-15
bx = [ulx,ulx,lrx,lrx,ulx]
by = [uly,lry,lry,uly,uly]
pdum = ngl.add_polygon(wks,plot,bx,by,pgres)

# ### use pre-draw polygon to fill in white areas near poles
# gsres             = ngl.Resources()
# gsres.gsFillColor = 'black'
# gsres.gsEdgesOn   = False
# py = [ -89.9,  89.9, 89.9,-89.9, -89.9]
# px = [ 360. , 360. ,  0. ,  0. , 360. ]
# ngl.polygon(wks, plot, px, py, gsres)


ngl.draw(plot)
ngl.frame(wks)
ngl.end()


#-------------------------------------------------------------------------------
### crop white space from png file
if os.path.isfile(f'{fig_file}.{fig_type}') :
  run_cmd(f'magick convert -trim {fig_file}.{fig_type} {fig_file}.{fig_type}')
  # additionall apply a black border along with "shave" to keep dimensions unchanged
  run_cmd(f'magick convert {fig_file}.{fig_type} -shave 5x5 -bordercolor "black" -border 5x5 {fig_file}.{fig_type}')
  # run_cmd(f'magick convert {fig_file}.{fig_type} -blur 0x20 {fig_file}.{fig_type}')

  # expand refined region to create coastal buffer
  run_cmd(f'magick convert {fig_file}.{fig_type} -blur 0x10 -fuzz 90% -fill white -opaque white  {fig_file}.{fig_type}')

  # # expand white region using mask
  # run_cmd(f'magick {fig_file}.{fig_type} -fuzz 10% -fill white -opaque white -fill black +opaque white {fig_file}.mask1.{fig_type}')
  # # run_cmd(f'magick {fig_file}.mask1.{fig_type} -morphology Dilate Disk:RADIUS -scale 200% {fig_file}.mask2.{fig_type}')
  # # run_cmd(f'magick convert {fig_file}.mask1.{fig_type} -gaussian-blur 0x20 {fig_file}.mask2.{fig_type}')
  # run_cmd(f'magick convert {fig_file}.mask1.{fig_type} -blur 0x10 -fuzz 90% -fill white -opaque white  {fig_file}.mask2.{fig_type}')
  # # run_cmd(f'magick {fig_file}.mask1.{fig_type} -blur 0x20 \\( +clone -fuzz 20% -fill green -opaque white \\) -compose over -composite  {fig_file}.mask2.{fig_type}')
  # # run_cmd(f'magick convert {fig_file}.mask1.{fig_type} -fill green -mask {fig_file}.mask2.{fig_type} -opaque white +mask  {fig_file}.mask1.{fig_type}')
  # run_cmd(f'magick {fig_file}.{fig_type} {fig_file}.mask2.{fig_type} -compose Plus -composite {fig_file}.{fig_type}')
else:
  raise FileNotFoundError(f'\n{fig_file}.{fig_type} does not exist?!\n')

print(); print(f'  {fig_file}.{fig_type}'); print()

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
   
