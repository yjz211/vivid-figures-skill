"""SVG browser text positioning to native, editable PowerPoint text boxes.

All scene lengths are global SVG viewBox units. scale is points / SVG unit;
origin is subtracted before scaling. No bitmap or outlined-text fallback.
"""
from __future__ import annotations
import base64
import hashlib
import io
import math
import re
from copy import deepcopy
from pathlib import Path

from fontTools.ttLib import TTFont
from pptx.util import Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn


TEXT_EXTRACT_JS = r"""(el) => {
  if (el.localName !== 'text') throw new Error('Text extractor expects SVG text');
  const svg=el.ownerSVGElement, ctx=document.createElement('canvas').getContext('2d');
  const m=svg.getScreenCTM().inverse().multiply(el.getScreenCTM());
  const sx=Math.hypot(m.a,m.b), sy=Math.hypot(m.c,m.d);
  if(Math.abs(sx-sy)>Math.max(sx,sy)*1e-4 || Math.abs(m.a*m.c+m.b*m.d)>sx*sy*1e-4 || m.a*m.d-m.b*m.c<=0)
    throw new Error('Unsupported skew/anisotropic/reflected text transform: '+(el.id||el.dataset.assetKey||''));
  const angle=Math.atan2(m.b,m.a), ca=Math.cos(angle),sa=Math.sin(angle);
  const trans=p=>({x:m.a*p.x+m.c*p.y+m.e,y:m.b*p.x+m.d*p.y+m.f});
  const nodes=[], walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);
  let n; while(n=walker.nextNode()) nodes.push(n);
  let chars=[];
  for(const n of nodes) {
    const style=getComputedStyle(n.parentElement);
    let s=n.nodeValue;
    if(!/pre|break-spaces/.test(style.whiteSpace)) s=s.replace(/[\t\r\n ]+/g,' ');
    for(const ch of s) chars.push({ch,style,node:n.parentElement});
  }
  // SVG collapses indentation and inter-node whitespace under the default mode.
  const rawCount=el.getNumberOfChars();
  // Chromium SVG character APIs use UTF-16 indices, while for-of preserves a
  // supplementary-plane symbol (e.g. mathematical italic x) as one codepoint.
  const utf16Length=items=>items.reduce((count,c)=>count+c.ch.length,0);
  if(utf16Length(chars)!==rawCount) {
    const collapsed=[];
    for(const c of chars) if(c.ch!==' ' || (collapsed.length&&collapsed[collapsed.length-1].ch!==' ')) collapsed.push(c);
    while(collapsed.length&&collapsed[collapsed.length-1].ch===' ') collapsed.pop();
    chars=collapsed;
  }
  if(utf16Length(chars)!==rawCount) throw new Error(`SVG text character mapping mismatch (${utf16Length(chars)}/${rawCount})`);
  let charOffset=0;
  for(const c of chars) {c.svgIndex=charOffset;charOffset+=c.ch.length;}
  let runs=[], current=null;
  for(const c of chars) {
    const i=c.svgIndex,charEnd=i+c.ch.length-1,s=c.style;
    if(s.visibility==='hidden'||s.display==='none')continue;
    if(s.writingMode!=='horizontal-tb') throw new Error('Unsupported vertical SVG text');
    const localRotation=el.getRotationOfChar(i);
    if(Math.abs(localRotation)>1e-4) throw new Error('Unsupported per-character SVG rotation');
    const localStart=el.getStartPositionOfChar(i);
    const p=trans(localStart), e=trans(el.getEndPositionOfChar(charEnd));
    const extent=el.getExtentOfChar(i);
    let opacity=1,ancestor=c.node;
    while(ancestor&&ancestor instanceof SVGElement) {opacity*=Number(getComputedStyle(ancestor).opacity);ancestor=ancestor.parentElement;}
    opacity*=Number(s.fillOpacity);
    const fontSize=parseFloat(s.fontSize)*sx;
    if(s.fill==='none'||opacity<=0) continue;
    if(s.stroke!=='none' && parseFloat(s.strokeWidth)>0) throw new Error('Outlined SVG text is unsupported');
    const sig=[s.fontFamily,s.fontWeight,s.fontStyle,s.fill,opacity,fontSize,s.textDecorationLine].join('|');
    const gap=current?(p.x-current.endX)*ca+(p.y-current.endY)*sa:0;
    const baseline=current?Math.abs(-(p.x-current.x)*sa+(p.y-current.y)*ca):0;
    const newRun=!current||current.signature!==sig||baseline>Math.max(.03,fontSize*.015)||Math.abs(gap)>fontSize*.5;
    if(newRun) {
      current={kind:'text',key:el.getAttribute('data-asset-key')||el.id||'',text:'',x:p.x,y:p.y,width:0,height:extent.height*sx,
        fontSize,fontFamily:s.fontFamily,fontWeight:s.fontWeight,fontStyle:s.fontStyle,fill:s.fill,opacity,
        rotation:angle*180/Math.PI,signature:sig,endX:p.x,endY:p.y,underline:s.textDecorationLine.includes('underline'),
        sourceCharStart:i,sourceCharEnd:charEnd,inferredSpaces:0,bbox:{x:0,y:0,width:0,height:0},_ink:null};
      runs.push(current);
    }
    // SVG extent is a font cell, not actual ink. Measure each glyph at its
    // explicit SVG start so clipping checks do not reject empty ascender space.
    ctx.font=`${s.fontStyle} ${s.fontWeight} ${parseFloat(s.fontSize)}px ${s.fontFamily}`;
    ctx.textAlign='left';ctx.textBaseline='alphabetic';
    const gm=ctx.measureText(c.ch);
    if(gm.actualBoundingBoxLeft+gm.actualBoundingBoxRight>0 && gm.actualBoundingBoxAscent+gm.actualBoundingBoxDescent>0) {
      const lx=localStart.x-gm.actualBoundingBoxLeft,rx=localStart.x+gm.actualBoundingBoxRight;
      const ty=localStart.y-gm.actualBoundingBoxAscent,by=localStart.y+gm.actualBoundingBoxDescent;
      const corners=[trans({x:lx,y:ty}),trans({x:rx,y:ty}),trans({x:rx,y:by}),trans({x:lx,y:by})];
      const gb=[Math.min(...corners.map(p=>p.x)),Math.min(...corners.map(p=>p.y)),Math.max(...corners.map(p=>p.x)),Math.max(...corners.map(p=>p.y))];
      current._ink=current._ink?[Math.min(current._ink[0],gb[0]),Math.min(current._ink[1],gb[1]),Math.max(current._ink[2],gb[2]),Math.max(current._ink[3],gb[3])]:gb;
    }
    // PDF extraction often omits U+0020 but retains its horizontal advance.
    // Preserve that local word gap instead of distributing it over the line.
    if(!newRun&&gap>=fontSize*.17&&!/\s$/.test(current.text)&&!/^\s/.test(c.ch)) {
      current.text+=' ';current.inferredSpaces++;
    }
    current.text+=c.ch;current.endX=e.x;current.endY=e.y;current.sourceCharEnd=charEnd;
    current.width=(e.x-current.x)*ca+(e.y-current.y)*sa;
    current.height=Math.max(current.height,extent.height*sx);
  }
  for(const r of runs) {
    ctx.font=`${r.fontStyle} ${r.fontWeight} ${r.fontSize/sx}px ${r.fontFamily}`;
    r.naturalWidth=ctx.measureText(r.text).width*sx;
    r.bbox={x:r.x,y:r.y-r.fontSize,width:r.width,height:r.height};
    r.ink_bbox=r._ink?[r._ink[0],r._ink[1],r._ink[2]-r._ink[0],r._ink[3]-r._ink[1]]:[r.x,r.y,0,0];
    delete r.signature;delete r.endX;delete r.endY;delete r._ink;
  }
  return runs;
}"""


