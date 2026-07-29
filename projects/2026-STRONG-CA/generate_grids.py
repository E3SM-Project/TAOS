#!/usr/bin/env python3
"""
generate_grids.py — Create the exodus and pg2 SCRIP files for this project.

Replaces the hand-run SQuadGen / TempestRemap commands documented in the
README. Grids are declared below with add_grid() and processed in a loop:

    RRM grid  : SQuadGen (refinement image) -> GenerateVolumetricMesh -> ConvertMeshToSCRIP
    uniform   : GenerateCSMesh             -> GenerateVolumetricMesh -> ConvertMeshToSCRIP

The refinement image must be created first with generate_refinement_image.py.
Paths (grid_root, refinement image location) come from project.yaml, so
nothing here needs editing when switching machines.

Usage
-----
    python generate_grids.py
"""
import os
import pathlib

from taos import taos_config
from taos.util import clr, ensure_dir, print_line, run_cmd, timer

#-------------------------------------------------------------------------------
# load config — grid_root and the project dir (where the refinement images live)
# are derived from paths.grid_data_root + project.name in project.yaml

proj_dir  = pathlib.Path(__file__).parent
cfg       = taos_config(proj_dir / 'project.yaml')

grid_root      = cfg['derived.grid_root']
ref_image_root = cfg['derived.proj_root']
unified_bin    = cfg.get('paths.unified_bin', '')

ensure_dir(grid_root)

def tool(name):
    """Return the path to a SQuadGen/TempestRemap executable.

    Prefers the e3sm-unified bin from project settings, falling back to the
    bare name (i.e. whatever is on PATH) when unified_bin is unset or does
    not provide the tool — e.g. a locally built SQuadGen.
    """
    exe = f'{unified_bin}/{name}'
    return exe if unified_bin and os.path.exists(exe) else name

#-------------------------------------------------------------------------------
# refinement images produced by generate_refinement_image.py

REF_IMAGE_V1 = f'{ref_image_root}/2026-STRONG-CA-RRM_refinement_image_v1.png'
REF_IMAGE_V2 = f'{ref_image_root}/2026-STRONG-CA-RRM_refinement_image_v2.png'

# SQuadGen options shared by all refined grids
REFINE_TYPE = 'LOWCONN'
SMOOTH_TYPE = 'SPRING'
SMOOTH_DIST = 10
SMOOTH_ITER = 20
LON_REF     = 240
LAT_REF     = 38

#-------------------------------------------------------------------------------
# grid list — comment out entries to skip them

grid_list = []
def add_grid(name, **kwargs):
    """Add a grid to the list to be generated.

    Refined (RRM) grid:  add_grid(name, base_res=..., refine_lvl=..., ref_image=...)
    Uniform grid:        add_grid(name, ne=...)
    """
    grid_list.append({'name': name, **kwargs})

add_grid('STRONG-CA-32x5-v1',  base_res=32,  refine_lvl=5, ref_image=REF_IMAGE_V1) # ne32 => ne1024
add_grid('STRONG-CA-32x5-v2',  base_res=32,  refine_lvl=5, ref_image=REF_IMAGE_V2) # ne32 => ne1024

add_grid('STRONG-CA-128x3-v1', base_res=128, refine_lvl=3, ref_image=REF_IMAGE_V1) # ne128 => ne1024
add_grid('STRONG-CA-128x3-v2', base_res=128, refine_lvl=3, ref_image=REF_IMAGE_V2) # ne128 => ne1024

# uniform (i.e. unrefined) grids for comparison
# add_grid('ne128', ne=128)

#-------------------------------------------------------------------------------

def generate_grid(opts):
    """Create the exodus, pg2 exodus, and pg2 SCRIP files for one grid."""
    grid_name = opts['name']

    # TempestRemap chokes on long absolute paths, so all commands run with
    # cwd=grid_root and refer to the mesh files by name (see taos.grid).
    exodus_file    = f'{grid_name}.g'
    pg2_file       = f'{grid_name}pg2.g'
    pg2_scrip_file = f'{grid_name}pg2_scrip.nc'

    print_line()
    print(f'\n  {clr.CYAN}{grid_name}{clr.END}\n')

    #---------------------------------------------------------------------------
    # base exodus mesh — SQuadGen for refined grids, GenerateCSMesh for uniform

    if 'ne' in opts:
        cmd = (f'{tool("GenerateCSMesh")} --alt'
               f' --res {opts["ne"]} --file {exodus_file}')
    else:
        ref_image = opts['ref_image']
        if not os.path.exists(ref_image):
            raise FileNotFoundError(
                f'Refinement image not found: {ref_image}\n'
                f'Run generate_refinement_image.py first.')
        cmd = (f'{tool("SQuadGen")}'
               f' --refine_file {ref_image}'
               f' --resolution {opts["base_res"]}'
               f' --refine_level {opts["refine_lvl"]}'
               f' --refine_type {REFINE_TYPE}'
               f' --smooth_type {SMOOTH_TYPE}'
               f' --smooth_dist {SMOOTH_DIST}'
               f' --smooth_iter {SMOOTH_ITER}'
               f' --lon_ref {LON_REF} --lat_ref {LAT_REF}'
               f' --output {exodus_file}')

    with timer.time(f'{grid_name}: exodus mesh'):
        run_cmd(cmd, cwd=grid_root)

    #---------------------------------------------------------------------------
    # pg2 exodus mesh

    cmd = (f'{tool("GenerateVolumetricMesh")}'
           f' --in {exodus_file} --out {pg2_file} --np 2 --uniform')
    with timer.time(f'{grid_name}: GenerateVolumetricMesh pg2'):
        run_cmd(cmd, cwd=grid_root)

    #---------------------------------------------------------------------------
    # pg2 SCRIP file

    cmd = (f'{tool("ConvertMeshToSCRIP")}'
           f' --in {pg2_file} --out {pg2_scrip_file}')
    with timer.time(f'{grid_name}: ConvertMeshToSCRIP pg2'):
        run_cmd(cmd, cwd=grid_root)

    #---------------------------------------------------------------------------

    for f in [exodus_file, pg2_file, pg2_scrip_file]:
        if not os.path.exists(f'{grid_root}/{f}'):
            raise RuntimeError(f'grid file creation FAILED: {grid_root}/{f}')

    run_cmd(f'ls -l {grid_root}/{grid_name}*')

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    print()
    print(f'  grid_root : {grid_root}')
    timer.start_total()
    for opts in grid_list:
        generate_grid(opts)
    print_line()
    timer.summary()

#-------------------------------------------------------------------------------
