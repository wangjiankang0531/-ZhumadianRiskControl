"""Scoped 0.8.7 -> R2 deployment. Run on the existing Windows server only.

No command execution endpoint, service registration, firewall/IIS binding changes,
or old backend shutdown. Existing login recipients and permissions are preserved.
"""
from pathlib import Path
from contextlib import closing
import datetime,hashlib,http.client,json,os,re,sqlite3,subprocess,sys,time,xml.etree.ElementTree as ET

OLD_MANIFEST_SHA='eb5c3b27cead42b518453a4b3fb963ebcf7012d35de3eb6f68f0c294cada2fbf'
OLD_NAME='ZhumadianBusiness_0.8.7_public_1'
NEW_NAME='ZhumadianBusiness_0.9.0_public_1'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def atomic(path,raw):
 pending=path.with_name(path.name+'.r2-pending')
 with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 pending.replace(path)
def safe_root(path):
 path=Path(path)
 for p in (path,*path.parents):
  if p.is_symlink() or p.is_junction():raise ValueError('Linked deployment path rejected')
 return path.resolve()
def backup_database(source,target):
 if target.exists():raise ValueError('Backup target already exists')
 with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)) as src,closing(sqlite3.connect(target)) as dst:
  src.backup(dst)
  if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or dst.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Database backup validation failed')
def ingress_changes(old,new):
 manifest=old/'package_manifest.json';raw=manifest.read_bytes()
 if digest(raw)!=OLD_MANIFEST_SHA:raise ValueError('Old manifest differs from verified server readback')
 value=json.loads(raw);proxy=old/'iis/App_Code/XnbyReferenceProxy.cs';entry=next(x for x in value['files'] if x['path']=='iis/App_Code/XnbyReferenceProxy.cs')
 if digest(proxy.read_bytes())!=entry['sha256']:raise ValueError('Old proxy differs from manifest')
 new_proxy=(new/'iis/App_Code/XnbyReferenceProxy.cs').read_bytes()
 if b'127.0.0.1:18874' not in new_proxy:raise ValueError('Candidate proxy target mismatch')
 config=old/'iis/web.config';config_raw=config.read_bytes();ET.fromstring(config_raw)
 pattern=rb'(<httpRuntime\b[^>]*\bmaxRequestLength\s*=\s*")[0-9]+(")'
 updated,count=re.subn(pattern,rb'\g<1>3072\2',config_raw)
 if count!=1:raise ValueError('Expected exactly one bounded httpRuntime body limit')
 ET.fromstring(updated)
 entry.update(bytes=len(new_proxy),sha256=digest(new_proxy));value['version']='0.8.7-public.1-portal.1-workflow-r2-ingress'
 return [(proxy,proxy.read_bytes(),new_proxy),(config,config_raw,updated),(manifest,raw,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))]
def switch(changes,backup):
 backup.mkdir(exist_ok=False);written=[]
 for index,(path,before,after) in enumerate(changes):(backup/(str(index)+'-'+path.name)).write_bytes(before)
 try:
  for path,before,after in changes:
   if path.read_bytes()!=before:raise ValueError('Ingress changed during deployment; refusing overwrite')
   atomic(path,after);written.append((path,before,after))
 except Exception:
  rollback(written);raise
 return written
def rollback(written):
 for path,before,after in reversed(written):
  if path.read_bytes()!=after:raise ValueError('Ingress changed after deployment; refusing rollback overwrite')
  atomic(path,before)
def loopback_ready(port,key,origin):
 h={'X-XNBY-Ingress':key,'X-XNBY-Public-Origin':origin};result=[]
 for path in ('/zhumadian/auth/login','/zhumadian/api/demo/workflow-catalog'):
  c=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
  try:c.request('GET',path,headers=h);r=c.getresponse();r.read();result.append(r.status)
  finally:c.close()
 return result==[200,401]
def stop_owned(root,process):
 record=json.loads((root/'logs/backend_runtime.json').read_text('utf-8'))
 if record.get('pid')!=process.pid:raise ValueError('Owned process identity mismatch')
 atomic(root/'logs/stop_request.json',json.dumps(dict(pid=process.pid,owner=record['owner'])).encode())
 process.wait(timeout=20)
 if process.returncode!=0:raise ValueError('Owned backend did not stop cleanly')
