"""Compare adapted architecture code with its saved starting files."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);args=p.parse_args()
    root=args.directory.resolve();base=root/'.vivid/template-sources';manifest=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    changes=[];diffs=[]
    for name,meta in manifest['files'].items():
        old=base/name;new=root/name
        if hashlib.sha256(old.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('Baseline hash mismatch: '+name)
        if not new.exists():raise ValueError('Missing working file: '+name)
        before=old.read_text(encoding='utf-8');after=new.read_text(encoding='utf-8')
        if before!=after:
            changes.append(name);diffs.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='baseline/'+name,tofile='adapted/'+name))
    result={'template':manifest['template'],'reference':manifest['source_reference'],'changed_files':changes,'note':'Differences support provenance and review; they do not establish visual fidelity or semantic correctness.'}
    (root/'source-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(root/'source-review.diff').write_text(''.join(diffs),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
