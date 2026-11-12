"""Retire only the 319 reconstructible regular source copies of the closed R2435 build."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
W=R/'work/resource-scene-control-r2435';TARGET=W/'source'
D=R/'Document/Deployment/resource_control_integration_r2440_20261112'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
def regular(p):
 assert not p.is_symlink()and not p.is_junction()and not p.lstat().st_file_attributes&1024,str(p)
def main():
 report=D/'source-retirement-r2441.json';assert not report.exists()
 term=j(D/'scene-outer-terminal.json');assert term['rootExitCode']==0 and term['actualJobBeforeClose']==0
 assert term['sourceSHA256']==sha(V/'rebuild_d176_scene_r2435.py')and not term['forceTerminationUsed']
 assert TARGET.resolve()==Path('D:/Project/Zhumadian/work/resource-scene-control-r2435/source')
 assert TARGET.is_relative_to(R/'work')and TARGET!=R/'work'
 for p in [R,R/'work',W,TARGET]:regular(p)
 query="""$ErrorActionPreference='Stop';$rows=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -and ($_.CommandLine -match 'resource-scene-control-r2435|rebuild_d176_scene_r2435[.]py')}); if($rows.Count){throw 'R2435_REFERENCED'}; 'R2435_FRESH_CIM_ZERO'"""
 scan=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 assert scan.returncode==0 and scan.stdout.decode('utf8',errors='replace').strip()=='R2435_FRESH_CIM_ZERO','SUCCESSFUL_CIM_ZERO_REQUIRED'
 indexp=A/'tools/experimental_source/resource_control_merge_r2433/scene-source-index.json'
 assert sha(indexp)=='74a891864b22f2223b2efca0b9cb40bd44a7557b2555bd33fe6aeb90202e645a'
 index=j(indexp);expected={};dirs=[]
 for n,row in index['files'].items():
  p=(TARGET/'web'/n).resolve();assert p.is_relative_to(TARGET)and p!=TARGET
  source=(A/row['source']).resolve();assert source.is_relative_to(A/'tools/experimental_source')
  regular(p);regular(source);assert p.stat().st_size==row['bytes']and sha(p)==sha(source)==row['sha256']
  expected[p]=row
 for root,sub,files in os.walk(TARGET,followlinks=False):
  p=Path(root);regular(p);dirs.append(p)
  for n in sub:regular(p/n)
  for n in files:assert(p/n).resolve()in expected,'UNKNOWN_FILE_KEEP'
 assert len(expected)==319 and sum(r['bytes']for r in expected.values())==5595971
 products=j(D/'scene-verification.json')['outputs'];pins={n:sha(W/'products'/n)for n in products}
 assert all(pins[n]==row['sha256']for n,row in products.items())
 before=shutil.disk_usage(R).free
 # Exact per-file deletion in Python only; no recursive shell command or wildcard.
 for p,row in expected.items():regular(p);assert sha(p)==row['sha256'];p.unlink()
 for p in sorted(dirs,key=lambda x:len(x.parts),reverse=True):regular(p);p.rmdir()
 assert not TARGET.exists()and all(sha(W/'products'/n)==h for n,h in pins.items())
 after=shutil.disk_usage(R).free
 result={'at':datetime.datetime.now().astimezone().isoformat(),'retiredRoot':str(TARGET),'retiredFiles':319,'retiredLogicalBytes':5595971,
  'actualOriginalRootExitCode':0,'actualOriginalJobBeforeClose':0,'freshSuccessfulCIMZero':True,'allFinalPathsBoundedAndNoReparse':True,
  'retainedOriginalSourceCopiesAndFixedIndexAllSHA256Matched':True,'fiveCurrentProductsSHAUnchanged':True,
  'diskFreeBeforeBytes':before,'diskFreeAfterBytes':after,'observedDeltaBytes':after-before,'notExclusivePhysicalAttribution':True,
  'allGISDLGModelsBusinessUploadsConfigurationKept':True,'serverHistoryDeleted':False,'publicUnchangedR51':True,
  'oldBuildSourceCopyRemovedRebuildNeedsPrepareFromFixedIndex':True}
 with report.open('x',encoding='utf8')as f:f.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
