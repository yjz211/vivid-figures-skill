"""Real regressions: band layers vs group count, quantitative axes and summaries."""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'original/resources/assets/shared-scripts'))
from recipe_style_review import compare_sources
from review_attention import summary_lines

BAND = '''n_layers=12
for k in range(n_layers,0,-1):
 frac=k/n_layers
 ax.fill_between(t,pred-frac*(pred-lo),pred+frac*(hi-pred),alpha=.025)
'''
REQUIREMENTS = {'quantitative_axes':[{'method':'hist','orientation':'horizontal','axis':'y'}]}


class AttentionTests(unittest.TestCase):
    def test_band_layers_report_twelve_to_eight_despite_more_sites_and_models(self):
        adapted = 'for site in sites:\n for model in ["A","B"]:\n' + ''.join('  '+line+'\n' for line in BAND.replace('n_layers=12','n_layers=8').splitlines())
        findings = compare_sources(BAND, adapted)['findings']
        focused = next(f for f in findings if f['kind']=='band_layers_changed')
        self.assertEqual(focused['before'],[12]); self.assertEqual(focused['after'],[8])
        self.assertEqual(focused['priority'],'focus')

    def test_more_groups_do_not_change_band_layers(self):
        adapted = 'for site in [1,2,3]:\n' + ''.join(' '+line+'\n' for line in BAND.splitlines())
        findings = compare_sources(BAND, adapted)['findings']
        self.assertFalse(any(f['kind'].startswith('band_layers') for f in findings))
        before='for g in range(3):\n ax.fill_between(x,lo[g],hi[g],alpha=.2)'
        after=before.replace('range(3)','range(6)')
        self.assertFalse(any(f['kind'].startswith('band_layers') for f in compare_sources(before,after)['findings']))

    def test_dynamic_layers_are_unresolved_not_a_claimed_count(self):
        findings=compare_sources(BAND,BAND.replace('n_layers=12','n_layers=choose_layers()'))['findings']
        f=next(f for f in findings if f['kind']=='band_layers_unresolved')
        self.assertEqual(f['after'],[None])

    def test_tick_hiding_and_missing_label_even_with_legacy_baseline(self):
        old="ax_hist.hist(e,orientation='horizontal')\nax_hist.set_yticklabels([])"
        new=old.replace('ax_hist','errors_ax')
        findings=compare_sources(old,new,REQUIREMENTS)['findings']
        self.assertTrue(any(f['kind']=='axis_ticks_hidden' for f in findings))
        self.assertTrue(any(f['kind']=='axis_label_missing' for f in findings))

    def test_relocated_ticks_and_real_units_are_allowed(self):
        before="ax.hist(e,orientation='horizontal')\nax.set_xlabel('Density'); ax.set_ylabel('Error (a.u.)')"
        after=before.replace('a.u.','kW')+"\nax.tick_params(axis='y',labelleft=False,labelright=True)"
        self.assertFalse(compare_sources(before,after,REQUIREMENTS)['findings'])
        # Restoring a deliberately hidden axis is supported; all-empty labels aren't readable.
        hidden=before+"\nax.set_yticklabels(['',''])"
        self.assertTrue(any(f['kind']=='axis_ticks_hidden' for f in compare_sources(before,hidden)['findings']))
        restored=hidden+"\nax.set_yticklabels(['0','1'])"
        self.assertFalse(compare_sources(before,restored)['findings'])

    def test_existing_shared_axis_hiding_does_not_create_universal_failure(self):
        code="ax.plot(x,y)\nax.tick_params(axis='y',labelleft=False)"
        self.assertFalse(compare_sources(code,code)['findings'])

    def test_new_box_survives_removal_of_other_unboxed_text(self):
        old="ax.text(1,2,'feasible')\nax.text(3,4,'unfeasible')\nax.annotate('point',xy=(1,2),bbox=dict(facecolor='white'))"
        new="ax.text(.1,.9,'service rule',bbox=dict(facecolor='white'))\nax.annotate('point',xy=(1,2),bbox=dict(facecolor='white'))"
        findings=compare_sources(old,new)['findings']
        f=next(f for f in findings if f['kind']=='annotation_box_added')
        self.assertEqual((f['before'],f['after']),(0,1))
        self.assertFalse(any(f['kind']=='annotation_box_added' for f in compare_sources(new,'for g in groups:\n '+new.replace('\n','\n '))['findings']))

    def test_removed_plot_layer_and_focus_precede_layout_details(self):
        old=BAND+"ax.scatter(x,y)\nfig.subplots_adjust(left=.1,right=.9,top=.9,bottom=.1,wspace=.1,hspace=.1)"
        new=BAND.replace('n_layers=12','n_layers=8')+"fig.subplots_adjust(left=.2,right=.8,top=.8,bottom=.2,wspace=.2,hspace=.2)"
        report=compare_sources(old,new)
        self.assertTrue(any(f['kind']=='operation_not_found' and f['priority']=='focus' for f in report['findings']))
        summary='\n'.join(summary_lines(report))
        self.assertIn('[12] → [8]',summary)
        self.assertLess(summary.index('band_layers_changed'),summary.index('其他差异'))
        self.assertTrue(all(f['severity']=='advisory' for f in report['findings']))


if __name__=='__main__':unittest.main()
