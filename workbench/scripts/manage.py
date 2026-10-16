"""Maintenance entry: serve the workbench, check its snapshot, run regressions."""
from pathlib import Path
from html.parser import HTMLParser
import argparse, ast, hashlib, importlib.util, json, os, shutil, subprocess, sys, time
import urllib.request
from datetime import datetime

WEB = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8766'
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
os.environ['NO_PROXY'] = ','.join(filter(None, [os.environ.get('NO_PROXY', ''), '127.0.0.1', 'localhost']))
os.environ['no_proxy'] = os.environ['NO_PROXY']

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf8'))

def health():
    try:
        return json.load(HTTP.open(URL+'/api/health', timeout=1))
    except OSError:
        return None

def run(command):
    print('运行：'+' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=WEB, check=True)

class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.paths = []
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag=='script' and attrs.get('src'): self.paths.append(attrs['src'])
        if tag=='link' and attrs.get('href'): self.paths.append(attrs['href'])

def check(skill_root=None):
    manifest = read(WEB/'docs/template-manifest.json')
    sources = manifest['sources']
    for record in sources:
        for name in ['original.py', 'preview.py']:
            path = WEB/'assets/sources'/record['id']/name
            if digest(path)!=record['sha256'][name]:
                raise ValueError(f'模板源码已变化，需要核对来源与更新记录：{path}')
        keys=['bundle', 'preview', 'thumb']
        if 'en' in manifest.get('preview_languages',[]):
            keys+=['preview_en','thumb_en']
            if len(record.get('preview_en',[]))!=len(record['preview']) or len(record.get('thumb_en',[]))!=len(record['thumb']):
                raise ValueError(f'英文模板预览不完整：{record["id"]}')
        for key in keys:
            for record_file in record[key]:
                path = WEB/record_file['path']
                if digest(path)!=record_file['sha256']:
                    raise ValueError(f'模板资源已变化：{path}')
        if skill_root:
            original = skill_root/'catalog'/record['skill_original']
            if digest(original)!=record['sha256']['original.py']:
                raise ValueError(f'Skill 与工作台原始源码不同：{record["id"]}')
    for relative, expected in manifest['shared_files'].items():
        if digest(WEB/relative)!=expected:
            raise ValueError(f'共享模板文件已变化：{relative}')
    ids = {record['id'] for record in sources}
    actual = {p.name for p in (WEB/'assets/sources').iterdir() if p.is_dir()}
    if ids!=actual: raise ValueError('模板目录与来源记录不同。')
    palettes = read(WEB/'editor_backend/_utils/palettes.json')['palettes']
    if len(palettes)!=manifest['palette_count']: raise ValueError('配色数量与来源记录不同。')
    for name in ['index.html', 'editor.html', 'agent.html']:
        parser = ResourceParser(); parser.feed((WEB/name).read_text(encoding='utf8'))
        for resource in parser.paths:
            if not (WEB/resource.split('?')[0]).is_file():
                raise ValueError(f'{name} 引用了不存在的文件：{resource}')
    for base in ['editor_backend', 'scripts', 'tests']:
        for path in (WEB/base).rglob('*.py'):
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    node = shutil.which('node')
    if not node: raise RuntimeError('检查 JavaScript 需要 Node.js。')
    for path in (WEB/'frontend').glob('*.js'):
        subprocess.run([node, '--check', str(path)], cwd=WEB, check=True, capture_output=True)
    print(f'通过：{len(sources)} 个模板、{len(palettes)} 套配色、页面资源及代码语法。', flush=True)
    if skill_root: print('通过：全部模板原始源码与指定 Skill 一致。', flush=True)

def collect_test_projects():
    """Only move IDs explicitly recorded by tests, never user drafts."""
    ids = set()
    for relative in ['studio/results.json', 'studio/dataflow-results.json',
                     'hit-testing/results.json', 'hit-coordinate/fixed-results.json']:
        path = WEB/'verification'/relative
        if not path.exists(): continue
        report = read(path)
        ids.update(report.get('project_ids', []))
        if report.get('project_id'): ids.add(report['project_id'])
    target = WEB/'verification/test-projects'/datetime.now().strftime('%Y%m%d-%H%M%S')
    count = 0
    for key in sorted(ids):
        if not key.startswith(('studio-test-', 'hit-test-', 'coords-test-')):
            continue
        source = WEB/'workspace/library/projects'/(key+'.json')
        if not source.is_file(): continue
        if not source.resolve().is_relative_to((WEB/'workspace/library/projects').resolve()):
            raise ValueError('测试项目路径越界。')
        target.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target/source.name)); count+=1
    if count: print(f'已将 {count} 个测试项目移入 verification/test-projects。', flush=True)

def test():
    check()
    if importlib.util.find_spec('playwright') is None:
        raise RuntimeError('浏览器测试需要 Playwright；安装 requirements-dev.txt。')
    (WEB/'verification').mkdir(exist_ok=True)
    server = None
    current = health()
    if current and (current.get('app')!='vivid-workbench' or Path(current.get('root','')).resolve()!=WEB):
        raise RuntimeError('8766 端口是另一个服务，请先处理端口冲突。')
    try:
        if not current:
            server = subprocess.Popen([sys.executable, '-X', 'utf8', str(WEB/'editor_backend/server.py')], cwd=WEB)
            for _ in range(100):
                if server.poll() is not None: raise RuntimeError('本地服务启动失败。')
                if health(): break
                time.sleep(.1)
            else: raise RuntimeError('本地服务启动超时。')
        node = shutil.which('node')
        run([node, 'tests/test_data_transform.cjs'])
        for name in ['test_archive_jobs.py', 'verify_browser.py', 'test_gallery_paths.py', 'test_studio.py',
                     'test_studio_dataflows.py', 'test_hit_regions.py', 'test_text_occlusion.py',
                     'test_render_export.py']:
            run([sys.executable, '-X', 'utf8', 'tests/'+name])
        print('通过：图库、数据整理、布局、文字拖动与旧任务访问回归。', flush=True)
    finally:
        collect_test_projects()
        if server:
            server.terminate(); server.wait(timeout=10)

def main():
    parser = argparse.ArgumentParser(description='Vivid 工作台维护入口')
    commands = parser.add_subparsers(dest='command', required=True)
    serve = commands.add_parser('serve', help='启动本地绘图服务')
    serve.add_argument('--open', action='store_true')
    agent = commands.add_parser('agent', help='启动 Agent 工作台（需 requirements-agent.txt）')
    agent.add_argument('--open', action='store_true')
    agent.add_argument('--port', type=int, default=8766)
    checks = commands.add_parser('check', help='检查资源、来源快照与代码语法')
    checks.add_argument('--skill-root', type=Path, help='额外比较指定 Skill 的原始源码')
    commands.add_parser('test', help='运行常用回归，测试项目自动收拢')
    args = parser.parse_args()
    if args.command=='serve':
        run([sys.executable, '-X', 'utf8', WEB/'editor_backend/server.py']+(['--open'] if args.open else []))
    elif args.command=='agent':
        local_python=WEB/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        run([local_python if local_python.exists() else sys.executable,'-X','utf8',WEB/'editor_backend/agent_server.py','--port',args.port]+(['--open'] if args.open else []))
    elif args.command=='check': check(args.skill_root)
    elif args.command=='test': test()

if __name__=='__main__':
    try: main()
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print('未通过：'+str(error), file=sys.stderr); sys.exit(1)