def _name(font, ids):
    for name_id in ids:
        for item in font['name'].names:
            if item.nameID == name_id:
                try:
                    return item.toUnicode()
                except Exception:
                    pass
    return ''


def font_metadata(data: bytes) -> dict:
    font=TTFont(io.BytesIO(data))
    units=font['head'].unitsPerEm
    family=_name(font,(16,1))
    style=_name(font,(17,2)).lower()
    os2=font.get('OS/2')
    return {'family':family,'bold':('bold' in style or (os2 is not None and os2.usWeightClass>=600)),
            'italic':any(x in style for x in ('italic','oblique')),
            'ascentRatio':font['hhea'].ascent/units,
            'descentRatio':-font['hhea'].descent/units,
            'lineGapRatio':font['hhea'].lineGap/units,
            'winAscentRatio':(os2.usWinAscent/units if os2 is not None else font['hhea'].ascent/units),
            'winDescentRatio':(os2.usWinDescent/units if os2 is not None else -font['hhea'].descent/units),
            'useTypoMetrics':bool(os2 is not None and os2.fsSelection & (1 << 7)),
            'typoAscentRatio':(os2.sTypoAscender/units if os2 is not None else font['hhea'].ascent/units),
            'typoDescentRatio':(-os2.sTypoDescender/units if os2 is not None else -font['hhea'].descent/units),
            'typoLineGapRatio':(os2.sTypoLineGap/units if os2 is not None else font['hhea'].lineGap/units),
            'fsType':int(os2.fsType) if os2 is not None else 0,
            'sha256':hashlib.sha256(data).hexdigest()}


