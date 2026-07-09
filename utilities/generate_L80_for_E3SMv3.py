import os, numpy as np, xarray as xr
#-------------------------------------------------------------------------------
'''
This script reproduces the L80 vertical grid file used in the atmospheric
component of E3SMv3. The grid is constructucted by modifying the L72 grid
used in previous versions of E3SM. There is no documented method or script
to reproduce the L72 grid, but it can be extracted from various E3SM files,
such as history output or initial condition data.
'''
#-------------------------------------------------------------------------------
p0 = 1000e2
ps = 1000e2

# flags for printing debugging/tuning info/lists
print_int_debug         = True
print_mid_debug         = True
print_L72_comparison    = True

nsmooth         = 40    # number of smoothing iterations
smooth_limit_z  = 10    # lower altitude limit for smoothing
refine_limit_z1 = 10    # lower altitude limit for refinement
refine_limit_z2 = 45    # upper altitude limit for refinement 
refine_min_dz   = 550   # minimum spacing for refinement


L72_vert_file = os.getenv('HOME')+f'/E3SM/vert_grid_files/L72_E3SM.nc'

output_file = 'L80_for_E3SMv3.nc'

#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
def main():
    #---------------------------------------------------------------------------
    # Load E3SM default L72 and convert to approx height 
    ds72 = xr.open_dataset(L72_vert_file)
    am72, bm72 = ds72.hyam.values, ds72.hybm.values
    ai72, bi72 = ds72.hyai.values, ds72.hybi.values
    mlev72 = compute_pressure_from_hybrid_coef(am72,bm72)
    ilev72 = compute_pressure_from_hybrid_coef(ai72,bi72)

    # rough estimate of height from pressure
    zlev = np.log(ilev72[::-1]/1e3) * -6740.
    
    # define lower limit for smoothing
    smooth_limit_k = (np.abs(zlev - smooth_limit_z*1e3)).argmin()

    dz = []
    for k in range(len(zlev)-1): dz.append(zlev[k+1]-zlev[k])
    
    #---------------------------------------------------------------------------
    # refine the grid by adding levels within a specified range
    zlev = refine(zlev,dz)

    # apply smoothing
    zlev = smooth(zlev,smooth_limit_k)
    #---------------------------------------------------------------------------
    # use curve fit from climatology to get pressure from height
    ilev = np.exp( -1*zlev/(6740.) ) * 1000
    ilev = ilev[::-1]
    num_ilev = len(ilev)
    num_mlev = num_ilev-1

    #---------------------------------------------------------------------------
    # Generate hybrid coefficients
    [ai,bi] = compute_hybrid_coef_from_pressure(ilev*1e2)

    # make sure bottom 3 levels are pure terrain following for L72
    if (num_ilev-1)==72:
        # for a,b in ai[-3:],bi[-3:]:
        for k in range(0,3):
            k2 = num_ilev-k-1
            if ai[k2]>0:
                bi[k2] = bi[k2] + ai[k2]
                ai[k2] = 0

    # calculate mid-level hybrid coefficients
    am = np.empty(num_mlev)
    bm = np.empty(num_mlev)
    for k in range(num_mlev):
        am[k] = ( ai[k+1] + ai[k] )/2.
        bm[k] = ( bi[k+1] + bi[k] )/2.

    mlev = compute_pressure_from_hybrid_coef(am,bm)

    #---------------------------------------------------------------------------
    # print interface levels for debugging
    if print_int_debug:
        for k in range(num_ilev): 
            k2 = num_ilev-k-1
            print(f'{k:02}  ({k2:02})    {ilev[k]:8.2f}    {zlev[k2]:8.1f}')

    #---------------------------------------------------------------------------
    # print mid-level pressure and height for debugging
    if print_mid_debug:
        print(f'            pressure    height')
        for k in range(num_mlev): 
            k2 = num_mlev-k-1
            dz = zlev[k2+1] - zlev[k2] 
            zmid = ( zlev[k2+1] + zlev[k2] ) / 2.
            print(f'{k:3}  ({k2:3})    {mlev[k]:8.2f}    {zmid:8.1f}     {dz:5.0f}')
        print()

    #---------------------------------------------------------------------------
    # exit without writing if in debug mode
    if print_int_debug or print_mid_debug: exit('Exiting before writing')

    #---------------------------------------------------------------------------
    # compare with L72 from EAMv2
    if print_L72_comparison:
        for k in range(num_ilev): 
            k2 = num_ilev-k-1
            if k2<num_ilev-1:
                dz = zlev[k2+1] - zlev[k2] 
            else:
                dz = 0
            if k<num_ilev-1:
                dlev1 = ilev[k+1] - ilev[k]
                dlev2 = ilev72[k+1] - ilev72[k]
            else:
                dlev1,dlev2 = 0,0
            print(f'{k:3}      {ilev[k]:6.1f}  ({dlev1:4.1f})       {ilev72[k]:6.1f}  ({dlev2:4.1f})')

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

    ds.to_netcdf(output_file)

    print(f'\n{output_file}\n')

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
def compute_pressure_from_hybrid_coef(a,b):
    """
    compute pressure from hybrid coefficients
    """
    lev = ( a*p0 + b*ps ) / 100.0
    return lev
