from pathlib import Path
import copy
import ast
import hashlib
import importlib.util
import json
import shutil
import sys

R=Path('D:/Project/Zhumadian')
A=R/'Application'
W=R/'work/user_feedback_20261031'
D=R/'Document/Deployment/public_test_home_viewport_r18_20261031_r2'
M=R/'Document/Deployment/server_directory_migration_20261030_r17d/delivery'
P=R/'work/public_test_update_20261029_r16/from-r15/bundle/payload/payload-manifest.json'
OLD='44742d772ff74dfe8bb14f601eb9bec9954526a81b39b8626cb8be73917f7044'
PAYLOAD='203aba75770eaeee1cde6483c57f032b630b0a7aec13c842251ace39d75dcbbb'
INDEX='cb3fbeb8286797412c3f955b6a52e13fb2c48a5bd1f9e64c38fac4c6fff95cdc'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)

def main():
 sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
 assert sha(M/'payload/release-manifest.json')==OLD and sha(P)==PAYLOAD
 index=Path('D:/Zqa20261025/Application/frontend/security_pc/index.html')
 assert sha(index)==INDEX
 proof=read(W/'home-layout-r1/home-viewport-layout-result.json')
 css=A/'tools/frontend/home-viewport.css'
 assert proof['passed'] and proof['normalBrowserClosed'] and proof['candidateCSSSha256']==sha(css)
 assert not D.exists()
 bundle=D/'delivery/bundle';bundle.mkdir(parents=True)
 old_release=read(M/'payload/release-manifest.json');old_payload=read(P)
 raw=index.read_bytes();eol=b'\r\n' if b'\r\n' in raw else b'\n'
 css_name='xnby-home-viewport-'+sha(css)[:12]+'.css'
 assert raw.count(b'</head>')==1 and b'data-xnby-home-viewport=' not in raw
 link=('<link rel="stylesheet" data-xnby-home-viewport="20261031" href="/zhumadian/'+css_name+'">').encode()
 files={'frontend/security_pc/index.html':raw.replace(b'</head>',link+eol+b'  </head>',1),
        'frontend/security_pc/'+css_name:css.read_bytes()}
 payload=copy.deepcopy(old_payload)
 for name,body in files.items():payload['files'][name]={'bytes':len(body),'sha256':digest(body)}
 assert {k for k in set(payload['files'])|set(old_payload['files']) if payload['files'].get(k)!=old_payload['files'].get(k)}==set(files)
 files['payload-manifest.json']=enc(payload)
 release=copy.deepcopy(old_release)
 release.update(payloadManifestSHA256=digest(files['payload-manifest.json']),
                publicTestRevision='20261031-R18-home-viewport',
                homeViewportRevision='browser-viewport-flex-clamp-and-nonblocking-decoration-v1',
                publicAccepted=False)
 assert release['controllerFiles']==old_release['controllerFiles']
 files['release-manifest.json']=enc(release)
 plan=read(R/'work/public_test_update_20261029_r16/from-r15/bundle/update-manifest.json')
 plan.update(updateId='20261031-R18-home-viewport-from-R17d',
             targetApplication='C:/inetpub/wwwroot/Zhumadian/Application',
             acceptedOldReleases={OLD:{'payloadManifestSHA256':PAYLOAD,'controllerFiles':old_release['controllerFiles']}},
             basePayloadManifestSHA256=PAYLOAD,newPayloadManifestSHA256=release['payloadManifestSHA256'],
             newReleaseSHA256=digest(files['release-manifest.json']),
             oldPayloadFiles={'frontend/security_pc/index.html':old_payload['files']['frontend/security_pc/index.html']},
             legacyEntrySHA256={},removedFrontendFiles={},
             files={name:{'bytes':len(body),'SHA256':digest(body)} for name,body in files.items()})
 for name,body in files.items():put(bundle/'payload'/name,body)
 put(bundle/'update-manifest.json',enc(plan));pin=sha(bundle/'update-manifest.json')
 check="""from pathlib import Path
import hashlib,importlib.util,sys
sys.dont_write_bytecode=True
app=Path('C:/inetpub/wwwroot/Zhumadian/Application')
root=Path(__file__).resolve().parent
def require_this_recovery(report):
 assert report.get('updateId')=='20261031-R18-home-viewport-from-R17d','ONLY_THIS_R18_UPDATE'
 assert report.get('oldReleaseSHA256')=='OLD','ONLY_THIS_OLD_RELEASE'
 assert report.get('newReleaseSHA256')=='NEW','ONLY_THIS_NEW_RELEASE'
 assert Path(report['attempt']).absolute().parent==app/'UserData/OriginalPublicUpdates','ONLY_OWNED_ATTEMPT'
source=app/'tools/original_public_test_update.py'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='8ee301b1d7466f08f39c40d0ed42c9edbe652bfd3a9223f694d7379c7970dad5','PINNED_R17D_UPDATER_REQUIRED'
sys.path.insert(0,str(app/'tools'))
spec=importlib.util.spec_from_file_location('owned_r18_updater',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
if sys.argv[1:]==['--recover-this-update']:
 report=m.read(m.regular(app,'UserData/OriginalPublicUpdates/pending.json'))
 require_this_recovery(report)
 m.recover_pending(app)
 sys.exit(0)
assert len(sys.argv)==1,'EXACT_PREFLIGHT_OR_OWN_RECOVERY_MODE'
plan,old,changes=m.load_bundle(app,root/'bundle','PIN')
assert old=='OLD' and len(changes)==4
row=m.owned_ready(app,old);m.health(app,row)
print('R18_HOME_VIEWPORT_PREFLIGHT_PASSED_EXISTING_RUNTIME_HEALTHY_NO_FILES_CHANGED')
"""
 check=check.replace("'PIN'","'"+pin+"'").replace("'OLD'","'"+OLD+"'").replace("'NEW'","'"+plan['newReleaseSHA256']+"'")
 guard=next(x for x in ast.parse(check).body if isinstance(x,ast.FunctionDef) and x.name=='require_this_recovery')
 guard_globals={'Path':Path,'app':Path('C:/inetpub/wwwroot/Zhumadian/Application')}
 exec(compile(ast.Module(body=[guard],type_ignores=[]),'fixed-generated-recovery-guard','exec'),guard_globals)
 good={'updateId':plan['updateId'],'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],
       'attempt':'C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/own_synthetic_attempt'}
 guard_globals['require_this_recovery'](good)
 for key,value in [('updateId','unrelated-update'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','1'*64),('attempt','C:/unrelated/attempt')]:
  changed=dict(good);changed[key]=value
  try:guard_globals['require_this_recovery'](changed)
  except AssertionError:pass
  else:raise ValueError('UNRELATED_RECOVERY_MUST_BE_REJECTED')
 put(D/'delivery/Check_Home_Viewport_R18.py',check.encode())
 launch=('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0Check_Home_Viewport_R18.py"\r\nif errorlevel 1 exit /b 1\r\n'
         '"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "C:\\inetpub\\wwwroot\\Zhumadian\\Application\\tools\\original_public_test_update.py" --application "C:\\inetpub\\wwwroot\\Zhumadian\\Application" --apply "%~dp0bundle" --manifest-sha256 '+pin+'\r\n')
 put(D/'delivery/Deploy_Home_Viewport_R18.cmd',launch.encode())
 recover=('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0Check_Home_Viewport_R18.py" --recover-this-update\r\n')
 put(D/'delivery/Recover_Pending_Home_Viewport_R18.cmd',recover.encode())
 # Exercise the actual retained updater's four-file transaction with synthetic copies.
 source=M/'payload/tools/original_public_test_update.py'
 spec=importlib.util.spec_from_file_location('r17_transaction',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 baseline={'frontend/security_pc/index.html':raw,'payload-manifest.json':P.read_bytes(),
           'release-manifest.json':(M/'payload/release-manifest.json').read_bytes()}
 changes={name:{'before':digest(baseline[name]) if name in baseline else None,'after':digest(body)} for name,body in files.items()}
 results=[]
 for fault in [False,True]:
  test=W/('r18-r2-fourth-write' if fault else 'r18-r2-normal-restore');app=test/'Application'
  assert not test.exists()
  for name,body in baseline.items():put(app/name,body)
  attempt=test/'backup';m.backup_code(app,attempt,changes);count=[0]
  def after(name):
   count[0]+=1
   if fault and count[0]==4:raise RuntimeError('OWN_R18_FOURTH_WRITE')
  caught=False
  try:m.replace_code(app,bundle,changes,after_each=after)
  except RuntimeError as error:
   assert fault and str(error)=='OWN_R18_FOURTH_WRITE';caught=True
  assert caught==fault and all(sha(app/name)==digest(body) for name,body in files.items())
  m.restore_code(app,attempt,changes)
  assert all((app/name).read_bytes()==body for name,body in baseline.items())
  assert not (app/('frontend/security_pc/'+css_name)).exists()
  results.append({'fourthWriteFault':fault,'writes':count[0],'oldThreeFilesExactlyRestored':True,'newCSSRemovedOnRestore':True})
 report={'scenarios':results,'exactExistingUpdaterUsed':True,'serverPreflightNotYetRun':True,'exactGeneratedRecoveryOwnershipGates':5,
         'allJavaBackendControllerIISDatabaseAndAuthBytesPreservedInCandidate':True,
         'changedInstallPaths':list(files),'publicDeployed':False,'sheetUpdated':False}
 put(D/'file-transaction-verification.json',enc(report))
 delivery={p.relative_to(D/'delivery').as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((D/'delivery').rglob('*')) if p.is_file()}
 manifest={'revision':'R18-home-viewport','targetFTP':'/Zhumadian/Zhumadian_Home_Viewport_20261031_R18/',
           'targetHTTPS':'https://www.joinlinksmart.com/zhumadian/',
           'files':delivery,'fileCount':len(delivery),'totalBytes':sum(x['bytes'] for x in delivery.values()),
           'updateManifestSHA256':pin,'acceptedOldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],
           'containsApplicationCSSAndInternalDeploymentPaths':True,
           'containsCredentialsAccountsSessionsBusinessRowsOrRawLogs':False,
           'serverManifestExportRequired':False,'publicDeployed':False}
 put(D/'delivery-manifest.json',enc(manifest))
 put(D/'delivery/delivery-manifest.json',enc(manifest))
 put(D/'preparation-result.json',enc({'manifestSHA256':sha(D/'delivery-manifest.json'),'files':len(delivery),'bytes':manifest['totalBytes'],'fileTransactionVerified':True,'localLayoutCases':7,'publicDeployed':False}))
 print(json.dumps({'manifestSHA256':sha(D/'delivery-manifest.json'),'files':len(delivery),'bytes':manifest['totalBytes'],'updateManifestSHA256':pin,'publicDeployed':False}))

if __name__=='__main__':main()
