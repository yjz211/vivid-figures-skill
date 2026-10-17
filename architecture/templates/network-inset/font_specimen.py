"""Render all six supported faces at paper size; values are typography samples."""
from pathlib import Path
import argparse,sys
try:
    from diagram import Diagram
except ModuleNotFoundError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'lib'))
    from diagram import Diagram
from font_assets import apply_font_profile


def build(profile):
    d=Diagram(600,228,'Architecture typography specimen')
    d.root.set('font-family','Times New Roman')
    d.text(18,18,'Architecture typography / '+profile,size=15,anchor='start',weight='bold')
    rows=[
      ('Serif / regular','Times New Roman','normal',False,'Flow q = 12.5 m³/s; α + β ≤ 1'),
      ('Serif / bold','Times New Roman','bold',False,'Monitoring coordinator'),
      ('Serif / italic','Times New Roman','normal',True,'Shared quality check'),
      ('Serif / bold italic','Times New Roman','bold',True,'Accepted readings'),
      ('Mono / regular','Consolas','normal',False,'event_id: H1  |  Il1 O0 0123456789'),
      ('Mono / bold','Consolas','bold',False,'STATE_UPDATE  ->  ALARM_CHECK'),
    ]
    for i,(label,family,weight,italic,sample) in enumerate(rows):
        y=53+26*i
        d.text(18,y,label,size=11,anchor='start')
        e=d.text(180,y,sample,size=13,anchor='start',weight=weight,italic=italic)
        e.set('font-family',family)
    d.text(18,212,'Specimen only. Font size and layout must be checked at the final insertion width.',size=10,anchor='start')
    apply_font_profile(d,profile)
    return d


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=['reference-system','portable'],default='reference-system')
    p.add_argument('--out',type=Path,default=Path('font-specimen'))
    a=p.parse_args();print(build(a.profile).save(a.out))