#-------------------------------------------------------------------------------
# functions to help with refinement method
def is_monotonic(nz,dz):
    for k in range(nz-1):
        if dz[k+1]<dz[k] and np.absolute(dz[k+1]-dz[k])>1:
            return False
    return True
def print_levs(zlev_new,zlev_old,dz_new,dz_old,refine_limit_k1,refine_limit_k2):
    print()
    for k in range(refine_limit_k1-2,len(zlev)-1): 
        msg1 = f'{zlev_old[k+1]:>8.2f}'
        msg2 = f'{zlev_new[k+1]:>8.2f}'
        if k<len(zlev):
            msg1 = msg1+f'{dz_old[k]:>10.2f}'
            msg2 = msg2+f'{dz_new[k]:>10.2f}'
        else:
            msg1 = msg1+' '*10
            msg2 = msg2+' '*10
        msg = f'k: {k:3d}      {msg1}       {msg2}'
        if k==refine_limit_k1: msg = msg + '  <<<<<<<<<<'
        if k==refine_limit_k2: msg = msg + '  <<<<<<<<<<'
        print(msg)
#-------------------------------------------------------------------------------
def refine(zlev_in,dz_in):
    zlev = zlev_in
    dz = dz_in
    #---------------------------------------------------------------------------
    # only refine between specified limits
    refine_limit_k1 = (np.abs(zlev - refine_limit_z1*1e3)).argmin()
    refine_limit_k2 = (np.abs(zlev - refine_limit_z2*1e3)).argmin()
    # first pass - reset levels to min spacing
    for k in range(refine_limit_k1,refine_limit_k2): 
        # only refine if spacing is sufficiently large
        if dz[k] > refine_min_dz:
            # put extra spacing into k+1 level to preserve grid height
            tmp_dz = dz[k]
            dz[k] = refine_min_dz
            dz[k+1] = dz[k+1] + (tmp_dz-refine_min_dz)
    #---------------------------------------------------------------------------
    # second pass - bisect levels until monotonic
    cnt = 0
    is_mono = is_monotonic(len(dz),dz)
    while not is_mono:
        # find level that violates monotonicity and bisect it
        for k in range(refine_limit_k1,refine_limit_k2+1): 
            if dz[k+1]<dz[k] and np.absolute(dz[k+1]-dz[k])>1:
                dz_tmp = dz[k]/2
                dz[k] = dz_tmp
                dz.insert(k,dz_tmp)
        # recalculate zlev
        zlev = np.zeros(len(dz)+1)
        for k in range(1,len(dz)+1): zlev[k] = zlev[k-1]+dz[k-1]
        # redefine loop limits
        refine_limit_k1 = (np.abs(zlev - refine_limit_z1*1e3)).argmin()
        refine_limit_k2 = (np.abs(zlev - refine_limit_z2*1e3)).argmin()
        # recheck monotonicity
        is_mono = is_monotonic(len(dz),dz)
        cnt += 1
        print(f'  refine bisection count: {cnt}')
        if cnt>100: exit(f'exiting refinement due to iteration limit!  (cnt={cnt})')
    #---------------------------------------------------------------------------
    # for L72 refinement make sure we have a round number
    if len(dz)==79:
        # find largest jump in dz and bisect it
        dzdz = np.zeros_like(dz)
        for k in range(1,len(dz)): dzdz[k] = np.absolute( dz[k] - dz[k-1])
        max_idx = np.where(dzdz == np.amax(dzdz))[0][0]
        print(f'max_idx: {max_idx}')
        dz_tmp = dz[max_idx]/2
        dz[max_idx] = dz_tmp
        dz.insert(max_idx,dz_tmp)
        # recalculate zlev
        zlev = np.zeros(len(dz)+1)
        for k in range(1,len(dz)+1): zlev[k] = zlev[k-1]+dz[k-1]
    #---------------------------------------------------------------------------
    return zlev
#-------------------------------------------------------------------------------
def smooth(zlev_in,smooth_limit_k):
    zlev = zlev_in
    #---------------------------------------------------------------------------
    # Apply smoothing
    ilev = np.exp( -1*zlev/(6740.) ) * 1000
    ilev = ilev[::-1]
    num_ilev = len(ilev)
    num_mlev = num_ilev-1
    dz_smoothed   = np.zeros(num_mlev)
    zlev_smoothed = np.copy(zlev)
    for s in range(nsmooth):
        zs_tmp = np.copy(zlev_smoothed)
        for k in range(smooth_limit_k,num_mlev): # only smooth upper levels
            zlev_smoothed[k] = ( 0.25*zs_tmp[k-1] + 0.5*zs_tmp[k] + 0.25*zs_tmp[k+1] )
    
    for k in range(0,num_mlev): dz_smoothed[k] = zlev_smoothed[k+1] - zlev_smoothed[k]

    zlev = zlev_smoothed
    #---------------------------------------------------------------------------
    return zlev
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------