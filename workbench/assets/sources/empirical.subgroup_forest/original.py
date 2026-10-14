import numpy as np, matplotlib.pyplot as plt
from _utils.plot_utils import setup_style, save_fig, PALETTE, COLORS, _lighten
setup_style()

groups = {
    'By Region': {'color': PALETTE[0],
        'items': [('East',-.035,.006,True,15.2),('Central',-.022,.008,True,12.8),('West',-.015,.009,False,10.5)],
        'pooled': (-.025,.004), 'I2': 38.5, 'Q_p': 0.12},
    'By Size': {'color': PALETTE[1],
        'items': [('Large',-.028,.005,True,16.1),('Medium',-.019,.007,True,13.4),('Small',-.008,.010,False,8.9)],
        'pooled': (-.020,.004), 'I2': 52.1, 'Q_p': 0.04},
    'By Ownership': {'color': PALETTE[2],
        'items': [('SOE',-.012,.008,False,11.2),('Private',-.031,.006,True,14.7),('Foreign',-.025,.007,True,12.2)],
        'pooled': (-.023,.005), 'I2': 45.3, 'Q_p': 0.08},
}

# ★ 自适应高度
_total_items = sum(len(gd['items']) for gd in groups.values()) + len(groups) * 2
_fig_h = max(6, _total_items * 0.65 + 2)
fig, ax = plt.subplots(figsize=(10, _fig_h)); yp = 0
for gn, gd in groups.items():
    gc = gd['color']; yp -= 0.5
    ax.axhspan(yp-0.4, yp+0.4, color=gc, alpha=0.08, zorder=0)
    ax.text(-0.065, yp, f'■ {gn}', ha='left', va='center', fontsize=10.5, fontweight='bold', color=gc)
    yp -= 1.2
    for lb, c, s, sig, wt in gd['items']:
        lo, hi = c-1.96*s, c+1.96*s
        ax.plot([lo, hi], [yp, yp], color=COLORS['text'], linewidth=1.0, zorder=2)
        ax.plot([lo, lo], [yp-.12, yp+.12], color=COLORS['text'], linewidth=1.0)
        ax.plot([hi, hi], [yp-.12, yp+.12], color=COLORS['text'], linewidth=1.0)
        ms = 4 + wt/3; fc = gc if sig else 'white'; ec = gc if sig else COLORS['ref_line']
        ax.plot(c, yp, 'o', color=fc, markersize=ms, markeredgecolor=ec, markeredgewidth=1.2, zorder=3)
        ax.text(-0.065, yp, f'  {lb}', ha='left', va='center', fontsize=9, color=COLORS['text'])
        ax.text(0.065, yp, f'{wt:.1f}%', ha='right', va='center', fontsize=8, color=COLORS['ref_line'])
        yp -= 1.3
    pc, ps = gd['pooled']; plo, phi = pc-1.96*ps, pc+1.96*ps; dh = 0.3
    ax.fill([plo,pc,phi,pc], [yp,yp+dh,yp,yp-dh], color=gc, alpha=0.7, zorder=4)
    ax.plot([plo,pc,phi,pc,plo], [yp,yp+dh,yp,yp-dh,yp], color=gc, linewidth=0.8, zorder=5)
    ax.text(-0.065, yp, '  Pooled', ha='left', va='center', fontsize=9, fontweight='bold', color=gc)
    ax.text(0.065, yp, f'I²={gd["I2"]:.1f}%, Q p={gd["Q_p"]:.3f}', ha='right', va='center',
            fontsize=7.5, color=COLORS['ref_line'], fontstyle='italic')
    yp -= 1.8

ax.axvline(x=0, color=COLORS['down'], linestyle='--', linewidth=1.5, alpha=0.7, zorder=1)
ax.set_yticks([]); ax.set_xlabel('Coefficient', fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False); ax.set_ylim(yp-0.5, 0.5); ax.invert_yaxis()
ax.grid(axis='x', alpha=0.15, linestyle='--')
fig.tight_layout()
save_fig(fig, 'figures/fig_subgroup.pdf')
