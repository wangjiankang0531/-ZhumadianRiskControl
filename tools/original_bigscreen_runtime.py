"""Bounded unchanged original bigscreen backend on an owned 12 KiB SQLite copy."""
import datetime,hashlib,json,os,pathlib,secrets,subprocess,time,zipfile

ARCHIVE_SHA256='97c2f1662a3a4494f01da4c2e83d7fa960e6832bda870e90424ffbaddf667cca'
DATABASE_SHA256='f35972a2fb79e41d076b0031ee77546664cc335ab0ce8ad83ff199e2c241cb8a'
NATIVE_SHA256='b0c53ebfcddc4031daad36aac9a2967921703431deba5e51234da5008ae45b2a'
HELPER_SHA256='799d1289e3122b0e73ef4b6a3c9639bc5c59d820c7670800c673a1b7acd5a508'
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def properties(path):return dict(line.split('=',1) for line in pathlib.Path(path).read_text('ascii').splitlines() if line and not line.startswith(('#','!')))

def compile_wrappers(root,jdk,helper,archive,deps,sources,env,native,lifecycle_proof=None):
  cp=os.pathsep.join(map(str,[helper,archive,*sorted(deps.glob('*.jar'))]));compile=subprocess.run([str(jdk/'bin/javac.exe'),'-proc:none','-source','1.8','-target','1.8','-encoding','UTF-8','-cp',cp,'-d',str(root/'classes'),*map(str,sources)],cwd=root,env=env,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW);(root/'compile.private.log').write_bytes(compile.stdout+compile.stderr);assert compile.returncode==0,'ORIGINAL_BIGSCREEN_WRAPPER_COMPILE_FAILED'
  class_pins={file.relative_to(root/'classes').as_posix():sha(file) for file in (root/'classes').rglob('*.class')}
  lifecycle_prefix='xnby/replica/CandidateLifecycleObservation'
  for rel,pin in class_pins.items():
   expected=lifecycle_proof['compiledLifecycleClassesSHA256'].get(rel) if lifecycle_proof and rel.startswith(lifecycle_prefix) else sha(native/'classes'/rel)
   assert expected==pin,'KNOWN_EXECUTED_WRAPPER_CLASS_REQUIRED'
  if lifecycle_proof:
   assert {rel:pin for rel,pin in class_pins.items() if rel.startswith(lifecycle_prefix)}==lifecycle_proof['compiledLifecycleClassesSHA256'],'EXACT_VERIFIED_LIFECYCLE_CLASS_SET_REQUIRED'

  return class_pins

