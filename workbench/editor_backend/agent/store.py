"""Immutable chart revisions and durable local workspaces. No model state is authoritative."""
from pathlib import Path
from contextlib import contextmanager
import hashlib, json, os, sqlite3, time, uuid
import jsonpatch

ROOT = Path(os.environ.get('VIVID_AGENT_HOME', Path(__file__).resolve().parents[2] / 'workspace' / 'agent'))
DB = ROOT / 'workspaces.sqlite3'

def encode(v): return json.dumps(v, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
def ident(): return uuid.uuid4().hex
def fingerprint(v): return hashlib.sha256(encode(v).encode()).hexdigest()

class Conflict(ValueError): pass

@contextmanager
def instance_lock():
    """One running orchestrator per workspace, even when different ports are requested."""
    ROOT.mkdir(parents=True,exist_ok=True)
    lock=(ROOT/'server.lock').open('a+b')
    try:
        lock.write(b'0');lock.flush();lock.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError:
        lock.close();raise RuntimeError('此工作区已有 Agent 服务运行，请使用已打开的服务。') from None
    try:yield
    finally:
        lock.seek(0)
        if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
        else:fcntl.flock(lock,fcntl.LOCK_UN)
        lock.close()

@contextmanager
def connection():
    ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()

def init():
    with connection() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,name TEXT NOT NULL,created REAL,updated REAL);
        CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY,session TEXT REFERENCES sessions(id),name TEXT,body TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS charts(id TEXT PRIMARY KEY,session TEXT REFERENCES sessions(id),name TEXT,head INTEGER,created REAL,updated REAL);
        CREATE TABLE IF NOT EXISTS revisions(chart TEXT REFERENCES charts(id),rev INTEGER,body TEXT,diff TEXT,label TEXT,actor TEXT,job TEXT,created REAL,PRIMARY KEY(chart,rev));
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY,session TEXT REFERENCES sessions(id),role TEXT,body TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,session TEXT REFERENCES sessions(id),chart TEXT,status TEXT,body TEXT,created REAL,updated REAL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,run TEXT REFERENCES runs(id),body TEXT,created REAL);
        CREATE TABLE IF NOT EXISTS effects(id TEXT PRIMARY KEY,body TEXT);
        ''')
        if 'domain' not in {r[1] for r in db.execute('PRAGMA table_info(sessions)')}:db.execute("ALTER TABLE sessions ADD COLUMN domain TEXT NOT NULL DEFAULT 'data'")

def require(db, table, key):
    # Table names are exclusively internal literals.
    row=db.execute(f'SELECT * FROM {table} WHERE id=?',(key,)).fetchone()
    if row is None: raise ValueError('记录不存在。')
    return dict(row)

def create_session(name='新的绘图项目',domain='data'):
    if domain not in ['data','architecture']:raise ValueError('工作区类型无效。')
    key=ident();now=time.time()
    with connection() as db: db.execute('INSERT INTO sessions(id,name,created,updated,domain) VALUES(?,?,?,?,?)',(key,str(name)[:100],now,now,domain))
    return session(key)

def sessions(domain=None):
    with connection() as db:
        return [dict(r) for r in db.execute('SELECT s.*, (SELECT count(*) FROM charts c WHERE c.session=s.id) chart_count FROM sessions s WHERE (? IS NULL OR s.domain=?) ORDER BY updated DESC',(domain,domain))]

def session(key):
    with connection() as db:
        result=require(db,'sessions',key)
        result['datasets']=[{**dict(r),'table':json.loads(r['body'])} for r in db.execute('SELECT * FROM datasets WHERE session=? ORDER BY created',(key,))]
        for d in result['datasets']: del d['body']
        result['charts']=[dict(r) for r in db.execute('SELECT * FROM charts WHERE session=? ORDER BY created',(key,))]
        result['messages']=[{**dict(r),'body':json.loads(r['body'])} for r in db.execute('SELECT * FROM messages WHERE session=? ORDER BY created',(key,))]
        result['runs']=[{**dict(r),'body':json.loads(r['body'])} for r in db.execute('SELECT * FROM runs WHERE session=? ORDER BY created DESC LIMIT 30',(key,))]
    return result

def dataset(session_id,name,table,operation=None):
    key=hashlib.sha256(operation.encode()).hexdigest()[:32] if operation else ident()
    with connection() as db:
        require(db,'sessions',session_id)
        db.execute('INSERT OR IGNORE INTO datasets VALUES(?,?,?,?,?)',(key,session_id,str(name)[:150],encode(table),time.time()))
        db.execute('UPDATE sessions SET updated=? WHERE id=?',(time.time(),session_id))
    return {'id':key,'name':name,'table':table}

def chart(key,rev=None):
    with connection() as db:
        item=require(db,'charts',key);n=item['head'] if rev is None else int(rev)
        row=db.execute('SELECT * FROM revisions WHERE chart=? AND rev=?',(key,n)).fetchone()
        if not row:raise ValueError('版本不存在。')
        item.update(revision=n,project=json.loads(row['body']),job=row['job'],label=row['label'],actor=row['actor'])
    return item

def revisions(key):
    with connection() as db:
        require(db,'charts',key)
        return [dict(r) for r in db.execute('SELECT rev,label,actor,job,created,diff FROM revisions WHERE chart=? ORDER BY rev DESC',(key,))]

def create_chart(session_id,project,label='选择模板',actor='user',job=None,operation=None):
    key=hashlib.sha256(operation.encode()).hexdigest()[:32] if operation else ident();now=time.time()
    with connection() as db:
        require(db,'sessions',session_id)
        db.execute('INSERT OR IGNORE INTO charts VALUES(?,?,?,?,?,?)',(key,session_id,project.get('name','未命名图表'),1,now,now))
        db.execute('INSERT OR IGNORE INTO revisions VALUES(?,?,?,?,?,?,?,?)',(key,1,encode(project),'[]',label,actor,job,now))
        db.execute('UPDATE sessions SET updated=? WHERE id=?',(now,session_id))
    return chart(key,1)

def save_revision(key,base,project,label='手动编辑',actor='user',job=None,operation=None):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        effect=db.execute('SELECT body FROM effects WHERE id=?',(operation,)).fetchone() if operation else None
        if effect:return chart(key,json.loads(effect['body'])['revision'])
        current=require(db,'charts',key)
        if current['head']!=base:raise Conflict('当前图已被修改；候选结果已保留，请选择作为新图打开。')
        old=json.loads(db.execute('SELECT body FROM revisions WHERE chart=? AND rev=?',(key,base)).fetchone()['body'])
        delta=jsonpatch.make_patch(old,project).patch
        n=base
        if delta:
            n=base+1;now=time.time()
            db.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?)',(key,n,encode(project),encode(delta),str(label)[:200],actor,job,now))
            db.execute('UPDATE charts SET head=?,name=?,updated=? WHERE id=?',(n,project.get('name',current['name']),now,key))
            db.execute('UPDATE sessions SET updated=? WHERE id=?',(now,current['session']))
        elif job:db.execute('UPDATE revisions SET job=? WHERE chart=? AND rev=?',(job,key,base))
        if operation:db.execute('INSERT INTO effects VALUES(?,?)',(operation,encode({'revision':n})))
    return chart(key,n)

def attach_job(key,rev,job):
    with connection() as db:db.execute('UPDATE revisions SET job=? WHERE chart=? AND rev=?',(job,key,rev))

def message(session_id,role,body,operation=None):
    with connection() as db:
        key=hashlib.sha256(operation.encode()).hexdigest()[:32] if operation else ident()
        db.execute('INSERT OR IGNORE INTO messages VALUES(?,?,?,?,?)',(key,session_id,role,encode(body),time.time()))

def create_run(session_id,chart_id,body):
    key=ident();now=time.time()
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        require(db,'sessions',session_id)
        if db.execute("SELECT 1 FROM runs WHERE session=? AND status IN ('queued','running','waiting')",(session_id,)).fetchone():raise ValueError('当前项目有进行中的任务，请先继续或停止它。')
        db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?)',(key,session_id,chart_id,'queued',encode(body),now,now))
    return run(key)

def reserve_resume(key):
    with connection() as db:
        db.execute('BEGIN IMMEDIATE');r=require(db,'runs',key)
        if db.execute("SELECT 1 FROM runs WHERE session=? AND id!=? AND status IN ('queued','running','waiting')",(r['session'],key)).fetchone():raise ValueError('当前项目有另一个进行中的任务，请先停止它。')
        if r['status'] not in ['waiting','interrupted','error']:raise ValueError('此任务无需恢复。')
        db.execute("UPDATE runs SET status='queued' WHERE id=?",(key,))

def run(key):
    with connection() as db:r=require(db,'runs',key)
    r['body']=json.loads(r['body']);return r

def update_run(key,status,**changes):
    with connection() as db:
        r=require(db,'runs',key);body=json.loads(r['body']);body.update(changes)
        db.execute('UPDATE runs SET status=?,body=?,updated=? WHERE id=?',(status,encode(body),time.time(),key))

def event(key,body):
    with connection() as db:
        cur=db.execute('INSERT INTO events(run,body,created) VALUES(?,?,?)',(key,encode(body),time.time()))
        return cur.lastrowid

def events(key,after=0):
    with connection() as db:return [{'seq':r['seq'],'event':json.loads(r['body'])} for r in db.execute('SELECT seq,body FROM events WHERE run=? AND seq>? ORDER BY seq',(key,after))]

def recover_runs():
    with connection() as db:
        db.execute("UPDATE runs SET status='interrupted' WHERE status IN ('queued','running')")
