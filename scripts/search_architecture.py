"""Rank architecture assets by purpose/topology; inspect previews before choosing."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SYNONYMS=[['反馈','闭环','feedback','control'],['资源','分配','调度','resource','allocation','scheduling'],['流程','阶段','pipeline','process'],['分层','layer','layered'],['部署','host','device','deployment'],['网络','拓扑','network','topology'],['矩阵','matrix'],['平台','模块','platform'],['输入','输出','input','output'],['对比','comparison','two-panel']]
SYNONYMS += [['融合','汇合','分量','fusion','multi-criteria','evaluation'],['测量','观测','measurement','measurements','observation'],['优化','搜索','optimization','search'],['离线','在线','offline','online','offline-online'],['预测','forecast','forecasting','prediction'],['需求','demand'],['共享','共享池','pool','shared'],['约束','目标','constraints','objective']]
def terms(text):
    result=set(re.findall(r'[a-z0-9][a-z0-9_-]*',text.lower()))
    for run in re.findall(r'[\u4e00-\u9fff]+',text):
        result.add(run)
        result.update(run[i:i+2] for i in range(len(run)-1))
    return result
def rank(query,cards=None,limit=8,family=None):
    cards=cards if cards is not None else json.loads((ROOT/'architecture/catalog.json').read_text(encoding='utf8'));q=terms(query)
    extra=set()
    for group in SYNONYMS:
        if any(w in query.lower() for w in group):extra.update(group)
    ranked=[]
    for c in cards:
        if family and c.get('family')!=family:continue
        high=' '.join([c['name'],c.get('family',''),' '.join(c.get('tags',[])),c.get('when_to_use','')]).lower()
        low=(c.get('summary','')+' '+c.get('adapt','')).lower()
        score=sum(4 for t in q if t in high)+sum(1 for t in q if t in low)+sum(1 for t in extra if t in high)
        if q and not score:continue
        ranked.append((score,c))
    ranked.sort(key=lambda p:(-p[0],p[1]['id']))
    return [dict(score=s,**c) for s,c in ranked[:limit]]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('query',nargs='?',default='');ap.add_argument('--family');ap.add_argument('--limit',type=int,default=8);ap.add_argument('--json',action='store_true');args=ap.parse_args()
    out=rank(args.query,limit=args.limit,family=args.family)
    if args.json:print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        for c in out:print(f"{c.get('display_code',c['id'])} | {c['name']} | score={c['score']}\n  {c.get('when_to_use','')}\n  preview: {ROOT/c['preview']}\n  avoid: {c.get('avoid','See TEMPLATE.md')}\n")
        if not out:print('No matching asset. Try a broader topology or adapt the nearest suitable asset; do not force a mismatched template.')
if __name__=='__main__':main()
