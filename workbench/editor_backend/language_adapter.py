"""Translate display text after drawing, keeping source data and geometry intact."""
import re
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def template_english_labels():
    # The reproduction ZIP keeps the same display dictionary beside this file.
    paths = [Path(__file__).with_name('english-labels.json'),
             Path(__file__).resolve().parent.parent/'assets/english-labels.json']
    for path in paths:
        if path.is_file():
            return json.loads(path.read_text(encoding='utf8'))
    return {}


def data_texts(project):
    tables=dict(project.get('tables') or {'data':project.get('table',{})})
    active=project.get('active_table')
    if active in tables:tables[active]=project.get('table',tables[active])
    result=set()
    for table in tables.values():
        for value in table.get('headers',[]):
            if isinstance(value,str):result.add(value)
        for row in table.get('rows',[]):
            result.update(v for v in row if isinstance(v,str))
    return result


def context(project,settings):
    from schema import sample
    protected=data_texts(project)-data_texts(sample(project['template']))
    protected.update(settings.get(k,'') for k in ['title','xlabel','ylabel','zlabel'])
    labels={key:value for key,value in template_english_labels().items() if key not in protected}
    labels.update(settings.get('english_labels',{}))
    return dict(language=settings.get('language','zh'),labels=labels,protected_texts=protected)


def localize_mpl(fig,project,settings):
    from _utils.figure_language import localize_figure, apply_figure_fonts
    apply_figure_fonts(fig, settings.get('language','zh'))
    return localize_figure(fig,**context(project,settings))


def localize_plotly(fig,project,settings):
    from _utils.figure_language import localize_plotly as translate
    return translate(fig,**context(project,settings))


def append_language_note(texts,settings,notes):
    if settings.get('language','zh')!='en':return
    remaining=list(dict.fromkeys(str(t) for t in texts if re.search('[\u3400-\u9fff]',str(t))))
    if remaining:
        shown='、'.join(t[:45] for t in remaining[:5])
        note=f'英文模式仍保留 {len(remaining)} 处中文名称：{shown}。可点选文字修改，或提供英文显示名称；原数据不变。'
        if note not in notes:notes.append(note)


def mpl_texts(fig):
    from matplotlib.text import Text
    return [t.get_text() for t in fig.findobj(match=Text) if t.get_visible()]


def plotly_texts(fig):
    out=[]
    def collect(node):
        if isinstance(node,dict):
            for key,value in node.items():
                if key in ('text','name','ticktext','hovertext','label') or (key=='title' and isinstance(value,str)):
                    if isinstance(value,str):out.append(value)
                    elif isinstance(value,(list,tuple)):out.extend(v for v in value if isinstance(v,str))
                elif key not in ('x','y','z','values','customdata','ids','source','target'):collect(value)
        elif isinstance(node,list):
            for value in node:collect(value)
    collect(fig.to_plotly_json())
    return out