def _font_weight(value):
    value=str(value).strip().lower()
    if value=='normal':return 400
    if value=='bold':return 700
    try:return int(float(value))
    except ValueError:return 400


def _font_style(value):
    value=str(value).strip().lower()
    return 'italic' if value.startswith(('italic','oblique')) else 'normal'


def _embedded_faces(svg_path):
    """Yield every embedded face with its CSS selection descriptors.

    A CSS family can declare several files. Keep a plain family key for the
    first face (and legacy one-face aliases), then give other faces unique IDs.
    Consumers which register or bundle fonts must retain all of these records.
    """
    source=Path(svg_path).read_text(encoding='utf-8')
    keys=set()
    for body in re.findall(r'@font-face\s*\{([^}]+)\}',source,re.I):
        fam=re.search(r'font-family\s*:\s*([^;]+)',body,re.I)
        encoded=re.search(r'base64,([A-Za-z0-9+/=\s]+)',body)
        if not (fam and encoded):continue
        alias=fam.group(1).strip().strip('\"\'')
        weight=re.search(r'font-weight\s*:\s*([^;]+)',body,re.I)
        style=re.search(r'font-style\s*:\s*([^;]+)',body,re.I)
        data=base64.b64decode(encoded.group(1))
        metadata=font_metadata(data)
        metadata.update(cssFamily=alias,
                        cssWeight=_font_weight(weight.group(1) if weight else 'normal'),
                        cssStyle=_font_style(style.group(1) if style else 'normal'))
        key=alias
        if key in keys:
            stem=f"{alias}:{metadata['cssWeight']}:{metadata['cssStyle']}:{metadata['sha256'][:20]}"
            key=stem;number=2
            while key in keys:
                key=f'{stem}:{number}';number+=1
        keys.add(key)
        yield key,metadata,data


def _select_font_face(font_map, aliases, weight, style):
    """Match a text run without confusing family aliases with individual faces."""
    for alias in aliases:
        faces=[info for key,info in (font_map or {}).items()
               if info.get('cssFamily',key).casefold()==alias.casefold()]
        if faces:
            # Prefer the requested style, then the closest declared weight.
            # Reversed order gives a later duplicate CSS declaration precedence.
            return min(reversed(faces),key=lambda info:(
                _font_style(info.get('cssStyle','normal'))!=_font_style(style),
                abs(_font_weight(info.get('cssWeight',400))-_font_weight(weight))))
    return {}


def build_font_map(svg_path, font_dir=None):
    """Resolve embedded CSS aliases to real OpenType names and baseline metrics.

    Does not install fonts. If font_dir is given, matching bundled files are
    recorded as `path`; callers can register those files for their own process.
    Keys identify individual faces; `cssFamily` retains their shared SVG alias.
    """
    result={}
    paths={}
    if font_dir:
        for path in Path(font_dir).rglob('*'):
            if path.suffix.lower() in ('.ttf','.otf'):
                paths[hashlib.sha256(path.read_bytes()).hexdigest()]=str(path)
    for key,metadata,_ in _embedded_faces(svg_path):
        if metadata['sha256'] in paths:metadata['path']=paths[metadata['sha256']]
        result[key]=metadata
    return result


def extract_embedded_fonts(svg_path, out_dir):
    """Write all embedded faces to a task output directory; return face metadata.

    This deliberately does not register system fonts or embed fonts in PPTX.
    fsType is retained for the caller to honor embedding permission bits.
    """
    target=Path(out_dir);target.mkdir(parents=True,exist_ok=True)
    result={}
    for key,metadata,data in _embedded_faces(svg_path):
        suffix='.otf' if data[:4]==b'OTTO' else '.ttf'
        path=target/(metadata['sha256'][:20]+suffix)
        if not path.exists():path.write_bytes(data)
        metadata['path']=str(path.resolve());result[key]=metadata
    return result


def _color(value):
    value=value or '#000000'
    if value.startswith('#'):
        code=value[1:]
        if len(code)==3:code=''.join(c*2 for c in code)
        return code[:6].upper(),(int(code[6:8],16)/255 if len(code)==8 else 1.)
    m=re.match(r'rgba?\(([^)]+)\)',value)
    if m:
        vals=[x.strip() for x in re.split(r'[, /]+',m.group(1))]
        rgb=[round(float(x[:-1])*2.55) if x.endswith('%') else round(float(x)) for x in vals[:3]]
        return ''.join(f'{max(0,min(255,x)):02X}' for x in rgb),float(vals[3]) if len(vals)>3 else 1.
    names={'black':'000000','white':'FFFFFF','red':'FF0000','blue':'0000FF','transparent':'000000'}
    if value in names:return names[value],0. if value=='transparent' else 1.
    raise ValueError(f'Unresolved text fill: {value}')


