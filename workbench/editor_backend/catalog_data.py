"""Template-specific multi-table contracts used by catalog adapters."""
from pathlib import Path
import json, numpy as np, pandas as pd
PATH=Path(__file__).parent/'catalog-contracts.json'
CONTRACTS=json.loads(PATH.read_text(encoding='utf8')) if PATH.exists() else {}

class Table:
    def __init__(self,table,contract):
        from schema import Invalid
        self.h=table.get('headers',[]);self.rows=table.get('rows',[]);self.contract=contract
        if not isinstance(self.h,list) or not self.h or len(self.h)>256 or len(set(map(str,self.h)))!=len(self.h):raise Invalid('数据表列名必须非空且不重复，最多 256 列。')
        if any(not str(h).strip() for h in self.h):raise Invalid('数据表列名不能为空。')
        if not isinstance(self.rows,list) or not 1<=len(self.rows)<=20000 or len(self.rows)*len(self.h)>500000:raise Invalid('数据表需要 1–20000 行，总单元格不超过 500000。')
        for i,row in enumerate(self.rows):
            if not isinstance(row,list) or len(row)!=len(self.h):raise Invalid('数据行长度与列名不一致。',i)
        expected=contract.get('headers')
        if contract['kind']=='columns' and len(self.h)!=len(expected):raise Invalid(f'此表需要 {len(expected)} 列：'+ '、'.join(expected))
    def text(self,col=0):
        from schema import Invalid
        out=[]
        for i,row in enumerate(self.rows):
            val=str(row[col]).strip() if row[col] is not None else ''
            if not val:raise Invalid(f'第 {i+1} 行「{self.h[col]}」不能为空。',i,col)
            out.append(val)
        return out
    def col(self,c=0):
        from schema import Invalid
        vals=[]
        for i,row in enumerate(self.rows):
            v=row[c]
            try:
                if self.contract.get('allow_blank') and (v is None or str(v).strip()==''):
                    vals.append(np.nan);continue
                if self.contract.get('allow_failure') and str(v).strip()=='失败':
                    vals.append(np.inf);continue
                if v is None or isinstance(v,bool) or str(v).strip()=='':raise ValueError()
                val=float(v)
                if not np.isfinite(val) or abs(val)>1e14:raise ValueError()
            except (ValueError,TypeError):raise Invalid(f'第 {i+1} 行「{self.h[c]}」需要有效数字。',i,c)
            vals.append(val)
        return np.array(vals)
    def matrix(self,start=1):return np.column_stack([self.col(c) for c in range(start,len(self.h))])
    def series(self):return {str(h):self.col(i) for i,h in enumerate(self.h) if i>0}
    def frame(self):
        data={}
        for i,h in enumerate(self.h):data[h]=self.text(i) if i in self.contract.get('text_columns',[]) else self.col(i)
        return pd.DataFrame(data)

def sample(tid):
    from schema import defaults
    c=CONTRACTS[tid];tables={t['key']:{'headers':t['headers'],'rows':t['rows']} for t in c['tables']}
    first=c['tables'][0]['key']
    return json.loads(json.dumps(dict(schema=1,template=tid,name=c['name'],tables=tables,active_table=first,table=tables[first],mapping={},settings=defaults(tid))))

