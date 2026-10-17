"""Start the packaged local viewer and open its URL without shell policy changes."""
import socket
import os
import hashlib
import argparse
import json
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8767);parser.add_argument('--no-browser',action='store_true');parser.add_argument('--page',choices=('scene','portal'),default='scene');parser.add_argument('--layers',type=Path);parser.add_argument('--layer-database',type=Path);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];url=f'http://127.0.0.1:{args.port}'
    expected_viewer=None
    expected_release=None
    expected_binding=None
    if args.layers or args.layer_database:
        projects=root/'projects'
        assets=projects.resolve().parent if projects.is_dir() and projects.resolve()!=projects.absolute() else root.parent/'Assets'
        paths=[os.path.normcase(str(Path(p).resolve())) for p in (args.layers or projects/'驻马店图层.json',args.layer_database or assets/'BusinessData/xnby_business.sqlite')]
        expected_binding=hashlib.sha256(json.dumps(paths,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
    manifest=root/'package.json'
    if manifest.is_file():
        raw=manifest.read_bytes();release=json.loads(raw)
        expected_release=hashlib.sha256(raw).hexdigest()
        expected_viewer=next((r['sha256'] for r in release.get('files',[]) if r['path']=='apps/landscape_web/dist/viewer.js'),None)
    def healthy():
        try:
            with urllib.request.urlopen(url+'/api/health',timeout=1) as r:
                health=json.load(r)
                if health['application'] not in ('xnby.landscape.web.v1','hongtu.landscape.web.v1'):return False
                if expected_release and health.get('release',{}).get('manifestSha256')!=expected_release:return False
                if expected_binding and health.get('dataBinding')!=expected_binding:return False
            if expected_viewer:
                with urllib.request.urlopen(url+'/viewer.js',timeout=2) as r:
                    if hashlib.sha256(r.read()).hexdigest()!=expected_viewer:return False
            return True
        except Exception:return False
    if not healthy():
        try:
            with socket.socket() as port_probe:port_probe.bind(('127.0.0.1',args.port))
        except OSError as error:
            raise RuntimeError(f'端口 {args.port} 已被其它版本或程序占用，请选择其它端口或关闭原版本') from error
        logs=root/'work/web_logs';logs.mkdir(parents=True,exist_ok=True);stamp=time.strftime('%Y%m%d_%H%M%S')
        with (logs/f'{stamp}.log').open('wb') as stream:
            command=[sys.executable,str(root/'tools/landscape_web_server.py'),f'--port={args.port}']
            if args.layers:command+=['--layers',str(args.layers)]
            if args.layer_database:command+=['--layer-database',str(args.layer_database)]
            process=subprocess.Popen(command,cwd=root,stdout=stream,stderr=stream,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
        (logs/f'{stamp}.pid').write_text(str(process.pid))
        for _ in range(40):
            if healthy():break
            if process.poll() is not None:raise RuntimeError(f'网页服务启动失败，请查看 {logs}')
            time.sleep(.15)
        else:raise RuntimeError(f'网页服务尚未就绪，请查看 {logs}')
    if args.page=='portal':url+='/portal.html'
    print('XNBY landscape viewer:',url)
    if not args.no_browser:webbrowser.open(url)

if __name__=='__main__':main()
