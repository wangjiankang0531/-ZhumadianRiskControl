"""Build a relocatable synthetic-business package, never copy any database/assets."""
import argparse, hashlib, json, zipfile
from pathlib import Path

APP_FILES = (
    'services/__init__.py', 'services/reference_demo.py',
    'services/business_workflow.py', 'services/business_materials.py',
    'services/reference_work_forms.py', 'services/reference_demo_catalog.json',
    'services/reference_plans.py', 'services/reference_errors.py', 'services/reference_plan_materials.py',
    'tools/serve_reference_demo.py',
)
STATIC_FILES = ('reference-demo.html', 'reference-demo.js', 'reference-demo.css', 'reference-home.css', 'home-access-qr.svg','business.html','mobile.html','business.js','business.css','mobile.webmanifest')
RUNTIME_ROOT = ('python.exe', 'python3.dll', 'python312.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'LICENSE.txt')

VERIFY = r'''"""Verify packaged immutable files; data and logs are intentionally separate."""
import hashlib, json
from pathlib import Path, PurePosixPath

def verify(root):
    manifest=json.loads((root/'package_manifest.json').read_text(encoding='utf-8'))
    if manifest.get('schema')!='xnby.synthetic.business.package.v1' or manifest.get('includesDatabase') is not False:
        raise ValueError('Invalid package identity')
    seen=set()
    for item in manifest['files']:
        name=item['path']; rel=PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or ':' in name or chr(92) in name or name in seen:
            raise ValueError('Unsafe or duplicate package path')
        seen.add(name); path=root.joinpath(*rel.parts)
        for part in (path, *path.parents):
            if part==root.parent:break
            if part.is_symlink() or part.is_junction():raise ValueError('Package link rejected: '+name)
        raw=path.read_bytes()
        if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ValueError('Package content mismatch: '+name)
    return {'version':manifest['version'],'files':len(seen),'verified':True}

if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent)))
'''

RUN = r'''"""Local validation entry. Public ingress/authentication must be configured separately."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from verify_package import verify
def main():
    verify(ROOT)
    from tools.serve_reference_demo import make_server
    config=json.loads((ROOT/'config/local.json').read_text(encoding='utf-8'))
    if set(config)!={'listen','port'} or config['listen']!='127.0.0.1' or type(config['port']) is not int or not 1024<=config['port']<=65535:
        raise ValueError('Only loopback validation is supported by this package')
    server=make_server(config['port'],ROOT/'web/dist',ROOT/'data/synthetic.sqlite')
    print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/','synthetic':True,'publicReady':False}),flush=True)
    try:server.serve_forever()
    finally:server.server_close()
if __name__=='__main__':main()
'''

README = """驻马店模拟业务 0.9.0 独立运行包（本机验收候选）

本包含 Python 3.12 运行时、共享PC/H5业务闭环与空白业务协同侧库、82 模拟业务模块、八类作业表单和结构化预案编制/评审/版本流程；首次启动在 data/synthetic.sqlite 新建984条合成数据。没有复制任何现有数据库、GIS、三维模型、DLG或凭据。不扫描相邻安装或迁移相邻业务库。

解压到新的版本目录。请先运行：
  runtime\\python\\python.exe -I -B verify_package.py
本机验收启动：
  runtime\\python\\python.exe -I -B run_local.py
访问 http://127.0.0.1:18872/#work-reservation 。退出本次服务使用启动控制台的 Ctrl+C。更改端口仅修改 config/local.json 的 port，不能更改 listen。本包不注册服务、不修改系统配置或网络/安全设置。

业务数据库在 data，升级时保留该目录；先使用SQLite在线备份（含WAL），不能仅在运行中复制主数据库。静态、源码、运行时逐文件SHA256清单用于传输完整性核对，不是发行签名。

目前只允许服务器本机验收，不具备公网登录和HTTPS入口，不应直接对公网开放18872。待核对现有站点和域名/证书后接独立入口；现有Game250系统保持独立。SQLite到MySQL、Windows到Linux/Apache仍为适配准备，未通过跨平台部署验收。Linux需要匹配的运行时，不能使用本包Windows Python。
"""

def checked(path,base):
    if path.is_symlink() or path.is_junction():raise ValueError('Links are not package input: '+str(path))
    if not path.resolve().is_relative_to(base.resolve()):raise ValueError('Input escapes root')
    for parent in path.parents:
        if parent==base:break
        if parent.is_symlink() or parent.is_junction():raise ValueError('Linked input parent')
    return path.read_bytes()

def build(app,static,output,*,public=False):
    app=app.resolve();static=static.resolve()
    items={name:checked(app/name,app) for name in APP_FILES}
    for name in STATIC_FILES:items['web/dist/'+name]=checked(static/name,static)
    runtime=app/'runtime/python'
    for name in RUNTIME_ROOT:items['runtime/python/'+name]=checked(runtime/name,runtime)
    for branch in ('Lib','DLLs'):
        for path in sorted((runtime/branch).rglob('*')):
            rel=path.relative_to(runtime)
            if any(part in ('__pycache__','site-packages','test','tests','idlelib','ensurepip','tkinter','turtledemo') for part in rel.parts):continue
            if path.is_symlink() or path.is_junction():raise ValueError('Runtime link rejected')
            if path.is_file() and path.suffix.lower() in ('.py','.pyd','.dll','.txt') and not path.name.startswith('_test') and not path.name.startswith(('tcl','tk8','_tkinter')):
                items['runtime/python/'+rel.as_posix()]=checked(path,runtime)
    items.update({'verify_package.py':VERIFY.encode(),'run_local.py':RUN.encode(),'config/local.json':b'{"listen":"127.0.0.1","port":18872}', 'README.txt':README.encode('utf-8')})
    if public:
        for name in ('services/reference_access.py','tools/serve_reference_public.py','tools/deploy_business_bluegreen.py'):
            items[name]=checked(app/name,app)
        items['run_public.py']=PUBLIC_RUN.encode()
        items['iis/App_Code/XnbyReferenceProxy.cs']=checked(app/'deploy/iis_reference/App_Code/XnbyReferenceProxy.cs',app)
        items['iis/web.config.template']=checked(app/'deploy/iis_reference/web.config.template',app)
        items['README_PUBLIC.txt']=PUBLIC_README.encode('utf-8')
    # Config is editable and is checked semantically at startup, outside immutable hashes.
    manifest={'schema':'xnby.synthetic.business.package.v1','version':'0.9.0-public.1' if public else '0.9.0-standalone.1','includesDatabase':False,'includes3D':False,'publicReady':False,
              'files':[dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in sorted(items.items()) if name!='config/local.json']}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as stream,zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,raw in sorted(items.items()):archive.writestr(name,raw)
        archive.writestr('package_manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    return dict(path=str(output),sha256=hashlib.sha256(output.read_bytes()).hexdigest(),bytes=output.stat().st_size,files=len(items)+1,publicReady=False)

PUBLIC_RUN = r'''"""Authenticated loopback business backend; no public administration endpoint."""
import datetime,json,os,secrets,sys,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from verify_package import verify
verification=verify(ROOT)
from tools.serve_reference_public import make_public_server
config=json.loads((ROOT/'config/public.json').read_text('utf-8'))
server=make_public_server(config,ROOT/'web/dist',ROOT/'data/public-synthetic.sqlite')
logs=ROOT/'logs';logs.mkdir(exist_ok=True);record=logs/'backend_runtime.json';owner=secrets.token_hex(32);done=threading.Event()
runtime=dict(kind='xnby.business.backend.v1',state='ready',version=verification['version'],pid=os.getpid(),port=server.server_port,owner=owner,nativeStarts=0,startedAt=datetime.datetime.now().astimezone().isoformat())
def save():
 pending=logs/'backend_runtime.pending.json';pending.write_text(json.dumps(runtime,indent=2),encoding='utf-8');pending.replace(record)
def monitor():
 while not done.wait(.5):
  request=logs/'stop_request.json'
  if request.exists():
   try:value=json.loads(request.read_text(encoding='utf-8'))
   except (OSError,ValueError):continue
   if isinstance(value,dict) and value.get('owner')==owner and value.get('pid')==os.getpid():server.shutdown();return
save();threading.Thread(target=monitor,daemon=True).start()
print(json.dumps(dict(loopback=f'127.0.0.1:{server.server_port}',version=verification['version'],nativeStarts=0)),flush=True)
try:server.serve_forever()
finally:
 done.set();server.server_close();runtime.update(state='stopped',stoppedAt=datetime.datetime.now().astimezone().isoformat());save()
'''

PUBLIC_README = '''公网模拟业务 0.9.0-public.1 候选

目标 https://www.joinlinksmart.com/zhumadian/ 。此包的运行时和业务代码可搬迁，三维/GIS/DLG/生产库/账号密码/入口密钥均未打包。新增business.html与mobile.html共用工作流，附件与坐标另有服务端校验，原82合成台账和预案版本附件继续保留。
run_public.py 仅绑定127.0.0.1:18874。必须单独提供 config/public.json（仅密码散列和随机入口密钥），并在 iis/web.config 中填入相同入口密钥。默认不配置账号、不自动发布公网、不修改原网站。
首次安装IIS子应用需独立.NET Framework v4 Integrated应用池，物理目录指向iis目录。已有0.8.7升级使用tools/deploy_business_bluegreen.py，保留旧IIS物理目录，仅在新后台就绪后切旧固定代理、请求上限和对应清单，并在新目录logs/ingress_backup保留旧字节。使用服务器现有ASP.NET4管理处理程序，固定转发至18874；不需要安装ARR/Rewrite。仅允许指定域名的HTTPS和/zhumadian/，不会代理其它地址；不要将包根目录作为网站目录。
启动：runtime\\python\\python.exe -I -B run_public.py 。启动前检查包内逐文件SHA，首次创建独立 data/public-synthetic.sqlite，保留已有0.8.7本机数据库和18872服务。此候选尚未验收Windows服务/重启自启，关闭RDP窗口与注销不是一回事；请勿将此当作正式长稳部署。
测试账号是临时访问门禁，原82模块保留合成台账；新增业务协同库初始为空，PC与H5用户录入记录和账号审计独立保存，不是企业IAM或角色/租户权限验收。密码PBKDF2-SHA256独立随机盐，Cookie Secure/HttpOnly/SameSite=Strict，8小时绝对会话，重启后需重新登录。访问失败限速，登录和会话容量有界。
升级先SQLite在线备份含WAL，不要覆盖data或将数据库放在iis目录。Linux/Apache可用同一业务协议与入口头契约，但需对应运行时和独立代理配置；未做Linux/MySQL实际部署验收。
'''

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--static',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--public',action='store_true');a=p.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parents[1],a.static,a.output,public=a.public),ensure_ascii=False))
