"""Verify the disposal observer against actual original/candidate Spring proxies without SQL."""
from pathlib import Path
import argparse,datetime,hashlib,json,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/event_disposal_atomic_20261029';W=R/'work/event_disposal_atomic_20261029';CLS='com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class'
sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from verify_original_work_reservation_sql import run
from verify_confirmed_operations_local_state import current
from verify_confirmed_operation_preservation import protected

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def dump(p,v):assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--revision',choices=['r1','r2','r3'],required=True);a=p.parse_args();out=D/('observer-context-'+a.revision);work=W/('observer-context-'+a.revision);assert not out.exists() and not work.exists();out.mkdir();work.mkdir();(work/'tmp').mkdir();before=current();held=protected();sql=read(D/'sql-verification.json');assert sql['candidateClassPins'][CLS]==sha(W/'candidate-classes'/CLS)=='8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2'
 deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for path,row in deps['inputPins'].items():assert sha(path)==row['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];classes=Q/'payload/business/run-template/classes';payload=read(Q/'payload-manifest.json');helper='payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class';assert sha(Q/helper)==payload['files'][helper]['sha256'];cp=str(classes)+';'+deps['classpath'];observer=T/'java/OriginalEventDisposalTransactionObservation.java';fixture=T/'java/OriginalEventDisposalTransactionObservationFixture.java';sources=[Path(__file__),observer,fixture,T/'java/OriginalTransactionObservation.java',T/'java/OriginalEventDisposalTableReadProbe.java'];pins={str(s):sha(s) for s in sources};snap=out/'executed-sources';snap.mkdir()
 for s in sources:(snap/s.name).write_bytes(s.read_bytes())
 dump(out/'prepared.json',{'sourcePins':pins,'javaSHA256':sha(java),'originalRuntimeObserverHelperSHA256':sha(Q/helper),'candidateClassSHA256':sha(W/'candidate-classes'/CLS),'runtimeBefore':before,'noSQLOrBusinessInvocationByObserver':True});(work/'observer-classes').mkdir();(work/'fixture-classes').mkdir()
 run(work,'compile-observer',[java.with_name('javac.exe'),'-J-Xmx128m','-encoding','UTF-8','-proc:none','-cp',cp,'-d',work/'observer-classes',observer],35)
 run(work,'compile-fixture',[java.with_name('javac.exe'),'-J-Xmx160m','-encoding','UTF-8','-proc:none','-cp',str(work/'observer-classes')+';'+cp,'-d',work/'fixture-classes',fixture,T/'java/OriginalEventDisposalTableReadProbe.java'],40)
 reports={}
 for mode in ['original','candidate']:
  target=work/mode;target.mkdir();service=W/(mode+'-classes');pin=sha(service/CLS);classpath=';'.join(map(str,[work/'fixture-classes',work/'observer-classes',service,classes]))+';'+deps['classpath'];run(work,'execute-'+mode,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(work/'tmp'),'-cp',classpath,'xnby.replica.OriginalEventDisposalTransactionObservationFixture',target,mode,pin],60);v=read(target/'result.json');assert len(v['contexts'])==7 and len(v['controllerContracts'])==2 and v['noSQLNetworkOrProductionRuntime'] and v['noBusinessCallsByObserver'] and v['candidateServiceBytes']==pin;reports[mode]=v
  dump(out/(mode+'-result.json'),v)
 for path,pin in pins.items():assert sha(path)==pin
 assert before==current() and held==protected();assert sha(R/'Document/Deployment/public_test_r15_20261029/delivery-manifest.json')=='86fe59c75b0d18588a93ef49de19a215e37061b464a23cfa14bc91a04a01eea3'
 observerClass=work/'observer-classes/xnby/replica/OriginalEventDisposalTransactionObservation.class';assert len(list((work/'observer-classes').rglob('*.class')))==1;result={'at':datetime.datetime.now().astimezone().isoformat(),'contextsPerMode':7,'actualOriginalControllerBooleanSerializationContractsPerMode':2,'actualCandidateSpringAutoProxyMatched':True,'originalAndMissingManagerUnproxiedUncheckedDuplicateMissingServiceRejected':True,'observerBusinessTransactionAndMapperCalls':0,'observerClass':str(observerClass),'observerClassSHA256':sha(observerClass),'observerSourceSHA256':sha(observer),'sourceInputsAndCurrentJ57AndHeldWorkUnchanged':True,'fixedR15Unchanged':True,'runtimeInstalledOrRestarted':False,'realSQLOrAuthenticatedHTTPOrNotificationsUsed':False,'fullCloneReady':False};dump(out/'result.json',result);print(json.dumps(result))
if __name__=='__main__':main()
