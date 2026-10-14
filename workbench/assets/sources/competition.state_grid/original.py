import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

# ── 数据：n_unit 行(单元/槽位) × n_frame 列(帧/时隙)，值 = 离散状态编码
#    真实项目里从仿真结果 JSON 读；此处用可复现的随机演示
rng = np.random.default_rng(7)
n_unit, n_frame = 16, 40
Z = rng.choice([0, 1, 2, 3], size=(n_unit, n_frame), p=[0.70, 0.18, 0.09, 0.03])
Z = Z.astype(float)
Z[rng.random(Z.shape) < 0.05] = np.nan          # 空缺单元用 nan，画成空白不画死0

STATE_NAMES = ['0（首传成功）', '1 轮重传', '2 轮', '3 轮']
# 离散色带：低档用浅色、高档用醒目色（语义递进），一律走 PALETTE 派生
CMAP = ListedColormap([_lighten(PALETTE[2], 0.42), _lighten(PALETTE[5], 0.20),
                       PALETTE[1], PALETTE[4]])
BOUNDS = [-0.5, 0.5, 1.5, 2.5, 3.5]            # 每档一个区间，边界卡在半整数
NORM = BoundaryNorm(BOUNDS, CMAP.N)

fig, ax = plt.subplots(figsize=(7.2, 4.4))
pc = ax.pcolormesh(np.arange(n_frame + 1) - 0.5, np.arange(n_unit + 1) - 0.5,
                   np.ma.masked_invalid(Z), cmap=CMAP, norm=NORM,
                   edgecolors='white', linewidth=0.30, zorder=3)

cb = fig.colorbar(pc, ax=ax, shrink=0.82, aspect=16, pad=0.03, ticks=[0, 1, 2, 3])
cb.set_ticklabels(STATE_NAMES)                  # ★ 离散标签写人话，不写 0/1/2/3
cb.set_label('该单元的状态档位', fontsize=10)
cb.ax.tick_params(labelsize=8.4)

ax.set_xlabel('帧 / 时隙序号 $k$', fontsize=10)
ax.set_ylabel('单元 / 槽位序号', fontsize=10)
ax.set_xticks([0, 9, 19, 29, 39]); ax.set_xticklabels(['1', '10', '20', '30', '40'])
ax.set_yticks([0, 3, 7, 11, 15]);  ax.set_yticklabels(['1', '4', '8', '12', '16'])
ax.tick_params(labelsize=9)
ax.set_title('(a) 仿真逐帧状态栅格', fontsize=11, fontweight='bold', loc='left', pad=6)

fig.tight_layout()
save_fig(fig, 'figures/fig_state_grid.pdf')
