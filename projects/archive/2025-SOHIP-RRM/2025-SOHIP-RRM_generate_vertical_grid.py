import os, numpy as np, xarray as xr

p0 = 1000e2
ps = 1000e2

# flags for printing debugging/tuning info/lists
print_int_debug = False
print_mid_debug = False
print_L72_comparison = False
print_end_summary = False

nsmooth = 40

# Set up terminal colors
class tcolor: ENDC,RED,GREEN,CYAN = '\033[0m','\033[31m','\033[32m','\033[36m'
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def main():

    #---------------------------------------------------------------------------
    # Load default L72 for comparison
    #---------------------------------------------------------------------------
    # home = os.getenv('HOME')
    # ds72 = xr.open_dataset(f'{home}/E3SM/vert_grid_files/L72_E3SM.nc')
    # am72, bm72 = ds72.hyam.values, ds72.hybm.values
    # ai72, bi72 = ds72.hyai.values, ds72.hybi.values
    # mlev72 = compute_pressure_from_hybrid_coef(am72,bm72)
    # ilev72 = compute_pressure_from_hybrid_coef(ai72,bi72)
    #---------------------------------------------------------------------------
    # Read array of height levels
    #---------------------------------------------------------------------------
    # height_file = open(os.getenv('HOME')+'/E3SM/vert_grid_files/grd_L100','r')
    # zlev_file = []
    # for z in height_file.read().split(): zlev_file.append( float(z) )
    # zlev_file = np.array(zlev_file)

    #---------------------------------------------------------------------------
    # simple recipe using a list of height thicknesses
    #---------------------------------------------------------------------------

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SCREAM_L128_v2.1_c20230216.nc'
    # dk_list = [ 5, 5, 5, 5,  5,  5,  5, 55, 10, 10, 18]
    # dz_list = [50,55,60,80,100,125,150,200,250,500,1e3]

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SCREAM_L128_v2.2_c20230216.nc'
    # dk_list = [ 5, 5, 5, 5,  5,  5,  5,  5, 60, 10, 18]
    # dz_list = [50,55,60,80,100,125,150,200,250,500,1e3]

    #---------------------------------------------------------------------------

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SOHIP_L192_v1_c20250414.nc'
    # dk_list = [ 5, 5, 5, 5,  5,  5,  5,  5, 60, 10, 18, 18, 64-18]
    # dz_list = [50,55,60,80,100,125,150,200,250,500,500,500,   500]

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SOHIP_L192_v2_c20250414.nc'
    # dk_list = [ 5, 5, 5, 5,  5,  5,  5,  5, 60, 10, 18, 18, 64-18]
    # dz_list = [50,55,60,80,100,125,150,200,250,250,250,250,   250]

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SOHIP_L256_v3_c20250414.nc'
    # dk_list = [ 5, 5, 5, 5,  5,  5,  5,  5,216,]
    # dz_list = [50,55,60,80,100,125,150,200,220,]

    # ofile = os.getenv('HOME')+f'/E3SM/vert_grid_files/SOHIP_L256_v4_c20250930.nc'
    ofile = os.getenv('HOME')+f'/E3SM_grid_support/2025-SOHIP-RRM/SOHIP_L256_v4_c20250930.nc'
    dk_list = [ 5, 5, 5, 5,  5,  5,  5,  5,216,]
    dz_list = [20,40,60,80,100,125,150,200,220,]
    nsmooth = 20
    fix_lowest_spacing = True

    #---------------------------------------------------------------------------
    dz = []
    if 'dz_list' in locals() and 'zlev' not in locals():
        zlev = np.zeros(np.sum(dk_list)+1)
        kk = 1
        for d,dk in enumerate(dk_list):
            for k in range(dk):
                zlev[kk] = zlev[kk-1] + dz_list[d]
                dz.append(dz_list[d])
                # print(f'{kk}  {zlev[kk]:10.1}  {dz_list[d]}')
                kk += 1
    #---------------------------------------------------------------------------
    # # use this to check basic level stats
    # print()
    # print(f'num zlev: {sum(dk_list)}')
    # print()
    # print(f'max zlev: {max(zlev)}')
    # print()
    # exit()
    #---------------------------------------------------------------------------
    # get pressure from height using curve fit from climatology to 
    ilev = np.exp( -1*zlev/(6740.) ) * 1000
    ilev = ilev[::-1]
    num_ilev = len(ilev)
    num_mlev = num_ilev-1
    #---------------------------------------------------------------------------
    # Smoothing
    # dz_smoothed   = np.zeros(num_mlev)
    zlev_smoothed = np.copy(zlev)

    smth_k_beg,smth_k_end = (2,num_mlev) if fix_lowest_spacing else (1,num_mlev)

    for s in range(nsmooth):
        zs_tmp = np.copy(zlev_smoothed)
        # for k in range(smth_k_beg,smth_k_end):
        for k in range(smth_k_beg,smth_k_end):
            zlev_smoothed[k] = ( 0.25*zs_tmp[k-1] + 0.5*zs_tmp[k] + 0.25*zs_tmp[k+1] )
    
    # print(); print(zlev_smoothed[1])
    # # address kink at second mid-point from the surface
    # if fix_lowest_spacing:
    #     zlev = zlev_smoothed
    #     zmid = np.array([ ((zlev[k]+zlev[k+1])/2.) for k in range(num_mlev) ])
    #     zmid[1] = ( zmid[0] + zmid[2] )/2.
    #     zlev[1] = ( zmid[0] + zmid[1] )/2.
    #     zlev_smoothed = zlev
    #     # for k in range(smth_k_beg,smth_k_beg+1):
    #     #     # zlev_smoothed[k] = ( 0.25*zs_tmp[k-1] + 0.5*zs_tmp[k] + 0.25*zs_tmp[k+1] )
    #     #     zlev_smoothed[k] = ( 0.5*zs_tmp[k-1] + 0.5*zs_tmp[k+1] )
    #     #     # zlev_smoothed[k] = ( 0.25*zs_tmp[k-1] + 0.75*zs_tmp[k] )
    #     # zlev_smoothed[2] = ( 0.5*zs_tmp[k-1] + 0.5*zs_tmp[k+1] )
    # print(); print(zlev_smoothed[1])
    # # exit()

    # for k in range(0,num_mlev): dz_smoothed[k] = zlev_smoothed[k+1] - zlev_smoothed[k]

    zlev = zlev_smoothed
    ilev = np.exp( -1*zlev/(6740.) ) * 1000
    ilev = ilev[::-1]

    #---------------------------------------------------------------------------
    # Generate hybrid vertical grid

    [ai,bi] = compute_hybrid_coef_from_pressure(ilev*1e2)

    ### make sure bottom 3 levels are pure terrain following for L72
    if (num_ilev-1)==72:
        # for a,b in ai[-3:],bi[-3:]:
        for k in range(0,3):
            k2 = num_ilev-k-1
            if ai[k2]>0:
                bi[k2] = bi[k2] + ai[k2]
                ai[k2] = 0

    ### calculate mid-level hybrid coefficients
    am = np.empty(num_mlev)
    bm = np.empty(num_mlev)
    for k in range(num_mlev):
        am[k] = ( ai[k+1] + ai[k] )/2.
        bm[k] = ( bi[k+1] + bi[k] )/2.

    mlev = compute_pressure_from_hybrid_coef(am,bm)

    #---------------------------------------------------------------------------
    # Debug print statements

    ### print interface levels
    if print_int_debug:
        for k in range(num_ilev): 
            k2 = num_ilev-k-1
            dz = zlev[k2] - zlev[k2-1] if k2>0 else 0
            print(f'{k:03}  ({k2:02})    {ilev[k]:8.2f}    {zlev[k2]:8.1f}    {dz:8.1f}')


    ### print mid-level pressure and height
    if print_mid_debug:
        print(f'            pressure    height')
        for k in range(num_mlev): 
            k2 = num_mlev-k-1
            dz = zlev[k2+1] - zlev[k2] 
            zmid = ( zlev[k2+1] + zlev[k2] ) / 2.
            # dlev = mlev72[k] - mlev[k]
            # print(f'{k:3}  ({k2:3})    {mlev[k]:8.2f}    {am[k]:5.3f}  {bm[k]:5.3f}')
            print(f'{k:3}  ({k2:3})    {mlev[k]:8.2f}    {zmid:8.1f}     {dz:5.0f}')
            # print(f'{k:02}  ({k2:02})    {mlev[k]:8.2f}    {zmid:8.1f}    ')
        print()
    
    if print_int_debug or print_mid_debug:
        exit('Exiting before writing')

    #---------------------------------------------------------------------------
    # compare with E3SM's L72
    #---------------------------------------------------------------------------
    # for k in range(num_mlev):
    #     k2 = num_mlev-k-1
    #     dz = zlev[k2+1] - zlev[k2] ; dlev = mlev72[k] - mlev[k]
    #     # print(f'{k:3}  ({k2:3})   {dz:8.1f}    {mlev[k]:8.2f}      {lev72[k]:8.2f}    {dlev:8.2f}')
    #     print(f'{k:3}  ({k2:3})     {am[k]:6.5f}  {am72[k]:6.5f}      {bm[k]:6.5f}  {bm72[k]:6.5f}')
    # print()
    if print_L72_comparison:
        for k in range(num_ilev): 
        # for k in range(20):
            k2 = num_ilev-k-1
            if k2<num_ilev-1:
                dz = zlev[k2+1] - zlev[k2] 
            else:
                dz = 0
            # dlev = ilev72[k] - ilev[k]
            # print(f'{k:3}  ({k2:3})   {dz:8.1f}    {ilev[k]:8.2f}      {ilev72[k]:8.2f}    {dlev:8.2f}')
            if k<num_ilev-1:
                dlev1 = ilev[k+1] - ilev[k]
                dlev2 = ilev72[k+1] - ilev72[k]
            else:
                dlev1,dlev2 = 0,0
            print(f'{k:3}      {ilev[k]:6.1f}  ({dlev1:4.1f})       {ilev72[k]:6.1f}  ({dlev2:4.1f})')
            # msg = f'{k:3}  ({k2:3})'
            # msg += f'         {ilev[k]:8.2f}  {ilev72[k]:8.2f}'
            # msg += f'         {ai[k]  :6.5f}  {ai72[k]  :6.5f}'
            # msg += f'         {bi[k]  :6.5f}  {bi72[k]  :6.5f}'
            # print(msg)
        # exit()
    #---------------------------------------------------------------------------
    # print mid and interface levels
    if print_end_summary:
        for k in range(num_mlev):
            k2 = num_mlev-k-1
            msg1 = f'{k:3}  ({k2:3})'
            msg2 = ' '*len(msg1)
            if k==0:
                ki = 0
                msg2 = msg2 +' '*4+' '*7+f'{ilev[ki]:8.2f}          {ai[ki]:8.5f}        {bi[ki]:8.5f}'
                msg2 = tcolor.GREEN + msg2 + tcolor.ENDC
                print(msg2)
            km = k
            ki = k+1
            msg1 = f'{k:3}  ({k2:3})'
            msg2 = ' '*len(msg1)
            msg1 = msg1 +' '*4+      f'{mlev[km]:8.2f}          {am[km]:8.5f}        {bm[km]:8.5f}'
            msg2 = msg2 +' '*4+' '*7+f'{ilev[ki]:8.2f}          {ai[ki]:8.5f}        {bi[ki]:8.5f}'
            msg2 = tcolor.GREEN + msg2 + tcolor.ENDC
            print(msg1)
            print(msg2)
    # exit()

    #---------------------------------------------------------------------------
    # Write to file

    mlev = xr.DataArray(mlev)
    ilev = xr.DataArray(ilev)

    ds = xr.Dataset()
    ds['lev']  = ('lev', mlev.data)
    ds['hyam'] = ('lev', am)
    ds['hybm'] = ('lev', bm)
    ds['ilev'] = ('ilev',ilev.data)
    ds['hyai'] = ('ilev',ai)
    ds['hybi'] = ('ilev',bi)
    ds['P0'] = p0

    ds['lev'].attrs['units']      = 'level'
    ds['lev'].attrs['positive']   = 'down'
    ds['ilev'].attrs['units']     = 'level'
    ds['ilev'].attrs['positive']  = 'down'
    ds['P0'].attrs['units']       = 'Pa'
    ds['P0'].attrs['long_name']   = 'reference pressure'
    ds['hyam'].attrs['long_name'] = 'hybrid A coefficient at layer midpoints'
    ds['hybm'].attrs['long_name'] = 'hybrid B coefficient at layer midpoints'
    ds['hyai'].attrs['long_name'] = 'hybrid A coefficient at layer interfaces'
    ds['hybi'].attrs['long_name'] = 'hybrid B coefficient at layer interfaces'

    ds.attrs['nsmooth'] = nsmooth
    
    print(f'\n{ofile}\n')

    ds.to_netcdf(ofile)

    print(f'\n{ofile}\n')

