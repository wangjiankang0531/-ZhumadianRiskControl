"""Run the actual original/candidate disposal service on two guarded connection-local tables."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,sys,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/event_disposal_atomic_20261029';ROOT=R/'work/event_disposal_atomic_20261029';CLS='com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl';RELEASE='b55043e1f135b4ba7fb97dc56b4d9a2da418bb67f7f76db081745b066cb55006';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from original_event_disposal_atomic_compat import PIN
from verify_original_work_reservation_sql import run
from verify_original_work_safety_batch_sql import resource_pin
from run_original_inventory_ownership_probe import state
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def dump(p,v):assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def scope(text):
 text=re.sub(r'#\d+','#',text.replace('\r\n','\n'));parts=re.split(r'(?m)(?=^  (?:public|private|protected).+;\s*$)',text);return ''.join(p for p in parts if not p.startswith('  public boolean saveRecord('))
def main():
 root=ROOT;assert not (root/'prepared.private.json').exists();initial=read(D/'prepared-source-and-state.json');original=Path(initial['source']);candidate=root/'candidate-src'/(CLS+'.java');fixture=T/'java/OriginalEventDisposalSqlFixture.java';assert sha(original)==PIN and sha(candidate)==initial['candidate']['candidateSourceSHA256'];current=state();assert current['controllerPID']==11344 and Path(current['run']).name=='j57' and sha(Q/'release-manifest.json')==RELEASE
 deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for p,row in deps['inputPins'].items():assert sha(p)==row['SHA256'],'DEPENDENCY_DRIFT'
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];payload=read(Q/'payload-manifest.json');rel='payload/business/application.jar';actualJar=Q/rel;assert sha(actualJar)==payload['files'][rel]['sha256'];assert not (Q/'payload/business/run-template/classes'/(CLS+'.class')).exists() and not (Path(current['run'])/'b/classes'/(CLS+'.class')).exists()
 with zipfile.ZipFile(actualJar) as jar:actualClassBytes=jar.read(CLS+'.class')
 originalClassPin=hashlib.sha256(actualClassBytes).hexdigest();assert originalClassPin==resource_pin(deps['classpath'],CLS+'.class')
 for folder in ['classes','original-classes','reference-classes','candidate-classes']:(root/folder).mkdir()
 copy=root/'original-classes'/(CLS+'.class');copy.parent.mkdir(parents=True);copy.write_bytes(actualClassBytes);sources=[Path(__file__),T/'original_event_disposal_atomic_compat.py',fixture,original,candidate,T/'verify_original_work_reservation_sql.py',T/'original_server_windows_job.py'];prepared={'at':datetime.datetime.now().astimezone().isoformat(),'sourcePins':{str(p):sha(p) for p in sources},'runtimeSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'configurationSHA256':sha(Path(current['run'])/'b/application.properties'),'releaseSHA256':RELEASE,'originalClassSHA256':originalClassPin,'javaSHA256':sha(java),'maximumConnections':2,'maximumSQLSecondsPerMode':90,'permanentWritesDDLAuthenticationHTTPNotificationOrRestartAllowed':False};dump(root/'prepared.private.json',prepared)
 for tag,out,source in [('compile-reference','reference-classes',original),('compile-candidate','candidate-classes',candidate),('compile-fixture','classes',fixture)]:run(root,tag,[java.with_name('javac.exe'),'-J-Xmx192m','-encoding','UTF-8','-proc:none','-cp',deps['classpath'],'-d',root/out,source],45)
 outputs={}
 for mode,cp in [('runtime',deps['classpath']),('reference',str(root/'reference-classes')+';'+deps['classpath']),('candidate',str(root/'candidate-classes')+';'+deps['classpath'])]:
  tag='bytecode-'+mode;run(root,tag,[java.with_name('javap.exe'),'-J-Xmx128m','-J-Dfile.encoding=UTF-8','-p','-c','-s','-classpath',cp,CLS.replace('/','.')],25);outputs[mode]=re.sub(r'#\d+','#',(root/(tag+'.stdout.log')).read_text(encoding='utf-8-sig').replace('\r\n','\n'))
 assert outputs['runtime']==outputs['reference'],'REFERENCE_AND_INSTALLED_CLASS_METHOD_MISMATCH';assert scope(outputs['runtime'])==scope(outputs['candidate']),'NON_TARGET_METHOD_INSTRUCTIONS_CHANGED';dump(root/'bytecode-scope.json',{'runtimeAllMethodInstructionsMatchReference':True,'allMethodsExceptSaveRecordInstructionsAndDescriptorsUnchanged':True})
 pins={p.relative_to(root/'candidate-classes').as_posix():sha(p) for p in (root/'candidate-classes').rglob('*.class')};assert len(pins)==1;dump(root/'class-pins.json',pins);reports={}
 for mode in ['original','candidate']:
  now=state();assert now['controllerPID']==current['controllerPID'] and now['databaseUUID']==current['databaseUUID'] and now['databasePort']==current['databasePort'];assert sha(Q/'UserData/OriginalServer/current-run.json')==prepared['runtimeSHA256'] and sha(Q/'release-manifest.json')==RELEASE
  for p,pin in prepared['sourcePins'].items():assert sha(p)==pin
  folder=root/mode;folder.mkdir();cp=str(root/'classes')+';'+str(root/(mode+'-classes'))+';'+deps['classpath'];secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
  try:run(root,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',cp,'xnby.replica.OriginalEventDisposalSqlFixture',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),mode,folder/'result.private.json'],90,secret)
  finally:del secret
  report=read(folder/'result.private.json');assert len(report['cases'])==11 and report['permanentTwoTableRowsAndDDLUnchanged'] and report['temporaryTablesDropped'] and report['transactionAttribute']==(mode=='candidate');reports[mode]=report
 assert reports['original']['permanentBefore']==reports['original']['permanentAfter']==reports['candidate']['permanentBefore']==reports['candidate']['permanentAfter'];assert reports['original']['loadedClassSHA256']==prepared['originalClassSHA256'] and reports['candidate']['loadedClassSHA256']==pins[CLS+'.class']
 assert state()['controllerPID']==11344 and sha(Q/'release-manifest.json')==RELEASE
 for p,pin in prepared['sourcePins'].items():assert sha(p)==pin
 assert sha(R/'Document/Deployment/public_test_r15_20261029/delivery-manifest.json')==initial['publicR15FixedManifestSHA256'];result={'at':datetime.datetime.now().astimezone().isoformat(),'originalCases':11,'candidateCases':11,'actualOriginalServiceMyBatisAndMySQLExecuted':True,'originalPartialEventStateOnSecondWriteFailureAndZeroReproduced':True,'candidateSpringTransactionExceptionAndBooleanFalseRollbackVerified':True,'realDuplicateKey1062RollbackVerified':True,'alreadyProcessingRealZeroAffectedUpdateAccepted':True,'missingAndBlankParentOrphansRejected':True,'originalExplicitAndDefaultTimeAndAttachmentPayloadPreserved':True,'allOtherMethodInstructionsUnchanged':True,'permanentTwoTableRowsAndDDLUnchanged':True,'temporaryTablesDropped':True,'candidateClassPins':pins,'runtimeInstalledOrRestarted':False,'authenticationHTTPOrNotificationsUsed':False,'fixedR15Unchanged':True,'publicDeployed':False,'fullCloneReady':False};dump(root/'result.json',result);dump(D/'sql-verification.json',result);print(json.dumps(result))
if __name__=='__main__':main()
