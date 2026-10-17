"""Architecture assets prefer the renamed bundle and retain legacy installs."""
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / 'editor_backend'))
import architecture_assets


class ArchitectureAssetPaths(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vivid-asset-paths-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / 'home'
        self.web = self.root / 'standalone/workbench'
        self.installed = self.home / '.codex/skills/vivid-illustration-skill/architecture'
        self.legacy = self.home / '.codex/skills/vivid-figures-skill/architecture'
        for setting in [patch.dict(os.environ, {}, clear=True),
                        patch.object(architecture_assets, 'WEB', self.web),
                        patch.object(Path, 'home', return_value=self.home)]:
            setting.start()
            self.addCleanup(setting.stop)

    @staticmethod
    def make_catalog(directory):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'catalog.json').write_text('[]', encoding='utf8')

    def test_renamed_install_has_priority_over_legacy(self):
        self.make_catalog(self.legacy)
        self.make_catalog(self.installed)
        self.assertEqual(architecture_assets.architecture_root(), self.installed.resolve())

    def test_legacy_install_remains_usable_when_new_assets_are_absent(self):
        self.installed.mkdir(parents=True)
        self.make_catalog(self.legacy)
        self.assertEqual(architecture_assets.architecture_root(), self.legacy.resolve())
        self.assertEqual(architecture_assets.architecture_file('catalog.json'), self.legacy.resolve() / 'catalog.json')

    def test_missing_install_points_to_renamed_default(self):
        self.assertEqual(architecture_assets.architecture_root(), self.installed.resolve())

    def test_bundled_and_explicit_paths_keep_priority(self):
        self.make_catalog(self.installed)
        bundled = self.web.parent / 'architecture'
        self.make_catalog(bundled)
        self.assertEqual(architecture_assets.architecture_root(), bundled.resolve())
        override = self.root / 'custom-assets'
        self.make_catalog(override)
        with patch.dict(os.environ, {'VIVID_ARCHITECTURE_ROOT': str(override)}):
            self.assertEqual(architecture_assets.architecture_root(), override.resolve())


if __name__ == '__main__':
    unittest.main(verbosity=2)
