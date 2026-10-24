"""Bounded original frontend/backend integration on one owned writable clone."""
import argparse,datetime,hashlib,http.client,json,msvcrt,os,pathlib,re,secrets,socket,subprocess,sys,threading,time,traceback,urllib.parse,uuid,zipfile
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=pathlib.Path,required=True)
parser.add_argument('--name',required=True)
parser.add_argument('--previous-receipt',type=pathlib.Path,required=True)
parser.add_argument('--gateway-port',type=int,default=18891)
parser.add_argument('--minutes',type=int,default=60)
parser.add_argument('--original-business-config',type=pathlib.Path)
parser.add_argument('--original-business-config-sha256')
parser.add_argument('--object-store-provider-receipt',type=pathlib.Path)
parser.add_argument('--object-store-provider-receipt-sha256')
args=parser.parse_args();assert 1<=args.minutes<=120 and 1024<=args.gateway_port<=65535,'OWN_EXPLICIT_CANDIDATE_LEASE_AND_PORT'
assert re.fullmatch(r'own-j[1-9][0-9]{0,3}',args.name),'OWN_EXPLICIT_RUN_NAME_REQUIRED'
from original_candidate_platform_gate import require_semantics_pair,wait_for_platform,allowed_ports
semantics_requested=require_semantics_pair(args.original_business_config,args.original_business_config_sha256)
store_requested=require_semantics_pair(args.object_store_provider_receipt,args.object_store_provider_receipt_sha256)
if store_requested and not semantics_requested:raise ValueError('OWN_OBJECT_STORE_REQUIRES_ORIGINAL_BUSINESS_SEMANTICS')
if store_requested:
 from original_object_store_runtime import OwnedObjectStore
if semantics_requested:
 assert args.original_business_config.is_file() and args.original_business_config.stat().st_size<=65536,'OWN_ORIGINAL_BUSINESS_CONFIG_REQUIRED'
 assert hashlib.sha256(args.original_business_config.read_bytes()).hexdigest()==args.original_business_config_sha256,'OWN_ORIGINAL_BUSINESS_CONFIG_PIN_MISMATCH'
P=pathlib.Path(__file__).parent;W=args.workspace.resolve(strict=True);A=W.parents[1];R=A.parent
assert A.name=='Application' and (A/'tools/reference_flat_runtime.py').is_file(),'OWN_KNOWN_APPLICATION_WORKSPACE_REQUIRED'
previous=json.loads(args.previous_receipt.read_bytes())
assert previous['ownMySQLExited'] and previous['ownMySQLExitCode']==0 and previous['ownRedisExited'] and previous['ownRedisExitCode']==0
assert previous['ownBusinessExited'] and previous['ownPlatformExited']
if previous.get('objectStoreRequested'):
 assert previous.get('ownObjectStoreExited') and previous.get('ownObjectStoreExitCode')==0 and not previous.get('ownObjectStoreTerminated'),'PREVIOUS_OWN_OBJECT_STORE_MUST_HAVE_CLOSED_NORMALLY'
root=W/args.name;assert not root.exists();root.mkdir();platform_root=root/'p';business_root=root/'b'
(root/'controller-source.py').write_bytes(pathlib.Path(__file__).read_bytes())
for folder in (platform_root,business_root):
 folder.mkdir()
 for name in ('tmp','home','files','logs','classes'):(folder/name).mkdir()
