"""Start the deployed synthetic demo without changing other services or data."""
import hashlib,json,sys,subprocess,time,urllib.request,webbrowser
from pathlib import Path

def main():
 root=Path(__file__).resolve().parents[1];database=root/'Assets/Demo/reference_demo.sqlite';port=8791;url=f'http://127.0.0.1:{port}/';identity=hashlib.sha256(str(database.resolve()).lower().encode()).hexdigest()
 def healthy():
  try:
   with urllib.request.urlopen(url+'api/demo/health',timeout=1) as response:return json.load(response)
  except (OSError,ValueError):return None
 def matches(value):return value and value.get('schema')=='xnby.reference.demo.v1' and value.get('databaseBinding')==identity
 existing=healthy()
 if existing and not matches(existing):raise RuntimeError('Port 8791 belongs to another installation; no process was terminated.')
 if not existing:
  import socket
  with socket.socket() as probe:probe.bind(('127.0.0.1',port))
  logs=root/'work';logs.mkdir(exist_ok=True)
  with (logs/'server.log').open('ab') as output:
   child=subprocess.Popen([sys.executable,'-X','utf8',str(root/'tools/serve_reference_demo.py'),'--port',str(port),'--static',str(root/'web/dist'),'--database',str(database)],cwd=root,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
  (logs/'server_process.json').write_text(json.dumps(dict(pid=child.pid,databaseBinding=identity,url=url)),encoding='utf-8')
  for _ in range(80):
   if matches(healthy()):break
   if child.poll() is not None:raise RuntimeError('Demo service failed. See work/server.log.')
   time.sleep(.1)
  else:raise RuntimeError('Service is still starting; inspect recorded process rather than relaunching.')
 webbrowser.open(url)
if __name__=='__main__':
 try:main()
 except Exception:
  import traceback
  root=Path(__file__).resolve().parents[1];(root/'startup_error.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
