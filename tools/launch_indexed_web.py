"""Launch an explicitly pinned local indexed scene without replacing a release.

The package owns its private runtime, reader and isolated layer workspace.
Close this controller or use --stop-state to stop only its verified service.
"""
from pathlib import Path
import argparse,json,os,secrets,socket,subprocess,sys,time,urllib.request,webbrowser
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from portable_source_runtime import load_package
from osgb_stdio_worker import OwnedWindowsJob

def request(base,path,owner=None):
    q=urllib.request.Request(base+path,data=b'' if owner else None,method='POST' if owner else 'GET',headers={'X-Local-Owner':owner} if owner else {})
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(q,timeout=10) as r:
        return r.status,json.loads(r.read()) if not owner else None

def stop(state):
    value=json.loads(state.read_bytes());assert value['status']=='ready'
    base='http://127.0.0.1:'+str(value['port'])
    code,status=request(base,'/api/runtime/status')
    if status['identity']!=value['identity'] or status['pid']!=value['servicePid']:
        raise ValueError('Scene identity changed; existing service left untouched')
    owner=Path(value['readyFile']).stem
    if len(owner)!=32 or any(c not in '0123456789abcdef' for c in owner):raise ValueError('Invalid own-service record')
    code,_=request(base,'/api/runtime/shutdown',owner)
    print(json.dumps({'shutdownStatus':code,'servicePid':status['pid']}),flush=True)

def run(root,identity,port,state,open_browser):
    package=load_package(root)
    if package['identity']!=identity:raise ValueError('Pinned package identity differs')
    if not 1024<=port<=65535:raise ValueError('Invalid local scene port')
    if state.exists():raise ValueError('Use a new controller state file; inspect existing owner before relaunch')
    with socket.socket() as check:
        if os.name=='nt':check.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        check.bind(('127.0.0.1',port))
    state.parent.mkdir(parents=True,exist_ok=True)
    owner=secrets.token_hex(16);ready=root/'UserData/Run'/(owner+'.json')
    report={'status':'starting','controllerPid':os.getpid(),'package':str(root),'identity':identity,'port':port,'readyFile':str(ready),'restartEnabled':False}
    process=job=None
    def publish():
        pending=state.with_suffix('.pending');pending.write_text(json.dumps(report,indent=2),encoding='utf-8');pending.replace(state)
    def shutdown():return request('http://127.0.0.1:'+str(port),'/api/runtime/shutdown',owner)[0]
    publish()
    try:
        with state.with_suffix('.log').open('xb') as log:
            process=subprocess.Popen([str(root/'runtime/python/python.exe'),'-I','-B',str(root/'application/tools/portable_source_runtime.py'),'--package',str(root),'--port',str(port),'--owner-token',owner],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            job=OwnedWindowsJob(process);report['servicePid']=process.pid;publish()
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                if process.poll() is not None:raise RuntimeError('Owned scene exited before ready')
                if ready.exists():
                    value=json.loads(ready.read_bytes())
                    if value.get('state')=='ready':break
                time.sleep(.1)
            else:raise TimeoutError('Owned scene readiness timeout')
            assert value['identity']==identity and value['pid']==process.pid and value['launchId']==owner and value['port']==port
            _,status=request('http://127.0.0.1:'+str(port),'/api/runtime/status')
            assert status['identity']==identity and status['pid']==process.pid and status['readOnly'] and not status['protectedWrites']
            report.update(status='ready',url=f'http://127.0.0.1:{port}/?topic=emergency&mode=command&levelIndex=1&levelCut=1')
            publish();print(json.dumps(report),flush=True)
            if open_browser:webbrowser.open(report['url'])
            try:process.wait()
            except KeyboardInterrupt:report['shutdownStatus']=shutdown();process.wait(timeout=30)
    finally:
        if process and process.poll() is None:
            try:report['shutdownStatus']=shutdown();process.wait(timeout=30)
            except Exception as error:report['cleanupError']=type(error).__name__
            if process.poll() is None and job:job.close();job=None;process.wait(timeout=15);report['forcedOwnJobCleanup']=True
        if job:job.close()
        if ready.exists():report['finalState']=json.loads(ready.read_bytes())
        report.update(status='stopped' if process and process.poll()==0 else 'failed',exitCode=process.poll() if process else None);publish()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path);p.add_argument('--identity');p.add_argument('--port',type=int,default=8768)
    p.add_argument('--state',type=Path);p.add_argument('--stop-state',type=Path);p.add_argument('--no-browser',action='store_true')
    a=p.parse_args()
    if a.stop_state:
        if a.package or a.identity or a.state:p.error('Stop takes only its explicit owner state')
        stop(a.stop_state);return
    if not a.package or not a.identity or not a.state:p.error('Explicit package, identity and state required')
    run(a.package.resolve(),a.identity,a.port,a.state.resolve(),not a.no_browser)

if __name__=='__main__':main()
