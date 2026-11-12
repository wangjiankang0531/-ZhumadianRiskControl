"""Retire two own support hard-link views only; preserve all original data and QA records."""
from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
Q=Path('D:/Temp/Administrator/xnby-resource-control-r2422');D=R/'Document/Deployment/resource_control_http_r2429_20261112'
def j(p):return json.loads(p.read_bytes())
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x',encoding='utf8')as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not D.exists();D.mkdir()
 result=j(Q/'verification.json');outer=j(V/'resource-control-r2423-outer-terminal.json')
 assert result['passed']and result['distinctChecks']==49 and outer['rootExitCode']==0 and outer['actualJobBeforeClose']==0
 assert all(row['rootExitCode']==0 and row['actualJobBeforeClose']==0 for row in result['actualOriginalRootsAndJobs'])
 for p,name in[(Q/'verification.json','verification.json'),(V/'resource-control-r2423-outer-terminal.json','outer-terminal.json'),(Q/'support-view-storage-plan.json','support-view-storage-plan.json')]:
  raw=p.read_bytes()
  with(D/name).open('xb')as f:f.write(raw)
 roots=[Q/'old/Zhumadian/Assets/Runtime',Q/'new/Zhumadian/Assets/Runtime']
 needles=[str(Q),'test_resource_control_chain_r2422.py','resource_control_http_backend_r2422.py','run_control_chain_r2423.py']
 ps="$ErrorActionPreference='Stop';$needles=ConvertFrom-Json '"+json.dumps(needles).replace("'","''")+"';$hits=@(Get-CimInstance Win32_Process|Where-Object{$_.Name-match '^(pythonw?|node|nginx)\\.exe$' -and $_.CommandLine -and $($line=$_.CommandLine;$hit=$false;foreach($n in $needles){if($line.IndexOf($n,[StringComparison]::OrdinalIgnoreCase)-ge 0){$hit=$true}};$hit)});[pscustomobject]@{querySucceeded=$true;refs=$hits.Count}|ConvertTo-Json -Compress"
 p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
 out,err=p.communicate();assert p.returncode==0;observed=json.loads(out.decode('utf-8-sig'));assert observed['querySucceeded']and observed['refs']==0
 manifest=R/'Application/Packages/ClientGISSettingsCandidate_20261107/client-gis-install.json';assert sha(manifest)=='26342711ce4091661d71893ce43a1e0431417117ba9f9d522d3ce8ea738cac72'
 pins=j(manifest)['offlineResources'];assert len(pins)==2356
 files=[];directories=[]
 for root in roots:
  assert root.resolve()==root and root.is_relative_to(Q)and root.parts[-3:]==('Zhumadian','Assets','Runtime')
  for p in[root,*root.parents]:assert not p.is_symlink()and not p.lstat().st_file_attributes&1024
  entries=list(root.rglob('*'));actual=set()
  for p in entries:
   assert p.resolve()==p and p.is_relative_to(root)and not p.lstat().st_file_attributes&1024
   if p.is_dir():directories.append(p);continue
   n=p.relative_to(root).as_posix();assert n in pins and p.stat().st_size==pins[n]['bytes']and sha(p)==pins[n]['sha256'];actual.add(n)
   files.append({'path':str(p),'bytes':pins[n]['bytes'],'sha256':pins[n]['sha256'],'sharedReadOnlyAttribute':bool(p.lstat().st_file_attributes&1)})
  assert actual==set(pins);directories.append(root)
 put(D/'retirement-fixed-files.json',{'files':files,'roots':[str(p)for p in roots],'freshCimZero':observed,'onlyReconstructibleSupportHardLinks':True,'realRawGISOrQADataIncluded':False})
 before=shutil.disk_usage(Q).free;retired=[];held=[]
 for row in files:
  p=Path(row['path']);assert sha(p)==row['sha256']and p.stat().st_size==row['bytes']and not p.lstat().st_file_attributes&1024
  if p.lstat().st_file_attributes&1:held.append(row);continue
  p.unlink();retired.append(row)
 for p in sorted(directories,key=lambda p:len(p.parts),reverse=True):
  if not any(p.iterdir()):p.rmdir()
 report={'retiredFiles':len(retired),'logicalBytes':sum(r['bytes']for r in retired),'heldSharedReadOnlyFiles':len(held),'sharedFileAttributesNeverCleared':True,
   'freeBefore':before,'freeAfter':shutil.disk_usage(Q).free,'exclusivePhysicalFreeNotClaimed':True,'allActualHandlesAndJobsNormalTerminal':True,
   'ownSyntheticSQLiteConfigurationControlIntentsTerminalsAndLogsPreserved':True,'original2356SupportFilesRawGISSourceAndUserDataPreserved':True,'publicOrClientInstallChanged':False,
   'retiredQAViewsNotRunnableAndNoRepeatScriptKept':True}
 put(D/'retirement-result.json',report);print(json.dumps(report))
if __name__=='__main__':main()
