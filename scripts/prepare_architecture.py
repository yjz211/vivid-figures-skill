"""Prepare a standalone Vivid architecture recipe and its editable baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id');parser.add_argument('--out',type=Path);parser.add_argument('--list',action='store_true')
    args=parser.parse_args();catalog=json.loads((ROOT/'architecture/catalog.json').read_text(encoding='utf-8'))
    if args.list:
        print(json.dumps(catalog,ensure_ascii=False,indent=2));return
    cards={}
    for card in catalog:
        for key in [card['id'],card.get('display_code')]:
            if not key:continue
            if key in cards and cards[key]['id']!=card['id']:raise ValueError(f'Duplicate catalog identifier: {key}')
            cards[key]=card
    if args.id not in cards or not args.out:parser.error('Choose a catalog --id and provide --out')
    card=cards[args.id];source=ROOT/card['directory'];out=args.out.resolve()
    if out.exists() and any(out.iterdir()):raise ValueError(f'Output must be an empty directory: {out}')
    out.mkdir(parents=True,exist_ok=True);baseline=out/'.vivid/template-sources';baseline.mkdir(parents=True)
    files={'make_figure.py':source/'make_figure.py','example.json':source/'example.json','diagram.py':ROOT/'architecture/lib/diagram.py','check_architecture_connections.py':ROOT/'scripts/check_architecture_connections.py','render_architecture.py':ROOT/'scripts/render_architecture.py','TEMPLATE.md':source/'TEMPLATE.md'}
    source_asset=(source/'asset.json').exists() and (source/'geometry.json').exists()
    if source_asset:
        files.pop('diagram.py')
        for name in ['source_asset.py','source_measure.py']:
            files[name]=ROOT/'architecture/lib'/name
    # Both vector recipes and code-built templates may use explicit semantic roles.
    files['semantic_palette.py']=ROOT/'architecture/lib/semantic_palette.py'
    files['PALETTE.md']=ROOT/'architecture/PALETTE.md'
    files['PPTX.md']=ROOT/'architecture/PPTX.md'
    files['requirements-architecture.txt']=ROOT/'requirements-architecture.txt'
    files['export_architecture_pptx.py']=ROOT/'scripts/export_architecture_pptx.py'
    for name in ['vivid_config.py','palettes.json']:
        files[name]=ROOT/'original/resources/assets/shared-scripts'/name
    # Template-local helpers and vector pieces travel with their actual code.
    # Include them in the hashed baseline so adaptation remains reviewable.
    native_files={'asset.json','geometry.json','labels.json','guide.json','diagram.svg','TEMPLATE.md','ATTRIBUTION.md','example.json','font_profile.json','FONTS.md'}
    for path in sorted(source.iterdir()):
        selected=(path.name in native_files or path.suffix=='.py') if source_asset else path.suffix in {'.py','.json','.svg','.md'}
        if path.is_file() and selected:
            files.setdefault(path.name,path)
    if source_asset:
        for required in ['diagram.svg','asset.json','geometry.json','guide.json','ATTRIBUTION.md']:
            if required not in files:raise FileNotFoundError(f'Incomplete Vivid asset: {source/required}')
    record={'template':card['id'],'display_code':card.get('display_code'),'source_reference':card['id'],'files':{}}
    for name,path in files.items():
        shutil.copy2(path,out/name);shutil.copy2(path,baseline/name)
        record['files'][name]={'sha256':sha(path),'source':str(path.relative_to(ROOT))}
    runtime=ROOT/'scripts/pptx_runtime'
    for path in sorted(runtime.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':continue
        name=Path('pptx_runtime')/path.relative_to(runtime)
        for target in [out/name,baseline/name]:
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        record['files'][name.as_posix()]={'sha256':sha(path),'source':str(path.relative_to(ROOT))}
    # Runtime assets are self-contained: never distribute the original reference folder.
    if source_asset:
        shutil.copytree(ROOT/'architecture/fonts/source-assets',out/'fonts')
        # SVG assets may carry additional, licensed font families or a font manifest.
        # Merge their local bundle after common replacement fonts so prepared output
        # can reproduce the same font profile without the installed package.
        local_fonts=source/'fonts'
        if local_fonts.is_dir():
            shutil.copytree(local_fonts,out/'fonts',dirs_exist_ok=True)
    elif (source/'font_profile.json').exists():
        shutil.copytree(ROOT/'architecture/fonts',out/'fonts')
    (baseline/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'id':card['id'],'display_code':card.get('display_code'),'directory':str(out),'source':str(out/'make_figure.py'),'guide':str(out/'TEMPLATE.md'),'next':'Read TEMPLATE.md and guide.json if present. Adapt example.json and make_figure.py as needed; run make_figure.py --out . --parts, inspect check_architecture_connections.py fig.svg findings and coverage, then render_architecture.py fig.svg.'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
