"""Only the exact original table hook: newest request owns rows, loading and callbacks."""
import hashlib
PIN='f0317e64feb283055dc62c41a8554f978e1de21716577f6b31e6810c25c5e89d'
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_TABLE_REQUEST_HOOK_REQUIRED')
 nl='\r\n'if b'\r\n'in raw else'\n';s=raw.decode().replace('\r\n','\n')
 replacements=[
 ('import { reactive, computed, toRefs } from "vue";','import { reactive, computed, toRefs, onBeforeUnmount } from "vue";'),
 ('  const getTableList = async () => {\n    if (!api) return;', '  let requestGeneration = 0;\n  let disposed = false;\n  onBeforeUnmount(() => { disposed = true; requestGeneration++; });\n  const getTableList = async () => {\n    if (!api || disposed) return;\n    const generation = ++requestGeneration;'),
 ('      dataCallBack && (data = dataCallBack(data));','      if (disposed || generation !== requestGeneration) return;\n      dataCallBack && (data = dataCallBack(data));\n      if (disposed || generation !== requestGeneration) return;'),
 ('      requestError && requestError(error);','      if (!disposed && generation === requestGeneration) requestError && requestError(error);'),
 ('      state.loading = false;','      if (!disposed && generation === requestGeneration) state.loading = false;')]
 for a,b in replacements:
  if s.count(a)!=1:raise ValueError('EXACT_TABLE_REQUEST_ANCHOR_REQUIRED')
  s=s.replace(a,b,1)
 result=s.replace('\n',nl).encode()
 reverse=s
 for a,b in reversed(replacements):
  if reverse.count(b)!=1:raise ValueError('EXACT_TABLE_GUARD_REVERSE_REQUIRED')
  reverse=reverse.replace(b,a,1)
 if reverse.replace('\n',nl).encode()!=raw:raise ValueError('TABLE_NON_REQUEST_SEMANTICS_CHANGED')
 return result,{'inputSHA256':PIN,'adaptedSHA256':hashlib.sha256(result).hexdigest(),'onlyLatestRequestOwnsRowsLoadingAndCallbacks':True,'unmountedInstanceIgnoresLateResults':True,'allOtherOriginalHookBytesRestorable':True}