assert len(str(business_root/'tmp'))<=80 and len(str(platform_root/'tmp'))<=80,'OWN_JDK_UNIX_SOCKET_TEMP_PATH_TOO_LONG'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
meta=json.loads((W/'own-pboot-r32/preparation.json').read_bytes());java17=pathlib.Path(meta['javaHome']);java8=pathlib.Path(meta['platformJavaHome'])
dbroot=W/'own-mysql-r27';mysql_home=W/'mysql-8.0.46-original-restore-runtime_20261024';mysql_exe=mysql_home/'bin/mysqld.exe'
rowmeta=json.loads((W/'own-mysql-r13/fixture_compile.json').read_bytes());flat=W/'original-shared-runtime-r1_20261024/flat'
dbspec=json.loads((dbroot/'receipt.json').read_bytes());dbconf=dict(line.split('=',1) for line in (dbroot/'own-connection.properties').read_text('ascii').splitlines())
assert dbconf['serverUUID']==dbspec['ownServerUUID']=='c4ae2011-cf86-11f1-9da8-10ffe0e39b19'
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
for name,pin in meta['preflightRelevantClassesSHA256'].items():assert sha(W/'own-pboot-r32'/name)==pin
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
 for old in (W/'own-pboot-r32'/directory).rglob('*'):
  if old.is_file():
   target=platform_root/directory/old.relative_to(W/'own-pboot-r32'/directory);target.parent.mkdir(parents=True,exist_ok=True);os.link(old,target)
