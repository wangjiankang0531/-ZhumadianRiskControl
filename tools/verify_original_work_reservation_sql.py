"""Bounded original/candidate SQL verification using only connection-local tables.

Reads the existing test installation identity; no real login, restart, permanent
write, original environment access or public deployment. Credentials enter Java
only through stdin and are never included in arguments or evidence output.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run_original_inventory_ownership_probe import state
from original_server_windows_job import OwnedWindowsJob
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application')
PRIOR=R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json'
BUNDLE=R/'work/work_reservation_end_time_update_20261028'
CLASS='payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
RELEASE='3f1ee528b0e2107da4aead4359786fdaf2d87cc7b43214d0822eca9a46c344cd'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,value):
    assert not p.exists(),'FRESH_EVIDENCE_REQUIRED'
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(root,tag,command,seconds,secret=None):
    assert not (root/(tag+'-started.json')).exists(),'SINGLE_START_PER_REVISION'
    env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'))
    p=subprocess.Popen(list(map(str,command)),env=env,cwd=root,stdin=subprocess.PIPE if secret else subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    dump(root/(tag+'-started.json'),{'pid':p.pid,'maximumSeconds':seconds})
    timed=False;job=None
    try:
        job=OwnedWindowsJob(p)
        try:out,err=p.communicate(secret,timeout=seconds)
        except subprocess.TimeoutExpired:timed=True;job.close();out,err=p.communicate(timeout=10)
    finally:
        if job:job.close()
        if p.poll() is None:p.kill();p.wait(timeout=5)
    assert secret is None or secret not in out and secret not in err,'SECRET_OUTPUT_REFUSED'
    (root/(tag+'.stdout.log')).write_bytes(out);(root/(tag+'.stderr.log')).write_bytes(err)
    dump(root/(tag+'-process.json'),{'exitCode':p.returncode,'timedOut':timed})
    if p.returncode or timed:raise RuntimeError(tag+': '+err.decode('utf-8',errors='replace')[-2200:])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--candidate-evidence',type=Path,required=True);a=p.parse_args()
    root=a.output.absolute();assert not root.exists() and root.parent.is_dir()
    assert sha(Q/'release-manifest.json')==RELEASE
    current=state();assert current['controllerPID']==35292 and Path(current['run']).name=='j41'
    prior=read(PRIOR)
    for path,pin in prior['inputPins'].items():assert sha(path)==pin['SHA256'],'PINNED_ORIGINAL_DEPENDENCY_DRIFT'
    java=Path(prior['java']);assert sha(java)==prior['javaSHA256']
    candidate_report=read(a.candidate_evidence/'result.json')
    assert candidate_report['candidateEditRollbackForExceptionDeclared'] and candidate_report['exactEndTimeAndEditTransactionDifferenceVerified']
    candidate=a.candidate_evidence/'candidate-classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
    assert sha(candidate)==candidate_report['candidateClassSHA256']
    root.mkdir();(root/'classes').mkdir();(root/'tmp').mkdir()
    sources=[HERE/'java/OriginalWorkReservationEndTimeFixture.java',HERE/'java/OriginalWorkReservationSqlFixture.java']
    (root/'candidate-classes/com/iemp/endanger/server/work/service/impl').mkdir(parents=True)
    copied=root/'candidate-classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class';copied.write_bytes(candidate.read_bytes());assert sha(copied)==sha(candidate)
    config=Path(current['run'])/'b/application.properties'
    prepared={'at':datetime.datetime.now().astimezone().isoformat(),'sourcePins':{str(x):sha(x) for x in sources+[Path(__file__)]},'dependencyPins':prior['inputPins'],'javaSHA256':sha(java),'candidateClassSHA256':sha(candidate),'controllerPID':current['controllerPID'],'databaseUUID':current['databaseUUID'],'databasePort':current['databasePort'],'stateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'configurationSHA256':sha(config),'releaseSHA256':RELEASE,'maximumConnections':2,'maximumSQLCaseProcessSeconds':80,'permanentDMLOrDDLAllowed':False,'authenticationOrHttpAllowed':False,'runtimeRestartAllowed':False}
    dump(root/'prepared.private.json',prepared)
    run(root,'compile',[java.with_name('javac.exe'),'-J-Xmx192m','-encoding','UTF-8','-proc:none','-cp',prior['classpath'],'-d',root/'classes',*sources],40)
    compiled={str(x.relative_to(root/'classes')):sha(x) for x in (root/'classes').rglob('*.class')};dump(root/'class-pins.json',compiled)
    reports={}
    for mode in ('original','candidate'):
        assert sha(Q/'release-manifest.json')==RELEASE and sha(config)==prepared['configurationSHA256']
        now=state();assert now['controllerPID']==current['controllerPID'] and now['databaseUUID']==current['databaseUUID'] and now['databasePort']==current['databasePort']
        folder=root/mode;folder.mkdir();cp=[str(root/'classes')]
        if mode=='candidate':cp.append(str(root/'candidate-classes'))
        cp.append(prior['classpath'])
        secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
        try:
            run(root,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',';'.join(cp),'xnby.replica.OriginalWorkReservationSqlFixture',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),mode,folder/'result.private.json'],80,secret)
        finally:del secret
        report=read(folder/'result.private.json');assert len(report['cases'])==(11 if mode=='candidate' else 10) and report['permanentRowsAndSchemasUnchanged'] and report['temporaryTablesDropped']
        reports[mode]=report
    assert reports['candidate']['loadedServiceClassSHA256']==sha(candidate)
    assert reports['original']['formalBefore']==reports['original']['formalAfter']==reports['candidate']['formalBefore']==reports['candidate']['formalAfter']
    assert state()['controllerPID']==current['controllerPID'] and sha(Q/'release-manifest.json')==RELEASE
    assert reports['candidate']['serviceMethodHasTransactionAttribute'] and not reports['original']['serviceMethodHasTransactionAttribute']
    result={'at':datetime.datetime.now().astimezone().isoformat(),'originalSQLCases':10,'candidateSQLCases':11,'eightTypedEndTimeWritesActuallyVerified':True,'directUnproxiedFailurePartialStateCharacterized':True,'explicitFixtureTransactionRollbackVerified':True,'candidateAnnotationDrivenSpringRollbackVerified':True,'permanentTenTableRowsAndSchemasUnchanged':True,'temporaryTablesDropped':True,'candidateLoadedBytesVerified':True,'candidateClassSHA256':sha(candidate),'serviceMethodTransactionAttributes':{mode:r['serviceMethodHasTransactionAttribute'] for mode,r in reports.items()},'runtimeOrDatabaseBusinessRowsChanged':False,'realAuthenticationOrHttpUsed':False,'productionTransactionAccepted':False,'candidateInstalled':False,'fullCloneReady':False}
    dump(root/'result.json',result);print(json.dumps(result))

if __name__=='__main__':main()
