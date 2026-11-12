"""Clean exact restored code before-images and normally closed owned Chrome profiles only."""
from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';D=R/'Document/Deployment/fine_browser_original_r1748_20261107'
def J(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def plain(p):
 assert p.is_absolute()and p.resolve()==p and p.is_relative_to(R/'work')and p!=R/'work'
 for q in[p,*p.parents]:
  if q.exists():assert not q.is_symlink()and not q.is_junction()and not(q.lstat().st_file_attributes&0x400)
 return p
assert not(D/'cleanup-complete-scene-r1758.json').exists()
accepted=J(R/'work/su1760/verified-result.json');assert accepted['passed']and accepted['originalCodeRestored']and accepted['originalPointerRestored']and accepted['allActualJobsZeroBeforeClose']
scopes=[]
for name,parent in [('su1746','r1745'),('su1749','r1748'),('su1751','r1748'),('su1752','r1748'),('su1760','r1748')]:
 w=R/'work'/name;number=name[2:];r=J(w/'verified-result.json');t=J(R/f'Document/Deployment/fine_browser_original_{parent}_20261107'/f'actual-parent-terminal-r{number}.json')
 assert r['originalCodeRestored']and r['originalPointerRestored']and r['allActualJobsZeroBeforeClose']and t['actualOuterJobZero']and not r['forceTerminationUsed']
 plan=J(R/f'work/fine-browser-parent-{parent}/prepared-plan.private.json');before=plain(w/'b/before');expected={n:row['before']for n,row in plan['mutations'].items()if row['before']is not None};actual={p.relative_to(before).as_posix():p for p in before.rglob('*')if p.is_file()};assert set(actual)==set(expected)
 for n,pin in expected.items():assert not n.startswith(('private/','UserData/','seed/','Assets/'))and actual[n].stat().st_size==pin['bytes']and sha(actual[n])==pin['sha256']and(G/n).stat().st_size==pin['bytes']and sha(G/n)==pin['sha256']
 scopes.append((before,'restored-code-before-exactly-equal-retained-G'))
 for ui in [w/'ui-restart']:
  if (ui/'chrome-profile').exists():
   terminal=J(ui/'browser-terminal.json');assert terminal['normalBrowserClosed']and terminal['exitCode']==0 and not terminal['forceTerminationUsed'];scopes.append((plain(ui/'chrome-profile'),'normally-closed-owned-browser-profile'))
component=J(R/'Document/Deployment/scene_library_component_r1740_20261107/actual-component-proof-r1740.json');terminal=J(R/'Document/Deployment/scene_library_component_r1740_20261107/actual-component-terminal-r1740.json');assert component['passed']and component['allHTTPThreadsJoined']and terminal['actualJobZero']and terminal['exitCode']==0
profile=plain(R/'work/scene-library-browser-r1740/browser/chrome-profile');assert profile.is_dir();scopes.append((profile,'normally-closed-component-browser-profile'))
query=r'''$ErrorActionPreference='Stop';@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'"|Where-Object {if($_.CommandLine){$s=$_.CommandLine.Replace([char]92,[char]47).ToLowerInvariant();$s.Contains('d:/project/zhumadian/_g/application') -or $s.Contains('/work/su1746') -or $s.Contains('/work/su1749') -or $s.Contains('/work/su1751') -or $s.Contains('/work/su1752') -or $s.Contains('/work/su1760') -or $s.Contains('/work/scene-library-browser-r1740')}else{$false}}).Count'''
p=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and int(p.stdout.decode('utf-8-sig').strip())==0
scene=R/'work/scene-files-original-r1748/cloud-scenes/原账号完整场景_r1749.scene.json';retained={str(p):sha(p)for p in[scene,R/'work/su1749/scene-file-write-intent.private.json',R/'work/si1460/layer-data/layers.sqlite',R/'work/si1460/project-files/原SDK网页工程_r1522.json']}
for root,_ in scopes:
 for p in root.rglob('*'):plain(p)
removed=[{'path':str(root),'kind':kind,'files':sum(p.is_file()for p in root.rglob('*')),'logicalBytes':sum(p.stat().st_size for p in root.rglob('*')if p.is_file())}for root,kind in scopes];free=shutil.disk_usage(R).free
for root,_ in scopes:shutil.rmtree(root)
assert all(not root.exists()for root,_ in scopes)and all(sha(Path(p))==h for p,h in retained.items())
proof={'completed':True,'removed':removed,'files':sum(x['files']for x in removed),'logicalBytes':sum(x['logicalBytes']for x in removed),'freshSuccessfulProcessMatches':0,'allActualJobsZero':True,'allSavedSceneFilesAndDLG_SQLiteJSONWriteIntentsRetained':True,'smallFailuresAndSourcesLatestCandidatesRetained':True,'retiredBeforeNotDirectRollback':True,'serverTouched':False,'diskFreeBefore':free,'diskFreeAfter':shutil.disk_usage(R).free,'diskDeltaNotExclusivelyAttributed':True,'sourceSHA256':sha(Path(__file__))}
(D/'cleanup-complete-scene-r1758.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(proof,ensure_ascii=False))
