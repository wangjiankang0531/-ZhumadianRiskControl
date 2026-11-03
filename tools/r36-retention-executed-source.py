from pathlib import Path
import json,sys,hashlib,re,shutil,subprocess,os,time
app=Path('C:/inetpub/wwwroot/Zhumadian/Application');ftp=Path('C:/FTP_Root/Zhumadian');root=ftp/'Zhumadian_Native_History_20261103_R36'
sys.path.insert(0,str(app/'tools'));import original_public_test_update as m
pin='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853';row=m.owned_ready(app,pin);m.health(app,row)
latest=m.read(app/'UserData/OriginalPublicUpdates/latest.json');pending=m.read(app/'UserData/OriginalPublicUpdates/pending.json')
assert latest['newReleaseSHA256']==pin and latest['ready'] and pending['ready'] and not pending.get('failureType') and latest['attempt']==pending['attempt'] and latest['newReleaseSHA256']==pending['newReleaseSHA256'] and pending['serverLocalTLSVerified']
deployed=m.read(root/'verification/r36-deployment-summary.json');assert deployed['passed'] and deployed['candidateVersion']=='R36' and deployed['fixedManifestSHA256']=='06c2351a7771ac6280fa5212d09698347bc89699b2b792ca401a6a12fe417a26'
identity=m.read(app/'UserData/OriginalServer/installation.json');keep={Path(latest['attempt']),Path(pending['attempt'])}
known=[{'ftpName': 'Zhumadian_Personal_Workflow_20261103_R35', 'manifestSHA256': 'ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3', 'updateManifestSHA256': 'fbe46a67cc6026e933af9b7cd5d2e4a552e996ef69f4338a22841daf7e69d7cf', 'releaseSHA256': 'ccede060e9c329d44e65aef3200d86f8666c73d071d743cc1535031ab15d0ca4'}, {'ftpName': 'Zhumadian_Native_History_20261103_R36', 'manifestSHA256': '06c2351a7771ac6280fa5212d09698347bc89699b2b792ca401a6a12fe417a26', 'updateManifestSHA256': '06505ba1f5ebb58e7d781bbacff6f6b0783a4a980e64fc5ac4eb0d190fdb85b6', 'releaseSHA256': 'daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'}]
updates=app/'UserData/OriginalPublicUpdates';targets=[];counts={'oldUpdateAttemptDirectories':0,'oldCodeBackupDirectories':0,'extractedStagingDirectories':0,'stoppedRuntimeDirectories':0,'failedFTPTransportDirectories':0}
def no_redirect(p,within):
 p=p.absolute();within=within.absolute();assert p!=within and p.is_relative_to(within) and p.resolve(strict=True)==p
 m.regular(p)
 for q in p.rglob('*'):m.regular(q)
 return p
def only_code(p):
 for q in p.rglob('*'):
  if not q.is_file():continue
  parts=q.relative_to(p).parts
  assert parts[0] in {'frontend','payload','tools','iis','deploy'} or len(parts)==1,'UNKNOWN_BACKUP_PATH'
  if parts[0]=='deploy':assert q.relative_to(p).as_posix() in {'deploy/iis_original/web.config.template','deploy/iis_original/App_Code/XnbyReferenceProxy.cs','deploy/branding/zhumadian-emergency.svg'} and q.stat().st_size<1024*1024,'ONLY_EXACT_OLD_IIS_TEMPLATE_PROXY_OR_ICON_SOURCE'
  assert parts[0] not in {'private','UserData','seed','Assets','Reference','runtime'},'DATA_OR_DEPENDENCIES_NOT_CODE_BACKUP'
