"""Execute the original/candidate third-party save with closed memory collaborators.

No SQL, real authentication, HTTP, runtime stop/start, installation or publication.
"""
from pathlib import Path
import argparse, datetime, difflib, hashlib, json, os, subprocess
from original_third_party_credentials_compat import adapt, build, SOURCE_SHA256

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/Project/Zhumadian')
REFERENCE=ROOT/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.java'
DEPS=ROOT/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj):
    assert not p.exists(),'FRESH_EVIDENCE_REQUIRED'
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def execute(root,tag,args,seconds):
    assert not (root/(tag+'-started.json')).exists(),'ONE_EXECUTION_PER_REVISION'
    env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'))
    proc=subprocess.Popen(list(map(str,args)),cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    dump(root/(tag+'-started.json'),{'PID':proc.pid,'maximumSeconds':seconds})
    timed=False
    try:out,err=proc.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:timed=True;proc.kill();out,err=proc.communicate(timeout=10)
    (root/(tag+'.stdout.log')).write_bytes(out);(root/(tag+'.stderr.log')).write_bytes(err)
    dump(root/(tag+'-process.json'),{'exitCode':proc.returncode,'timedOut':timed})
    if timed or proc.returncode:raise RuntimeError(tag+': '+err.decode('utf-8',errors='replace')[-2500:])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.output.absolute()
    assert root.parent.is_dir() and not root.exists(),'FRESH_OUTPUT_REQUIRED'
    root.mkdir();(root/'tmp').mkdir();(root/'fixture-classes').mkdir();(root/'candidate-classes').mkdir()
    raw=REFERENCE.read_bytes();assert sha(REFERENCE)==SOURCE_SHA256
    try:adapt(raw+b'\n')
    except ValueError:pass
    else:raise AssertionError('UNKNOWN_SOURCE_MUST_BE_REJECTED')
    candidate=root/'generated/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.java';recipe=build(REFERENCE,candidate)
    old=raw.decode('utf-8').splitlines();new=candidate.read_text('utf-8').splitlines()
    removed=[];inserted=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():
        if tag!='equal':removed.extend(old[i:j]);inserted.extend(new[k:l])
    assert removed==['            credentialMapper.insertBatch(vo.getCredentials());'],'ONLY_MISPLACED_CALL_REMOVED'
    assert inserted.count('            credentialMapper.insertBatch(vo.getCredentials());')==1
    assert inserted.count('    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)')==2
    assert inserted.count('        validateCredentialNames(vo);')==2
    assert len(inserted)==16,'EXACT_RELOCATION_ANNOTATION_AND_PRIVATE_NAME_GUARD_DIFFERENCE'
    fixture=HERE/'java/OriginalThirdPartyCredentialsFixture.java'
    if not fixture.exists():fixture=HERE/'OriginalThirdPartyCredentialsFixture.java'
    deps=json.loads(DEPS.read_text('utf-8-sig'))
    for file,pin in deps['inputPins'].items():assert sha(file)==pin['SHA256'],'DEPENDENCY_CHANGED'
    java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];javac=java.with_name('javac.exe');cp=deps['classpath']
    lombok=[Path(s) for s in cp.split(';') if Path(s).name=='lombok-1.18.30.jar'];assert len(lombok)==1
    source_files=[Path(__file__),HERE/'original_third_party_credentials_compat.py',fixture]
    dump(root/'prepared.private.json',{'at':datetime.datetime.now().astimezone().isoformat(),'recipe':recipe,'sourcePins':{str(s):sha(s) for s in source_files},'dependencyPins':deps['inputPins'],'javaSHA256':sha(java),'javacSHA256':sha(javac),'maximumCompileSeconds':45,'maximumExecuteSeconds':40,'databaseOrRealAuthenticationOrHttpOrInstallAllowed':False})
    execute(root,'compile-fixture',[javac,'-J-Xmx192m','-encoding','UTF-8','-proc:none','-cp',cp,'-d',root/'fixture-classes',fixture],40)
    execute(root,'compile-candidate',[javac,'-J-Xmx192m','-encoding','UTF-8','-cp',cp,'-processorpath',lombok[0],'-processor','lombok.launch.AnnotationProcessorHider$AnnotationProcessor','-d',root/'candidate-classes',candidate],45)
    classes=list((root/'candidate-classes').rglob('*.class'));assert len(classes)==1 and classes[0].name=='ThirdPartyUnitInfoServiceImpl.class'
    for mode in ('original','candidate'):
        target=root/mode;target.mkdir();paths=[str(root/'fixture-classes')]
        if mode=='candidate':paths.append(str(root/'candidate-classes'))
        paths.append(cp)
        execute(root,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',';'.join(paths),'xnby.replica.OriginalThirdPartyCredentialsFixture',mode,target/'result.json'],40)
    reports={mode:json.loads((root/mode/'result.json').read_text('utf-8')) for mode in ('original','candidate')}
    for report in reports.values():assert len(report['cases'])==18 and not report['databaseRealLoginHttpOrDockingUsed'] and not report['transactionRollbackOrInstalledRuntimeProven']
    assert reports['candidate']['loadedServiceClassSHA256']==sha(classes[0]) and reports['original']['loadedServiceClassSHA256']!=sha(classes[0])
    assert sha(REFERENCE)==SOURCE_SHA256
    result={'at':datetime.datetime.now().astimezone().isoformat(),'originalCases':18,'candidateCases':18,'exactRelocationNameGuardAndTransactionDeclarationsVerified':True,'actualServiceAndOriginalIdentityHelperWithSyntheticCollaborators':True,'candidateExecutedClassSHA256':sha(classes[0]),'referenceSHA256':SOURCE_SHA256,'originalMissingCredentialAndEmptyBatchPathsCharacterized':True,'candidateNullEmptyOneTwoCredentialsWithAndWithoutAccidentsAndAppraisalsPassed':True,'duplicateGuardBeforeIdentityAndWritesPreserved':True,'oversizeNameRejectedBeforeIdentityAndWrites':True,'realSQLOrTransactionRollbackPassed':False,'installedOrRestarted':False,'publicDeployed':False,'fullCloneReady':False}
    dump(root/'result.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
