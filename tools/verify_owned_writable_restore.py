"""Cold-restore the stopped owned database; prove one durable write can be restored."""
import argparse,datetime,gzip,hashlib,json,msvcrt,os,pathlib,re,shutil,socket,subprocess,sys,time,traceback
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=pathlib.Path,required=True)
parser.add_argument('--name',required=True)
args=parser.parse_args();W=args.workspace.resolve(strict=True);A=W.parents[1];R=A.parent
assert A.name=='Application' and (A/'tools/verify_original_database_export.py').is_file(),'OWN_KNOWN_WORKSPACE_REQUIRED'
assert re.fullmatch(r'own-mysql-r[1-9][0-9]{1,3}',args.name) and args.name!='own-mysql-r26','OWN_FRESH_CLONE_NAME_REQUIRED'
base=W/'own-mysql-r26';root=W/args.name;runtime=W/'mysql-8.0.46-original-restore-runtime_20261024'
assert not root.exists(),'OWN_FRESH_ROOT_REQUIRED'
prior=json.loads((W/'own-j3/receipt.json').read_bytes());assert prior['ownMySQLExited'] and prior['ownMySQLExitCode']==0
restore=json.loads((base/'receipt.json').read_bytes());baseline=base/'restored-verification-export'
original=json.loads((R/'Document/Deployment/real_original_restore_20261024/full_original_restore_roundtrip.json').read_bytes());assert original['exportedContentEqual']
sealed=pathlib.Path('//192.168.0.107/Fofme/TianjinReadOnlyExportV2_20261024/exports/export_20261024_104112_f57c50d4')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(baseline/'manifest.json')==restore['targetManifestSHA256']
assert sha(sealed/'manifest.json')==original['sourceManifestSHA256']
for item in json.loads((sealed/'manifest.json').read_bytes())['files']:
 assert item['name'] in ('catalog.json','jnpf.rows.jsonl.gz','tj_endanger.rows.jsonl.gz')
 assert (sealed/item['name']).is_file() and (sealed/item['name']).stat().st_size==item['bytes']
