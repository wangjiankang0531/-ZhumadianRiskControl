"""Common installation launcher for a selected EXE/WEB pair.

Version directories remain unchanged. The small server adapter adds installation
identity to legacy health responses while retaining each version's own renderer,
converter, assets and Python modules. It never terminates an occupied service.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
import webbrowser
if __package__:
    from .release_catalog import Catalog, ROOT
else:
    from release_catalog import Catalog, ROOT

CONTROLLER = 'xnby.selected.release.v1'


def binding(selected):
    paths=[os.path.normcase(str((ROOT/selected['data'][key]).resolve())) for key in ('layers','database')]
    return hashlib.sha256(json.dumps(paths,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()


def identity(plan):
    selected=plan['selected']
    return {'controller':CONTROLLER, 'dataBinding':binding(selected),
            'release':{**{k:selected[k] for k in ('editorVersion','webVersion','apiVersion')},
                       'manifestSha256':selected['manifestSha256']}}


def matches(health, expected):
    return health.get('application')=='xnby.landscape.web.v1' and all(health.get(k)==v for k,v in expected.items())


def serve(catalog, revision, port):
    plan=catalog.plan('web',port)
    if plan['revision']!=revision:
        raise RuntimeError('Selection changed before server startup; launch again')
    folder=Path(plan['cwd']);server=folder/'tools/landscape_web_server.py'
    # Fresh process: dependencies come from this version, not the common tools.
    sys.path[:0]=[str(folder/'tools'),str(folder)]
    spec=importlib.util.spec_from_file_location('_xnby_selected_landscape',server)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    bound=identity(plan)
    original=module.Handler
    class Handler(original):
        def do_GET(self):
            if self.path.split('?',1)[0]=='/api/health':
                raw=json.dumps({'application':'xnby.landscape.web.v1','scene':'zhumadian',**bound},separators=(',',':')).encode('utf8')
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                return
            return super().do_GET()
    module.Handler=Handler
    sys.argv=[str(server),*plan['command'][4:]]
    module.main()


def launch_web(catalog, port, page, no_browser):
    plan=catalog.plan('web',port);expected=identity(plan);url=f'http://127.0.0.1:{port}'
    folder,release,_=catalog.package(plan['selected']['package'],plan['selected']['manifestSha256'])
    viewer=next(r['sha256'] for r in release['files'] if r['path']=='apps/landscape_web/dist/viewer.js')
    def healthy():
        try:
            with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
                if not matches(json.load(response),expected):return False
            with urllib.request.urlopen(url+'/viewer.js',timeout=2) as response:
                return hashlib.sha256(response.read()).hexdigest()==viewer
        except (OSError,ValueError,KeyError):return False
    pid=None
    if not healthy():
        try:
            with socket.socket() as probe:probe.bind(('127.0.0.1',port))
        except OSError as error:
            raise RuntimeError(f'端口 {port} 已被其它版本或数据服务占用；请先结束原服务或使用其它端口') from error
        logs=ROOT/'work/release_logs';logs.mkdir(parents=True,exist_ok=True)
        name=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
        command=[plan['command'][0],'-X','utf8',str(Path(__file__).resolve()),'--state',str(catalog.state),'--port',str(port),'--serve','--revision',str(plan['revision'])]
        with (logs/(name+'.log')).open('wb') as stream:
            process=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        pid=process.pid
        (logs/(name+'.json')).write_text(json.dumps({'pid':pid,'command':command,'identity':expected,'selectionRevision':plan['revision']},ensure_ascii=False,indent=2),encoding='utf8')
        for _ in range(60):
            if healthy():break
            if process.poll() is not None:raise RuntimeError('Selected service failed to start: '+str(logs/(name+'.log')))
            time.sleep(.15)
        else:raise RuntimeError(f'Service is not ready; inspect existing PID {pid} before retrying')
    if page=='portal':url+='/portal.html'
    result={'url':url,'startedPid':pid,'identity':expected,'selectionRevision':plan['revision']}
    print(json.dumps(result,ensure_ascii=False),flush=True)
    if not no_browser:webbrowser.open(url)
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path,default=ROOT/'Packages/active_release.json')
    p.add_argument('--kind',choices=('editor','scene','portal','qa'),default='scene')
    p.add_argument('--port',type=int,default=8767);p.add_argument('--no-browser',action='store_true')
    p.add_argument('--wait',action='store_true');p.add_argument('--serve',action='store_true');p.add_argument('--revision',type=int)
    args,extra=p.parse_known_args();extra=extra[1:] if extra[:1]==['--'] else extra
    catalog=Catalog(ROOT,args.state)
    if args.serve:
        if extra or args.revision is None:p.error('Server adapter requires an exact selection revision')
        serve(catalog,args.revision,args.port);return 0
    if args.kind=='qa':
        if extra:p.error('Unknown QA arguments: '+' '.join(extra))
        plan=catalog.plan('web',args.port)
        folder=Path(plan['cwd'])
        command=[plan['command'][0],'-X','utf8',str(folder/'tools/launch_business_portal_qa.py'),'--page','portal','--port',str(args.port)]
        if args.no_browser:command.append('--no-browser')
        return subprocess.call(command,cwd=folder)
    if args.kind=='editor':
        plan=catalog.plan('editor',extra=extra)
        process=subprocess.Popen(plan['command'],cwd=plan['cwd'],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        if args.wait:return process.wait()
        print(json.dumps({'startedPid':process.pid,'selectionRevision':plan['revision'],'editorVersion':plan['selected']['editorVersion']},ensure_ascii=False));return 0
    if extra:p.error('Unknown webpage arguments: '+' '.join(extra))
    return launch_web(catalog,args.port,args.kind,args.no_browser)


if __name__=='__main__':sys.exit(main())
