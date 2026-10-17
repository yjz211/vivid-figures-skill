"""Channel loading stays independent of cwd and does not mix host workflows."""
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

WEB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEB / 'editor_backend'))
from agent import architecture, provider, runtime, skill_workspace


class SkillChannelLoading(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vivid-skill-channels-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.documents = {
            'SKILL.md': 'ROOT_ROUTER_ONLY',
            'channels/vivid-figure-skill/SKILL.md': 'DATA_CHANNEL_ONLY',
            'channels/vivid-architecture-diagram-skill/SKILL.md': 'ARCHITECTURE_CHANNEL_ONLY',
            'architecture/COMMON.md': 'COMMON_DESIGN_RULES',
            'architecture/PALETTE.md': 'ARCHITECTURE_PALETTE_ONLY',
            'architecture/WORKFLOW.md': 'FILE_HOST_AB_ORCHESTRATION_ONLY',
            'PALETTE.md': 'DATA_PALETTE_ONLY',
        }
        for name, content in self.documents.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf8')
        self.root_patch = patch.object(skill_workspace, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_auto_context_is_architecture_only(self):
        text = skill_workspace.skill_context()
        for name in ['channels/vivid-architecture-diagram-skill/SKILL.md', 'architecture/COMMON.md', 'architecture/PALETTE.md']:
            self.assertIn('--- ' + name + ' ---', text)
            self.assertIn(self.documents[name], text)
        for name in ['SKILL.md', 'channels/vivid-figure-skill/SKILL.md', 'architecture/WORKFLOW.md', 'PALETTE.md']:
            self.assertNotIn(self.documents[name], text)

    def test_default_read_and_explicit_paths_use_bundle_root_from_child_cwd(self):
        previous = Path.cwd()
        try:
            os.chdir(self.root / 'channels/vivid-architecture-diagram-skill')
            default = skill_workspace.execute({}, 'read_skill', {})
            explicit = skill_workspace.execute({}, 'read_skill', {'path': 'architecture/PALETTE.md'})
            optional = skill_workspace.execute({}, 'read_skill', {'path': 'PALETTE.md'})
            text = skill_workspace.skill_context()
        finally:
            os.chdir(previous)
        self.assertIn('ARCHITECTURE_CHANNEL_ONLY', default['text'])
        self.assertIn('ARCHITECTURE_PALETTE_ONLY', explicit['text'])
        self.assertIn('DATA_PALETTE_ONLY', optional['text'])
        self.assertIn('COMMON_DESIGN_RULES', text)
        with self.assertRaises(ValueError):
            skill_workspace.execute({}, 'read_skill', {'path': '../outside.md'})
        with self.assertRaises(ValueError):
            skill_workspace.execute({}, 'read_skill', {'path': 'workbench/settings.json'})

    def test_architecture_planner_receives_channel_and_single_candidate_boundary(self):
        decision = {'message': 'ready', 'status': 'complete', 'question': '', 'actions': []}
        state = {'run_id': 'channel-test', 'full_skill': True, 'round': 0}
        with patch.object(runtime, 'activity'), patch.object(architecture, 'context', return_value={}), \
             patch.object(provider, 'config', return_value={'review': False}), \
             patch.object(provider, 'call', return_value=(decision, {})) as model:
            result = architecture.plan(state)
        prompt = model.call_args.args[0]
        self.assertEqual(result['decision'], decision)
        self.assertIn('ARCHITECTURE_CHANNEL_ONLY', prompt)
        self.assertIn('COMMON_DESIGN_RULES', prompt)
        self.assertIn('当前宿主是网页单候选工作台', prompt)
        self.assertIn('read_skill', prompt)
        for name in ['SKILL.md', 'channels/vivid-figure-skill/SKILL.md', 'architecture/WORKFLOW.md', 'PALETTE.md']:
            self.assertNotIn(self.documents[name], prompt)

    def test_data_planner_does_not_load_architecture_context(self):
        decision = {'message': 'ready', 'status': 'complete', 'question': '', 'actions': []}
        state = {'run_id': 'data-channel-test', 'domain': 'data', 'round': 0}
        with patch.object(runtime, 'activity'), patch.object(runtime, 'context', return_value={}), \
             patch.object(provider, 'config', return_value={'max_rounds': 12}), \
             patch.object(skill_workspace, 'skill_context', side_effect=AssertionError('wrong channel')), \
             patch.object(provider, 'call', return_value=(decision, {})) as model:
            result = runtime.plan(state)
        self.assertEqual(result['decision'], decision)
        prompt = model.call_args.args[0]
        self.assertNotIn('read_skill', prompt)
        self.assertNotIn('ARCHITECTURE_CHANNEL_ONLY', prompt)
        self.assertNotIn('网页单候选工作台', prompt)

    def test_real_context_preserves_design_rules_without_loading_ab_workflow(self):
        with patch.object(skill_workspace, 'ROOT', WEB.parent):
            text = skill_workspace.skill_context()
            default = skill_workspace.execute({}, 'read_skill', {})
        self.assertIn('name: vivid-architecture-diagram-skill', default['text'])
        self.assertIn('图案与象形示意不能退化为纯文字', text)
        self.assertIn('真实字重', text)
        self.assertIn('源字体缺少所需字符时', text)
        self.assertIn('**视觉保真对照**', text)
        self.assertIn('网页单候选任务遵循当前宿主', text)
        self.assertNotIn('--- architecture/WORKFLOW.md ---', text)
        self.assertNotIn('--- SKILL.md ---', text)
        self.assertNotIn('--- channels/vivid-figure-skill/SKILL.md ---', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
