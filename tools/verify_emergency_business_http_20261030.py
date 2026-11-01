"""Original HTTP save/reopen + actual mapper transactions on owner-only TEMP tables and private MinIO."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,socket,subprocess,sys,time,urllib.request,uuid
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/event_delivery_consistency_20261030';D=R/'Document/Deployment/event_delivery_consistency_20261030';Q=Path('D:/Zqa20261025/Application');PW=R/'work/emergency_plan_report_20261030';sys.path.insert(0,str(T));sys.path.insert(0,str(Q/'tools'))
from verify_plan_report_local_state_20261030 import current
from verify_confirmed_operation_preservation import protected
from run_original_inventory_ownership_probe import state
from verify_original_work_reservation_sql import run
from original_server_windows_job import OwnedWindowsJob
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True);a=parser.parse_args();assert a.revision.startswith('r') and a.revision[1:].isdigit();root=W/('emergency-business-http-'+a.revision);assert not root.exists();root.mkdir();(root/'tmp').mkdir();(root/'classes').mkdir();(root/'service-classes').mkdir();before=current();held=protected();db=state();assert before['currentBS']=='j68' and before['controllerPID']==35972;meta=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');java=Path(meta['java']);assert sha(java)==meta['javaSHA256'];live=Path(db['run'])/'b/classes';pins={'com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class':'384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b','com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class':'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece'}
 for name,value in pins.items():
  assert sha(live/name)==value;dest=root/'service-classes'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((live/name).read_bytes())
 jar=PW/'local-update-emergency-modules-r1/payload/tools/task-identity/business.jar';cm=read(W/'emergency-modules-components-r1/components-manifest.json');assert sha(jar)==cm['componentJarSHA256'] and sha(PW/'local-update-emergency-modules-r1/update-manifest.json')=='7bc362447f681a604fcc5c3ef696b702b47960baab8982e8de87888b76e554cf';cp=str(root/'classes')+';'+str(root/'service-classes')+';'+str(jar)+';'+meta['classpath'];sources=[T/'java/OriginalEmergencyBusinessHttpFixture.java',T/'java/OriginalPlanReportSqlFixture.java',T/'java/OriginalEmergencyExerciseSqlFixture.java',T/'java/OriginalSocketProcessBoundary.java',T/'java/OriginalEventReportSchemaCompatibility.java'];controls=root/'control-sources';controls.mkdir()
 for source in [*sources,Path(__file__)]: (controls/source.name).write_bytes(source.read_bytes())
 dump(root/'source-pins.json',{str(p):sha(p) for p in [*sources,Path(__file__),jar]});run(root,'compile',[java.with_name('javac.exe'),'-J-Xmx256m','-encoding','UTF-8','-parameters','-proc:none','-cp',cp,'-d',root/'classes',*sources],45);store=root/'store';store.mkdir();certs=root/'certs';certs.mkdir();store_port,console_port=port(),port();assert store_port!=console_port;credentials={'access':'OWN'+uuid.uuid4().hex[:16].upper(),'secret':'OWN'+uuid.uuid4().hex+uuid.uuid4().hex};process=None;job=None;output=open(root/'minio-owned.log','wb')
 try:
  env={k:v for k,v in os.environ.items() if k.upper() not in ('MINIO_ROOT_USER','MINIO_ROOT_PASSWORD','MINIO_ACCESS_KEY','MINIO_SECRET_KEY')};env.update(MINIO_ROOT_USER=credentials['access'],MINIO_ROOT_PASSWORD=credentials['secret'],MINIO_BROWSER='off',MINIO_UPDATE='off',MINIO_CALLHOME_ENABLE='off',GOMAXPROCS='2',TMP=str(root/'tmp'),TEMP=str(root/'tmp'));process=subprocess.Popen([str(Q/'runtime/minio/minio.exe'),'--quiet','--certs-dir',str(certs),'server','--address','127.0.0.1:'+str(store_port),'--console-address','127.0.0.1:'+str(console_port),str(store)],cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=OwnedWindowsJob(process);dump(root/'own-store-started.json',{'pid':process.pid,'dataRoot':str(store),'port':store_port,'syntheticOnly':True});opener=urllib.request.build_opener(urllib.request.ProxyHandler({}));deadline=time.monotonic()+30
  while True:
   assert process.poll() is None,'OWN_STORE_EXITED'
   try:
    with opener.open('http://127.0.0.1:'+str(store_port)+'/minio/health/live',timeout=1) as reply:
     if reply.status==200:break
   except OSError:pass
   assert time.monotonic()<deadline,'OWN_STORE_TIMEOUT';time.sleep(.1)
  credentials['databasePassword']=read(Q/'private/server-configuration.json')['seedRootPassword'];encoded=json.dumps(credentials).encode()
  try:run(root,'execute',[java,'-Xmx256m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-Down.boundary.trace=true','-cp',cp,'xnby.replica.OriginalEmergencyBusinessHttpFixture',str(db['databasePort']),db['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),str(store_port),'xnby-http-sql-'+uuid.uuid4().hex[:16],str(root)],120,encoded)
  finally:credentials.pop('databasePassword',None);del encoded
 finally:
  if job:job.close()
  if process is not None and process.poll() is None:process.wait(timeout=10)
  output.close();credentials.clear();dump(root/'own-store-stopped.json',{'pid':None if process is None else process.pid,'exitCode':None if process is None else process.returncode,'jobClosed':job is not None,'productionStoreChanged':False})
 report=read(root/'result.json');assert len(report['cases'])==12 and report['temporaryTablesDropped'] and report['permanentDDLUnchanged'] and report['connectionAndTemporaryTableIdentityCheckedBeforeEveryMapperStatement'];assert current()==before and protected()==held and not(PW/'lifecycle-emergency-modules-r1').exists();result={'at':datetime.datetime.now().astimezone().isoformat(),'previousStageClassification':'progress','stageClassification':'progress','actualOriginalControllerSqlAndFileCases':len(report['cases']),'only14ConnectionPrivateTemporaryTablesWritten':True,'permanentBusinessRowsSnapshotRead':False,'permanentDDLUnchanged':True,'actualCurrentServiceClassPins':pins,'candidate72ComponentJarUsed':True,'syntheticIdentity':True,'normalUserRoleOrRestartDurabilityAccepted':False,'currentBSSceneAndFixedPackagesPreserved':True,'runtimeInstalled':False,'publicChanged':False,'fullCloneReady':False};dump(D/('emergency-business-http-'+a.revision+'.json'),result);dump(root/'stage-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