env={key:value for key,value in os.environ.items() if key.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH') and not key.upper().startswith('LOADER_')}
env['TMP']=env['TEMP']=str(root/'tmp');(root/'tmp').mkdir();flags=subprocess.CREATE_NO_WINDOW
observer=P/'java/OriginalJointRedisObservation.java'
for target,classpath in [(platform_root,[pathlib.Path(row['file']) for row in meta['compileDependencies']]),(business_root,[flat/'application.jar',pathlib.Path(rowmeta['boundaryJar']),*deps])]:
 run=subprocess.run([str(java17/'bin/javac.exe'),'-proc:none','--release','8','-encoding','UTF-8','-cp',os.pathsep.join(map(str,classpath)),'-d',str(target/'classes'),str(observer),str(P/'java/CandidateLifecycleObservation.java'),*([str(P/'java/OriginalWritableServiceObservation.java')]+([str(P/'java/OriginalInternalPlatformObservation.java'),str(P/'java/OriginalBusinessLaunch.java')] if semantics_requested else [])+([str(P/'java/OriginalObjectStoreObservation.java')] if store_requested else []) if target==business_root else [])],cwd=target,env=env,capture_output=True,creationflags=flags,timeout=30)
 (target/'observer-compile.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'OWN_JOINT_OBSERVER_COMPILE_FAILED'
with zipfile.ZipFile(W/'own-pboot-r32/own-platform-observation.jar') as old,zipfile.ZipFile(platform_root/'own-platform-observation.jar','w',zipfile.ZIP_DEFLATED) as new:
 for info in old.infolist():new.writestr(info,old.read(info))
 for path in (platform_root/'classes').rglob('*.class'):new.write(path,path.relative_to(platform_root/'classes').as_posix())
for name in ('expected-current-item-ids.txt','expected-platform-organization-count.txt','expected-database-server-uuid.txt'):
 (business_root/name).write_bytes((W/'own-dbboot-r5'/name).read_bytes())
def port():
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',0));return s.getsockname()[1]
dbport,redisport=port(),port();assert dbport!=redisport
redis_password=secrets.token_urlsafe(32);owner=str(uuid.uuid4());probe_key='__xnby_joint_wire_'+owner
result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'ownerId':owner,'readOnlyOwnedDatabase':False,'oneSharedMySQL':True,'oneSharedRedis':True,
 'runnerSourceSHA256':sha(pathlib.Path(__file__)),'observerSourceSHA256':sha(observer),
 'platformSourceSHA256':meta['sourceJarSHA256'],'businessSourceSHA256':'4c5bcf1bb3f76a3865c0cd6969cfef845934a11343d2987413f33715411dc902',
 'sourceDatabaseConnected':False,'loginOrJwtAttempted':False,'syntheticProbeKeyIsAuthenticationKey':False,'fullCloneReady':False,'publicDeployed':False,
 'originalBusinessSemanticsRequested':semantics_requested,'originalBusinessConfigSHA256':args.original_business_config_sha256 if semantics_requested else None,
 'ownedBusinessLauncherClass':'xnby.replica.OriginalBusinessLaunch' if semantics_requested else 'xnby.replica.OriginalIsolatedLaunch',
 'ownedBusinessLauncherSourceSHA256':sha(P/'java/OriginalBusinessLaunch.java') if semantics_requested else None}
result['objectStoreRequested']=store_requested
(root/'attempt_started.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
object_store=None;object_probe_cleaned=False
db=redis=platform=business=nginx=None;archive_server=archive_worker=None;handles=[];lock=(dbroot/'own-joint-controller.lock').open('a+b');lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
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
 if store_requested:
  print('START_OWN_PERSISTENT_OBJECT_STORE',flush=True)
  object_store=OwnedObjectStore(W,root/'s',args.object_store_provider_receipt,args.object_store_provider_receipt_sha256);object_store.start()
  result['objectStoreRuntime']=dict(object_store.result)
 print('START_OWN_SHARED_MYSQL_REDIS',flush=True)
 db=start([str(mysql_exe),'--no-defaults','--no-monitor','--basedir='+str(mysql_home),'--datadir='+str(dbroot/'data'),'--lower-case-table-names=1',
 '--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M',
 '--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL',
 '--super-read-only=OFF','--read-only=OFF','--transaction-read-only=OFF','--bind-address=127.0.0.1','--port='+str(dbport),'--pid-file='+str(dbroot/'own-mysqld.pid'),'--console','--max-connections=24','--skip-slave-start'],root,'mysql.private.log')
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
 base['context.initializer.classes']='xnby.replica.OriginalStartupObservation,xnby.replica.CandidateLifecycleObservation,xnby.replica.OriginalWritableServiceObservation,xnby.replica.OriginalJointRedisObservation'+(',xnby.replica.OriginalInternalPlatformObservation' if semantics_requested else '')+(',xnby.replica.OriginalObjectStoreObservation' if store_requested else '')
 base['logging.level.root']='WARN'
 for name,schema in [('master','tj_endanger'),('tow','jnpf')]:
  prefix='spring.datasource.dynamic.datasource.'+name+'.';base[prefix+'password']=dbconf['password']
  base[prefix+'url']='jdbc:mysql://127.0.0.1:'+str(dbport)+'/'+schema+'?useSSL=false&allowPublicKeyRetrieval=true&autoReconnect=false&allowMultiQueries=false&serverTimezone=UTC&characterEncoding=UTF-8&sessionVariables=transaction_read_only=0'
  base[prefix+'hikari.is-read-only']='false'
 (business_root/'application.properties').write_text('\n'.join(key+'='+value for key,value in base.items())+'\n',encoding='ascii')
 connection=root/'own-redis-connection.private.json';connection.write_text(json.dumps({'schema':'zhumadian.original.joint-redis.v1','ownerId':owner,'host':'127.0.0.1','port':redisport,'database':0,'password':redis_password}),encoding='ascii')
 prepare_original_shared_redis.prepare(root/'overlays',business_root/'application.properties',platform_root/'application.properties',connection)
 # Each process may write only its own directory, so duplicate just four owned connection properties.
 for side,folder in [('platform',platform_root),('business',business_root)]:
  (folder/'redis-overlay.private.properties').write_bytes((root/'overlays'/(side+'-redis.properties')).read_bytes())
  (folder/'own-process-only.policy').write_text('grant { permission java.security.AllPermission; };\n',encoding='ascii')
 platform_config=prepare_original_shared_redis.own_properties(platform_root/'application.properties')
 platform_config['context.initializer.classes']='xnby.platform.PlatformStartupObservation,xnby.platform.PlatformWritableObservation,xnby.platform.OriginalIdGeneratorShutdown,xnby.platform.OriginalBootstrapOrphanGuard,xnby.replica.CandidateLifecycleObservation,xnby.replica.OriginalJointRedisObservation'
 (platform_root/'application.properties').write_text('\n'.join(key+'='+value for key,value in platform_config.items())+'\n',encoding='ascii')
 print('START_TWO_ORIGINAL_APPLICATIONS_ON_SHARED_RESOURCES',flush=True)
 start_order=[('platform',platform_root),('business',business_root)] if semantics_requested else [('business',business_root),('platform',platform_root)]
 for side,folder in start_order:
  internal_platform_port=None;internal_platform_base=None
  if side=='business' and semantics_requested:
   print('WAIT_FOR_OWN_PLATFORM_ORIGINAL_MAIN_BEFORE_BUSINESS',flush=True)
   internal_platform_port=wait_for_platform(platform_root,platform,[db,redis],progress=lambda:print('OWN_PLATFORM_ORIGINAL_INITIALIZATION_PENDING',flush=True))
   allowed_ports(dbport,redisport,internal_platform_port)
   config_probe=probe_http(internal_platform_port,'/api/oauth/getLoginConfig');assert config_probe['applicationCode']==200,'OWN_PLATFORM_CONFIG_BEFORE_BUSINESS_FAILED'
   assert platform.poll() is None,'OWN_PLATFORM_EXITED_BEFORE_BUSINESS_CONFIGURATION'
   internal_platform_base='http://127.0.0.1:'+str(internal_platform_port)
   diagnostic=folder/'diagnostic-application.private.properties';diagnostic.write_bytes((folder/'application.properties').read_bytes())
   import prepare_original_business_semantics
   semantics=prepare_original_business_semantics.prepare(java17,meta['yamlJar'],'1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b',args.original_business_config,args.original_business_config_sha256,diagnostic,internal_platform_base,folder/'business-semantics')
   assert semantics['originalSemanticKeysCopied']==20 and not semantics['originalCredentialsCopied'],'OWN_ORIGINAL_BUSINESS_SEMANTICS_FAILED'
   (folder/'application.properties').write_bytes((folder/'business-semantics/application.private.properties').read_bytes())
   result['originalBusinessSemanticsPreparation']=semantics;result['businessPlatformPortPermitted']=True
   print('ORIGINAL_BUSINESS_SEMANTICS_APPLIED_TO_NEW_BUSINESS_PROCESS_ONLY',flush=True)
   if store_requested:
    assert object_store.process.poll() is None,'OWN_STORE_EXITED_BEFORE_BUSINESS'
    connection=folder/'object-store-connection.private.properties';object_store.write_private_connection(connection)
    import prepare_original_object_store
    store_overlay=prepare_original_object_store.prepare(java17,meta['yamlJar'],'1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b',args.original_business_config,args.original_business_config_sha256,folder/'application.properties',connection,folder/'object-store-overlay')
    (folder/'application.properties').write_bytes((folder/'object-store-overlay/application.private.properties').read_bytes())
    result['objectStoreOverlayPreparation']=store_overlay
    print('OWN_OBJECT_STORE_APPLIED_TO_NEW_BUSINESS_PROCESS_ONLY',flush=True)
  common=['-Xmx512m','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(folder/'tmp'),'-Duser.home='+str(folder/'home'),
   '-Djdk.net.unixdomain.tmpdir='+str(folder/'tmp'),'-Djava.security.policy=='+(folder/'own-process-only.policy').as_uri(),
   '-Down.allowed.loopback.ports='+allowed_ports(dbport,redisport,internal_platform_port)+(','+str(object_store.port) if side=='business' and store_requested else ''),'-Down.joint.root='+str(folder),'-Down.candidate.root='+str(folder),'-Down.candidate.maximum-seconds='+str(args.minutes*60),'-Down.expected.database.uuid='+dbspec['ownServerUUID'],'-Down.expected.database.port='+str(dbport),
   '-Dspring.config.location='+(folder/'application.properties').as_uri()+','+(folder/'redis-overlay.private.properties').as_uri()]
  if side=='business':
   if internal_platform_base:common+=['-Down.internal.platform.base='+internal_platform_base,'-Down.expected.redis.port='+str(redisport)]
   if store_requested:common+=['-Down.internal.object-store.base=http://127.0.0.1:'+str(object_store.port),'-Down.object-store.probe.owner='+owner]
   java_args=common+['-Down.direct.main=true','-Down.startup.observation='+str(folder/'startup-observation.txt'),'-Down.startup.bean.definitions='+str(folder/'startup-bean-definitions.tsv'),'-Down.startup.lifecycle.directory='+str(folder),
    '-cp',os.pathsep.join(map(str,[folder/'classes',W/'own-dbboot-r5/classes',pathlib.Path(rowmeta['boundaryJar']),schedule,flat/'application.jar',*deps])),
    ('xnby.replica.OriginalBusinessLaunch' if semantics_requested else 'xnby.replica.OriginalIsolatedLaunch'),str(folder)]
   argfile=folder/'java-arguments.private.txt';argfile.write_text('\n'.join('"'+a.replace('\\','\\\\').replace('"','\\"')+'"' for a in java_args)+'\n',encoding='utf-8')
   business=start([str(java17/'bin/java.exe'),'@'+str(argfile)],folder,'startup.private.log');result['ownBusinessPID']=business.pid
  else:
   java_args=common+['-Down.platform.manage.id-generator-shutdown=true','-Down.platform.rehydrate-existing-definitions=true','-Djava.awt.headless=true','-Down.platform.root='+str(folder),'-Down.platform.cached.resources=true','-Down.platform.source.path='+meta['sourceArchive'],
    '-Down.platform.independent.jar.wrappers=true','-Djava.protocol.handler.pkgs=xnby.platform.protocol','-Dlogging.config='+(folder/'own-logback.xml').as_uri(),
    '-Dspring.cloud.bootstrap.enabled=false','-Dspring.profiles.active=own-platform-isolation','-cp',os.pathsep.join([meta['bootstrapParentJar'],str(folder/'wrapper-classes'),meta['guardJar']]),
    'xnby.platform.OriginalPlatformLaunch',meta['sourceArchive'],str(folder)]
   platform=start([str(java8/'bin/java.exe'),*java_args],folder,'startup.private.log');result['ownPlatformPID']=platform.pid
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
 writable=read_properties(business_root/'original-writable-service-observation.properties');assert writable.get('passed')=='true','OWN_WRITABLE_SERVICE_OBSERVATION_FAILED'
 result['originalWritableServiceObservation']=writable
 if semantics_requested:
  observation=business_root/'internal-platform-observation.properties';limit=time.monotonic()+30
  while not observation.exists():
   assert all(process.poll() is None for process in (db,redis,platform,business)),'OWN_PROCESS_EXITED_DURING_INTERNAL_HTTP_CHECK'
   assert time.monotonic()<limit,'OWN_BUSINESS_INTERNAL_PLATFORM_TIMEOUT'
   time.sleep(.2)
  internal=read_properties(observation);result['businessInternalPlatformObservation']=internal
  assert internal.get('passed')=='true' and internal.get('originalBeanBusinessBindingsMatched')=='14' and internal.get('businessProcessAnonymousPlatformHTTPVerified')=='true','OWN_BUSINESS_INTERNAL_PLATFORM_CHECK_FAILED'
  result['originalBusinessSemanticsAppliedToNewProcess']=True
  print('ORIGINAL_BUSINESS_BINDINGS_AND_ANONYMOUS_INTERNAL_HTTP_VERIFIED',flush=True)
 platform_port=int((platform_root/'own-platform-http-port.txt').read_text());business_port=int((business_root/'own-http-port.txt').read_text())
 result['platformAnonymousConfig']=probe_http(platform_port,'/api/oauth/getLoginConfig');assert result['platformAnonymousConfig']['applicationCode']==200
 result['platformAnonymousCurrentUser']=probe_http(platform_port,'/api/oauth/CurrentUser?systemCode=safety')
 result['businessAnonymousPage']=probe_http(business_port,'/checkItems/page?current=1&size=10')
 result['jointOriginalRedisReadWriteVerified']=True;result['originalApplicationReadyEventsObserved']=True
 result['platformOriginalMainReturned']=(platform_root/'original-platform-main-returned.txt').exists()
 result['authenticatedBusinessVerified']=False
 print('JOINT_ORIGINAL_REDIS_ROUNDTRIP_VERIFIED',flush=True)
 bootstrap_wait=time.monotonic()+60
 while not (platform_root/'original-platform-main-returned.txt').exists():
  assert platform.poll() is None and business.poll() is None,'OWN_ORIGINAL_APPLICATION_EXITED_BEFORE_BOOTSTRAP'
  if (platform_root/'bootstrap-rehydration-observation.properties').exists():
   boot=read_properties(platform_root/'bootstrap-rehydration-observation.properties')
   assert not boot.get('failureClass'),'OWN_ORIGINAL_BOOTSTRAP_FAILED'
  assert time.monotonic()<bootstrap_wait,'OWN_ORIGINAL_BOOTSTRAP_TIMEOUT'
  time.sleep(.2)
 boot=read_properties(platform_root/'bootstrap-rehydration-observation.properties')
 assert boot.get('originalBootstrapMethodCompleted')=='true' and boot.get('outsideBootstrapCriticalFieldsSignaturePreserved')=='true','OWN_ORIGINAL_BOOTSTRAP_PARITY_FAILED'
 result['bootstrapRehydration']=boot;result['platformOriginalMainReturned']=True
 import readonly_original_static_archive,adapt_original_admin_archive,prepare_original_frontend_gateway
 archive=pathlib.Path('//192.168.0.107/Fofme/TJZY/home/tool/nginx/www/ap/dist_new.tar.gz')
 original_admin,archive_receipt=readonly_original_static_archive.load_archive(archive,'f64765343660b98322554a800f05ff8b76da14c92e3729d7f01ff2d9f85a3b08')
 admin_files,admin_recipe=adapt_original_admin_archive.adapt_admin_files(original_admin,'/zhumadian/admin',pathlib.Path('D:/Program Files/nodejs/node.exe'),W/'security_pc/node_modules/@babel/parser/lib/index.js')
 archive_server=readonly_original_static_archive.ArchiveServer(admin_files,mount_prefix='/zhumadian/admin');archive_worker=threading.Thread(target=archive_server.serve_forever,daemon=True);archive_worker.start()
 oldroots=json.loads((W/'original-home-map-gateway-r3/unavailable/receipt.json').read_bytes())['roots'];roots={name:pathlib.Path(value) for name,value in oldroots.items()};roots['security_pc']=W/'original-admin-home-deployment-r1/dist'
 nginx_runtime=W/'local-gateway-runtime_20261024/nginx-1.31.8';gateway=root/'gw'
 gate=prepare_original_frontend_gateway.prepare(gateway,nginx_runtime,roots,args.gateway_port,business_port,platform_port,'/zhumadian',archive_server.server_port)
 assert gate['nginxExecutableSHA256']=='c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44'
 (gateway/'tmp').mkdir()
 config=gateway/'nginx.conf';text=config.read_text('utf-8');text=text.replace("log_format without_query '$request_method $uri $status';","log_format without_query '$request_method $status';");config.write_text(text,encoding='utf-8')
 gate.update(configSHA256=sha(config),interactiveRequestPathsAndQueriesNotLogged=True)
 (gateway/'receipt.json').write_text(json.dumps(gate,indent=2),encoding='utf-8')
 check=subprocess.run([str(nginx_runtime/'nginx.exe'),'-p',str(gateway)+'/', '-c',str(config),'-t'],cwd=gateway,env=env,capture_output=True,creationflags=flags,timeout=10);(gateway/'config-check.log').write_bytes(check.stdout+check.stderr);assert check.returncode==0,'OWN_GATEWAY_CONFIGURATION_FAILED'
 nginx=start([str(nginx_runtime/'nginx.exe'),'-p',str(gateway)+'/', '-c',str(config)],gateway,'nginx-process.log')
 for _ in range(60):
  assert nginx.poll() is None,'OWN_GATEWAY_EXITED'
  try:
   with socket.create_connection(('127.0.0.1',args.gateway_port),timeout=.2):break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('OWN_GATEWAY_READY_TIMEOUT')
 assert int((gateway/'nginx.pid').read_text().strip())==nginx.pid
 entry='http://127.0.0.1:'+str(args.gateway_port)
 for path in ('/zhumadian/home','/zhumadian/h5/','/zhumadian/admin/'):
  connection=http.client.HTTPConnection('127.0.0.1',args.gateway_port,timeout=8);connection.request('GET',path);response=connection.getresponse();raw=response.read(4*1024**2);assert response.status==200 and b'<html' in raw.lower(),'OWN_ORIGINAL_FRONTEND_ENTRY_FAILED';connection.close()
 if store_requested:
  observation=business_root/'object-store-observation.private.properties';limit=time.monotonic()+30
  while not observation.exists():
   assert all(process.poll() is None for process in (db,redis,platform,business,nginx,object_store.process)),'OWN_COMPONENT_EXITED_DURING_OBJECT_STORE_CHECK'
   assert time.monotonic()<limit,'OWN_SPRING_OBJECT_STORE_OBSERVATION_TIMEOUT'
   time.sleep(.2)
  observed=read_properties(observation)
  assert observed.get('passed')=='true' and observed.get('originalBeanBindingsMatched')=='6' and observed.get('probeOwner')==owner,'OWN_ORIGINAL_SPRING_OBJECT_STORE_FAILED'
  assert observed['url']=='/sys-file/'+observed['bucket']+'/'+observed['object'],'OWN_SYNTHETIC_FILE_URL_MISMATCH'
  connection=http.client.HTTPConnection('127.0.0.1',args.gateway_port,timeout=8)
  try:
   connection.request('GET','/zhumadian/api/serv'+observed['url']);response=connection.getresponse();raw=response.read(8193)
   assert response.status==200 and len(raw)==int(observed['payloadBytes']) and hashlib.sha256(raw).hexdigest()==observed['payloadSHA256'],'OWN_ORIGINAL_FILE_GATEWAY_BYTES_MISMATCH'
  finally:connection.close()
  result['originalObjectStoreGatewayObservation']={'originalBeanBindingsMatched':6,'originalSpringBeanUploadAndReadbackExact':True,'originalAnonymousDownloadHTTPStatus':200,'gatewayBytes':len(raw),'gatewayBodySHA256':hashlib.sha256(raw).hexdigest(),'authenticatedHTTPUploadVerified':False,'historicalObjectsRecovered':False}
  result['originalObjectStoreGatewayObservation']['probeCleanup']=object_store.cleanup_spring_probe(observed,owner);object_probe_cleaned=True
  print('ORIGINAL_SPRING_FILE_BEAN_AND_GATEWAY_BYTE_READBACK_VERIFIED',flush=True)
 ready_age=max(time.time()-(folder/'candidate-ready.txt').stat().st_mtime for folder in (platform_root,business_root))
 remaining=max(1,args.minutes*60-ready_age-5)
 result['remainingLeaseSeconds']=int(remaining)
 result.update(state='ready-for-original-login',readyAt=datetime.datetime.now().astimezone().isoformat(),gatewayPID=nginx.pid,
  portalURL=entry+'/zhumadian/home',mobileURL=entry+'/zhumadian/h5/',adminURL=entry+'/zhumadian/admin/',
  leaseMinutes=args.minutes,realLoginAttempted=False,authenticatedBusinessVerified=False,originalAdminResourcesCopied=False,sourceArchive=archive_receipt,
  stopFile=str(root/'stop'),legacyDataAnomaliesRemain=True,fullCloneReady=False,publicDeployed=False)
 (root/'ready.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({key:result[key] for key in ('state','portalURL','mobileURL','adminURL','leaseMinutes','fullCloneReady')}),flush=True)
 deadline=time.monotonic()+remaining
 while time.monotonic()<deadline and not (root/'stop').exists():
  assert all(process.poll() is None for process in (db,redis,platform,business,nginx)),'OWN_INTEGRATED_COMPONENT_EXITED'
  assert archive_worker.is_alive(),'OWN_STATIC_COMPONENT_EXITED'
  if store_requested:assert object_store.process.poll() is None,'OWN_OBJECT_STORE_COMPONENT_EXITED'
  time.sleep(.5)
 result['interactiveLeaseFinished']=True

except Exception:
 (root/'controller-failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');result['failed']=True
 print('OWN_JOINT_TRIAL_FAILED_DETAILS_RETAINED',flush=True)
finally:
 if nginx is not None and nginx.poll() is None:
  gateway=root/'gw';nginx_runtime=W/'local-gateway-runtime_20261024/nginx-1.31.8'
  assert int((gateway/'nginx.pid').read_text().strip())==nginx.pid,'OWN_GATEWAY_OWNER_MISMATCH'
  stop=subprocess.run([str(nginx_runtime/'nginx.exe'),'-p',str(gateway)+'/', '-c',str(gateway/'nginx.conf'),'-s','quit'],cwd=gateway,env=env,capture_output=True,creationflags=flags,timeout=10);(gateway/'shutdown.log').write_bytes(stop.stdout+stop.stderr)
  try:nginx.wait(timeout=8)
  except subprocess.TimeoutExpired:nginx.terminate();nginx.wait(timeout=10);result['ownGatewayTerminated']=True
 result['ownGatewayExited']=nginx is None or nginx.poll() is not None;result['ownGatewayExitCode']=nginx.returncode if nginx else None
 if archive_server is not None:
  archive_server.shutdown();archive_server.server_close();archive_worker.join(timeout=3);result['ownAdminStaticStopped']=not archive_worker.is_alive()

 for folder,process,name in [(business_root,business,'business'),(platform_root,platform,'platform')]:
  if process is not None and process.poll() is None:(folder/'own-stop-requested.txt').write_text('finish-owned-joint-readonly-trial\n',encoding='ascii')
 deadline=time.monotonic()+20
 while time.monotonic()<deadline and any(process is not None and process.poll() is None for process in (business,platform)):time.sleep(.2)
 for process,name in [(business,'Business'),(platform,'Platform')]:
  if process is not None and process.poll() is None:process.terminate();process.wait(timeout=15);result['own'+name+'Terminated']=True
  result['own'+name+'Exited']=process is None or process.poll() is not None;result['own'+name+'ExitCode']=process.returncode if process else None
 if object_store is not None:
  if not object_probe_cleaned and object_store.process is not None and object_store.process.poll() is None:
   try:
    observation=business_root/'object-store-observation.private.properties'
    if observation.exists() and read_properties(observation).get('passed')=='true':object_store.cleanup_spring_probe(read_properties(observation),owner);object_probe_cleaned=True
   except Exception as error:result['ownObjectProbeCleanupErrorType']=type(error).__name__
  store_end=object_store.stop();result.update(ownObjectStoreExited=store_end.get('exited',False),ownObjectStoreExitCode=store_end.get('exitCode'),ownObjectStoreTerminated=store_end.get('forcedTermination',False),objectStoreEnd=store_end,ownedSyntheticObjectProbeCleaned=object_probe_cleaned)
 if redis is not None and redis.poll() is None:
  try:
   sock,stream=session()
   with sock,stream:
    assert resp(stream,'AUTH',redis_password)=='OK';stream.write(b'*2\r\n$8\r\nSHUTDOWN\r\n$6\r\nNOSAVE\r\n');stream.flush()
  except OSError:pass
  try:redis.wait(timeout=8)
  except subprocess.TimeoutExpired:redis.terminate();redis.wait(timeout=10);result['ownRedisTerminated']=True
 if db is not None and db.poll() is None:
  cp=[str(W/'own-dbboot-r5/classes'),str(W/'own-mysql-r26/classes'),str(dbroot/'classes')]+[rowmeta[k] for k in ('exporterJar','yamlJar','mysqlConnectorJar')]+rowmeta['additionalClasspath']
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
