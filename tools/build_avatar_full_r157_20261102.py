from pathlib import Path
from contextlib import contextmanager
import datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).parent;W=R/'work/user_feedback_20261031';ROOT=W/'avatar-full-r157'
sys.path.insert(0,str(T));sys.dont_write_bytecode=True
from original_header_avatar_compat import header_avatar_override,HEADER,EXTRA,adapt_header_avatar
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def inventory(root):
 result={}
 for parent,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if n not in ['node_modules','.git','dist','.vite']]
  for n in names:
   p=Path(parent)/n
   if n=='node_modules':continue
   assert p.resolve()==p and not p.is_symlink() and not p.is_junction()
   result[p.relative_to(root).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
 return result
def own_copy(origin,target):
 rows=inventory(origin);amount=sum(x['bytes']for x in rows.values());free=shutil.disk_usage(R).free
 assert amount<1024**3 and free>amount*2+512*1024**2 and not target.exists()
 target.mkdir(parents=True)
 dump(target.parent/'storage-plan.json',{'sourceBytes':amount,'sourceFiles':len(rows),'freeBefore':free,'conservativeAdditionalBudget':amount*2+512*1024**2,'noAssetsCopied':True,'dependenciesShared':True})
 for n in rows:
  p=target/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin/n,p)
 assert inventory(target)==rows;return rows
def normal_run(command,**kwargs):
 kwargs.pop('timeout',None);p=subprocess.Popen(command,**kwargs);p.wait();return subprocess.CompletedProcess(command,p.returncode)
def main():
 sys.stdout.reconfigure(encoding='utf-8');role=sys.argv[1];assert role in ['security_pc','emergency_pc'];stage=ROOT/role;assert not stage.exists()
 current=J(W/'r31-task-unified-candidate-r2/bundle/payload/payload-manifest.json')['files'];baseline=W/('security-build-risk-r22-from-r21-r2/build/dist'if role=='security_pc'else'emergency-workflow-source-r17/dist')
 oldfiles={n.split('/',2)[2]:p for n,p in current.items()if n.startswith('frontend/'+role+'/')}
 assert all(sha(baseline/n)==p['sha256']for n,p in oldfiles.items())
 adapter={};captured={};original_run=subprocess.run
 def intercept(command,*args,**kwargs):
  if isinstance(command,list)and any('vite' in str(x) and str(x).endswith('vite.js')for x in command):
   project=Path(kwargs['cwd']);captured.update(inventory(project));return normal_run(command,**kwargs)
  return original_run(command,*args,**kwargs)
 if role=='security_pc':
  import build_risk_frontend_r22_r2_20261101 as recipe
  import original_public_login_query_compat_20261101 as login
  old_login=login.published_login_query_override
  @contextmanager
  def combined(project,reference):
   with old_login(project,reference) as original,header_avatar_override(project)as avatar:
    adapter.update(avatar);adapter['receipt']=avatar;yield original
  login.published_login_query_override=combined;recipe.STAGE=stage;subprocess.run=intercept
  try:recipe.main()
  finally:subprocess.run=original_run;login.published_login_query_override=old_login
  assert adapter['receipt']['originalSourcesRestored'];dist=stage/'build/dist';after=inventory(stage/'source')
  dump(stage/'actual-compiled-source-files.json',captured)
  cfg=J(R/'Document/Deployment/confirmed_operations_20261029/security-build-r2-config.json')
  assert after==inventory(Path(cfg['project']))
  retained=J(ROOT/'security-baseline-source-capture/actual-retained-recipe-source-files.json')
  assert {n for n in set(retained)|set(captured)if retained.get(n)!=captured.get(n)}=={HEADER,EXTRA}
 else:
  origin=W/'emergency-workflow-source-r17/source';before=own_copy(origin,stage/'source')
  with header_avatar_override(stage/'source')as receipt:
   adapter=receipt;captured=inventory(stage/'source');assert set(captured)==set(before)|{EXTRA}
   assert {n:p for n,p in captured.items()if n not in[HEADER,EXTRA]}=={n:p for n,p in before.items()if n!=HEADER}
   assert (stage/'source'/HEADER).read_bytes()==adapt_header_avatar((origin/HEADER).read_bytes())
   with(stage/'build.log').open('wb')as log:p=normal_run(['D:/Program Files/nodejs/node.exe',str(V/'build_avatar_full_r157_20261102.mjs'),role],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   assert p.returncode==0
  assert receipt['originalSourcesRestored'] and inventory(stage/'source')==before and inventory(origin)==before
  dump(stage/'actual-compiled-source-files.json',captured);dist=stage/'dist'
 files=inventory(dist);assert files and (dist/'index.html').is_file()
 for rel in[HEADER,EXTRA]:assert rel in captured
 assert captured[EXTRA]['sha256']==sha(T/'frontend/OriginalHeaderAvatarSource.ts')
 dump(stage/'full-build-result.json',{'at':datetime.datetime.now().astimezone().isoformat(),'role':role,'buildPassed':True,'baselinePublicR31FrontendFilesExact':len(oldfiles),'compiledFiles':files,'fileCount':len(files),'actualCompiledSourceFiles':len(captured),'actualSourcePinsSHA256':sha(stage/'actual-compiled-source-files.json'),'onlyAvatarHeaderAndHelperAddedToRetainedRecipe':True,'avatarAdapter':adapter,'sourceRestored':True,'allPreviousRecipeAdaptersRetained':True,'actualFullCompiledBrowserAccepted':False,'publicInstalled':False,'fullCloneReady':False})
 print(json.dumps({'role':role,'buildPassed':True,'files':len(files),'actualSourceFiles':len(captured),'sourceRestored':True,'publicInstalled':False}))
if __name__=='__main__':main()