for d in updates.iterdir():
 m.regular(d)
 if not d.is_dir() or not re.fullmatch('[0-9a-f]{32}',d.name):continue
 receipt=m.read(d/'result.json');assert receipt.get('schema')=='zhumadian.public-test-update.receipt.v1' and receipt.get('databaseOrUploadsCopied') is False
 assert receipt['newReleaseSHA256']in{k['releaseSHA256']for k in known},'UNKNOWN_RETIRED_UPDATE_RELEASE'
 if (d/'before').exists():
  no_redirect(d/'before',updates);only_code(d/'before')
  changes=m.read(d/'changes.json');expected={name for name,p in changes.items()if p['before']is not None}
  assert {q.relative_to(d/'before').as_posix()for q in (d/'before').rglob('*')if q.is_file()}==expected,'BACKUP_EXACT_OLD_PATHS'
  for name,p in changes.items():
   if p['before']is not None:m.check_file(d/'before',name,p['before'])
  counts['oldCodeBackupDirectories']+=1
 if d in keep:
  if (d/'before').exists():targets.append(d/'before')
 else:
  targets.append(no_redirect(d,updates));counts['oldUpdateAttemptDirectories']+=1
staging=updates/'staging'
for d in staging.iterdir():
 if d.is_file():assert d.name=='web.config';continue
 no_redirect(d,staging);plan=m.read(d/'update-manifest.json');assert hashlib.sha256((d/'update-manifest.json').read_bytes()).hexdigest()in {k['updateManifestSHA256']for k in known},'UNKNOWN_STAGE_MANIFEST'
 for name,p in plan['files'].items():m.check_file(d/'payload',name,p['SHA256'],p['bytes'])
 assert plan.get('schema')=='zhumadian.public-test-update.v1' and plan.get('databaseUploadsCredentialsGISOrDependenciesIncluded') is False
 assert plan['targetApplication'] in ['C:/inetpub/wwwroot/Zhumadian/Application','C:/Zdm/Application']
 for q in d.rglob('*'):
  if not q.is_file():continue
  rel=q.relative_to(d)
  assert rel.parts[0] in {'payload'} or rel.as_posix() in {'update-manifest.json','web.config'}
 only_code(d/'payload');targets.append(d);counts['extractedStagingDirectories']+=1
for category,parent,active in [('business',app/'UserData/OriginalServer/runs',Path(row['run'])),('platform',app/'UserData/TianjinOriginalPlatform/runs',Path(row['platformRun']))]:
 assert active.parent==parent
 for d in parent.iterdir():
  assert d.is_dir() and re.fullmatch('j[1-9][0-9]{0,3}',d.name)
  if d==active:continue
  no_redirect(d,parent)
  rp=(d if category=='business' else app/'UserData/OriginalServer/runs'/d.name)/'receipt.json'
  rec=m.read(rp);assert rec.get('allOwnedChildrenExited') is True,'OLD_CHILDREN_EXIT_UNPROVEN'
  attachment=d/'b/files' if category=='business' else d/'files'
  assert not attachment.exists() or not any(q.is_file()for q in attachment.rglob('*')),'OLD_RUNTIME_ATTACHMENT_PRESENT'
  assert not any((d/n).exists()for n in ['database','data','store-data','uploads','attachments']),'OLD_RUNTIME_DATA_DIRECTORY_PRESENT'
  targets.append(d);counts['stoppedRuntimeDirectories']+=1
old_ftp=[]
for d in ftp.iterdir():
 if d==root:continue
 k=next((k for k in known if k['ftpName']==d.name),None);assert k is not None,'UNKNOWN_FTP_ENTRY'
 no_redirect(d,ftp);assert hashlib.sha256((d/'delivery-manifest.json').read_bytes()).hexdigest()==k['manifestSHA256'],'OLD_FTP_MANIFEST_DRIFT'
 transport=m.read(d/'delivery-manifest.json')
 for name,p in transport['files'].items():m.check_file(d,name,p['sha256'],p['bytes'])
 old_ftp.append(d)
