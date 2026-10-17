"""Mixed full-plan preparation keeps complete templates and provenance intact."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / 'original/resources/assets/shared-scripts'
sys.path.insert(0, str(SHARED))
from get_recipe import Recipes
from template_sources import complete_source


class MixedTemplatePreparationTests(unittest.TestCase):
    def run_tool(self, tool, *args, cwd):
        return subprocess.run([sys.executable, str(tool), *map(str, args)], cwd=cwd,
                              capture_output=True, encoding='utf-8')

    def test_full_plan_prepares_normal_and_complete_sources_with_matching_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            plan=root/'FIGURE_PLAN.json'
            plan.write_text(json.dumps({'figures':[
                {'recipe':'recipe:basic.line'},
                {'recipe':'template.shap_dependence'},
                {'recipe':'template.sem_violin_pearson'},
                {'recipe':'asset:VA-001'},
            ]}),encoding='utf-8')
            result=self.run_tool(SHARED/'get_recipe.py','--plan',plan,'--scripts-dir',root/'figures','--workspace',root,cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            records=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual({r['template'] for r in records},{'basic.line','template.shap_dependence','template.sem_violin_pearson'})
            for key in ('template.shap_dependence','template.sem_violin_pearson'):
                batch=root/'figures'/('gen_fig_'+key.replace('.','_')+'.py')
                code, source=complete_source(key,root)
                self.assertEqual(batch.read_text(encoding='utf-8'),code)
                record=json.loads(Path(next(r['record'] for r in records if r['template']==key)).read_text(encoding='utf-8'))
                self.assertEqual(record['source'],source)
            direct=root/'figures/direct.py'
            result=self.run_tool(ROOT/'scripts/prepare_complete_template.py','--id','template.shap_dependence','--script',direct,'--workspace',root,cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(direct.read_bytes(),(root/'figures/gen_fig_template_shap_dependence.py').read_bytes())
            direct.write_text(direct.read_text(encoding='utf-8')+'\n# adapted\n',encoding='utf-8')
            result=self.run_tool(SHARED/'get_recipe.py','--id','template.shap_dependence','--script',direct,'--workspace',root,cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'],'preserved')
            self.assertTrue(direct.read_text(encoding='utf-8').endswith('# adapted\n'))

    def test_mixed_batch_is_preflighted_before_any_script_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); plan=root/'plan.md'
            plan.write_text('recipe:basic.line template.shap_dependence template.does_not_exist',encoding='utf-8')
            result=self.run_tool(SHARED/'get_recipe.py','--plan',plan,'--scripts-dir',root/'figures','--workspace',root,cwd=root)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Unknown complete template',result.stderr)
            self.assertFalse((root/'figures').exists())

    def test_bootstrapped_helper_finds_complete_sources_through_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); utils=root/'_utils'; utils.mkdir(); (root/'.vivid').mkdir()
            for name in ('get_recipe.py','template_sources.py','recipe_registry.json'):
                shutil.copyfile(SHARED/name,utils/name)
            (root/'.vivid/runtime.json').write_text(json.dumps({'runtime_skill':str(ROOT/'original/resources')}),encoding='utf-8')
            result=self.run_tool(utils/'get_recipe.py','--id','template.shap_contribution','--script',root/'figure.py',cwd=root)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((root/'figure.py').read_text(encoding='utf-8'),complete_source('template.shap_contribution')[0])
            plan=root/'plan.md'; plan.write_text('template.shap_dependence',encoding='utf-8')
            with tempfile.TemporaryDirectory() as elsewhere:
                result=self.run_tool(utils/'get_recipe.py','--plan',plan,'--scripts-dir',root,cwd=elsewhere)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((root/'gen_fig_template_shap_dependence.py').is_file())

    def test_legacy_prefixed_complete_reference_is_deduplicated(self):
        self.assertEqual(Recipes().references('template.shap_dependence recipe:template.shap_dependence asset:VA-001'),['template.shap_dependence'])


if __name__=='__main__': unittest.main()
