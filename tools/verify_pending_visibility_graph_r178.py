from pathlib import Path
import json,hashlib,re,datetime,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;sys.path.insert(0,str(V))
from original_workflow_pending_visibility_r178 import transform,RELATIVE
W=R/'work/user_feedback_20261031/workflow-pending-visibility-r178';F=W/'dist';read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=read(W/'full-build-result.json');assert m['passed']and m['sourceRestored']and m['changedSourcePaths']==[RELATIVE]
rows=m['compiledFiles'];assert len(rows)==338
assert {p.relative_to(F).as_posix()for p in F.rglob('*')if p.is_file()}==set(rows)
for n,p in rows.items():assert (F/n).stat().st_size==p['bytes']and sha(F/n)==p['sha256']
missing=[];count=0
for name in rows:
 if Path(name).suffix not in {'.js','.css','.html'}:continue
 text=(F/name).read_text(encoding='utf-8');refs=re.findall(r'''["']([^"'\r\n]{1,220}\.(?:js|css|woff2?|ttf|svg|png|jpe?g|gif|ico)(?:\?[^"']*)?)["']''',text)
 if name.endswith('.css'):refs+=re.findall(r'''url\(([^)"']+)\)''',text)
 for ref in refs:
  if ref.startswith(('http:','https:','data:','blob:','//','#')):continue
  ref=ref.split('?',1)[0].split('#',1)[0]
  if ref.startswith('/zhumadian/emergency/'):p=F/ref.removeprefix('/zhumadian/emergency/')
  elif ref.startswith('assets/'):p=F/ref
  elif ref.startswith(('./','../')):p=(F/name).parent/ref
  else:continue
  count+=1
  if not p.resolve().is_relative_to(F.resolve())or not p.is_file():missing.append({'consumer':name,'reference':ref})
assert not missing,missing[:5]
origin=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'/RELATIVE
generated,pin=transform(origin.read_bytes());candidate=R/'Application/tools/frontend/WorkflowInfoPendingVisibilityR178.vue'
assert generated==candidate.read_bytes()and sha(origin)==pin['beforeSHA256']
proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'compiledFileCount':len(rows),'localAssetReferencesChecked':count,'missingAssets':0,'exactR33CompilerSourceDelta':[RELATIVE],'sourceRestored':True,'candidateVueIndependentlyRegenerated':True,'candidateSHA256':sha(candidate),'membershipMatchesProcessAndExactOperator':True,'publicInstalled':False,'wholeAcceptance':False}
(W/'graph-and-source-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
