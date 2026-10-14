import numpy as np; from _utils.palette_maps import palette_cmap, palette_stops, contrast_text
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyArrowPatch
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten

setup_style()
np.random.seed(42)

# === 模拟数据：输入图 / 注意力图 / 输出图 ===
H, W = 80, 80
y, x = np.mgrid[0:H, 0:W]
input_img = np.exp(-((x - 28)**2 + (y - 32)**2) / 250) + \
            0.6 * np.exp(-((x - 52)**2 + (y - 48)**2) / 200) + \
            np.random.normal(0, 0.04, (H, W))
attention = np.exp(-((x - 40)**2 + (y - 40)**2) / 500) * (input_img > 0.2)
output_img = input_img * attention * 1.6

# === 1 行 3 列 + 上方薄色条 ===
fig = plt.figure(figsize=(9, 4))
gs = GridSpec(2, 3, height_ratios=[0.5, 6], hspace=0.05, wspace=0.12)

titles = ['(a) 输入', '(b) 注意力图', '(c) 重构输出']
images = [input_img, attention, output_img]
v = max(np.max(im) for im in images)

axes_img = []
for col in range(3):
    ax = fig.add_subplot(gs[1, col])
    im = ax.imshow(images[col], cmap=palette_cmap('sequential'), vmin=0, vmax=v,
                   interpolation='bilinear')
    ax.set_title(titles[col], fontsize=11, fontweight='bold',
                 color=COLORS['text'], pad=8)
    ax.axis('off')
    axes_img.append((ax, im))

# === 顶部共享色条 ===
cbar_ax = fig.add_subplot(gs[0, :])
cbar = fig.colorbar(axes_img[0][1], cax=cbar_ax, orientation='horizontal')
cbar.set_label('归一化激活', fontsize=8); cbar.ax.xaxis.set_label_position('top'); cbar.ax.xaxis.set_ticks_position('top')
cbar.ax.tick_params(labelsize=7, length=2)
cbar.outline.set_linewidth(0.4)
cbar.outline.set_edgecolor(COLORS['grid'])

# === 子图间流向箭头（用 figure-level transform）===
def add_arrow(fig, axL, axR, label=None):
    bbL = axL.get_position(); bbR = axR.get_position()
    y_mid = (bbL.y0 + bbL.y1) / 2
    arrow = FancyArrowPatch((bbL.x1 + 0.005, y_mid), (bbR.x0 - 0.005, y_mid),
                             transform=fig.transFigure,
                             arrowstyle='->', mutation_scale=14,
                             color=COLORS['highlight'], linewidth=1.5,
                             clip_on=False)
    fig.patches.append(arrow)
    if label:
        fig.text((bbL.x1 + bbR.x0) / 2, y_mid + 0.04, label,
                 fontsize=8, ha='center', color=COLORS['highlight'],
                 fontweight='bold', style='italic')

add_arrow(fig, axes_img[0][0], axes_img[1][0], 'Encoder')
add_arrow(fig, axes_img[1][0], axes_img[2][0], 'Decoder')

save_fig(fig, 'figures/fig_triptych.pdf')
