"""Exact extraction, recovery, source integrity and advisory review regressions."""
import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT/'original/resources/assets/shared-scripts'
sys.path.insert(0, str(SHARED))
from get_recipe import Recipes
from template_sources import materialize, preflight, read_record, locations, digest
from recipe_style_review import compare_sources


class SourceTests(unittest.TestCase):
    def test_all_primary_sources_match_previews_exactly(self):
        recipes = Recipes(SHARED)
        cards = {c['id']:c for c in json.loads((ROOT/'catalog/cards.json').read_text(encoding='utf8'))['cards']}
        self.assertEqual(len(recipes.entries), 145)
        for tid in recipes.entries:
            with self.subTest(tid=tid):
                code, source = recipes.script(tid)
                ast.parse(code)
                self.assertEqual(code.strip(), (ROOT/'catalog'/cards[tid]['source']['original_code']).read_text(encoding='utf8').strip())
                self.assertEqual(source['codeSha256'], digest(code))

    def test_variant_is_not_concatenated_with_demo(self):
        recipes = Recipes(SHARED)
        code, source = recipes.script('advanced.cluster_heatmap', 'two_way')
        main, _ = recipes.script('advanced.cluster_heatmap')
        self.assertNotEqual(code, main)
        self.assertEqual(source['blocks'], [2])
        self.assertTrue(source['requiredInputs'])
        with self.assertRaises(ValueError): recipes.script('basic.line', 'made_up')

    def test_recovery_preserves_adapted_code_and_rejects_mismatch(self):
        code, source = Recipes(SHARED).script('basic.line')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'figures/line.py'
            result = materialize(target, code, source, tmp)
            self.assertEqual(target.read_text(encoding='utf8'), code)
            target.write_text(code+'# adapted\n', encoding='utf8')
            self.assertEqual(materialize(target, code, source, tmp)['status'], 'preserved')
            self.assertTrue(target.read_text(encoding='utf8').endswith('# adapted\n'))
            with self.assertRaises(ValueError): materialize(target, code, dict(source, variant='other'), tmp)
            baseline=Path(result['record']).with_suffix('.py')
            baseline.write_text('changed', encoding='utf8')
            with self.assertRaises(ValueError): read_record(result['record'], tmp)

    def test_missing_candidate_untracked_file_and_outside_workspace(self):
        code, source = Recipes(SHARED).script('basic.line')
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'line.py'
            target.write_text('# user file', encoding='utf8')
            with self.assertRaises(ValueError): materialize(target, code, source, tmp)
            self.assertEqual(target.read_text(encoding='utf8'), '# user file')
            with self.assertRaises(ValueError): preflight(Path(tmp).parent/'escape.py', code, source, tmp)
            with self.assertRaises(ValueError): preflight(Path(tmp)/'.vivid/source.py', code, source, tmp)
            result=materialize(Path(tmp)/'other.py',code,source,tmp)
            (Path(tmp)/'other.py').unlink()
            with self.assertRaises(ValueError): read_record(result['record'],tmp)

    def test_batch_preflight_and_legacy_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); plan=root/'plan.md'
            plan.write_text('recipe:basic.line recipe:basic.scatter',encoding='utf8')
            (root/'figures').mkdir()
            (root/'figures/gen_fig_basic_scatter.py').write_text('# existing',encoding='utf8')
            cmd=[sys.executable,str(SHARED/'get_recipe.py')]
            result=subprocess.run(cmd+['--plan',str(plan),'--scripts-dir',str(root/'figures'),'--workspace',tmp],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((root/'figures/gen_fig_basic_line.py').exists())
            result=subprocess.run(cmd+['--id','basic.line'],capture_output=True,encoding='utf8')
            self.assertEqual(result.returncode,0);self.assertIn('```python', result.stdout)

    def test_real_review_findings_and_advisory_exit(self):
        before='fig,ax=plt.subplots(figsize=(11,5))\nax.fill_between(x,lo,hi,alpha=.15)\nax.text(.1,.9,"N=5",bbox=dict(facecolor="white",alpha=.8,pad=.2))\n'
        after=before.replace('(11,5)','(6.5,3.6)').replace('alpha=.15','alpha=1').replace('pad=.2','pad=1.2')+'ax.text(.1,.6,"new explanation",bbox=dict(facecolor="white"))\n'
        findings=compare_sources(before,after)['findings']
        self.assertTrue(any(f['kind']=='layout_changed' for f in findings))
        self.assertTrue(any(f.get('parameter')=='alpha' for f in findings))
        self.assertTrue(any(f['kind']=='call_sites_changed' and f['method']=='text' for f in findings))
        self.assertTrue(any(f.get('parameter')=='bbox.pad' for f in findings))
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'figure.py'
            materialize(target,before,dict(id='basic.line',variant='test',codeSha256=digest(before)),tmp)
            target.write_text(after,encoding='utf8')
            cmd=[sys.executable,str(SHARED/'recipe_style_review.py'),'--workspace',tmp,'--summary','--output',str(Path(tmp)/'report.json')]
            self.assertEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            target.write_text('def broken(',encoding='utf8')
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)

    def test_font_defaults_and_new_bbox_are_visible(self):
        before='plt.rcParams.update({"font.size":11})\nax.text(.1,.5,"value")\n'
        after='plt.rcParams.update({"font.size":7})\nax.text(.1,.5,"value",bbox=dict(facecolor="white",pad=1.2))\n'
        findings=compare_sources(before,after)['findings']
        self.assertTrue(any(f['method']=='rcParams' and f.get('before')==[11] and f.get('after')==[7] for f in findings))
        self.assertTrue(any(f['kind']=='parameter_added' and f.get('parameter')=='bbox.pad' for f in findings))
        self.assertTrue(all(f['severity']=='advisory' for f in findings))
        axis_changes=compare_sources('ax_hist=fig.add_subplot(gs[1])', 'ax_hist=fig.add_subplot(gs[1],sharey=ax)')['findings']
        self.assertTrue(any(f.get('parameter')=='sharey' and f['kind']=='parameter_added' for f in axis_changes))

    def test_checker_scans_registered_arbitrary_names_and_detects_parse_failure(self):
        bash = 'C:/Program Files/Git/bin/bash.exe' if os.name == 'nt' else shutil.which('bash')
        if not bash or not Path(bash).exists(): self.skipTest('Bash unavailable')
        code = 'from _utils.plot_utils import setup_style, save_fig\nsetup_style()\nfig,ax=plt.subplots()\nax.plot(x,y)\nsave_fig(fig,"figures/result.png")\n'
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'figures/custom-name.py'
            materialize(target,code,dict(id='basic.line',variant='test',codeSha256=digest(code)),tmp)
            cmd=[bash,str(SHARED/'figure_check.sh')]
            env=dict(os.environ,VIVID_PYTHON=sys.executable,PYTHONUTF8='1')
            result=subprocess.run(cmd,cwd=tmp,env=env,capture_output=True,encoding='utf8',errors='replace')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('实际扫描脚本: 1',result.stdout)
            self.assertIn('custom-name.py',result.stdout)
            target.write_text(code+'def broken(',encoding='utf8')
            result=subprocess.run(cmd,cwd=tmp,env=env,capture_output=True,encoding='utf8',errors='replace')
            self.assertNotEqual(result.returncode,0)


if __name__ == '__main__': unittest.main()
