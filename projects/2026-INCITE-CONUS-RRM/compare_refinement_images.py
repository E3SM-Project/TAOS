import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

#-------------------------------------------------------------------------------
# Compare PyNGL and Matplotlib versions of refinement image
#-------------------------------------------------------------------------------

file_ngl = '2026-INCITE-CONUS-RRM_refinement_image_ngl.png'
file_mpl = '2026-INCITE-CONUS-RRM_refinement_image_mpl.png'

# Load images
img_ngl = np.array(Image.open(file_ngl))
img_mpl = np.array(Image.open(file_mpl))

print(f'\nImage dimensions:')
print(f'  PyNGL: {img_ngl.shape}')
print(f'  MPL:   {img_mpl.shape}')

# Check if images are the same size
if img_ngl.shape != img_mpl.shape:
    print(f'\nWARNING: Images have different dimensions!')
    print(f'  Resizing matplotlib image to match PyNGL dimensions for comparison')
    img_mpl_resized = np.array(Image.fromarray(img_mpl).resize(
        (img_ngl.shape[1], img_ngl.shape[0]), 
        Image.Resampling.LANCZOS))
else:
    img_mpl_resized = img_mpl

# Convert to grayscale if needed (for simpler comparison)
if len(img_ngl.shape) == 3:
    img_ngl_gray = np.mean(img_ngl[:,:,:3], axis=2)
else:
    img_ngl_gray = img_ngl

if len(img_mpl_resized.shape) == 3:
    img_mpl_gray = np.mean(img_mpl_resized[:,:,:3], axis=2)
else:
    img_mpl_gray = img_mpl_resized

# Calculate difference
diff = np.abs(img_ngl_gray - img_mpl_gray)
max_diff = np.max(diff)
mean_diff = np.mean(diff)
pct_different = np.sum(diff > 10) / diff.size * 100

print(f'\nPixel difference statistics:')
print(f'  Max difference:  {max_diff:.2f}')
print(f'  Mean difference: {mean_diff:.2f}')
print(f'  % pixels with diff > 10: {pct_different:.2f}%')

# Create comparison figure
fig, axes = plt.subplots(2, 2, figsize=(12, 12))

axes[0, 0].imshow(img_ngl_gray, cmap='gray')
axes[0, 0].set_title('PyNGL Version')
axes[0, 0].axis('off')

axes[0, 1].imshow(img_mpl_gray, cmap='gray')
axes[0, 1].set_title('Matplotlib Version')
axes[0, 1].axis('off')

axes[1, 0].imshow(diff, cmap='hot')
axes[1, 0].set_title(f'Absolute Difference (max={max_diff:.1f})')
axes[1, 0].axis('off')

# Thresholded difference
diff_thresh = diff > 10
axes[1, 1].imshow(diff_thresh, cmap='gray')
axes[1, 1].set_title(f'Difference > 10 ({pct_different:.2f}% of pixels)')
axes[1, 1].axis('off')

fig_file = 'comparison_ngl_vs_mpl.png'

plt.tight_layout()
plt.savefig(fig_file, dpi=150, bbox_inches='tight')
print(f'\nComparison figure saved to: comparison_ngl_vs_mpl.png')

# plt.show()
plt.close()

print()
print(f'  {fig_file}')
print()

#-------------------------------------------------------------------------------