def prepare(project):
    from schema import Invalid
    tid=project['template'];c=CONTRACTS[tid];tables=project.get('tables',{})
    # table is the visible sheet, also synchronized by the client on every edit.
    tables=dict(tables)
    if project.get('active_table') in tables:tables[project['active_table']]=project['table']
    parsed={}
    for spec in c['tables']:
        key=spec['key']
        if key not in tables:raise Invalid('缺少数据表：'+spec['title'])
        mapping=project.get('column_mappings',{}).get(key)
        if mapping is None and spec['kind']=='columns':mapping=list(range(len(spec['headers'])))
        try:
            table=tables[key]
            if mapping is not None and spec['kind']=='columns':
                if len(mapping)!=len(spec['headers']) or len(set(mapping))!=len(mapping) or any(type(i)!=int or not 0<=i<len(table['headers']) for i in mapping):raise Invalid('数据列对应必须完整，且不能重复。')
                table={'headers':[table['headers'][i] for i in mapping],'rows':[[row[i] for i in mapping] for row in table['rows']]}
            parsed[key]=Table(table,spec)
        except Invalid as e:
            e.detail['table']=key
            if mapping and e.detail.get('col') is not None:e.detail['col']=mapping[e.detail['col']]
            raise
    scope={'np':np,'pd':pd,'T':parsed,'settings':project['settings']}
    try:exec(c['setup'],scope)
    except Invalid:raise
    except Exception as e:raise Invalid('数据表之间的维度或内容不符合模板要求：'+str(e))
    if tid=='basic.multipanel':
        scope.update(line_names=parsed['line'].h[1:],line_labels=parsed['line'].text(),line_axis=parsed['line'].h[0],
                     bar_names=parsed['bar'].h[1:],bar_labels=parsed['bar'].text(),bar_axis=parsed['bar'].h[0],
                     scatter_axes=parsed['scatter'].h[1:],hist_axis=parsed['hist'].h[1])
    import types
    result={k:v for k,v in scope.items() if k not in ['__builtins__','np','pd','T'] and not isinstance(v,(Table,types.ModuleType)) and not callable(v)}
    return result,c.get('notes',[])

def adapt(tid,code):
    import ast
    c=CONTRACTS[tid]
    start,end=c['cut']
    if start:
        a=code.index(start);b=code.index(end,a)
        removed=code[a:b]
        # Preserve complete helper function definitions/imports in the replaced data block.
        keep=[]
        try:
            for node in ast.parse(removed).body:
                if isinstance(node,(ast.FunctionDef,ast.Import,ast.ImportFrom)):keep.append(ast.get_source_segment(removed,node))
        except SyntaxError:pass
        code=code[:a]+'\n'.join(keep)+'\nglobals().update(V)\n'+c.get('derive','')+'\n\n'+code[b:]
    else:code=code+'\nglobals().update(V)\n'+c.get('derive','')+'\n'
    for before,after in c.get('patches',[]):
        if before not in code:raise RuntimeError('适配位置不再匹配：'+before[:60])
        code=code.replace(before,after)
    if tid=='basic.multipanel':
        replacements=[
            ("label=f'系列{i + 1}'","label=line_names[i]"),
            ("enumerate(['方法A', '方法B'])","enumerate(bar_names)"),
            ("label=f'类{i + 1}'","label=sg[i]"),
            ("label=f'分布{i + 1}'","label=hg[i]"),
            ("ax.set_ylabel('累计值', fontsize=10)","ax.set_ylabel('数值', fontsize=10)\nline_ticks=np.unique(np.linspace(0,len(line_data)-1,min(6,len(line_data))).astype(int))\nax.set_xticks(line_ticks);ax.set_xticklabels([line_labels[i] for i in line_ticks],fontsize=8)\nax.set_xlabel(line_axis,fontsize=10)"),
            ("ax.set_ylabel('得分', fontsize=10)","ax.set_ylabel('数值', fontsize=10)\nax.set_xticks(x);ax.set_xticklabels(bar_labels,rotation=30,ha='right',fontsize=8)\nax.set_xlabel(bar_axis,fontsize=10)"),
            ("ax = axes[1, 0]","ax = axes[1, 0]\nax.set_xlabel(scatter_axes[0],fontsize=10);ax.set_ylabel(scatter_axes[1],fontsize=10)"),
            ("ax.set_ylabel('频次', fontsize=10)","ax.set_ylabel('频次', fontsize=10)\nax.set_xlabel(hist_axis,fontsize=10)"),
        ]
        for before,after in replacements:
            if before not in code:raise RuntimeError('组合图标签适配位置不再匹配：'+before)
            code=code.replace(before,after)
    import re
    code=re.sub(r'\bPALETTE\[([ijkcs])\]',r'PALETTE[\1 % len(PALETTE)]',code)
    return code