class OriginalBigscreen:
 def __init__(self,workspace,output,minutes=30,lifecycle_receipt=None,lifecycle_sha256=None):
  self.workspace=pathlib.Path(workspace).resolve(strict=True);self.root=pathlib.Path(output).resolve();assert self.root.is_relative_to(self.workspace) and not self.root.exists();assert 1<=minutes<=60
  from prepare_original_bigscreen_lifecycle import select as select_lifecycle
  self.lifecycle_proof=select_lifecycle(self.workspace,lifecycle_receipt,lifecycle_sha256)
  self.lifecycle_sha256=lifecycle_sha256
  self.tools=pathlib.Path(__file__).parent;self.minutes=minutes;self.process=None;self.log=None;self.result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'originalApplicationStarted':False,'referenceDatabaseOpenedWritable':False,'realVideoQueryOrControlAttempted':False,'forcedTermination':False,'fullCloneReady':False}
 def start(self):
  W=self.workspace;root=self.root;native=W/'own-bigscreen-native-cli-r1';meta=json.loads((native/'preparation.json').read_bytes());proof=json.loads((native/'receipt.json').read_bytes());assert proof['passedChecks']==13 and proof['ownExitCode']==0
  self.archive=pathlib.Path(meta['sourceArchive']);self.reference=pathlib.Path(meta['referenceDatabase']);helper=pathlib.Path(meta['helperJar']);jdk=pathlib.Path(meta['javaHome']);deps=pathlib.Path(meta['dependencyRoot']);assert deps.is_relative_to(W)
  assert sha(self.archive)==ARCHIVE_SHA256 and sha(self.reference)==DATABASE_SHA256 and sha(helper)==HELPER_SHA256 and sha(native/'native/sqlitejdbc.dll')==NATIVE_SHA256
  java_pins=json.loads((W/'own-pboot-r32/preparation.json').read_bytes())
  assert jdk.resolve()==pathlib.Path(java_pins['platformJavaHome']).resolve()
  for name,pin in java_pins['platformRuntimePins'].items():assert sha(jdk/name)==pin
  sources=[self.tools/'java'/name for name in ('OriginalBigscreenProcessBoundary.java','OriginalBigscreenLaunch.java','OriginalBigscreenObservation.java','CandidateLifecycleObservation.java')]
  for source in sources:
   expected=self.lifecycle_proof['lifecycleSourceSHA256'] if self.lifecycle_proof and source.name=='CandidateLifecycleObservation.java' else meta['sourceSHA256'][source.name]
   assert sha(source)==expected,'KNOWN_BIGSCREEN_WRAPPER_SOURCE_REQUIRED'
  root.mkdir()
  for name in ('native','data','classes','tmp','home'):(root/name).mkdir()
  (root/'native/sqlitejdbc.dll').write_bytes((native/'native/sqlitejdbc.dll').read_bytes());(root/'data/working.db').write_bytes(self.reference.read_bytes());assert sha(root/'data/working.db')==DATABASE_SHA256
  self.env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};self.env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'))
  class_pins=compile_wrappers(root,jdk,helper,self.archive,deps,sources,self.env,native,self.lifecycle_proof)
  if self.lifecycle_proof:
   self.result['lifecycleCompatibility']={'receiptSHA256':self.lifecycle_sha256,'checks':self.lifecycle_proof['checks'],'eventConstructorArity':self.lifecycle_proof['eventConstructorArity'],'oldNativeReceiptModified':False,'nativeFixtureReexecuted':False}
  with zipfile.ZipFile(root/'own-launcher.jar','w',zipfile.ZIP_DEFLATED) as launch,zipfile.ZipFile(root/'own-observation.jar','w',zipfile.ZIP_DEFLATED) as observation:
   for file in (root/'classes').rglob('*.class'):
    target=launch if file.name.startswith(('OriginalBigscreenLaunch','OriginalBigscreenProcessBoundary')) else observation;target.write(file,file.relative_to(root/'classes').as_posix())
  (root/'own-logback.xml').write_text('<configuration><appender name="OWN" class="ch.qos.logback.core.ConsoleAppender"><encoder><pattern>%level %logger - %msg%n</pattern></encoder></appender><root level="WARN"><appender-ref ref="OWN"/></root></configuration>',encoding='ascii')
  settings={'file.encoding':'UTF-8','java.io.tmpdir':str(root/'tmp'),'user.home':str(root/'home'),'org.sqlite.lib.path':str(root/'native'),'org.sqlite.lib.name':'sqlitejdbc.dll','org.sqlite.tmpdir':str(root/'tmp'),'server.address':'127.0.0.1','server.port':'0','server.ssl.enabled':'false','sqlite.file':str(root/'data/working.db'),'hkinfo.app-host':'127.0.0.1:9','hkinfo.app-key':'own-'+secrets.token_hex(8),'hkinfo.app-secret':'own-'+secrets.token_hex(16),'spring.cloud.bootstrap.enabled':'false','spring.cloud.nacos.config.enabled':'false','spring.cloud.nacos.discovery.enabled':'false','spring.jmx.enabled':'false','management.server.port':'-1','management.endpoints.enabled-by-default':'false','spring.devtools.restart.enabled':'false','spring.main.banner-mode':'off','logging.config':(root/'own-logback.xml').as_uri(),'logback.configurationFile':str(root/'own-logback.xml'),'own.boundary.trace':'true','own.candidate.root':str(root),'own.candidate.maximum-seconds':str(self.minutes*60),'context.initializer.classes':'xnby.bigscreen.OriginalBigscreenObservation,xnby.replica.CandidateLifecycleObservation'}
  command=[str(jdk/'bin/java.exe'),'-Xmx256m',*['-D'+key+'='+value for key,value in settings.items()],'-cp',os.pathsep.join(map(str,[self.archive,root/'own-launcher.jar',helper])),'xnby.bigscreen.OriginalBigscreenLaunch',str(self.archive),str(root)]
  self.log=(root/'startup.private.log').open('wb');self.process=subprocess.Popen(command,cwd=root,env=self.env,stdout=self.log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);self.result.update(originalApplicationStarted=True,ownPID=self.process.pid,ownClasses=class_pins,sourceArchiveSHA256=ARCHIVE_SHA256,referenceDatabaseSHA256=DATABASE_SHA256)
  (root/'attempt_started.json').write_text(json.dumps(self.result,indent=2)+'\n',encoding='utf-8');end=time.monotonic()+90
  while not all((root/n).exists() for n in ('candidate-ready.txt','candidate-http-port.txt','original-main-returned.txt','original-bigscreen-observation.properties')):
   assert self.process.poll() is None,'ORIGINAL_BIGSCREEN_EXITED_BEFORE_READY';assert time.monotonic()<end,'ORIGINAL_BIGSCREEN_READY_TIMEOUT';time.sleep(.2)
  observed=properties(root/'original-bigscreen-observation.properties');assert observed.get('passed')=='true' and observed['originalSurveyRows']=='4' and observed['originalServletContextPath']==''
  self.port=int((root/'candidate-http-port.txt').read_text());self.result.update(readyAt=datetime.datetime.now().astimezone().isoformat(),ownPort=self.port,originalObservation=observed,originalMainReturned=True,leaseMinutes=self.minutes);(root/'ready.json').write_text(json.dumps(self.result,indent=2)+'\n',encoding='utf-8');return self.port
 def close(self):
  if self.process is not None and self.process.poll() is None:
   (self.root/'own-stop-requested.txt').write_text('normal-stop-owned-bigscreen\n',encoding='ascii')
   try:self.process.wait(timeout=18)
   except subprocess.TimeoutExpired:self.process.terminate();self.process.wait(timeout=10);self.result['forcedTermination']=True
  if self.log is not None:self.log.close()
  self.result.update(completedAt=datetime.datetime.now().astimezone().isoformat(),ownExitCode=self.process.returncode if self.process else None,contextClosed=(self.root/'candidate-context-closed.txt').exists(),referenceDatabaseUnchanged=sha(self.reference)==DATABASE_SHA256 if hasattr(self,'reference') else None,sourceArchiveUnchanged=sha(self.archive)==ARCHIVE_SHA256 if hasattr(self,'archive') else None)
  if (self.root/'boundary-result.properties').exists():self.result['boundaryAfterClose']=properties(self.root/'boundary-result.properties')
  if self.root.exists():(self.root/'receipt.json').write_text(json.dumps(self.result,indent=2)+'\n',encoding='utf-8')
  return self.result