meta=json.loads((W/'own-mysql-r13/fixture_compile.json').read_bytes());jdk=pathlib.Path(meta['javaHome'])
cp=[str(base/'classes'),str(W/'own-dbboot-r5/classes')]+[meta[k] for k in ('boundaryJar','exporterJar','yamlJar','mysqlConnectorJar')]+meta['additionalClasspath']
for k in ('boundaryJar','exporterJar','yamlJar','mysqlConnectorJar'):assert digest(pathlib.Path(meta[k]))==meta[k+'SHA256']
assert digest(runtime/'bin/mysqld.exe')=='47ffd2c32f36e5cb79f78bed0ff5272d7559c383f88c43c753470d5a5dfbe8a0'
files=sorted(p for p in (base/'data').rglob('*') if p.is_file());size=sum(p.stat().st_size for p in files)
assert size<800*1024**2 and shutil.disk_usage(W).free>32*1024**3
for p in [base/'data',*(base/'data').rglob('*')]:assert not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400
root.mkdir();(root/'tmp').mkdir();(root/'classes').mkdir()
receipt={'startedAt':datetime.datetime.now().astimezone().isoformat(),'sourceDatabaseConnected':False,'copiedOriginalMachinePhysicalDatabase':False,'coldRestoreFromOwnedVerifiedDatabase':True,'copyBytesBudget':size,'estimatedTemporaryPeakBytes':size+128*1024**2,'freeDBefore':shutil.disk_usage(W).free,'fullCloneReady':False}
def save(name,obj):(root/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save('attempt_started.json',receipt)
lock=(base/'own-joint-controller.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
server=None;log_handle=None;started=time.monotonic();copied={}
env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};env['TEMP']=env['TMP']=str(root/'tmp');flags=subprocess.CREATE_NO_WINDOW
def run_java(main,*args,timeout=330):
 return subprocess.run([str(jdk/'bin/java.exe'),'-Xmx256m','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-Duser.home='+str(root/'tmp'),'-cp',os.pathsep.join([str(root/'classes'),*cp]),main,*map(str,args)],cwd=root,env=env,capture_output=True,creationflags=flags,timeout=timeout)
try:
 print('COPY_OWN_STOPPED_DATABASE_WITH_SHA_VERIFICATION',flush=True)
 for p in files:
  before=p.stat();relative=p.relative_to(base/'data');pin=digest(p);target=root/'data'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  assert digest(target)==pin and p.stat().st_mtime_ns==before.st_mtime_ns and p.stat().st_size==before.st_size
  copied[relative.as_posix()]={'sha256':pin,'bytes':before.st_size}
 save('cold-copy-manifest.json',copied)
 # Preserve the copied identity file outside datadir; this clone gets its own UUID.
 (root/'data/auto.cnf').replace(root/'copied-original-auto.cnf')
 (root/'own-initialization-complete.txt').write_text('Cold-restored verified stopped own database; see cold-copy-manifest.json\n',encoding='ascii')
 (root/'baseline-catalog.json').write_bytes((baseline/'catalog.json').read_bytes())
 source=pathlib.Path(__file__).parent/'java/OwnedWritableRestoreProbe.java'
 build=subprocess.run([str(jdk/'bin/javac.exe'),'-proc:none','--release','17','-encoding','UTF-8','-cp',os.pathsep.join(cp),'-d',str(root/'classes'),str(source)],cwd=root,env=env,capture_output=True,creationflags=flags,timeout=30)
 (root/'compile.private.log').write_bytes(build.stdout+build.stderr);assert build.returncode==0,'OWN_PROBE_COMPILE_FAILED'
 receipt['probeSourceSHA256']=sha(source)
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 log_handle=(root/'mysql.private.log').open('wb')
 command=[str(runtime/'bin/mysqld.exe'),'--no-defaults','--no-monitor','--basedir='+str(runtime),'--datadir='+str(root/'data'),'--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL','--super-read-only=OFF','--read-only=OFF','--transaction-read-only=OFF','--bind-address=127.0.0.1','--port='+str(port),'--pid-file='+str(root/'own-mysqld.pid'),'--console','--max-connections=8','--skip-slave-start']
 server=subprocess.Popen(command,cwd=root,env=env,stdout=log_handle,stderr=subprocess.STDOUT,creationflags=flags)
 for _ in range(300):
  assert server.poll() is None,'OWN_MYSQL_EXITED'
  if 'ready for connections' in (root/'mysql.private.log').read_text('utf-8',errors='replace'):break
  time.sleep(.1)
 else:raise RuntimeError('OWN_MYSQL_READY_TIMEOUT')
 assert int((root/'own-mysqld.pid').read_text().strip())==server.pid
 own_uuid=re.search(r'^server-uuid=(.+)$',(root/'data/auto.cnf').read_text('ascii'),re.M).group(1).strip();assert own_uuid!=restore['ownServerUUID']
 save('own-server-process.json',{'pid':server.pid,'port':port,'host':'127.0.0.1','serverUUID':own_uuid})
 old=dict(line.split('=',1) for line in (base/'own-connection.properties').read_text('ascii').splitlines())
 (root/'own-connection.properties').write_text('port='+str(port)+'\npassword='+old['password']+'\nserverUUID='+own_uuid+'\n',encoding='ascii')
 receipt.update(ownServerUUID=own_uuid,ownServerPID=server.pid)
 print('OWN_WRITABLE_UUID_VERIFIED_READY_FOR_PROBE',flush=True)
 probe=run_java('xnby.export.OwnedWritableRestoreProbe',root);(root/'probe.private.log').write_bytes(probe.stdout+probe.stderr);receipt['probeExitCode']=probe.returncode
 assert probe.returncode==0,'OWN_WRITABLE_PROBE_FAILED'
 receipt['writeProbe']=json.loads((root/'writable-probe-receipt.json').read_bytes())
 print('DURABLE_WRITE_RESTORED_COMPARE_ALL_ORIGINAL_ROWS',flush=True)
 sys.path.insert(0,str(A/'tools'));import verify_original_database_export as verify,compare_original_database_exports as compare
 target=root/'verification-export';pins=[original['sourceManifestSHA256'],receipt['writeProbe']['targetManifestSHA256']];roots=[sealed,target]
 stamps=[compare.input_stamp(p) for p in roots];reports=[verify.verify(p,pin) for p,pin in zip(roots,pins)]
 catalogs=[json.loads((p/'catalog.json').read_bytes()) for p in roots]
 assert compare.metadata_entries(catalogs[0])==compare.metadata_entries(catalogs[1]),'OWN_METADATA_DIFFERENCE'
 assert compare.context_entries(catalogs[0])==compare.context_entries(catalogs[1]),'OWN_EXPORT_CONTEXT_DIFFERENCE'
 counts=[{(x['schema'],x['table']):(x['rows'],x['rowStreamSHA256']) for x in r['tableCounts']} for r in reports];assert counts[0]==counts[1] and len(counts[0])==398
 comparisons=[]
 for schema in ('jnpf','tj_endanger'):
  h=hashlib.sha256();total=0
  with gzip.open(sealed/(schema+'.rows.jsonl.gz'),'rb') as left,gzip.open(target/(schema+'.rows.jsonl.gz'),'rb') as right:
   while True:
    x,y=left.read(1024**2),right.read(1024**2);assert x==y,'OWN_RAW_ROW_DIFFERENCE'
    if not x:break
    h.update(x);total+=len(x);assert time.monotonic()-started<900
  comparisons.append({'schema':schema,'bytes':total,'sha256':h.hexdigest(),'exactUncompressedBytesEqual':True})
 for p,pin,stamp in zip(roots,pins,stamps):compare.recheck(p,pin,stamp,time.monotonic()+120)
 for name,row in copied.items():assert digest(base/'data'/name)==row['sha256'],'OWN_BASE_DATABASE_CHANGED'
 receipt.update(passed=True,rows=reports[0]['rows'],tables=398,allMetadataEqual=True,allTableRowCountsAndHashesEqual=True,exactUncompressedRowStreamsEqual=True,streamComparisons=comparisons,ownedBaselineAllFilesUnchanged=True)
except Exception:
 (root/'controller-failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');receipt['passed']=False;print('OWN_TRIAL_FAILED_PRIVATE_DETAILS_RETAINED',flush=True)
finally:
 if server is not None and server.poll() is None:
  try:
   stop=run_java('xnby.export.OwnedRestoredServerShutdown',root,root,timeout=30);(root/'shutdown.private.log').write_bytes(stop.stdout+stop.stderr);receipt['shutdownJVMExitCode']=stop.returncode
   server.wait(timeout=30)
  except Exception:
   (root/'shutdown-failure.private.log').write_text(traceback.format_exc(),encoding='utf-8')
   if server.poll() is None:server.terminate();server.wait(timeout=15);receipt['ownServerTerminated']=True
 if log_handle:log_handle.close()
 receipt.update(completedAt=datetime.datetime.now().astimezone().isoformat(),ownServerExited=server is None or server.poll() is not None,ownServerExitCode=server.returncode if server else None,freeDAfter=shutil.disk_usage(W).free,fullCloneReady=False)
 save('receipt.json',receipt);lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
 print(json.dumps({k:receipt.get(k) for k in ('passed','rows','tables','ownServerExitCode','shutdownJVMExitCode','fullCloneReady')}),flush=True)
sys.exit(0 if receipt.get('passed') and receipt.get('ownServerExitCode')==0 else 1)
