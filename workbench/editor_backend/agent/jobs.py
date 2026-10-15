"""Original Vivid worker with cancellable process handles and bounded concurrency."""
from pathlib import Path
import json, os, shutil, subprocess, sys, threading, time, uuid
from schema import prepare
import object_editor

WEB=Path(__file__).resolve().parents[2]
JOBS=WEB/'workspace/jobs'
SEMAPHORE=threading.Semaphore(2)
ACTIVE={};CANCELLED=set();LOCK=threading.Lock()

def folder(job):
    if len(job)!=32 or any(c not in '0123456789abcdef' for c in job):raise ValueError('任务编号无效。')
    return JOBS/job

def status(job):
    p=folder(job)/'status.json'
    if not p.exists():raise ValueError('绘图任务不存在。')
    try:r=json.loads(p.read_text(encoding='utf8'))
    except (json.JSONDecodeError,PermissionError):return {'state':'running','message':'正在写入结果'}
    if r.get('state')=='done':r['base']=f'/workspace/jobs/{job}/'
    return r

def kill(process):
    if process.poll() is not None:return
    if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    else:process.terminate()

def cancel(job):
    with LOCK:
        CANCELLED.add(job);p=ACTIVE.get(job)
    if p:kill(p)

def execute(job):
    f=folder(job)
    with SEMAPHORE:
        try:
            if job in CANCELLED:raise InterruptedError('绘图已停止')
            with (f/'render.log').open('w',encoding='utf8') as log:
                p=subprocess.Popen([sys.executable,'-X','utf8',str(WEB/'editor_backend/worker.py'),str(f)],cwd=f,stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                with LOCK:ACTIVE[job]=p
                started=time.monotonic()
                while p.poll() is None:
                    if job in CANCELLED:kill(p);raise InterruptedError('绘图已停止')
                    if time.monotonic()-started>180:kill(p);raise TimeoutError('绘图超过 180 秒，请减少数据或调整模板。')
                    time.sleep(.15)
                if job in CANCELLED:raise InterruptedError('绘图已停止')
                if p.returncode:raise RuntimeError('绘图失败，详情见此任务的 render.log。')
        except Exception as e:(f/'status.json').write_text(json.dumps({'state':'error','message':str(e)},ensure_ascii=False),encoding='utf8')
        finally:
            with LOCK:ACTIVE.pop(job,None);CANCELLED.discard(job)

def submit(project):
    object_editor.validate(project);_,notes=prepare(project)
    job=uuid.uuid4().hex;f=folder(job);f.mkdir(parents=True)
    (f/'project.json').write_text(json.dumps(project,ensure_ascii=False,allow_nan=False),encoding='utf8')
    source=WEB/'assets/sources'/project['template']
    shutil.copy2(source/'preview.py',f/'source.py');shutil.copy2(source/'original.py',f/'original.py')
    (f/'status.json').write_text('{"state":"queued","message":"等待绘图"}',encoding='utf8')
    threading.Thread(target=execute,args=(job,),daemon=True).start()
    return {'job':job,'notes':notes}

def wait(job,cancelled):
    while True:
        if cancelled():cancel(job);raise InterruptedError('任务已停止')
        r=status(job)
        if r['state']=='done':return r
        if r['state']=='error':raise ValueError(r['message'])
        time.sleep(.2)
