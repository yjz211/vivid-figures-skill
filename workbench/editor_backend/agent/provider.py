"""Model adapters: local authenticated Codex CLI, or an OpenAI-compatible API."""
from pathlib import Path
import asyncio, base64, ctypes, json, os, shutil, subprocess, time
from urllib.parse import urlsplit
import httpx
from . import store, jobs

DEFAULT={'provider':'codex','model':'','base_url':'https://api.openai.com/v1','review':True,'timeout':180,'max_rounds':8}
SETTINGS=store.ROOT/'settings.json'

def _protect(value,decrypt=False):
    if os.name!='nt':return value
    from ctypes import wintypes
    class Blob(ctypes.Structure):_fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_char))]
    raw=base64.b64decode(value) if decrypt else value.encode()
    buf=ctypes.create_string_buffer(raw);src=Blob(len(raw),ctypes.cast(buf,ctypes.POINTER(ctypes.c_char)));dst=Blob()
    fn=ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(src),None,None,None,None,0,ctypes.byref(dst)):raise OSError('无法使用本机凭据加密。')
    try:out=ctypes.string_at(dst.data,dst.size)
    finally:ctypes.windll.kernel32.LocalFree(dst.data)
    return out.decode() if decrypt else base64.b64encode(out).decode()

def config(public=False):
    c=dict(DEFAULT)
    if SETTINGS.exists():c.update(json.loads(SETTINGS.read_text(encoding='utf8')))
    secret=c.pop('secret','')
    if public:return {**c,'has_key':bool(secret or os.environ.get('VIVID_API_KEY')),'codex_available':bool(shutil.which('codex'))}
    c['api_key']=_protect(secret,True) if secret else os.environ.get('VIVID_API_KEY','')
    return c

def save_config(data):
    c=config(public=False);old_key=c.pop('api_key','')
    if data.get('provider',c['provider']) not in ['codex','api']:raise ValueError('模型入口无效。')
    for k in DEFAULT:
        if k in data:c[k]=data[k]
    c['timeout']=max(20,min(600,int(c['timeout'])));c['max_rounds']=max(2,min(12,int(c['max_rounds'])))
    if not isinstance(c['review'],bool):raise ValueError('视觉检查应为开关。')
    for key in ['model','base_url']:
        if not isinstance(c[key],str) or len(c[key])>400:raise ValueError('模型设置过长。')
    url=urlsplit(c['base_url'])
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password or url.query or url.fragment:raise ValueError('API 地址需要有效的 HTTP(S) 基础地址，密钥请单独填写。')
    key=data.get('api_key',old_key)
    if key is None:key=old_key
    if not isinstance(key,str) or len(key)>2000:raise ValueError('API Key 格式无效。')
    c['secret']=_protect(key) if key else ''
    store.ROOT.mkdir(parents=True,exist_ok=True)
    temp=SETTINGS.with_suffix('.tmp');temp.write_text(store.encode(c),encoding='utf8');os.chmod(temp,0o600);temp.replace(SETTINGS)
    return config(public=True)

DECISION_SCHEMA={'type':'object','properties':{
    'message':{'type':'string'},'status':{'type':'string','enum':['continue','complete','question']},
    'question':{'type':'string'},'actions':{'type':'array','items':{'type':'object','properties':{'tool':{'type':'string'},'arguments_json':{'type':'string'}},'required':['tool','arguments_json'],'additionalProperties':False}}
},'required':['message','status','question','actions'],'additionalProperties':False}
REVIEW_SCHEMA={'type':'object','properties':{'summary':{'type':'string'},'preserve':{'type':'array','items':{'type':'string'}},'issues':{'type':'array','items':{'type':'string'}},'edits':{'type':'array','items':{'type':'object','properties':{'object_id':{'type':'string'},'property':{'type':'string','enum':['offset_x','offset_y','fontsize','loc','ncols','rotation']},'value_json':{'type':'string'}},'required':['object_id','property','value_json'],'additionalProperties':False}}},'required':['summary','preserve','issues','edits'],'additionalProperties':False}