targets+=old_ftp;counts['retiredFTPTransportDirectories']=len(old_ftp)
no_redirect(root,ftp)
assert hashlib.sha256((root/'delivery-manifest.json').read_bytes()).hexdigest()=='06c2351a7771ac6280fa5212d09698347bc89699b2b792ca401a6a12fe417a26'
assert root not in targets;counts['failedFTPTransportDirectories']=0
assert len(targets)<=32 and counts['stoppedRuntimeDirectories']<=8 and counts['oldCodeBackupDirectories']<=4,'ONLY_BOUNDED_VERIFIED_RETIRED_RELEASES'
assert latest['updateId']==pending['updateId'] and latest['updateId']=='20261103-R36-native-history-from-exact-R35'
assert len(targets)==len(set(targets)) and not any(a!=b and a.is_relative_to(b) for a in targets for b in targets)
def idle_targets():
 ps=r"[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; @(Get-CimInstance Win32_Process | Select-Object ProcessId,ExecutablePath,CommandLine) | ConvertTo-Json -Compress"
 r=subprocess.run(['powershell.exe','-NoProfile','-Command',ps],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
 rows=json.loads(r.stdout.decode('utf-8-sig'))
 for proc in rows:
  text=(proc.get('CommandLine') or '').replace('/','\\').lower();exe=(proc.get('ExecutablePath') or '').replace('/','\\').lower()
  for d in targets:
   stem=str(d).replace('/','\\').lower()+'\\'
   assert not exe.startswith(stem) and stem not in text,'OLD_PROGRAM_STILL_REFERENCED_BY_PROCESS'
idle_targets()
out={'schema':'xnby.public.r36.version-retention-result.v1','activeRelease':'R36','passed':False,'retainedOnlyActiveBusinessAndPlatformRuntime':False,'oldCodeBackupsRemoved':False,'ftpContainsNoExpiredOrFailedPackages':False,'filesRemoved':0,'logicalBytesRemoved':0,'directoriesRemoved':0,'categories':counts,'allAbsoluteTargetsInsideExplicitRootsAndNoReparse':True,'activeDatabaseUploadsConfigurationAndIISChanged':False,'noForceTermination':True,'historicalVersionRollbackBackupsRemovedPerUserInstruction':True}
report=app/'UserData/OriginalMaintenance/latest-version-retention.json';report.parent.mkdir(exist_ok=True)
scope_file=report.parent/'r36-retention-scope.private.json'
scope={'release':pin,'run':row,'targets':[str(d)for d in targets],'counts':counts}
if sys.argv[1:]==['inspect']:
 m.write_json(scope_file,scope)
 summary={'schema':'xnby.public.r36.version-retention-preflight.v1','activeRelease':'R36','passed':True,'targetDirectories':len(targets),'categories':counts,'allAbsoluteTargetsInsideExplicitRootsAndNoReparse':True,'noActiveProcessReferencesTargets':True,'latestFTPTransportKept':True,'sourceDatabaseUploadsConfigurationIISAndActiveRunsKept':True}
 print(json.dumps(summary));raise SystemExit(0)
assert sys.argv[1:]==['apply'] and m.read(scope_file)==scope,'EXACT_INSPECTED_RETENTION_SCOPE_REQUIRED'

free=shutil.disk_usage(app).free;m.write_json(report,out)
for d in targets:
 assert m.read(app/'UserData/OriginalServer/current-run.json')==row
 idle_targets();m.regular(d)
 files=[q for q in d.rglob('*')if q.is_file()];n=len(files);size=sum(q.stat().st_size for q in files)
 shutil.rmtree(d);assert not d.exists()
 out['filesRemoved']+=n;out['logicalBytesRemoved']+=size;out['directoriesRemoved']+=1;m.write_json(report,out)
assert m.read(app/'UserData/OriginalServer/installation.json')==identity
assert len(list((app/'UserData/OriginalServer/runs').iterdir()))==len(list((app/'UserData/TianjinOriginalPlatform/runs').iterdir()))==1
assert list(ftp.iterdir())==[root] and not any(updates.glob('*/before')) and not any(q.is_dir()for q in staging.iterdir())
assert m.owned_ready(app,pin)==row;m.health(app,row)
out.update(passed=True,retainedOnlyActiveBusinessAndPlatformRuntime=True,oldCodeBackupsRemoved=True,ftpContainsNoExpiredOrFailedPackages=True,originalTenPlusHistoryElevenReadinessAndControllerUnchanged=True,databaseIdentityMatched=True,observedFreeDelta=shutil.disk_usage(app).free-free)
m.write_json(report,out);print(json.dumps(out))
