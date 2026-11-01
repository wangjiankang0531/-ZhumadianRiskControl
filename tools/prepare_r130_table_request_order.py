from pathlib import Path
import hashlib,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';B=R/'work/user_feedback_20261031';old=B/'emergency-workflow-source-r9';new=B/'emergency-workflow-source-r10';assert not new.exists()
relative='src/hooks/useTable.ts';original=(old/'source'/relative).read_bytes();pin=hashlib.sha256(original).hexdigest()
helper='''"""Only the exact original table hook: newest request owns rows, loading and callbacks."""
import hashlib
PIN='''+repr(pin)+'''
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_TABLE_REQUEST_HOOK_REQUIRED')
 nl='\\r\\n'if b'\\r\\n'in raw else'\\n';s=raw.decode().replace('\\r\\n','\\n')
 replacements=[
 ('import { reactive, computed, toRefs } from "vue";','import { reactive, computed, toRefs, onBeforeUnmount } from "vue";'),
 ('  const getTableList = async () => {\\n    if (!api) return;', '  let requestGeneration = 0;\\n  let disposed = false;\\n  onBeforeUnmount(() => { disposed = true; requestGeneration++; });\\n  const getTableList = async () => {\\n    if (!api || disposed) return;\\n    const generation = ++requestGeneration;'),
 ('      dataCallBack && (data = dataCallBack(data));','      if (disposed || generation !== requestGeneration) return;\\n      dataCallBack && (data = dataCallBack(data));\\n      if (disposed || generation !== requestGeneration) return;'),
 ('      requestError && requestError(error);','      if (!disposed && generation === requestGeneration) requestError && requestError(error);'),
 ('      state.loading = false;','      if (!disposed && generation === requestGeneration) state.loading = false;')]
 for a,b in replacements:
  if s.count(a)!=1:raise ValueError('EXACT_TABLE_REQUEST_ANCHOR_REQUIRED')
  s=s.replace(a,b,1)
 result=s.replace('\\n',nl).encode()
 reverse=s
 for a,b in reversed(replacements):
  if reverse.count(b)!=1:raise ValueError('EXACT_TABLE_GUARD_REVERSE_REQUIRED')
  reverse=reverse.replace(b,a,1)
 if reverse.replace('\\n',nl).encode()!=raw:raise ValueError('TABLE_NON_REQUEST_SEMANTICS_CHANGED')
 return result,{'inputSHA256':PIN,'adaptedSHA256':hashlib.sha256(result).hexdigest(),'onlyLatestRequestOwnsRowsLoadingAndCallbacks':True,'unmountedInstanceIgnoresLateResults':True,'allOtherOriginalHookBytesRestorable':True}
'''
(T/'original_table_request_order_compat.py').write_text(helper,encoding='utf-8')
import importlib.util
spec=importlib.util.spec_from_file_location('request_order',T/'original_table_request_order_compat.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);updated,receipt=m.transform(original)
shutil.copytree(old/'source',new/'source',copy_function=os.link);p=new/'source'/relative;p.unlink();p.write_bytes(updated)
stored=T/'frontend/emergency-table-request-order'/relative;stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(updated)
meta=json.loads((old/'source-closure.json').read_bytes());key=relative.removeprefix('src/');meta['sourceFiles'][key]={'source':str(stored),'sha256':hashlib.sha256(updated).hexdigest(),'bytes':len(updated),'overlay':True};meta['overlayFiles']=sorted(set(meta['overlayFiles'])|{key});meta['tableRequestOrderAdaptation']={'path':relative,**receipt}
(new/'source-closure.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
diff=[]
for p in(old/'source').rglob('*'):
 if p.is_file()and p.read_bytes()!=(new/'source'/p.relative_to(old/'source')).read_bytes():diff.append(p.relative_to(old/'source').as_posix())
assert diff==[relative];(new/'table-request-order-source-proof.json').write_text(json.dumps({'onlyOneOriginalHookChanged':True,'previousAllGuardsAndWorkflowImportSourcesUnchanged':True,**receipt},indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
 p=T/name;s=p.read_text(encoding='utf-8');needle="'r7','r8','r9'";assert needle in s;s=s.replace(needle,"'r7','r8','r9','r10'");p.write_text(s,encoding='utf-8')
print(json.dumps({'revision':'r10','onlyHookSourceChanged':True,'sourceFiles':len(meta['sourceFiles']),'overlays':len(meta['overlayFiles']),'actualRuntimePending':True}))