def restore_deployment(root,old):
 logs=root/'logs';result=json.loads((logs/'deployment_result.json').read_text('utf-8'))
 names=['iis/App_Code/XnbyReferenceProxy.cs','iis/web.config','package_manifest.json'];written=[]
 if result.get('state')!='ingress-switched-awaiting-public-acceptance' or result.get('changedIngress')!=names:raise ValueError('No matching deployment to roll back')
 for index,name in enumerate(names):
  path=old/name;before=(logs/'ingress_backup'/(str(index)+'-'+path.name)).read_bytes();after=path.read_bytes()
  if digest(before)!=result['beforeHashes'][index] or digest(after)!=result['afterHashes'][index]:raise ValueError('Rollback input changed; refusing overwrite')
  written.append((path,before,after))
 rollback(written)
 record=json.loads((logs/'backend_runtime.json').read_text('utf-8'))
 if record.get('pid')!=result['pid'] or record.get('port')!=18874:raise ValueError('Ingress restored; new backend identity requires manual inspection')
 if record.get('state')=='ready':
  atomic(logs/'stop_request.json',json.dumps(dict(pid=record['pid'],owner=record['owner'])).encode())
  deadline=time.monotonic()+20
  while time.monotonic()<deadline:
   if json.loads((logs/'backend_runtime.json').read_text('utf-8')).get('state')=='stopped':break
   time.sleep(.25)
  else:raise TimeoutError('Ingress restored; own backend did not confirm stopped')
 result.update(state='rolled-back',dataPreserved=True,rolledBackAt=datetime.datetime.now().astimezone().isoformat());atomic(logs/'deployment_result.json',(json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result),flush=True)
def main():
 root=safe_root(Path(__file__).resolve().parents[1]);parent=safe_root(Path('C:/FTP_Root/Zhumadian'))
 if root!=parent/NEW_NAME:raise ValueError('Run only from the fixed new version directory on the existing server')
 old=safe_root(parent/OLD_NAME)
 if sys.argv[1:]==['--rollback']:return restore_deployment(root,old)
 if sys.argv[1:]:raise ValueError('Unexpected deployment arguments')
 sys.path.insert(0,str(root));from verify_package import verify
 checked=verify(root)
 if checked['version']!='0.9.0-public.1':raise ValueError('Unexpected candidate version')
 changes=ingress_changes(old,root)
 private_raw=(old/'config/public.json').read_bytes();config=json.loads(private_raw)
 if config['port']!=18873 or config['origin']!='https://www.joinlinksmart.com' or config['prefix']!='/zhumadian/':raise ValueError('Old deployment identity mismatch')
 if (root/'config/public.json').exists() or (root/'data').exists() or (root/'logs/backend_runtime.json').exists():raise ValueError('New version already initialized; inspect existing state instead of retrying')
 config['port']=18874
 from tools.serve_reference_public import validate_config
 validate_config(config)
 logs=root/'logs';logs.mkdir(exist_ok=True);data=root/'data';data.mkdir(exist_ok=False)
 backup_database(old/'data/public-synthetic.sqlite',data/'public-synthetic.sqlite')
 backup_database(old/'data/public-synthetic.sqlite',logs/'old-legacy-online-backup.sqlite')
 atomic(root/'config/public.json',(json.dumps(config,indent=2)+'\n').encode())
 (logs/'old-public-config.json').write_bytes(private_raw)
 process=None;written=[]
 with (logs/'backend_stdout.log').open('xb') as out:
  try:
   process=subprocess.Popen([str(root/'runtime/python/python.exe'),'-I','-B',str(root/'run_public.py')],cwd=root,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   deadline=time.monotonic()+30
   while time.monotonic()<deadline:
    if process.poll() is not None:raise ValueError('New backend exited before readiness')
    record=logs/'backend_runtime.json'
    if record.exists():
     current=json.loads(record.read_text('utf-8'))
     if current.get('state')=='ready' and current.get('pid')==process.pid and current.get('port')==18874 and loopback_ready(18874,config['proxyKey'],config['origin']):break
    time.sleep(.25)
   else:raise TimeoutError('New owned backend readiness timed out')
   if (old/'config/public.json').read_bytes()!=private_raw:raise ValueError('Old private configuration changed during deployment')
   written=switch(changes,logs/'ingress_backup')
   result=dict(state='ingress-switched-awaiting-public-acceptance',version=checked['version'],referenceRevision='20261022-r2',pid=process.pid,port=18874,oldBackendStopped=False,originalDatabaseModified=False,changedIngress=[x[0].relative_to(old).as_posix() for x in written],beforeHashes=[digest(x[1]) for x in written],afterHashes=[digest(x[2]) for x in written],recordedAt=datetime.datetime.now().astimezone().isoformat(),publicAcceptance=False)
   (logs/'deployment_result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
  except Exception:
   if written:rollback(written)
   if process is not None and process.poll() is None:stop_owned(root,process)
   raise
if __name__=='__main__':main()
