"""Local atomic project drafts and reusable appearance presets."""
from pathlib import Path
import json,uuid,re,threading,datetime
from schema import validate_language_settings
ROOT=Path(__file__).resolve().parent.parent/'workspace/library'
LOCK=threading.Lock()

def path(kind,key):
    if kind not in ['projects','styles'] or not re.fullmatch('[a-zA-Z0-9_-]{1,90}',key):raise ValueError('无效的本地保存编号。')
    return ROOT/kind/(key+'.json')

def get(kind,key):return json.loads(path(kind,key).read_text(encoding='utf8'))

def listing(kind):
    if kind not in ['projects','styles']:raise ValueError('未知项目类型。')
    result=[]
    for p in (ROOT/kind).glob('*.json'):
        try:
            data=json.loads(p.read_text(encoding='utf8'));value=data['value']
            result.append(dict(id=p.stem,name=value.get('name','未命名'),template=value.get('template',''),updated=data['updated']))
        except (ValueError,KeyError,OSError):continue
    return sorted(result,key=lambda x:x['updated'],reverse=True)

def save(kind,data):
    key=data.get('id') or uuid.uuid4().hex;p=path(kind,key)
    value=data['value']
    if not isinstance(value,dict):raise ValueError('保存内容需要对象。')
    validate_language_settings(value.get('settings',{}))
    record=dict(id=key,updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),value=value)
    content=json.dumps(record,ensure_ascii=False,allow_nan=False)
    with LOCK:
        p.parent.mkdir(parents=True,exist_ok=True)
        temp=p.with_suffix('.'+uuid.uuid4().hex+'.tmp');temp.write_text(content,encoding='utf8');temp.replace(p)
    return record
