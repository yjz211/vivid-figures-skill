"""A display-language switch must keep existing direct edits attached."""
from pathlib import Path
import io
import sys
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'original/resources/assets/shared-scripts'),str(ROOT/'workbench/editor_backend')]
from figure_language import localize_figure, localize_plotly
import object_editor


def manifest():
    return {'guard':'unchanged-source-and-inputs','objects':[],'skipped':[]}


def edit(props):
    return {'guard':'unchanged-source-and-inputs','props':props}


def mpl_figure(language, edits=None):
    fig,ax=plt.subplots()
    ax.plot([0,1],[1,2],label='本文方法',color='blue')
    ax.set_xticks([0,1],['均值','中位数'])
    ax.text(.5,1.5,'均值')
    ax.legend()
    localize_figure(fig,language=language)
    state=manifest()
    object_editor.mpl_edit(fig,{'object_edits':edits or {}},state)
    return fig,ax,state


class LanguageObjectIdentityTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_text_drag_and_manual_wording_survive_language_switch(self):
        _,_,zh=mpl_figure('zh')
        annotation=next(o for o in zh['objects'] if '-text-' in o['id'])
        tick=next(o for o in zh['objects'] if '-x-tick-' in o['id'] and o['props']['text']=='均值')
        changes={annotation['id']:edit({'text':'Pinned mean','offset_x':18,'offset_y':6}),
                 tick['id']:edit({'text':'Pinned tick','rotation':40})}
        plain,plain_ax,_=mpl_figure('en')
        fig,ax,en=mpl_figure('en',changes)
        objects={o['id']:o for o in en['objects']}
        self.assertEqual(objects[annotation['id']]['props']['text'],'Pinned mean')
        self.assertEqual(objects[annotation['id']]['props']['offset_x'],18)
        self.assertEqual(objects[tick['id']]['props']['text'],'Pinned tick')
        self.assertEqual(objects[tick['id']]['props']['rotation'],40)
        # Measure the applied display-plane offset, not only the saved payload.
        a=plain_ax.texts[0].get_window_extent(plain.canvas.get_renderer())
        b=ax.texts[0].get_window_extent(fig.canvas.get_renderer())
        self.assertAlmostEqual(b.x0-a.x0,18*fig.dpi/72,places=5)
        self.assertAlmostEqual(b.y0-a.y0,-6*fig.dpi/72,places=5)
        output=io.StringIO();fig.savefig(output,format='svg')
        self.assertIn('Pinned mean',output.getvalue())
        self.assertIn('Pinned tick',output.getvalue())
        self.assertEqual(en['skipped'],[])

    def test_line_color_updates_translated_legend_after_column_repack(self):
        _,_,zh=mpl_figure('zh')
        line=next(o for o in zh['objects'] if o['kind']=='line')
        legend=next(o for o in zh['objects'] if o['kind']=='legend')
        changes={line['id']:edit({'color':'#ff0000'}),legend['id']:edit({'ncols':2})}
        _,ax,_=mpl_figure('en',changes)
        self.assertEqual(ax.lines[0].get_color(),'#ff0000')
        self.assertEqual(ax.get_legend().texts[0].get_text(),'Our method')
        self.assertEqual(ax.get_legend().legend_handles[0].get_color(),'#ff0000')

    def test_plotly_opacity_and_visibility_survive_language_switch(self):
        def figure(language,edits=None):
            fig=go.Figure(go.Scatter(x=[0,1],y=[2,3],name='本文方法'))
            localize_plotly(fig,language=language)
            state=manifest();object_editor.plotly_edit(fig,{'object_edits':edits or {}},state)
            return fig,state
        _,zh=figure('zh')
        trace=next(o for o in zh['objects'] if o['kind']=='trace')
        fig,en=figure('en',{trace['id']:edit({'alpha':.35,'visible':False})})
        self.assertEqual(fig.data[0].name,'Our method')
        self.assertEqual(fig.data[0].opacity,.35)
        self.assertIs(fig.data[0].visible,False)
        self.assertIn(trace['id'],{o['id'] for o in en['objects']})
        self.assertEqual(list(fig.data[0].x),[0,1])
        self.assertEqual(list(fig.data[0].y),[2,3])


if __name__=='__main__':
    unittest.main()
