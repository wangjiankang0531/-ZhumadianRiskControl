"""One bounded, read-only shared-resource trial of both original backends."""
import argparse,datetime,hashlib,http.client,json,msvcrt,os,pathlib,re,secrets,socket,subprocess,sys,time,traceback,urllib.parse,uuid,zipfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=pathlib.Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--previous-receipt',type=pathlib.Path,required=True)
args=parser.parse_args();assert re.fullmatch(r'own-j[1-9][0-9]{0,3}',args.name),'OWN_EXPLICIT_RUN_NAME_REQUIRED'
P=pathlib.Path(__file__).parent;W=args.workspace.resolve(strict=True);A=W.parents[1];R=A.parent
assert A.name=='Application' and (A/'tools/reference_flat_runtime.py').is_file(),'OWN_KNOWN_APPLICATION_WORKSPACE_REQUIRED'
previous=json.loads(args.previous_receipt.read_bytes())
assert previous['ownMySQLExited'] and previous['ownMySQLExitCode']==0 and previous['ownRedisExited'] and previous['ownRedisExitCode']==0
assert previous['ownBusinessExited'] and previous['ownPlatformExited']
root=W/args.name;assert not root.exists();root.mkdir();platform_root=root/'p';business_root=root/'b'
for folder in (platform_root,business_root):
 folder.mkdir()
 for name in ('tmp','home','files','logs','classes'):(folder/name).mkdir()
assert len(str(business_root/'tmp'))<=80 and len(str(platform_root/'tmp'))<=80,'OWN_JDK_UNIX_SOCKET_TEMP_PATH_TOO_LONG'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
meta=json.loads((W/'own-pboot-r27/preparation.json').read_bytes());java17=pathlib.Path(meta['javaHome']);java8=pathlib.Path(meta['platformJavaHome'])
dbroot=W/'own-mysql-r26';mysql_home=W/'mysql-8.0.46-original-restore-runtime_20261024';mysql_exe=mysql_home/'bin/mysqld.exe'
rowmeta=json.loads((W/'own-mysql-r13/fixture_compile.json').read_bytes());flat=W/'original-shared-runtime-r1_20261024/flat'
dbspec=json.loads((dbroot/'receipt.json').read_bytes());dbconf=dict(line.split('=',1) for line in (dbroot/'own-connection.properties').read_text('ascii').splitlines())
assert dbconf['serverUUID']==dbspec['ownServerUUID']=='c0a47e62-cf57-11f1-9120-10ffe0e39b19'
for previous in ('own-pboot-r27','own-dbboot-r5'):
 receipt=json.loads((W/previous/'receipt.json').read_bytes());assert receipt['ownMySQLExited'] and receipt['ownMySQLExitCode']==0 and receipt['ownRedisExited'] and receipt['ownRedisExitCode']==0
wire=json.loads((W/'own-original-redis-wire-cli-r1/receipt.json').read_bytes());assert wire['passed'] and wire['originalSerializationCompatibilityVerified']
sys.path.insert(0,str(A/'tools'));import reference_flat_runtime,prepare_original_shared_redis
reference_flat_runtime.verify(flat)
assert digest(mysql_exe)=='47ffd2c32f36e5cb79f78bed0ff5272d7559c383f88c43c753470d5a5dfbe8a0'
assert digest(pathlib.Path(meta['sourceArchive']))==meta['sourceJarSHA256']
assert sha(pathlib.Path(meta['guardJar']))==meta['guardJarSHA256'] and sha(pathlib.Path(rowmeta['boundaryJar']))==rowmeta['boundaryJarSHA256']
assert sha(pathlib.Path(meta['bootstrapParentJar']))==meta['bootstrapParentJarSHA256']
for name,pin in meta['platformRuntimePins'].items():assert digest(java8/name)==pin
for row in meta['compileDependencies']:assert sha(pathlib.Path(row['file']))==row['sha256']
for name,pin in meta['preflightRelevantClassesSHA256'].items():assert sha(W/'own-pboot-r27'/name)==pin
schedule_spec=json.loads((W/'original-scheduling-isolation-fixture-r2_20261024/receipt.json').read_bytes());schedule=pathlib.Path(schedule_spec['packagedGuardJar']['path']);assert sha(schedule)==schedule_spec['packagedGuardJar']['sha256']
with zipfile.ZipFile(flat/'application.jar') as archive:
 manifest=archive.read('META-INF/MANIFEST.MF').decode('utf-8').replace('\r\n ','').replace('\n ','')
 paths=next(line[len('Class-Path: '):] for line in manifest.splitlines() if line.startswith('Class-Path: ')).split()
