"""Language is explicit, backward-compatible and independent from source data."""
from pathlib import Path
import copy, sys, tempfile, unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'editor_backend'))
from schema import Invalid, defaults, prepare, sample


class LanguageSettings(unittest.TestCase):
    templates = ('basic.grouped_bar', 'advanced.grouped_radial_bar')

    def test_existing_projects_default_to_chinese(self):
        for tid in self.templates:
            with self.subTest(template=tid):
                project = sample(tid)
                self.assertEqual(defaults(tid)['language'], 'zh')
                project['settings'].pop('language')
                prepared, _ = prepare(project)
                self.assertEqual(prepared['settings']['language'], 'zh')

    def test_language_does_not_modify_original_data(self):
        for tid in self.templates:
            for language in ('zh', 'en'):
                with self.subTest(template=tid, language=language):
                    project = sample(tid)
                    project['settings']['language'] = language
                    before = copy.deepcopy(project)
                    prepared, _ = prepare(project)
                    self.assertEqual(prepared['settings']['language'], language)
                    self.assertEqual(project, before)

    def test_explicit_english_labels_preserve_original_table(self):
        project = sample('basic.grouped_bar')
        project['settings'].update(language='en', english_labels={'本文方法':'Our method','指标A':'Metric A'})
        before = copy.deepcopy(project)
        prepared, _ = prepare(project)
        self.assertEqual(prepared['settings']['english_labels'], before['settings']['english_labels'])
        self.assertEqual(project, before)

    def test_gallery_names_do_not_translate_uploaded_names_without_a_mapping(self):
        import language_adapter
        from _utils.figure_language import translate_text
        project=sample('basic.grouped_bar')
        project['table']['rows'][0][0]='北京'
        project['settings'].update(language='en',title='需求预测')
        before=copy.deepcopy(project)
        with patch.object(language_adapter,'template_english_labels',return_value={
            '北京':'Beijing','需求预测':'Demand forecast','指标B':'Metric B'}):
            context=language_adapter.context(project,project['settings'])
            self.assertEqual(translate_text('北京',**context),'北京')
            self.assertEqual(translate_text('需求预测',**context),'需求预测')
            self.assertEqual(translate_text('指标B',**context),'Metric B')
            project['settings']['english_labels']={'北京':'Beijing monitoring site'}
            explicit=language_adapter.context(project,project['settings'])
            self.assertEqual(translate_text('北京',**explicit),'Beijing monitoring site')
        self.assertEqual(project['table'],before['table'])

    def test_malformed_english_labels_are_rejected(self):
        for mapping in (None, [], {'a':None}, {1:'One'}, {'a':''}, {'a':'x'*301}, {str(i):'x' for i in range(501)}):
            with self.subTest(mapping=mapping):
                project = sample('basic.grouped_bar')
                project['settings']['english_labels'] = mapping
                with self.assertRaisesRegex(Invalid, '英文显示名'):
                    prepare(project)

    def test_draft_save_validates_language_without_requiring_complete_data(self):
        import library
        with tempfile.TemporaryDirectory(prefix='vivid-language-') as directory, patch.object(library, 'ROOT', Path(directory)):
            draft = {'template':'basic.grouped_bar', 'settings':{'language':'en'}, 'table':{'headers':['Group','Value'], 'rows':[['A','']]}}
            saved = library.save('projects', {'id':'draft', 'value':draft})
            self.assertEqual(saved['value'],draft)
            draft['settings']['language'] = 'fr'
            with self.assertRaisesRegex(Invalid, '图内语言'):
                library.save('projects', {'id':'draft', 'value':draft})
            self.assertEqual(library.get('projects','draft')['value']['settings']['language'],'en')

    def test_unknown_or_malformed_language_is_rejected(self):
        for tid in self.templates:
            for language in ('English', 'ZH', '', 'fr', None, True, [], {}):
                with self.subTest(template=tid, language=language):
                    project = sample(tid)
                    project['settings']['language'] = language
                    with self.assertRaisesRegex(Invalid, '图内语言'):
                        prepare(project)


if __name__ == '__main__':
    unittest.main(verbosity=2)
