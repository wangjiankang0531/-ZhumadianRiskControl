from pathlib import Path
import argparse,hashlib,json,subprocess,os,re
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_registration_r260_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','restore']);p.add_argument('--attempt',required=True,choices=['r133','r134']);o=p.parse_args();P=C/('prepared-'+o.attempt)
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
cmd="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
classrel='payload/business/run-template/own-mapper-observation-r260.jar'
if o.action=='prepare':
 assert not(C/o.attempt).exists()and not(P/'mapper-observer-scope.json').exists()and not(A/classrel).exists()
 before={n:(A/n).read_bytes()for n in ['private/server-configuration.json','payload-manifest.json','release-manifest.json']}
 cfg=J(A/'private/server-configuration.json');business=cfg['configuration']['business'];arguments=cfg['businessArguments'];indexes=[i for i,x in enumerate(arguments)if 'application.jar' in x and ';' in x];assert len(indexes)==1
 cpindex=indexes[0];newjar='${APP}/payload/business/run-template/own-mapper-observation-r260.jar';assert newjar not in arguments[cpindex];arguments[cpindex]+=';'+newjar;assert set(re.findall(r'\$\{([^}]+)\}',arguments[cpindex]))<={'APP','BUSINESS_RUN','PLATFORM_RUN','PLATFORM_DATA'},'UNKNOWN_CLASSPATH_TOKEN_REFUSED'
 mapper_keys=[x for x in business if 'mapper' in x.lower()and'location' in x.lower()];assert not mapper_keys,'EXPLICIT_MAPPER_CONFIGURATION_MUST_NOT_BE_OVERWRITTEN'
 after={'private/server-configuration.json':enc(cfg),classrel:(D/'own-mapper-observation-r260.jar').read_bytes()};q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json')
 for n,b in after.items():q['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 after['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=hashlib.sha256(after['payload-manifest.json']).hexdigest();after['release-manifest.json']=enc(release)
 scope={'onlyOwnedStoppedSyntheticFixture':True,'observerOnlyOrCandidateSetting':o.attempt,'oldFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in before.items()},'newFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in after.items()},'newPaths':[classrel],'originalJarSQLAndDatasourceAndSchemaChanged':False}
 for n,b in before.items():p=P/'mapper-observer-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 (P/'mapper-observer-scope.json').write_bytes(enc(scope))
 for n,b in after.items():
  p=A/n;assert p.resolve()==p and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert not p.lstat().st_file_attributes&0x400;p.unlink()
  p.write_bytes(b)
 baseline=J(P/'controller-fixture-ready.json');baseline['releaseSHA256']=sha(A/'release-manifest.json');(P/'controller-fixture-ready.json').write_bytes(enc(baseline));print(json.dumps({'prepared':True,'mode':o.attempt,'onlyOwnSyntheticClasspathAndListenerJar':True,'allOriginalControllerJarAndSQLBytesKept':True}))
else:
 t=J(C/o.attempt/'controller-terminal.json');outer=J(C/(o.attempt+'-outer-terminal.json'));receipt=J(C/o.attempt/'scoped-controller-receipt.json');assert t['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 scope=J(P/'mapper-observer-scope.json')
 for n,pin in scope['newFiles'].items():assert sha(A/n)==pin['sha256'],'FOREIGN_DRIFT_REFUSE_RESTORE'
 for n,pin in scope['oldFiles'].items():assert sha(P/'mapper-observer-before'/n)==pin['sha256']
 for n in scope['newPaths']:(A/n).unlink()
 for n in scope['oldFiles']:
  p=A/n;tmp=p.with_name(p.name+'.own-r260-restore.tmp');assert not tmp.exists();tmp.write_bytes((P/'mapper-observer-before'/n).read_bytes());os.replace(tmp,p)
 assert all(sha(A/n)==pin['sha256']for n,pin in scope['oldFiles'].items())and all(not(A/n).exists()for n in scope['newPaths'])
 proof={'passed':True,'originalConfigAndManifestsRestored':True,'onlyOwnListenerJarRemoved':True,'normalAllComponentsAndActualDescendantsZero':True,'businessDataOrSchemaChangedByRestore':False};(P/'mapper-observer-restored.json').write_bytes(enc(proof));print(json.dumps(proof))
