"""Start the deployed synthetic demo without changing other services or data."""
import hashlib,json,sys,subprocess,time,urllib.request,webbrowser,sqlite3
from pathlib import Path

def backup_previous_demo(root,database):
 # Fork the previous independent demo using SQLite online backup, including WAL.
 previous=root.parent/'ReferenceWeb_0.8.6/Assets/Demo/reference_demo.sqlite'
 if not database.exists() and previous.is_file():
  from contextlib import closing
  database.parent.mkdir(parents=True,exist_ok=True)
  temporary=database.with_suffix('.migrating')
  try:
   with closing(sqlite3.connect(previous.as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(temporary)) as target:source.backup(target)
   temporary.replace(database)
  except Exception:
   temporary.unlink(missing_ok=True);raise


def main():
 root=Path(__file__).resolve().parents[1];database=root/'Assets/Demo/reference_demo.sqlite';port=8792;url=f'http://127.0.0.1:{port}/';identity=hashlib.sha256(str(database.resolve()).lower().encode()).hexdigest()
 def healthy():
  try:
   with urllib.request.urlopen(url+'api/demo/health',timeout=1) as response:return json.load(response)
  except (OSError,ValueError):return None
 def matches(value):return value and value.get('schema')=='xnby.reference.demo.v1' and value.get('databaseBinding')==identity and value.get('version')=='0.8.7'
 backup_previous_demo(root,database)
 existing=healthy()
 if existing and not matches(existing):raise RuntimeError('Port 8792 belongs to another installation; no process was terminated.')
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
