import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

np.random.seed(42)
methods = ['Input', 'Ours', 'Method A', 'Method B', 'Ground Truth']
n_samples = 2

# Simulated metrics (PSNR/SSIM)
psnr_scores = {
    'Ours': [32.5, 31.8], 'Method A': [28.3, 27.9], 'Method B': [26.1, 25.5]
}
ssim_scores = {
    'Ours': [0.95, 0.94], 'Method A': [0.88, 0.87], 'Method B': [0.82, 0.81]
}

fig, axes = plt.subplots(n_samples * 2, len(methods), figsize=(13, 8))  # 2 rows per sample: image + error

for i in range(n_samples):
    for j, method in enumerate(methods):
        # Image row
        ax = axes[i * 2, j]
        img = np.random.rand(64, 64, 3) * 0.3
        if method == 'Ours':
            img += 0.45
        elif method == 'Ground Truth':
            img += 0.5
        elif method == 'Input':
            img += 0.15
        else:
            img += 0.3
        img = np.clip(img, 0, 1)
        ax.imshow(img)
        ax.axis('off')

        # Red box highlight on key region
        if method not in ['Input', 'Ground Truth']:
            rect = Rectangle((10, 10), 20, 20, linewidth=1.5, edgecolor=COLORS['down'],
                              facecolor='none', linestyle='-')
            ax.add_patch(rect)

        # Title with scores
        if i == 0:
            title = method
            if method in psnr_scores:
                title += f'\n{psnr_scores[method][i]:.1f}/{ssim_scores[method][i]:.2f}'
            fontw = 'bold' if method == 'Ours' else 'normal'
            color = PALETTE[0] if method == 'Ours' else COLORS['text']
            ax.set_title(title, fontsize=8.5, fontweight=fontw, color=color)

        # Error map row
        ax_err = axes[i * 2 + 1, j]
        if method in ['Input', 'Ground Truth']:
            ax_err.axis('off')
            if method == 'Ground Truth' and i == 0:
                ax_err.text(0.5, 0.5, 'Error Map\n(|pred - GT|)', ha='center', va='center',
                            fontsize=7, color=COLORS['ref_line'], transform=ax_err.transAxes)
        else:
            error = np.random.rand(64, 64) * (0.1 if method == 'Ours' else 0.3 if method == 'Method A' else 0.5)
            ax_err.imshow(error, cmap=palette_cmap('sequential'), vmin=0, vmax=0.5)
            ax_err.axis('off')
            # PSNR/SSIM annotation
            if method in psnr_scores:
                ax_err.text(0.5, -0.05, f'PSNR: {psnr_scores[method][i]:.1f} | SSIM: {ssim_scores[method][i]:.2f}',
                            ha='center', va='top', fontsize=6.5, color=COLORS['text'],
                            transform=ax_err.transAxes)

fig.tight_layout(pad=0.5, h_pad=0.3)
save_fig(fig, 'figures/fig_qualitative.pdf')
