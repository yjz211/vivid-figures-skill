"""Continuous heatmap colors derived from the active Vivid project palette."""
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, to_rgb, to_rgba, to_hex
try:
    from . import vivid_config as vc
except ImportError:
    import vivid_config as vc


def palette_stops(kind='sequential', count=3, center='#ffffff', reverse=False):
    """Read current configuration on every call, including custom palettes.

    Sequential maps run from a light background to the first theme color.
    Diverging maps use the first color and the most distinct theme color,
    with the supplied neutral midpoint. This avoids nearly identical ends
    in palettes whose first two entries are neighboring shades.
    """
    colors = vc.palette_colors()
    first = np.array(to_rgb(colors[0]))
    if kind == 'sequential':
        stops = [to_hex(.9 * np.ones(3) + .1 * first), colors[0]]
    elif kind == 'diverging':
        other = max(colors[1:], key=lambda c: np.linalg.norm(np.array(to_rgb(c)) - first))
        stops = [colors[0], center, other]
    else:
        raise ValueError("kind must be 'sequential' or 'diverging'")
    if count < 2:
        raise ValueError('At least two color stops are required')
    if kind == 'diverging' and count % 2 == 0:
        raise ValueError('Diverging stops require an odd count to retain the neutral midpoint')
    # Odd LUT size retains the exact midpoint during interpolation.
    cmap = LinearSegmentedColormap.from_list('vivid_stops', stops, N=4097)
    result = [to_hex(cmap(float(t))) for t in np.linspace(0, 1, count)]
    return result[::-1] if reverse else result


def palette_cmap(kind='sequential', *, center='#ffffff', reverse=False, N=256):
    """Construct a continuous colormap; never discretize the data."""
    return LinearSegmentedColormap.from_list(
        'vivid_' + kind, palette_stops(kind, center=center, reverse=reverse), N=N)


def contrast_text(color, alpha=None, background='white'):
    """Choose dark or white text using the actual composited fill color."""
    rgba = to_rgba(color)
    a = rgba[3] if alpha is None else alpha
    rgb = np.array(rgba[:3]) * a + np.array(to_rgb(background)) * (1 - a)
    def luminance(c):
        linear = np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
        return float(linear @ np.array([.2126, .7152, .0722]))
    lum = luminance(rgb)
    dark_lum = luminance(np.array(to_rgb('#333333')))
    dark_ratio = (max(lum, dark_lum) + .05) / (min(lum, dark_lum) + .05)
    white_ratio = 1.05 / (lum + .05)
    return '#333333' if dark_ratio >= white_ratio else '#ffffff'
