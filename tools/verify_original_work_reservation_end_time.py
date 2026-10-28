"""Execute real original/candidate reservation edit methods without DB/auth/HTTP.

Only reads pinned packaged dependencies; writes a fresh small verification tree.
Neither installs a candidate nor restarts any application or changes Reference.
"""
from pathlib import Path
import argparse, datetime, difflib, hashlib, json, os, subprocess, sys

HERE = Path(__file__).resolve().parent
R = Path('D:/Project/Zhumadian')
PREPARED = R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json'
REFERENCE = R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.java'
sys.path.insert(0, str(HERE))
from original_work_reservation_end_time_compat import build, adapt, SOURCE_SHA256


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(p, obj):
    if p.exists():
        raise ValueError('FRESH_RECEIPT_REQUIRED')
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def execute(root, tag, args, seconds):
    assert not (root/(tag+'-started.json')).exists(), 'ONE_EXECUTION_PER_REVISION'
    env = {k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    env.update(TEMP=str(root/'tmp'), TMP=str(root/'tmp'))
    p = subprocess.Popen(list(map(str,args)), cwd=root, env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
    dump(root/(tag+'-started.json'), {'pid':p.pid, 'maximumSeconds':seconds})
    timed=False
    try:
        out,err=p.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        timed=True;p.kill();out,err=p.communicate(timeout=10)
    (root/(tag+'.stdout.log')).write_bytes(out)
    (root/(tag+'.stderr.log')).write_bytes(err)
    dump(root/(tag+'-process.json'), {'exitCode':p.returncode,'timedOut':timed})
    if p.returncode or timed:
        raise RuntimeError(tag+': '+err.decode('utf-8',errors='replace')[-2400:])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();root=a.output.absolute()
    assert not root.exists() and root.parent.is_dir(), 'FRESH_EXISTING_PARENT_REQUIRED'
    root.mkdir();(root/'tmp').mkdir();(root/'fixture-classes').mkdir();(root/'candidate-classes').mkdir()
    raw=REFERENCE.read_bytes();assert sha(REFERENCE)==SOURCE_SHA256
    # Check provenance and the fail-closed gates before compiling or running.
    denied=False
    try:adapt(raw+b'\n')
    except ValueError:denied=True
    assert denied,'UNKNOWN_REFERENCE_MUST_BE_REJECTED'
    candidate=root/'generated/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.java'
    recipe=build(REFERENCE,candidate)
    candidate_raw=candidate.read_bytes()
    old_lines=raw.decode('utf-8').splitlines()
    new_lines=candidate_raw.decode('utf-8').splitlines()
    edits=[(tag,old_lines[i:j],new_lines[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(a=old_lines,b=new_lines,autojunk=False).get_opcodes() if tag!='equal']
    assert edits==[('insert',[],['    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)']),('insert',[],['        work.setEndTime(vo.getBase().getEndTime());'])], 'EXACT_END_TIME_AND_EDIT_TRANSACTION_DIFFERENCE_REQUIRED'
    # Save already assigns end time; only update gains one assignment.
    assert candidate_raw.count(b'work.setEndTime(vo.getBase().getEndTime());')==raw.count(b'work.setEndTime(vo.getBase().getEndTime());')+1
    fixture=HERE/'java/OriginalWorkReservationEndTimeFixture.java'
    deps=json.loads(PREPARED.read_text(encoding='utf-8-sig'))
    for file,pin in deps['inputPins'].items():
        assert sha(file)==pin['SHA256'],'ORIGINAL_DEPENDENCY_DRIFT'
    java=Path(deps['java']);assert sha(java)==deps['javaSHA256']
    cp=deps['classpath'];javac=java.with_name('javac.exe')
    lombok=[Path(p) for p in cp.split(';') if Path(p).name=='lombok-1.18.30.jar']
    assert len(lombok)==1
    dump(root/'prepared.private.json',{'at':datetime.datetime.now().astimezone().isoformat(),
        'recipe':recipe,'sourcePins':{str(p):sha(p) for p in (Path(__file__),HERE/'original_work_reservation_end_time_compat.py',fixture)},
        'dependencyPins':deps['inputPins'],'javaSHA256':sha(java),'javacSHA256':sha(javac),
        'databaseAuthenticationHttpOrRuntimeChangesAllowed':False})
    execute(root,'compile-fixture',[javac,'-J-Xmx192m','-encoding','UTF-8','-proc:none','-cp',cp,'-d',root/'fixture-classes',fixture],40)
    execute(root,'compile-candidate',[javac,'-J-Xmx192m','-encoding','UTF-8','-cp',cp,'-processorpath',lombok[0],'-processor','lombok.launch.AnnotationProcessorHider$AnnotationProcessor','-d',root/'candidate-classes',candidate],45)
    class_files=list((root/'candidate-classes').rglob('*.class'))
    assert len(class_files)==1 and class_files[0].name=='WorkReservationBaseServiceImpl.class','EXACT_SINGLE_CANDIDATE_CLASS_REQUIRED'
    for mode in ('original','candidate'):
        target=root/mode;target.mkdir()
        paths=[str(root/'fixture-classes')]
        if mode=='candidate':paths.append(str(root/'candidate-classes'))
        paths.append(cp)
        execute(root,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8',
            '-Djava.io.tmpdir='+str(root/'tmp'),'-cp',';'.join(paths),'xnby.replica.OriginalWorkReservationEndTimeFixture',mode,target/'result.json'],40)
    reports={mode:json.loads((root/mode/'result.json').read_text(encoding='utf-8')) for mode in ('original','candidate')}
    assert len(reports['original']['cases'])==8 and len(reports['candidate']['cases'])==16
    assert reports['candidate']['loadedServiceClassSHA256']==sha(class_files[0]), 'EXECUTED_CANDIDATE_CLASS_MUST_MATCH_COMPILATION'
    assert reports['original']['loadedServiceClassSHA256']!=reports['candidate']['loadedServiceClassSHA256'], 'ORIGINAL_AND_CANDIDATE_CLASS_MUST_DIFFER'
    assert reports['candidate']['explicitEditRollbackForException'] and not reports['original']['explicitEditRollbackForException']
    assert sha(REFERENCE)==SOURCE_SHA256
    result={'at':datetime.datetime.now().astimezone().isoformat(),'originalCases':8,'candidateCases':16,
        'actualServiceMethodsExecuted':True,'strictInMemoryMapperCaptures':True,'originalMissingEndTimeReproducedForEightTypes':True,
        'candidateEndTimeAndUnchangedFieldsPassed':True,'candidateNullValueSemanticsOnlyNotSqlClearance':True,
        'candidateClassSHA256':sha(class_files[0]),'referenceSHA256':SOURCE_SHA256,
        'executedCandidateBytesVerified':True,'exactEndTimeAndEditTransactionDifferenceVerified':True,
        'candidateEditRollbackForExceptionDeclared':True,
        'referenceChanged':False,'databaseOrAuthenticationOrHttpUsed':False,'runtimeInstalledOrRestarted':False,'fullCloneReady':False}
    dump(root/'result.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
