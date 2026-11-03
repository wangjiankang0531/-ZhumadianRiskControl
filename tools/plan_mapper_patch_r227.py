"""Stage/restore the byte-exact original plan XML in the stopped owned fixture's default mapper scan."""
from pathlib import Path
import argparse,copy,hashlib,json,os,subprocess,zipfile,importlib.util
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes())
encode=lambda v:(json.dumps(v,indent=2)+'\n').encode()
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','restore']);parser.add_argument('--attempt',required=True,choices=['r115','r116']);options=parser.parse_args()
P=C/('prepared-'+options.attempt);target='payload/business/run-template/classes/mapper/EmergencyPlanMapper.xml'
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='redis-server.exe' OR Name='nginx.exe' OR Name='chrome.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
for name in ['payload-manifest.json','release-manifest.json',target]:
 p=A/name
 for q in [p,*p.parents]:
  if q.exists():assert q.resolve()==q and not getattr(q.lstat(),'st_file_attributes',0)&0x400
if options.mode=='prepare':
 assert P.exists()and not(P/'plan-mapper-scope.json').exists()and not(C/options.attempt).exists()
 old={n:(A/n).read_bytes()for n in ['payload-manifest.json','release-manifest.json','tools/original_public_test_update.py']};payload=json.loads(old['payload-manifest.json']);release=json.loads(old['release-manifest.json'])
 ready=J(P/'controller-fixture-ready.json');assert sha(A/'release-manifest.json')==ready['releaseSHA256']
 assert target not in payload['files']and not(A/target).exists()
 main=A/'payload/business/application.jar';assert sha(main)==payload['files']['payload/business/application.jar']['sha256']
 with zipfile.ZipFile(main)as z:raw=z.read('xml/EmergencyPlanMapper.xml')
 assert len(raw)==829 and digest(raw)=='a4d921f1b007444e3618233035a5453c05dec8ae59f33eed46d045de3609425c'
 payload['files'][target]={'bytes':len(raw),'sha256':digest(raw)}
 updater=R/'Application/tools/original_public_test_update_r37_plan_exercise_r225.py'
 assert J(R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103/descriptor-gates.json')['passed']
 assert sha(updater)==J(R/'Document/Deployment/plan_exercise_mapper_candidate_r225_20261103/updater-source-preparation.json')['updaterSHA256']
 spec=importlib.util.spec_from_file_location('declared_plan_updater',updater);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 release[module.R37_PLAN_FIELD]=module.R37_PLAN_CONTRACT
 changed={target:raw,'payload-manifest.json':encode(payload),'tools/original_public_test_update.py':updater.read_bytes()}
 release['controllerFiles']['tools/original_public_test_update.py']=digest(changed['tools/original_public_test_update.py'])
 release['payloadManifestSHA256']=digest(changed['payload-manifest.json']);changed['release-manifest.json']=encode(release)
 scope={'onlyOwnedStoppedSyntheticFixture':True,'sourceOriginalBusinessJarSHA256':sha(main),'originalSourceResource':'xml/EmergencyPlanMapper.xml','target':target,
        'oldFiles':{n:digest(b)for n,b in old.items()},'newFiles':{n:digest(b)for n,b in changed.items()},'originalSQLBytesUnchanged':True,'defaultMapperPath':'classpath*:/mapper/**/*.xml','newDDLJavaArchiveAuthenticationOrConfig':False}
 for n,b in old.items():p=P/'plan-mapper-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 (P/'plan-mapper-scope.json').write_bytes(encode(scope))
 for n,b in changed.items():
  p=A/n;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():p.unlink()
  p.write_bytes(b)
 ready['updaterSHA256']=sha(A/'tools/original_public_test_update.py');ready['releaseSHA256']=sha(A/'release-manifest.json');ready['temporaryOriginalPlanXMLDefaultScan']=True
 (P/'controller-fixture-ready.json').write_bytes(encode(ready))
 print(json.dumps({'prepared':True,'byteExactOriginalPlanXML':True,'mappedStatements':3,'onlyOwnCodeAndManifestPaths':4,'publicOrFormalChanged':False}))
else:
 terminal=J(C/options.attempt/'controller-terminal.json');outer=J(C/(options.attempt+'-outer-terminal.json'));receipt=J(C/options.attempt/'scoped-controller-receipt.json')
 assert terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']
 scope=J(P/'plan-mapper-scope.json');assert scope['onlyOwnedStoppedSyntheticFixture']
 for n,pin in scope['newFiles'].items():assert sha(A/n)==pin,'PLAN_MAPPER_FOREIGN_DRIFT_REFUSED'
 for n,pin in scope['oldFiles'].items():assert sha(P/'plan-mapper-before'/n)==pin
 for n,pin in scope['oldFiles'].items():
  p=A/n;temp=p.with_name(p.name+'.own-plan-r227.tmp');assert not temp.exists();temp.write_bytes((P/'plan-mapper-before'/n).read_bytes());os.replace(temp,p)
 (A/target).unlink()
 assert not(A/target).exists()and all(sha(A/n)==pin for n,pin in scope['oldFiles'].items())
 proof={'passed':True,'onlyOriginalPlanXMLUpdaterAndTwoManifestsRestored':True,'normalOwnedShutdownAndActualDescendantsZero':True,'businessRowsOrSchemaRewritten':False}
 (P/'plan-mapper-restored.json').write_bytes(encode(proof));print(json.dumps(proof))
