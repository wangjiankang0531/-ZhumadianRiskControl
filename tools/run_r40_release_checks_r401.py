from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103/release-verification'
J=lambda p:json.loads(p.read_bytes());prepared=J(D/'prepared-sources-r401.json');results=[]
assert not(D/'completed-r401.json').exists()
for row in prepared['sources']:
 p=V/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
 log=D/row['variant']/(row['kind']+'-driver-r401.log');assert not log.exists()
 print('OWN_R40_'+row['variant'].upper()+'_'+row['kind'].upper()+'_START',flush=True)
 with log.open('xb')as stream:done=subprocess.run([sys.executable,str(p)],stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 if done.returncode:
  (D/'failure-r401.json').write_text(json.dumps({'variant':row['variant'],'kind':row['kind'],'exitCode':done.returncode,'sourceSHA256':row['sha256'],'servicesStarted':False},indent=2)+'\n',encoding='utf-8')
  raise RuntimeError('OWN_R40_RELEASE_CHECK_FAILED_INSPECT_SCOPED_LOG')
 proof=J(D/row['variant']/('full-program-preflight.json'if row['kind']=='full'else'composition-and-recovery.json'))
 assert proof['allPassed'if row['kind']=='full'else'passed']
 results.append({'kind':row['kind'],'variant':row['variant'],'passed':True,'sourceSHA256':row['sha256']})
 print('OWN_R40_'+row['variant'].upper()+'_'+row['kind'].upper()+'_PASSED',flush=True)
final={'passed':True,'drivers':results,'servicesStarted':False,'serverOrPublicOrDesktopTouched':False}
(D/'completed-r401.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8');print(json.dumps(final),flush=True)
