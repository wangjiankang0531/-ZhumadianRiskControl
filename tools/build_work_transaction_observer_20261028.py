from pathlib import Path
import datetime,hashlib,json,sys
W=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';Q=Path('D:/Zqa20261025/Application')
sys.path.insert(0,str(A/'tools'))
from verify_original_work_reservation_sql import run
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def main():
 root=R/'work/work_transaction_observer_20261028';assert not root.exists();deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for p,pin in deps['inputPins'].items():assert sha(p)==pin['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];root.mkdir();(root/'classes').mkdir();(root/'tmp').mkdir()
 java_root=W/'java' if (W/'java').is_dir() else W;sources=[java_root/'OriginalTransactionObservation.java',A/'tools/java/OriginalTransactionObservationFixture.java',java_root/'OriginalWorkTransactionObservationFixture.java'];pins={str(p):sha(p) for p in sources+[Path(__file__)]}
 (root/'prepared.private.json').write_text(json.dumps({'sourcePins':pins,'dependencyPins':deps['inputPins'],'javaSHA256':sha(java),'runtimeInstallationAllowed':False},indent=2)+'\n',encoding='utf-8')
 run(root,'compile',[java.with_name('javac.exe'),'-J-Xmx192m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',root/'classes',*sources],40)
 reservation=R/'work/work_reservation_end_time_update_20261028_v2/payload/payload/business/run-template/classes';third=R/'work/third_party_credentials_candidate_20261028/candidate-classes'
 rc=reservation/'com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class';tc=third/'com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class'
 assert sha(rc)=='4f569208da945cc8c7042f539c11c24dc19f382e507758c93dac63ae69961af2' and sha(tc)=='1bac35eef2c07fc8cfb44af14260730bb24b0b3bed09f89f097b8b302850f67b'
 cp=';'.join(map(str,[root/'classes',reservation,third]))+';'+deps['classpath'];quiet=root/'quiet-logback.xml';quiet.write_text('<configuration><root level="ERROR"/></configuration>',encoding='ascii')
 for name,fixture in [('original-observer','OriginalTransactionObservationFixture'),('work-observer','OriginalWorkTransactionObservationFixture')]:
  folder=root/name;folder.mkdir();run(root,name,[java,'-Xmx192m','-XX:ActiveProcessorCount=2','-Dlogback.configurationFile='+str(quiet),'-cp',cp,'xnby.replica.'+fixture,folder],40)
  result=read(folder/'result.json');assert result['noOriginalServiceMethodsOrTransactionsInvoked'] and result['noNetworkOrDatabase']
 work=read(root/'work-observer/result.json');assert len(work['contexts'])==4
 for row in work['contexts']:
  if row['mode']!='missing-singletons':assert row['reservationClassSHA256']==sha(rc) and row['thirdPartyClassSHA256']==sha(tc)
 for p,pin in pins.items():assert sha(p)==pin
 artifact=root/'classes/xnby/replica/OriginalTransactionObservation.class';report={'at':datetime.datetime.now().astimezone().isoformat(),'originalContexts':2,'additionalContexts':4,'observerClassSHA256':sha(artifact),'observerBytes':artifact.stat().st_size,'reservationClassSHA256':sha(rc),'thirdPartyClassSHA256':sha(tc),'actualCandidateClassBytesVerified':True,'businessOrTransactionInvoked':False,'networkOrDatabaseUsed':False,'runtimeInstalled':False,'actualRuntimeProxyAccepted':False}
 (root/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
