"""Renaming display labels must not alter a template's highlighted series."""
import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HELPERS = ROOT / "original/resources/assets/shared-scripts"
CASES = {
    "basic.line": ("series", {"本文方法": "Our method", "方法B": "Method B", "方法C": "Method C"}),
    "basic.grouped_bar": ("groups", {"本文方法": "Our method", "方法B": "Method B", "方法C": "Method C"}),
    "competition.radar": ("methods", {"本文方法": "Our method", "方案A": "Method A", "方案B": "Method B", "方案C": "Method C"}),
    "competition.convergence": ("methods", {"本文算法": "Our algorithm", "遗传算法 (GA)": "Genetic algorithm (GA)", "粒子群 (PSO)": "Particle swarm (PSO)", "模拟退火 (SA)": "Simulated annealing (SA)"}),
    "competition.multistep_decay": ("models", {"本文模型": "Our model"}),
    "competition.roc": ("models", {"本文模型 (AUC=0.952)": "Our model (AUC=0.952)", "随机森林 (AUC=0.921)": "Random forest (AUC=0.921)", "逻辑回归 (AUC=0.845)": "Logistic regression (AUC=0.845)"}),
}


def snapshot(fig):
    def values(a):
        return np.round(np.asarray(a, dtype=float), 10).tolist()
    axes = []
    for ax in fig.axes:
        lines = [(values(l.get_xdata()), values(l.get_ydata()), l.get_linewidth(), l.get_alpha(), l.get_marker()) for l in ax.lines]
        patches = [(p.get_linewidth(), p.get_alpha(), values(p.get_facecolor()), values(p.get_edgecolor()), values(p.get_path().vertices)) for p in ax.patches]
        collections = [(c.get_alpha(), values(c.get_facecolors()), values(c.get_edgecolors()), [values(p.vertices) for p in c.get_paths()]) for c in ax.collections]
        axes.append((lines, patches, collections))
    return axes


class HighlightLanguageTests(unittest.TestCase):
    def test_english_display_names_preserve_highlight_and_data_layers(self):
        package = types.ModuleType("_utils")
        package.__path__ = [str(HELPERS)]
        with patch.dict(sys.modules, {"_utils": package}):
            utils = importlib.import_module("_utils.plot_utils")
            with patch.object(utils, "save_fig", lambda *args, **kwargs: None):
                for tid, (key, translations) in CASES.items():
                    with self.subTest(template=tid):
                        path = ROOT / "catalog/sources" / tid / "original.py"
                        source = path.read_text(encoding="utf8")
                        english = source
                        for original, replacement in translations.items():
                            english = english.replace(repr(original), repr(replacement))
                        signatures = []
                        for code in [source, english]:
                            np.random.seed(42)
                            namespace = {"__file__": str(path), "__name__": "language_highlight_test"}
                            exec(compile(code, str(path), "exec"), namespace)
                            signatures.append(snapshot(namespace["fig"]))
                            plt.close(namespace["fig"])
                        self.assertEqual(signatures[0], signatures[1])
                        self.assertTrue(set(translations.values()).issubset(namespace[key]))


if __name__ == "__main__":
    unittest.main()