deps=[]
for uri in paths:
 path=urllib.parse.unquote(urllib.parse.urlsplit(uri).path)
 if re.match(r'^/[A-Za-z]:',path):path=path[1:]
 deps.append(pathlib.Path(path) if uri.startswith('file:') else flat/path)
assert len(deps)==219
for directory in ('wrapper-classes','builder-classes'):
 for old in (W/'own-pboot-r27'/directory).rglob('*'):
  if old.is_file():
   target=platform_root/directory/old.relative_to(W/'own-pboot-r27'/directory);target.parent.mkdir(parents=True,exist_ok=True);os.link(old,target)
env={key:value for key,value in os.environ.items() if key.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH') and not key.upper().startswith('LOADER_')}
env['TMP']=env['TEMP']=str(root/'tmp');(root/'tmp').mkdir();flags=subprocess.CREATE_NO_WINDOW
observer=P/'java/OriginalJointRedisObservation.java'
for target,classpath in [(platform_root,[pathlib.Path(row['file']) for row in meta['compileDependencies']]),(business_root,[flat/'application.jar',*deps])]:
 run=subprocess.run([str(java17/'bin/javac.exe'),'-proc:none','--release','8','-encoding','UTF-8','-cp',os.pathsep.join(map(str,classpath)),'-d',str(target/'classes'),str(observer)],cwd=target,env=env,capture_output=True,creationflags=flags,timeout=30)
 (target/'observer-compile.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'OWN_JOINT_OBSERVER_COMPILE_FAILED'
with zipfile.ZipFile(W/'own-pboot-r27/own-platform-observation.jar') as old,zipfile.ZipFile(platform_root/'own-platform-observation.jar','w',zipfile.ZIP_DEFLATED) as new:
 for info in old.infolist():new.writestr(info,old.read(info))
 for path in (platform_root/'classes').rglob('*.class'):new.write(path,path.relative_to(platform_root/'classes').as_posix())
for name in ('expected-current-item-ids.txt','expected-platform-organization-count.txt','expected-database-server-uuid.txt'):
 (business_root/name).write_bytes((W/'own-dbboot-r5'/name).read_bytes())
def port():
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',0));return s.getsockname()[1]
dbport,redisport=port(),port();assert dbport!=redisport
redis_password=secrets.token_urlsafe(32);owner=str(uuid.uuid4());probe_key='__xnby_joint_wire_'+owner
result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'ownerId':owner,'readOnlyOwnedDatabase':True,'oneSharedMySQL':True,'oneSharedRedis':True,
 'runnerSourceSHA256':sha(pathlib.Path(__file__)),'observerSourceSHA256':sha(observer),
 'platformSourceSHA256':meta['sourceJarSHA256'],'businessSourceSHA256':'4c5bcf1bb3f76a3865c0cd6969cfef845934a11343d2987413f33715411dc902',
 'sourceDatabaseConnected':False,'loginOrJwtAttempted':False,'syntheticProbeKeyIsAuthenticationKey':False,'fullCloneReady':False,'publicDeployed':False}
(root/'attempt_started.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
db=redis=platform=business=None;handles=[];lock=(dbroot/'own-joint-controller.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
def start(command,folder,log):
 output=(folder/log).open('wb');handles.append(output);ownenv=dict(env,TMP=str(folder/'tmp'),TEMP=str(folder/'tmp'));return subprocess.Popen(command,cwd=folder,env=ownenv,stdout=output,stderr=subprocess.STDOUT,creationflags=flags)
def resp(stream,*words):
 data=[str(word).encode('ascii') for word in words];stream.write(b'*'+str(len(data)).encode()+b'\r\n'+b''.join(b'$'+str(len(word)).encode()+b'\r\n'+word+b'\r\n' for word in data));stream.flush()
 line=stream.readline();kind,value=line[:1],line[1:-2]
 if kind==b'+':return value.decode('ascii')
 if kind==b':':return int(value)
 if kind==b'-':raise RuntimeError('OWN_REDIS_COMMAND_FAILED')
 if kind==b'$':
  length=int(value);assert 0<=length<=1024**2;body=stream.read(length);assert stream.read(2)==b'\r\n';return body.decode('ascii')
 raise RuntimeError('OWN_REDIS_REPLY_FORMAT')
def session():
 sock=socket.create_connection(('127.0.0.1',redisport),timeout=4);return sock,sock.makefile('rwb')
def read_properties(path):return dict(line.split('=',1) for line in path.read_text('ascii').splitlines() if line and not line.startswith(('#','!')))
def probe_http(port,path):
 connection=http.client.HTTPConnection('127.0.0.1',port,timeout=6)
 try:
  connection.request('GET',path);response=connection.getresponse();raw=response.read(2*1024**2+1);assert len(raw)<=2*1024**2
  code=json.loads(raw).get('code')
  return {'status':response.status,'applicationCode':code,'bodyBytes':len(raw),'bodySHA256':hashlib.sha256(raw).hexdigest(),'authenticated':False}
 finally:connection.close()
try:
 print('START_OWN_SHARED_MYSQL_REDIS',flush=True)
 db=start([str(mysql_exe),'--no-defaults','--no-monitor','--basedir='+str(mysql_home),'--datadir='+str(dbroot/'data'),'--lower-case-table-names=1',
 '--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M',
 '--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL',
 '--super-read-only=ON','--transaction-read-only=ON','--bind-address=127.0.0.1','--port='+str(dbport),'--pid-file='+str(dbroot/'own-mysqld.pid'),'--console','--max-connections=24','--skip-slave-start'],root,'mysql.private.log')
 for _ in range(300):
  assert db.poll() is None,'OWN_MYSQL_EXITED'
  if 'ready for connections' in (root/'mysql.private.log').read_text('utf-8',errors='replace'):break
  time.sleep(.1)
 else:raise RuntimeError('OWN_MYSQL_READY_TIMEOUT')
 assert int((dbroot/'own-mysqld.pid').read_text().strip())==db.pid
 (root/'previous-mysql-owner.json').write_bytes((dbroot/'own-server-process.json').read_bytes())
 (dbroot/'own-server-process.json').write_text(json.dumps({'pid':db.pid,'host':'127.0.0.1','port':dbport,'serverUUID':dbspec['ownServerUUID']}),encoding='utf-8')
 (dbroot/'own-connection.properties').write_text('port='+str(dbport)+'\npassword='+dbconf['password']+'\nserverUUID='+dbspec['ownServerUUID']+'\n',encoding='ascii')
 redis_exe=W/'own-redis-runtime_20261024/redis-server.exe';redis_spec=json.loads((redis_exe.parent/'receipt.json').read_bytes());assert sha(redis_exe)==next(row['sha256'] for row in redis_spec['files'] if row['file']=='redis-server.exe')
 (root/'redis-data').mkdir();redis_conf=root/'redis.private.conf'
 redis_conf.write_text('\n'.join(['bind 127.0.0.1','port '+str(redisport),'protected-mode yes','requirepass '+redis_password,'maxmemory 96mb','maxmemory-policy noeviction','persistence-available no',
 'dir "'+(root/'redis-data').as_posix()+'"','logfile "'+(root/'redis.private.log').as_posix()+'"','loglevel notice'])+'\n',encoding='ascii')
 redis=start([str(redis_exe),str(redis_conf)],root,'redis-process.private.log')
 for _ in range(60):
  assert redis.poll() is None,'OWN_REDIS_EXITED'
  try:
   with socket.create_connection(('127.0.0.1',redisport),timeout=.2):break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('OWN_REDIS_READY_TIMEOUT')
 sock,stream=session()
 with sock,stream:
  assert resp(stream,'AUTH',redis_password)=='OK' and resp(stream,'PING')=='PONG' and resp(stream,'DBSIZE')==0
  info=dict(line.split(':',1) for line in resp(stream,'INFO','server').splitlines() if ':' in line);assert int(info['process_id'])==redis.pid
  assert resp(stream,'CONFIG','SET','save','')=='OK'
 result.update(ownMySQLPID=db.pid,ownRedisPID=redis.pid)
 for side,folder in [('platform',platform_root),('business',business_root)]:
  expected={'side':side,'host':'127.0.0.1','port':str(redisport),'database':'0','password':redis_password,'processId':str(redis.pid),'probeKey':probe_key}
  (folder/'joint-redis-expected.private.properties').write_text('\n'.join(k+'='+v for k,v in expected.items())+'\n',encoding='ascii')
 own={'mysqlPort':str(dbport),'mysqlPassword':dbconf['password'],'mysqlPublicKeyPath':(dbroot/'data/public_key.pem').as_posix(),'redisPort':str(redisport),'redisPassword':redis_password,'ownSecret':secrets.token_hex(16)}
 (platform_root/'own-integration.properties').write_text('\n'.join(k+'='+v for k,v in own.items())+'\n',encoding='ascii')
 (platform_root/'own-logback.xml').write_text('<configuration><appender name="OWN" class="ch.qos.logback.core.ConsoleAppender"><encoder><pattern>%level %logger - %msg%n</pattern></encoder></appender><root level="WARN"><appender-ref ref="OWN"/></root></configuration>',encoding='ascii')
 config_build=subprocess.run([str(java17/'bin/java.exe'),'-Xmx128m','-cp',os.pathsep.join([str(platform_root/'builder-classes'),meta['yamlJar']]),'xnby.platform.OriginalPlatformConfigBuilder',meta['sourceArchive'],str(platform_root)],cwd=platform_root,env=env,capture_output=True,creationflags=flags,timeout=30)
 (platform_root/'builder.private.log').write_bytes(config_build.stdout+config_build.stderr);assert config_build.returncode==0,'OWN_PLATFORM_CONFIG_FAILED'
 base=prepare_original_shared_redis.own_properties(W/'own-dbboot-r5/application.properties')
 base['spring.data.redis.port']=str(redisport);base['spring.data.redis.password']=redis_password
 base['context.initializer.classes']='xnby.replica.OriginalSourceDataObservation,xnby.replica.OriginalJointRedisObservation'
 for name,schema in [('master','tj_endanger'),('tow','jnpf')]:
  prefix='spring.datasource.dynamic.datasource.'+name+'.';base[prefix+'password']=dbconf['password']
  base[prefix+'url']='jdbc:mysql://127.0.0.1:'+str(dbport)+'/'+schema+'?useSSL=false&allowPublicKeyRetrieval=true&autoReconnect=false&allowMultiQueries=false&serverTimezone=UTC&characterEncoding=UTF-8&sessionVariables=transaction_read_only=1'
 (business_root/'application.properties').write_text('\n'.join(key+'='+value for key,value in base.items())+'\n',encoding='ascii')
 connection=root/'own-redis-connection.private.json';connection.write_text(json.dumps({'schema':'zhumadian.original.joint-redis.v1','ownerId':owner,'host':'127.0.0.1','port':redisport,'database':0,'password':redis_password}),encoding='ascii')
 prepare_original_shared_redis.prepare(root/'overlays',business_root/'application.properties',platform_root/'application.properties',connection)
 # Each process may write only its own directory, so duplicate just four owned connection properties.
 for side,folder in [('platform',platform_root),('business',business_root)]:
  (folder/'redis-overlay.private.properties').write_bytes((root/'overlays'/(side+'-redis.properties')).read_bytes())
  (folder/'own-process-only.policy').write_text('grant { permission java.security.AllPermission; };\n',encoding='ascii')
 platform_config=prepare_original_shared_redis.own_properties(platform_root/'application.properties')
 platform_config['context.initializer.classes']='xnby.platform.PlatformStartupObservation,xnby.replica.OriginalJointRedisObservation'
 (platform_root/'application.properties').write_text('\n'.join(key+'='+value for key,value in platform_config.items())+'\n',encoding='ascii')
 print('START_TWO_ORIGINAL_APPLICATIONS_ON_SHARED_RESOURCES',flush=True)
 for side,folder in [('business',business_root),('platform',platform_root)]:
  common=['-Xmx512m','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(folder/'tmp'),'-Duser.home='+str(folder/'home'),
   '-Djdk.net.unixdomain.tmpdir='+str(folder/'tmp'),'-Djava.security.policy=='+(folder/'own-process-only.policy').as_uri(),
   '-Down.allowed.loopback.ports='+str(dbport)+','+str(redisport),'-Down.joint.root='+str(folder),
   '-Dspring.config.location='+(folder/'application.properties').as_uri()+','+(folder/'redis-overlay.private.properties').as_uri()]
  if side=='business':
   args=common+['-Down.direct.main=true','-Down.startup.observation='+str(folder/'startup-observation.txt'),'-Down.startup.bean.definitions='+str(folder/'startup-bean-definitions.tsv'),'-Down.startup.lifecycle.directory='+str(folder),
    '-cp',os.pathsep.join(map(str,[folder/'classes',W/'own-dbboot-r5/classes',pathlib.Path(rowmeta['boundaryJar']),schedule,flat/'application.jar',*deps])),
    'xnby.replica.OriginalIsolatedLaunch',str(folder)]
   argfile=folder/'java-arguments.private.txt';argfile.write_text('\n'.join('"'+a.replace('\\','\\\\').replace('"','\\"')+'"' for a in args)+'\n',encoding='utf-8')
   business=start([str(java17/'bin/java.exe'),'@'+str(argfile)],folder,'startup.private.log');result['ownBusinessPID']=business.pid
  else:
   args=common+['-Djava.awt.headless=true','-Down.platform.root='+str(folder),'-Down.platform.cached.resources=true','-Down.platform.source.path='+meta['sourceArchive'],
    '-Down.platform.independent.jar.wrappers=true','-Djava.protocol.handler.pkgs=xnby.platform.protocol','-Dlogging.config='+(folder/'own-logback.xml').as_uri(),
    '-Dspring.cloud.bootstrap.enabled=false','-Dspring.profiles.active=own-platform-isolation','-cp',os.pathsep.join([meta['bootstrapParentJar'],str(folder/'wrapper-classes'),meta['guardJar']]),
    'xnby.platform.OriginalPlatformLaunch',meta['sourceArchive'],str(folder)]
   platform=start([str(java8/'bin/java.exe'),*args],folder,'startup.private.log');result['ownPlatformPID']=platform.pid
 start_at=time.monotonic();last=-30
 while True:
  assert db.poll() is None and redis.poll() is None,'OWN_SHARED_DEPENDENCY_EXITED'
  if time.monotonic()-start_at-last>=30:
   print(json.dumps({'phase':'joint_original_startup','seconds':round(time.monotonic()-start_at),'businessAlive':business.poll() is None,'platformAlive':platform.poll() is None,
    'businessReady':(business_root/'own-application-ready.txt').exists(),'platformReady':(platform_root/'own-platform-ready.txt').exists()}),flush=True);last=time.monotonic()-start_at
  files=[platform_root/'joint-redis-observation.properties',business_root/'joint-redis-observation.properties']
  if all(path.exists() for path in files):break
  if business.poll() is not None or platform.poll() is not None:raise RuntimeError('OWN_ORIGINAL_APPLICATION_EXITED')
  if time.monotonic()-start_at>150:raise RuntimeError('OWN_JOINT_OBSERVATION_TIMEOUT')
  time.sleep(.2)
 observations={side:read_properties(folder/'joint-redis-observation.properties') for side,folder in [('platform',platform_root),('business',business_root)]}
 result['jointRedisObservations']=observations
 assert all(value.get('passed')=='true' for value in observations.values()),'OWN_JOINT_REDIS_OBSERVATION_FAILED'
 assert observations['platform']['actualRedisProcessId']==observations['business']['actualRedisProcessId']==str(redis.pid)
 assert observations['business']['originalBusinessReadFieldsMatched']=='6' and observations['business']['syntheticKeyDeleted']=='true'
 readonly=(business_root/'original-read-service-results.tsv').read_text('utf-8').splitlines();assert len(readonly)==11 and all(line.endswith('\tPASS') for line in readonly)
 result['originalReadOnlyServiceChecks']=readonly
 platform_port=int((platform_root/'own-platform-http-port.txt').read_text());business_port=int((business_root/'own-http-port.txt').read_text())
 result['platformAnonymousConfig']=probe_http(platform_port,'/api/oauth/getLoginConfig');assert result['platformAnonymousConfig']['applicationCode']==200
 result['platformAnonymousCurrentUser']=probe_http(platform_port,'/api/oauth/CurrentUser?systemCode=safety')
 result['businessAnonymousPage']=probe_http(business_port,'/checkItems/page?current=1&size=10')
 result['jointOriginalRedisReadWriteVerified']=True;result['originalApplicationReadyEventsObserved']=True
 result['platformOriginalMainReturned']=(platform_root/'original-platform-main-returned.txt').exists()
 result['authenticatedBusinessVerified']=False
 print('JOINT_ORIGINAL_REDIS_ROUNDTRIP_VERIFIED',flush=True)
except Exception:
 (root/'controller-failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');result['failed']=True
 print('OWN_JOINT_TRIAL_FAILED_DETAILS_RETAINED',flush=True)
finally:
 for folder,process,name in [(business_root,business,'business'),(platform_root,platform,'platform')]:
  if process is not None and process.poll() is None:(folder/'own-stop-requested.txt').write_text('finish-owned-joint-readonly-trial\n',encoding='ascii')
 deadline=time.monotonic()+20
 while time.monotonic()<deadline and any(process is not None and process.poll() is None for process in (business,platform)):time.sleep(.2)
 for process,name in [(business,'Business'),(platform,'Platform')]:
  if process is not None and process.poll() is None:process.terminate();process.wait(timeout=15);result['own'+name+'Terminated']=True
  result['own'+name+'Exited']=process is None or process.poll() is not None;result['own'+name+'ExitCode']=process.returncode if process else None
 if redis is not None and redis.poll() is None:
  try:
   sock,stream=session()
   with sock,stream:
    assert resp(stream,'AUTH',redis_password)=='OK';stream.write(b'*2\r\n$8\r\nSHUTDOWN\r\n$6\r\nNOSAVE\r\n');stream.flush()
  except OSError:pass
  try:redis.wait(timeout=8)
  except subprocess.TimeoutExpired:redis.terminate();redis.wait(timeout=10);result['ownRedisTerminated']=True
 if db is not None and db.poll() is None:
  cp=[str(W/'own-dbboot-r5/classes'),str(dbroot/'classes')]+[rowmeta[k] for k in ('exporterJar','yamlJar','mysqlConnectorJar')]+rowmeta['additionalClasspath']
  stop=subprocess.run([str(java17/'bin/java.exe'),'-Xmx128m','-cp',os.pathsep.join(cp),'xnby.export.OwnedRestoredServerShutdown',str(dbroot),str(root)],cwd=root,env=env,capture_output=True,creationflags=flags,timeout=30)
  (root/'mysql-shutdown.private.log').write_bytes(stop.stdout+stop.stderr);result['mysqlShutdownJVMExitCode']=stop.returncode
  try:db.wait(timeout=30)
  except subprocess.TimeoutExpired:db.terminate();db.wait(timeout=10);result['ownMySQLTerminated']=True
 for handle in handles:handle.close()
 result.update(completedAt=datetime.datetime.now().astimezone().isoformat(),ownRedisExited=redis is None or redis.poll() is not None,ownRedisExitCode=redis.returncode if redis else None,
  ownMySQLExited=db is None or db.poll() is not None,ownMySQLExitCode=db.returncode if db else None,
  businessContextClosed=(business_root/'own-context-closed.txt').exists(),platformContextClosed=(platform_root/'own-platform-context-closed.txt').exists(),
  fullCloneReady=False,authenticatedBusinessVerified=False,sourceDatabaseConnected=False)
 (root/'receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8');lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1);lock.close()
 print(json.dumps({key:result.get(key) for key in ('jointOriginalRedisReadWriteVerified','failed','ownBusinessExitCode','ownPlatformExitCode','ownRedisExitCode','ownMySQLExitCode','fullCloneReady')}),flush=True)