def add_text(slide,item,scale=1,origin=(0,0),font_map=None):
    """Create native editable text. Returns one textbox (or [] for empty text).

    `y` is the baseline, not textbox top. Office's zero-inset first-line
    placement uses Windows ascent for legacy fonts. USE_TYPO_METRICS fonts use
    typographic ascent with exact font-size line spacing (avoiding Office's
    extra single-spacing leading). `width` is the browser positioned advance.
    """
    if not item.get('text'):return []
    aliases=[x.strip().strip('\"\'') for x in item.get('fontFamily','Arial').split(',')]
    info=_select_font_face(font_map,aliases,item.get('fontWeight','400'),item.get('fontStyle','normal'))
    family=info.get('family',aliases[0])
    if family.startswith('VividSource-'):
        raise ValueError(f'Unresolved embedded font alias {family}; pass build_font_map result')
    font_size=float(item['fontSize'])
    use_typo=bool(info.get('useTypoMetrics',False))
    default_ascent=info.get('typoAscentRatio',info.get('ascentRatio',.9053)) if use_typo else info.get('winAscentRatio',.9053)
    baseline_ratio=float(item.get('baselineRatio',default_ascent))
    ascent=font_size*baseline_ratio
    descent=info.get('typoDescentRatio',.25) if use_typo else info.get('winDescentRatio',.25)
    height=max(font_size*1.5,float(item.get('height',font_size)),ascent+font_size*descent)
    width=max(float(item.get('width',0)),.1)
    # A little extra invisible width prevents Office wrapping on rounding while
    # preserving requested glyph spacing; no autofit is used.
    boxwidth=width+max(font_size*.15,.5)
    angle=math.radians(float(item.get('rotation',0)))
    ux,uy=math.cos(angle),math.sin(angle)
    vx,vy=-uy,ux
    cx=float(item['x'])+ux*boxwidth/2+vx*(height/2-ascent)
    cy=float(item['y'])+uy*boxwidth/2+vy*(height/2-ascent)
    shape=slide.shapes.add_textbox(Pt((cx-boxwidth/2-origin[0])*scale),Pt((cy-height/2-origin[1])*scale),Pt(boxwidth*scale),Pt(height*scale))
    shape.rotation=float(item.get('rotation',0))%360
    shape.name=f"{item.get('key','text')}:text:{item.get('sourceCharStart',0)}"
    tf=shape.text_frame
    tf.clear();tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.word_wrap=False;tf.auto_size=MSO_AUTO_SIZE.NONE;tf.vertical_anchor=MSO_ANCHOR.TOP
    p=tf.paragraphs[0];p.space_before=Pt(0);p.space_after=Pt(0)
    if use_typo:p.line_spacing=Pt(font_size*scale)
    run=p.add_run();run.text=item['text']
    run.font.name=family;run.font.size=Pt(font_size*scale)
    weight=str(item.get('fontWeight','400'))
    run.font.bold=bool(info.get('bold',False) or weight=='bold' or (weight.isdigit() and int(weight)>=600))
    run.font.italic=bool(info.get('italic',False) or item.get('fontStyle') in ('italic','oblique'))
    run.font.underline=bool(item.get('underline',False))
    color,alpha=_color(item.get('fill'));run.font.color.rgb=RGBColor.from_string(color)
    alpha*=float(item.get('opacity',1))
    if alpha<1:
        node=OxmlElement('a:alpha');node.set('val',str(round(max(0,alpha)*100000)))
        run.font.color._xFill.srgbClr.append(node)
    rpr=run._r.get_or_add_rPr()
    # Disable Office automatic kerning threshold ambiguity; explicit spacing
    # matches SVG's measured advance when per-character x arrays add tracking.
    if len(item['text'])>1 and 'naturalWidth' in item:
        tracking=(width-float(item['naturalWidth']))/(len(item['text'])-1)
        rpr.set('spc',str(round(tracking*scale*100)))
    for script in ('ea','cs'):
        node=OxmlElement('a:'+script);node.set('typeface',family);rpr.append(node)
    if use_typo:
        # No inherited theme-font size may take part in first-line metrics.
        ppr=p._p.get_or_add_pPr()
        for old in list(ppr):
            if old.tag==qn('a:defRPr'):ppr.remove(old)
        default=deepcopy(rpr);default.tag=qn('a:defRPr');ppr.append(default)
        for old in list(p._p):
            if old.tag==qn('a:endParaRPr'):p._p.remove(old)
        ending=deepcopy(rpr);ending.tag=qn('a:endParaRPr');p._p.append(ending)
    return [shape]
