from pathlib import Path
import copy,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application'
OLD=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104'
PUB=R/'Document/Deployment/event_result_runtime_r1000_20261105';BUILD=R/'work/event-result-full-r996'
D=R/'Document/Deployment/event_result_owned_full_r1003_20261105'
J=lambda p:json.loads(Path(p).read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p):return {'bytes':Path(p).stat().st_size,'sha256':sha(p)}if Path(p).is_file()else None
assert not D.exists();base=J(OLD/'full-source-and-restore-plan.private.json')
assert J(PUB/'verified-metadata-contract-r1002.json')['passed']
assert J(R/'Document/Deployment/event_crud_native_r990_20261104/independent-restore-r994.json')['passed']
assert sha(G/'release-manifest.json')==base['baseOwnedReleaseSHA256']and pin(G/'private/server-configuration.json')==base['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==base['installationBefore']
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
release=J(PUB/'candidate/release-manifest.json');payload=J(PUB/'candidate/payload-manifest.json')
payload['files']['private/server-configuration.json']=base['configBefore']
sources={n:copy.deepcopy(p)for n,p in base['sources'].items()if not n.startswith('frontend/emergency_pc/')}
for rel,p in J(BUILD/'verified-bounded-full-build-r673.json')['files'].items():
 file=BUILD/'dist'/rel;assert pin(file)==p;sources['frontend/emergency_pc/'+rel]={'source':str(file),**p}
for n,name in [('tools/original_public_test_update.py','original_public_test_update.py'),('tools/original_public_test_base_r46.py','original_public_test_base_r46.py')]:
 p=PUB/'source'/name;sources[n]={'source':str(p),**pin(p)}
expected={n:p for n,p in payload['files'].items()if not n.startswith('seed/mysql/')}
for n,p in release['controllerFiles'].items():
 if n in expected:assert expected[n]['sha256']==p
 else:expected[n]={'bytes':sources[n]['bytes'],'sha256':p}
assert set(expected)==set(sources)
for n,p in sources.items():assert {k:p[k]for k in ['bytes','sha256']}==expected[n]and pin(Path(p['source']))==expected[n],n
payloadraw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(payloadraw).hexdigest();releaseraw=enc(release)
D.mkdir();(D/'candidate').mkdir();(D/'candidate/payload-manifest.json').write_bytes(payloadraw);(D/'candidate/release-manifest.json').write_bytes(releaseraw)
rows={}
for n,p in sources.items():
 before=pin(G/n);after={k:p[k]for k in ['bytes','sha256']}
 if before!=after:
  assert not n.startswith(('private/','UserData/','Assets/','seed/'))
  rows[n]={'before':before,'after':after,'source':p['source']}
for n in ['payload-manifest.json','release-manifest.json']:rows[n]={'before':pin(G/n),'after':pin(D/'candidate'/n),'source':str(D/'candidate'/n)}
retired={n:p for n,p in J(G/'payload-manifest.json')['files'].items()if n.startswith('frontend/')and n not in payload['files']and(G/n).exists()}
for n,p in retired.items():assert pin(G/n)==p
for n,p in base['knownRebuildableCachesToRemoveOnlyDuringFutureApply'].items():assert pin(G/n)==p
plan=copy.deepcopy(base)
plan.update(candidateReleaseSHA256=sha(D/'candidate/release-manifest.json'),candidatePayloadManifestSHA256=sha(D/'candidate/payload-manifest.json'),sources=sources,mutations=rows,retiredKnownFrontendPaths=retired,
 exactPreparedR48ProgramAndControllerBytes=True,onlyPrivateConfigurationManifestPinAdapted=True,preparedR48PublicPayloadManifestSHA256=sha(PUB/'candidate/payload-manifest.json'))
plan.pop('exactPublicR47ProgramAndControllerBytes',None);plan.pop('sourceR47BundleManifestSHA256',None)
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
report={'preparedOnly':True,'ownedSyntheticApplicationOnly':True,'sourcesResolved':len(sources),'actualEmergencyCompiledFiles':344,'mutationPaths':len(rows),'retiredFrontendPaths':len(retired),
 'preparedR48ProgramsAndControllersExact':True,'onlyPrivateManifestPinAdapted':True,'runtimeLifecycleNotYetExecuted':True,'newR48SparsePublisherNotExercisedByThisCodeTransaction':True,'existingDataOrCodeChanged':False,'fullCloneReady':False}
(D/'prepared-owned-r1003.json').write_bytes(enc(report));print(json.dumps(report))