#-------------------------------------------------------------------------------
# print some other sueful info
#-------------------------------------------------------------------------------
    print()
    print(f'  zmid max: { ( (zlev[num_ilev-1]+zlev[num_ilev-2])/2. ) }')
    print(f'  pmid min: {np.min(mlev.values)}')
    print(f'  zint max: {np.max(zlev)}')
    print(f'  pint min: {np.min(ilev.values)}')
    print()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def compute_hybrid_coef_from_pressure(plev):
    """ 
    compute hybrid coefficients from pressure levels 
    """
    pm = 18230.50  # level to switch from sigma to pressure? [pa]
    pt = 100.0     # top pressure? [pa]

    psize = len(plev)
    a = np.empty(psize)
    b = np.empty(psize)

    for i in range(psize) :
        # compute sigma
        if plev[i]<pm:
            sigma = ( plev[i] - pm ) / ( pm - pt )
        else:
            sigma = ( plev[i] - pm ) / ( ps - pm )
        # compute delta
        delta = 0.0 if sigma<0.0 else 1.0
        # compute A and B, pressure coefficients
        a[i] = ( pm*(1-sigma)*delta + (1-delta)*(pm*(1+sigma)-sigma*pt) ) / p0
        b[i] = np.abs( sigma*delta )

    return [a,b]
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def compute_pressure_from_hybrid_coef(a,b):
    """
    compute pressure from hybrid coefficients
    """
    lev = ( a*p0 + b*ps ) / 100.0
    return lev
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------