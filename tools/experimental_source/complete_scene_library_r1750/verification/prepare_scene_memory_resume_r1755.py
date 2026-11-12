"""Memory refusal occurred before any child; remove only its empty root and move gate before mkdir."""
from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/su1752';D=R/'Document/Deployment/fine_browser_original_r1748_20261107'
assert W.is_dir()and not list(W.iterdir())and W.resolve()==W and W.parent==R/'work'and not W.is_symlink()and not W.is_junction()
r=json.loads((R/'work/su1751/verified-result.json').read_bytes());assert r['originalCodeRestored']and r['originalPointerRestored']and r['allActualJobsZeroBeforeClose']
source=V/'launch_original_configuration_lifecycle_r1752.py';s=source.read_text('utf8')
a="assert not W.exists();W.mkdir();assert not(W/'parent-started-r1752.json').exists()and not(W/'harness-started-r1752.json').exists()"
assert s.count(a)==1;s=s.replace(a,"assert not W.exists()")
b="assert min(memory['availablePhysicalBytes'],memory['availableCommitBytes'])>=15*1024**3";assert s.count(b)==1;s=s.replace(b,b+"\nW.mkdir();assert not(W/'parent-started-r1752.json').exists()and not(W/'harness-started-r1752.json').exists()")
ast.parse(s);target=V/'launch_original_configuration_lifecycle_r1755.py';assert not target.exists();target.write_text(s,encoding='utf8')
W.rmdir() # Exact, empty-only, non-recursive. No restore/database or scene directory involved.
proof={'prepared':True,'priorMemoryGateRejectedBeforeAnyChildOrApplicationChange':True,'onlyEmptyUnstartedRunDirectoryRemoved':str(W),'memoryGateMovedBeforeRunDirectoryAllocation':True,'minimumPhysicalAndCommitGiBUnchanged':15,'sameReadOnlyHarnessAndPinnedProductPlan':True,'successfulSceneCreateNotReplayed':True,'publicChanged':False,'oldLauncherSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'newLauncherSHA256':hashlib.sha256(target.read_bytes()).hexdigest()}
p=D/'memory-resume-r1755.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