def call(prompt,schema,workdir,cancelled=lambda:False,images=None,on_process=None,effort='medium'):
    c=config();start=time.monotonic();usage={};workdir=Path(workdir);workdir.mkdir(parents=True,exist_ok=True)
    if c['provider']=='codex':
        exe=shutil.which('codex')
        if not exe:raise ValueError('没有找到 Codex CLI。可在模型设置里选择兼容 API。')
        schema_path=workdir/'response-schema.json';answer=workdir/'response.json'
        schema_path.write_text(store.encode(schema),encoding='utf8')
        if answer.exists():answer.unlink()
        if effort not in ['low','medium','high']:raise ValueError('推理强度无效。')
        args=[exe,'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--json','--output-schema',str(schema_path),'-o',str(answer),'-C',str(workdir),'-c','model_reasoning_effort="'+effort+'"']
        for flag in ['shell_tool','multi_agent','apps','plugins','hooks','browser_use','computer_use','skill_search','sleep_tool']:
            args+=['--disable',flag]
        args+=['--enable','skip_host_skill_discovery']
        if c['model'].strip():args+=['-m',c['model'].strip()]
        for img in images or []:args+=['-i',str(img)]
        args+=['-']
        # Runtime logs stay private; only parsed usage and final JSON reach the UI.
        with (workdir/'model-events.jsonl').open('w',encoding='utf8') as out, (workdir/'model-errors.log').open('w',encoding='utf8') as err:
            env=dict(os.environ);env.pop('CODEX_THREAD_ID',None)
            p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=out,stderr=err,text=True,encoding='utf8',env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if on_process:on_process(p)
            try:
                p.stdin.write(prompt);p.stdin.close()
                while p.poll() is None:
                    if cancelled():jobs.kill(p);raise InterruptedError('任务已停止')
                    if time.monotonic()-start>c['timeout']:jobs.kill(p);raise TimeoutError('模型响应超时；可以保留项目后重试。')
                    time.sleep(.15)
                if cancelled():raise InterruptedError('任务已停止')
            finally:
                if p.poll() is None:jobs.kill(p)
                if on_process:on_process(None)
        if p.returncode or not answer.exists():
            raise RuntimeError('Codex 连接失败。请确认 CLI 已登录、模型名称有效，再重试；诊断日志保存在本地任务目录。')
        for line in (workdir/'model-events.jsonl').read_text(encoding='utf8').splitlines():
            try:event=json.loads(line)
            except ValueError:continue
            if event.get('type')=='turn.completed':usage=event.get('usage',{})
        result=json.loads(answer.read_text(encoding='utf8'))
    else:
        if not c['model'].strip():raise ValueError('请在模型设置中填写模型名称。')
        content=[{'type':'text','text':prompt+'\n只返回符合这个JSON Schema的JSON对象：'+store.encode(schema)}]
        for image in images or []:
            content.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(Path(image).read_bytes()).decode()}})
        async def request():
            async with httpx.AsyncClient(timeout=c['timeout']) as client:
                task=asyncio.create_task(client.post(c['base_url'].rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+c['api_key']},json={'model':c['model'],'messages':[{'role':'user','content':content if images else content[0]['text']}],'response_format':{'type':'json_object'}}))
                try:
                    while not task.done():
                        if cancelled():raise InterruptedError('任务已停止')
                        await asyncio.sleep(.15)
                    return await task
                finally:
                    if not task.done():
                        task.cancel()
                        try:await task
                        except asyncio.CancelledError:pass
        try:r=asyncio.run(request())
        except httpx.HTTPError:raise RuntimeError('模型 API 连接失败或超时，请检查地址与网络。') from None
        if r.status_code>=400:raise ValueError(f'模型 API 返回 HTTP {r.status_code}。请检查地址、模型、密钥与图片/JSON支持。')
        d=r.json();usage=d.get('usage',{});text=d['choices'][0]['message']['content'].strip()
        if text.startswith('```'):text=text.split('\n',1)[1].rsplit('```',1)[0].strip()
        result=json.loads(text)
        if cancelled():raise InterruptedError('任务已停止')
    from jsonschema import validate
    validate(result,schema)
    return result,{'provider':c['provider'],'model':c['model'] or 'Codex 默认模型','seconds':round(time.monotonic()-start,2),**usage}
