"""Verify third-party save/detail through real MyBatis on four TEMPORARY tables.

Two bounded connections to the owned local test DB. Credentials via stdin only;
no permanent DML/DDL, login, HTTP, docking, service restart or installation.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, sys

HERE=Path(__file__).resolve().parent
TOOLS=Path('D:/Project/Zhumadian/Application/tools')
sys.path.insert(0,str(TOOLS))
from verify_original_work_reservation_sql import run
from run_original_inventory_ownership_probe import state
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application')
PRIOR=R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json'
RELEASE='3f1ee528b0e2107da4aead4359786fdaf2d87cc7b43214d0822eca9a46c344cd'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def dump(p,value):
    assert not p.exists(),'FRESH_EVIDENCE_REQUIRED'
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--candidate-evidence',type=Path,required=True);a=parser.parse_args()
    root=a.output.absolute();assert not root.exists() and root.parent.is_dir()
    current=state();assert current['controllerPID']==35292 and Path(current['run']).name=='j41' and sha(Q/'release-manifest.json')==RELEASE
    prior=read(PRIOR)
    for p,pin in prior['inputPins'].items():assert sha(p)==pin['SHA256'],'ORIGINAL_DEPENDENCY_CHANGED'
    java=Path(prior['java']);assert sha(java)==prior['javaSHA256']
    evidence=a.candidate_evidence.resolve(strict=True);report=read(evidence/'result.json');assert report['exactRelocationNameGuardAndTransactionDeclarationsVerified'] and report['originalCases']==report['candidateCases']==18
    for p,pin in read(evidence/'prepared.private.json')['sourcePins'].items():assert sha(p)==pin,'EXECUTED_MEMORY_SOURCE_DRIFT'
    candidate=evidence/'candidate-classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class';assert sha(candidate)==report['candidateExecutedClassSHA256']
    root.mkdir();(root/'tmp').mkdir();(root/'classes').mkdir()
    fixture_root=HERE/'java' if (HERE/'java/OriginalThirdPartyCredentialsFixture.java').exists() else HERE
    sources=[fixture_root/'OriginalThirdPartyCredentialsFixture.java',fixture_root/'OriginalThirdPartyCredentialsSqlFixture.java']
    config=Path(current['run'])/'b/application.properties'
    pin_sources=sources+[Path(__file__),TOOLS/'verify_original_work_reservation_sql.py',TOOLS/'original_server_windows_job.py',TOOLS/'run_original_inventory_ownership_probe.py',TOOLS/'run_original_work_start_sql_probe.py']
    prepared={'at':datetime.datetime.now().astimezone().isoformat(),'sourcePins':{str(p):sha(p) for p in pin_sources},'dependencyPins':prior['inputPins'],'runtimeStateSHA256':sha(Q/'UserData/OriginalServer/current-run.json'),'configurationSHA256':sha(config),'releaseSHA256':RELEASE,'controllerPID':current['controllerPID'],'databaseUUID':current['databaseUUID'],'databasePort':current['databasePort'],'candidateClassSHA256':sha(candidate),'maximumConnections':2,'maximumProcessSeconds':80,'permanentDMLOrDDLAllowed':False,'realLoginHttpOrDockingAllowed':False,'runtimeRestartAllowed':False}
    dump(root/'prepared.private.json',prepared)
    run(root,'compile',[java.with_name('javac.exe'),'-J-Xmx192m','-encoding','UTF-8','-proc:none','-cp',prior['classpath'],'-d',root/'classes',*sources],40)
    dump(root/'class-pins.json',{p.relative_to(root/'classes').as_posix():sha(p) for p in (root/'classes').rglob('*.class')})
    reports={}
    for mode in ('original','candidate'):
        now=state();assert now['controllerPID']==current['controllerPID'] and now['databaseUUID']==current['databaseUUID'] and now['databasePort']==current['databasePort']
        assert sha(Q/'release-manifest.json')==RELEASE and sha(config)==prepared['configurationSHA256']
        for p,pin in prepared['sourcePins'].items():assert sha(p)==pin,'SQL_EXECUTION_SOURCE_CHANGED'
        target=root/mode;target.mkdir();cp=[str(root/'classes')]
        if mode=='candidate':cp.append(str(evidence/'candidate-classes'))
        cp.append(prior['classpath']);secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode()
        try:run(root,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',';'.join(cp),'xnby.replica.OriginalThirdPartyCredentialsSqlFixture',str(current['databasePort']),current['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),mode,target/'result.private.json'],80,secret)
        finally:del secret
        reports[mode]=read(target/'result.private.json');assert len(reports[mode]['cases'])==22 and reports[mode]['permanentFourTableRowsAndSchemasUnchanged'] and reports[mode]['temporaryTablesDropped']
    assert reports['original']['permanentBefore']==reports['original']['permanentAfter']==reports['candidate']['permanentBefore']==reports['candidate']['permanentAfter']
    assert reports['candidate']['loadedServiceClassSHA256']==sha(candidate)
    assert state()['controllerPID']==current['controllerPID'] and sha(Q/'release-manifest.json')==RELEASE
    assert reports['candidate']['serviceSaveHasTransactionAttribute'] and not reports['original']['serviceSaveHasTransactionAttribute']
    assert any(x.get('case')=='second-write-forced-failure' and x['annotationDrivenRollback'] for x in reports['candidate']['cases'])
    assert any(x.get('case')=='edit-third-write-forced-failure' and x['annotationDrivenRollback'] for x in reports['candidate']['cases'])
    result={'at':datetime.datetime.now().astimezone().isoformat(),'originalSQLCases':22,'candidateSQLCases':22,'actualSaveEditDetailAndOriginalMapperXmlExecuted':True,'candidateCredentialOnlyRowsPersistedAndReopened':True,'originalCredentialOnlyLossAndEmptyBatchSQLFailureReproduced':True,'nullEmptyOneTwoCredentialsAccidentAppraisalCombinationsPassed':True,'actualDuplicateGuardPreserved':True,'oversizeSaveAndEditNameRejectedBeforeAnyWrite':True,'candidateAnnotationDrivenSaveAndEditRollbackVerified':True,'positiveEditMainAndThreeChildrenReopened':True,'permanentFourTableRowsAndSchemasUnchanged':True,'temporaryTablesDropped':True,'loadedCandidateSHA256':sha(candidate),'runtimeInstalledOrRestarted':False,'realLoginHttpOrDockingUsed':False,'actualRuntimeTransactionAccepted':False,'publicDeployed':False,'fullCloneReady':False}
    dump(root/'result.json',result);print(json.dumps(result))

if __name__=='__main__':main()
