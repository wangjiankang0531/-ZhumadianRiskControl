param([Parameter(Mandatory=$true)][ValidatePattern('^r[1-9][0-9]*$')][string]$Revision)
$ErrorActionPreference = 'Stop'
$target = (Resolve-Path -LiteralPath 'D:\Project\Zhumadian\_b').Path
if ($target -cne 'D:\Project\Zhumadian\_b') { throw 'Unexpected code-only cleanup target' }
$live = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python|java|javaw|mysqld|minio|chrome)\.exe$' -and $_.CommandLine -and $_.CommandLine.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 })
if ($live.Count -ne 0) { throw 'Owned runtime still has live processes' }
@'
from pathlib import Path
import json,hashlib,shutil,sys,zipfile
R=Path('D:/Project/Zhumadian');S=R/'_b';C=R/'work/event_delivery_consistency_20261030'/('full-business-main-'+sys.argv[1]);v=json.loads((S/'own-fixture.json').read_bytes());assert v['evidenceRoot']==str(C)and v['preparedRuntime'];term=json.loads((S/'controller-terminal.json').read_bytes());pins=json.loads((S/'runtime-code-pins.json').read_bytes());before={n.replace(chr(92),'/'):pin for n,pin in json.loads((C/'production-class-pins.json').read_bytes()).items()};old=json.loads((R/'work/user_feedback_20261031/r22-risk-candidate-r1/r21-base-payload-manifest.json').read_bytes())['files'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['business','identity','mysql','object-store','own-redis']:
 p=C/(name+'-stopped.json');assert p.exists();r=json.loads(p.read_bytes());assert not r.get('forced',False)and not r.get('forcedJobClosure',False)
 if name!='business':assert r['exitCode']==0
candidate=json.loads((R/'work/user_feedback_20261031/r22-risk-candidate-r3/candidate-stage.json').read_bytes());declared={x['relative']:x['newSHA256']for x in candidate['backendOperations']};assert len(declared)==5
nativePins={n.replace(chr(92),'/'):pin for n,pin in json.loads((C/'platform-production-input-pins.json').read_bytes()).items()};nativeMeta={'actual-writable-datasource.properties','application.properties','callback-route-pins.json','callback-routes-ready.properties','classloader-lifecycle.private.log','closing-threads-500ms.private.log','id-worker-close-observation.properties','id-worker-ready-observation.properties','original-platform-main-requested.txt','original-platform-main-returned.txt','own-stop-requested.txt','password-identity-claims-ready.properties','process-boundary-result.txt','server-context-closed.txt','server-http-port.txt','server-owner.properties','server-ready.txt'}
codebase='Application/UserData/OriginalServer/runs/j1/b/';platform='Application/UserData/TianjinOriginalPlatform/runs/j1/';extra={};jar=S/platform/'own-platform-observation.jar';assert sha(jar)=='eae7642792992da2ed4d2f6ff94f55001bda649888c754ffb0aeba4a39ae19d5'
with zipfile.ZipFile(jar)as z:
 for n in ['OriginalMissingAuthInterceptor','OriginalMissingAuthInitializer']:extra['classes/xnby/replica/'+n+'.class']=hashlib.sha256(z.read('xnby/replica/'+n+'.class')).hexdigest()
allowed={'application.properties','server-owner.properties','own-stop-requested.txt','process-boundary-result.txt','server-ready.txt','server-http-port.txt','server-context-closed.txt','server-context-closed-threads.txt','server-context-stopping.txt','server-configuration-key-inventory.json','server-normal-stop-requested.txt','missing-auth-guard-ready.json','missing-auth-guard-ready.properties','native-session-guard-ready.properties','own-finding-observer-ready.json','own-main-invocation-requested.txt','own-main-returned.txt','public-risk-chain-observation-failed.json','public-risk-chain-result.json','risk-batch-service-integration.json','risk-whole-import-integration.json','public-chain-native-risk-template.xlsx','emergency-exercise-transaction-observation.json','emergency-team-transaction-observation.json','event-disposal-transaction-observation.json','training-transaction-observation.json','transaction-bean-observation.json','work-safety-batch-observation.json','work-services-transaction-observation.json'};proof={};metadata=C/'closed-short-runtime-evidence';metadata.mkdir(exist_ok=True)
for p in S.rglob('*'):
 assert not p.lstat().st_file_attributes&0x400
 if not p.is_file():continue
 rel=p.relative_to(S).as_posix();h=sha(p)
 if rel.startswith('Application/runtime/'):assert pins[str(p.relative_to(S))]==h
 elif rel.startswith(codebase):
  sub=rel[len(codebase):]
  if sub in before:assert before[sub]==h
  elif sub in extra:assert extra[sub]==h
  elif 'payload/business/run-template/'+sub in declared:assert declared['payload/business/run-template/'+sub]==h
  elif 'payload/business/run-template/'+sub in old:assert old['payload/business/run-template/'+sub]['sha256']==h
  elif sub.startswith('own-import-fixtures/'):
   fixture=R/'Application/tools/test-data/risk-import-atomic-r83';pin=json.loads((fixture/'fixture-manifest.json').read_bytes())['files'][sub.split('/',1)[1]];assert pin['sha256']==h
  else:
   assert sub in allowed or(sub.startswith('logs/')and sub.endswith('.log')),sub
   dest=metadata/sub;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 elif rel.startswith(platform):
  sub=rel[len(platform):]
  if sub in nativePins:assert nativePins[sub]==h
  elif 'payload/platform/run-template/'+sub in old:assert old['payload/platform/run-template/'+sub]['sha256']==h
  else:
   assert sub in nativeMeta or(sub.startswith('log/jnpf-admin/')and sub.endswith('.log')),sub
   dest=metadata/'platform'/sub;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 elif rel=='Application/UserData/TianjinOriginalPlatform/identity.properties':
  owner=dict(line.split('=',1)for line in p.read_text(encoding='ascii').splitlines()if'='in line);assert owner['ownerId']==v['owner'];shutil.copyfile(p,metadata/'platform-data-identity.properties')
 elif rel.startswith('Application/UserData/_runtime_tmp/'):pass
 else:assert rel in ['own-fixture.json','runtime-code-pins.json','bootstrap.stdout.log','bootstrap.stderr.log','controller-terminal.json'],rel
 proof[rel]={'sha256':h,'bytes':p.stat().st_size}
for n in ['own-fixture.json','runtime-code-pins.json','bootstrap.stdout.log','bootstrap.stderr.log','controller-terminal.json']:shutil.copyfile(S/n,C/('closed-'+n))
(C/'short-code-cleanup-proof.json').write_text(json.dumps({'files':proof,'logicalBytes':sum(x['bytes']for x in proof.values()),'onlyOwnedRuntimeCodeAndSyntheticMetadata':True,'allDeclaredCodePinsMatched':True,'noOriginalDatabaseSourceGISReferenceIncluded':True,'requiredLiveProcessCount':0,'controllerTerminal':term},indent=2),encoding='utf-8');print('OWN_CLOSED_PUBLIC_CHAIN_SHORT_CODE_VERIFIED',len(proof))
'@ | & 'D:\Zqa20261025\Application\runtime\python\python.exe' -I -B - $Revision
if ($LASTEXITCODE -ne 0) { throw 'Closed runtime identity proof failed' }
$freeBefore = (Get-PSDrive -Name D).Free
Remove-Item -LiteralPath $target -Recurse -Force
$freeAfter = (Get-PSDrive -Name D).Free
$receipt = [pscustomobject]@{TargetAbsent= -not(Test-Path -LiteralPath $target);LiveOwnedProcesses=$live.Count;ObservedFreedBytes=($freeAfter-$freeBefore)}
$receipt | ConvertTo-Json -Compress
$receipt | ConvertTo-Json | Set-Content -LiteralPath ('D:\Project\Zhumadian\work\event_delivery_consistency_20261030\full-business-main-'+$Revision+'\short-code-cleanup-completed.json') -Encoding UTF8
