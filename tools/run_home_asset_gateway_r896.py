"""Own loopback Nginx + rendering fixture; real R45 filters, no database/services/desktop."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,socket,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
W=R/'work/ha902'; O=W/'browser-r896'
assert not W.exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
jobs_source=G/'tools/original_server_windows_job.py'
assert sha(jobs_source)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('asset_job_r896',jobs_source);budget=load('asset_budget_r896',A/'tools/bounded_build_job_r671.py')
memory=budget.memory_snapshot();assert memory['availablePhysicalBytes']>3*1024**3 and memory['availableCommitBytes']>3*1024**3
assert shutil.disk_usage(V).free>2*1024**3+128*1024**2
oldplan=J(V/'feedback_r889/full-source-and-restore-plan.private.json')
assert sha(V/'feedback_r889/full-source-and-restore-plan.private.json')=='9132ea7ba5a48b22f6a55fa27067c7be7bec7bbc6a869230aaaa91b3bedc9efc'
candidate=V/'performance-assets-r893/candidate-r900';built=J(V/'performance-assets-r893/lossless-candidate-r900.json');assert built['passed']
W.mkdir();(W/'logs').mkdir();(W/'temp').mkdir();root=W/'www/zhumadian';root.mkdir(parents=True)
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def sealed(n):
    row=oldplan['sources'][n];p=Path(row['source']);raw=p.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];return raw
for n in ['assets/css/index-ClWHaJx5.css','assets/css/index-DoM5WgUA.css','assets/png/background-BHYqFd8n.png','assets/png/header-Cp7ANu3F.png','assets/png/title_line-B0Cs5B57.png','assets/ttf/YouSheBiaoTiHei-fahbdFno.ttf']:
    put(root/n,sealed('frontend/security_pc/'+n))
for rel,pin in built['files'].items():
    assert sha(candidate/rel)==pin['sha256'] and (candidate/rel).stat().st_size==pin['bytes']
    if rel!='index.html':put(root/rel,(candidate/rel).read_bytes())
extra=next(n for n in built['files'] if n.endswith('.css'))
base='''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="/zhumadian/assets/css/index-ClWHaJx5.css"><link rel="stylesheet" href="/zhumadian/assets/css/index-DoM5WgUA.css">EXTRA<style>body{margin:0;min-height:100vh;background:#001332}.title{font-size:30px}.card-title{font-family:YouSheBiaoTiHei;font-size:32px;color:white}.background-pattern{position:fixed!important}.sample{padding:50px}header{height:60px}</style></head><body><div class="background-pattern" data-v-7244265a></div><header data-v-7244265a><div class="header-content" data-v-7244265a><div class="title" data-v-7244265a>驻马店重大风险防控</div></div></header><div class="sample"><h2 class="card-title">系统导航</h2><h2 class="card-title">快捷链接</h2><h2 class="card-title">浏览器扫码</h2></div></body></html>'''
for variant in ['baseline','candidate']:
    link='' if variant=='baseline' else '<link rel="stylesheet" href="/zhumadian/'+extra+'">'
    put(root/(variant+'.html'),base.replace('EXTRA',link).encode('utf8'))
app=W/'control-app';put(app/'tools/original_project_branding.py',sealed('tools/original_project_branding.py'))
put(app/'deploy/branding/zhumadian-emergency.svg',sealed('deploy/branding/zhumadian-emergency.svg'))
branding=load('asset_actual_branding_r896',app/'tools/original_project_branding.py')
with socket.socket()as reserve:reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
assert port not in {18891,18892,8767}
nginx=G/'runtime/nginx/nginx.exe';mime=G/'runtime/nginx/conf/mime.types';assert nginx.is_file() and mime.is_file()
assert sha(nginx)==oldplan['sources']['runtime/nginx/nginx.exe']['sha256']
config='\n'.join(['daemon off;','master_process on;','worker_processes 1;','pid "'+(W/'nginx.pid').as_posix()+'";','error_log "'+(W/'error.log').as_posix()+'" warn;','events { worker_connections 64; }','http {',' include "'+mime.as_posix()+'";',' default_type application/octet-stream;',' access_log off;','server {',' listen 127.0.0.1:'+str(port)+';',' server_name 127.0.0.1;',' location /zhumadian/ {','  root "'+(W/'www').as_posix()+'";',' }','}','}',''])
config=config.replace(' location /zhumadian/ {', ' location /zhumadian/ {\n  add_header Content-Security-Policy "default-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; font-src \'self\'; connect-src \'none\'; script-src \'none\';" always;')
config,branded=branding.brand_static_config(config,branding.PROJECT_NAME);put(W/'nginx.conf',config.encode('utf8'))
cmd=[str(nginx),'-p',W.as_posix()+'/', '-c','nginx.conf']
test=subprocess.run(cmd+['-t'],capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);put(W/'nginx-config-test.private.log',test.stdout+test.stderr);assert test.returncode==0
wrapper="import sys,subprocess; expected=b'ASSET_NGINX_R896\\n'; assert sys.stdin.buffer.readline(64)==expected; raise SystemExit(subprocess.call(sys.argv[1:]))"
children=[];failure=None;normal_nginx_quit=False
def launch(command,wire,cap,label):
    log=(W/(label+'.private.log')).open('xb');p=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    c={'p':p,'job':None,'label':label,'log':log};children.append(c)
    c['job']=jobs.OwnedWindowsJob(p);c['budget']=budget.BoundedBuildJob(c['job'],cap);p.stdin.write(wire);p.stdin.close();return c
def wait(c):
    p=c['p']
    while p.poll()is None:
        try:p.wait(timeout=15)
        except subprocess.TimeoutExpired:print('OWN_ASSET_'+c['label']+'_HANDLE_LIVE_NO_RESTART',flush=True)
    assert c['job'] is not None
    while c['job'].active_processes():time.sleep(.2)
    info={'exitCode':p.returncode,'actualJobDescendantsZero':True,'budget':c['budget'].metrics(),'forceTerminationUsed':False};c['job'].close();c['log'].close();return info
ng=None;browser=None;terms={}
try:
    ng=launch([sys.executable,'-I','-B','-c',wrapper,*cmd],b'ASSET_NGINX_R896\n',512*1024**2,'nginx')
    deadline=time.monotonic()+20
    owned_nginx_pid=None
    while True:
        assert ng['p'].poll()is None and time.monotonic()<deadline
        if (W/'nginx.pid').is_file():
            value=(W/'nginx.pid').read_bytes()
            if value.strip().isdigit():owned_nginx_pid=value;break
        time.sleep(.1)
    while True:
        assert ng['p'].poll()is None and time.monotonic()<deadline
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=1):break
        except OSError:time.sleep(.1)
    browser=launch(['D:/Program Files/nodejs/node.exe','--max-old-space-size=256',str(V/'verify_lossless_home_assets_r896.mjs')],(json.dumps({'base':'http://127.0.0.1:'+str(port),'output':O.as_posix()})+'\n').encode(),1024**3,'browser')
    terms['browser']=wait(browser);assert terms['browser']['exitCode']==0 and J(O/'result.json')['passed']
except BaseException as e:
    failure={'type':type(e).__name__,'message':str(e)}
    put(W/'failure-before-cleanup.json',(json.dumps(failure,indent=2)+'\n').encode('utf8'))
finally:
    if browser is not None and 'browser' not in terms:terms['browser']=wait(browser)
    if ng is not None:
        if ng['p'].poll()is None:
            assert (W/'nginx.pid').read_bytes()==owned_nginx_pid,'OWN_NGINX_PID_FILE_CHANGED_NO_SIGNAL'
            q=subprocess.run(cmd+['-s','quit'],capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
            put(W/'normal-quit.private.log',q.stdout+q.stderr);assert q.returncode==0;normal_nginx_quit=True
        terms['nginx']=wait(ng)
    proof={'passed':False,'browserPassed':failure is None,'failure':failure,'terminals':terms,'normalOwnNginxQuitRequested':normal_nginx_quit,'actualR45BrandingCodeSHA256':sha(app/'tools/original_project_branding.py'),'actualNginxSHA256':sha(nginx),'mockDOMWithOriginalCompiledCSS':True,'originalSDKOrSixComponentLifecycleAccepted':False,'publicOrDesktopTouched':False}
    put(W/'gateway-result.json',(json.dumps(proof,indent=2)+'\n').encode('utf8'))
if failure:print(json.dumps(proof));raise SystemExit(1)
sys.path.insert(0,str(V/'performance-assets-r893/direct-wheel-deps'));from PIL import Image,ImageChops
comparisons=[]
for width in [1366,1920,3840]:
    a=Image.open(O/('baseline-'+str(width)+'.png')).convert('RGBA');b=Image.open(O/('candidate-'+str(width)+'.png')).convert('RGBA')
    assert a.size==b.size
    different=sum(x!=y for x,y in zip(a.tobytes(),b.tobytes()));assert different==0,'EXACT_RENDERED_PIXELS_REQUIRED'
    comparisons.append({'width':width,'height':a.height,'differentChannels':different,'allPixelsIdentical':True})
proof['renderComparisons']=comparisons;proof['passed']=True;put(W/'gateway-result.json',(json.dumps(proof,indent=2)+'\n').encode('utf8'))
print(json.dumps({'passed':True,'actualNginxCacheVerified':True,'pixelIdenticalViewportCount':len(comparisons),'normalChildExitCodes':{n:t['exitCode']for n,t in terms.items()},'originalSDKAccepted':False}))
