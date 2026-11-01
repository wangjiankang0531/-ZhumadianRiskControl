"""Settle original confirmation operations and gate every catalogued caller on success."""
from contextlib import contextmanager
from pathlib import Path
import hashlib,json,os,uuid
HERE=Path(__file__).resolve().parent
CATALOG_SHA256='80ff80179d254cc77d4d8134b6bd75659b3995a3122ee78a5629f004115daf07'
HOOK_SHA256='e054023b17ae087eb1e4c1cb07f37567c147043f434b9904c9fa1be33579ae28'
NOTICE='未完成，请核对记录状态后重试。'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def need(v,c):
 if not v:raise ValueError(c)
def catalog():
 p=HERE/'original_confirmed_operation_callers_20261029.json';raw=p.read_bytes();need(digest(raw)==CATALOG_SHA256,'PINNED_CONFIRMATION_CATALOG_REQUIRED');v=json.loads(raw)
 for kind,calls,files in [('security_pc',46,40),('emergency_pc',9,9)]:
  row=v['kindResults'][kind];need(row['activeCallCount']==calls and row['activeCallerFiles']==files and not row['unsupported'] and row['hook']['SHA256']==HOOK_SHA256,'COMPLETE_CONFIRMED_CALLER_SET_REQUIRED')
 return v
def transform_hook(raw):
 need(digest(raw)==HOOK_SHA256,'PINNED_ORIGINAL_CONFIRMATION_HOOK_REQUIRED');nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf8').replace('\r\n','\n');anchor='export const useHandleData = (';need(text.count(anchor)==1,'EXACT_ORIGINAL_CONFIRMATION_EXPORT');prefix=text[:text.index(anchor)]
 original_options='''ElMessageBox.confirm(`是否${message}?`, "温馨提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: confirmType,
      draggable: true
    })'''
 need(text.count(original_options)==1,'EXACT_ORIGINAL_CONFIRMATION_OPTIONS')
 body='''export const useHandleData = async (
  api: (params: any) => Promise<any>,
  params: any = {},
  message: string,
  confirmType: HandleData.MessageType = "warning"
): Promise<boolean> => {
  try {
    await '''+original_options+''';
  } catch {
    return false;
  }
  let response: any;
  try {
    response = await api(params);
  } catch {
    return false;
  }
  const succeeded = response === true || (
    response !== null && typeof response === "object" &&
    (response.code === 0 || response.code === 200) && response.data !== false
  );
  if (!succeeded) {
    ElMessage({ type: "error", message: `${message}'''+NOTICE+'''` });
    return false;
  }
  ElMessage({ type: "success", message: `${message}成功!` });
  return true;
};
'''
 return (prefix+body).replace('\n',nl).encode('utf8')
def extra_control_flow_patches(raw,row):
 calls=row['calls']
 if not calls or calls[0]['path']!='src/views/intelligentInspection/responsibility/index.vue':return []
 need(len(calls)==2 and {c['api'] for c in calls}=={'postDuty.removeById','postPerson.removeById'} and all(c['functionName']=='handleDelete' for c in calls),'EXACT_RESPONSIBILITY_CALLBACK_REQUIRED')
 function=calls[0]['enclosingVariableStatement'].encode('utf8');need(calls[1]['enclosingVariableStatement'].encode('utf8')==function and raw.count(function)==1,'EXACT_RESPONSIBILITY_FUNCTION_SPAN')
 start=raw.index(function);patches=[]
 for old,new,label in [(b'  if (activeTab.value == "2") {',b'  else if (activeTab.value == "2") {','one-selected-tab-operation'),(b'proTable1.value!.getTableList();',b'proTable1.value?.getTableList();','unmounted-first-table-safe'),(b'proTable2.value!.getTableList();',b'proTable2.value?.getTableList();','unmounted-second-table-safe')]:
  need(function.count(old)==1,'EXACT_RESPONSIBILITY_CONTROL_ANCHOR');offset=start+function.index(old);patches.append({'startByte':offset,'endByte':offset+len(old),'originalText':old.decode('utf8'),'replacement':new.decode('utf8'),'controlFlowGuard':label})
 return patches
def transform_caller(raw,row):
 need(digest(raw)==row['originalSHA256'],'PINNED_ORIGINAL_CONFIRMED_CALLER_REQUIRED');patches=sorted([*(c['patch'] for c in row['calls']),*extra_control_flow_patches(raw,row)],key=lambda p:p['startByte'],reverse=True);updated=raw;last=len(raw)
 for patch in patches:
  start,end=patch['startByte'],patch['endByte'];need(type(start) is int and type(end) is int and 0<=start<end<=last,'DISJOINT_EXACT_CALLER_SPANS');need(raw[start:end]==patch['originalText'].encode('utf8'),'EXACT_ORIGINAL_AWAIT_SPAN');need(bool(patch.get('controlFlowGuard')) or patch['replacement']=='if (!('+patch['originalText'].rstrip(';')+')) return;','EXACT_FALSE_RETURN_GUARD_REQUIRED');updated=updated[:start]+patch['replacement'].encode('utf8')+updated[end:];last=start
 return updated
def regular(p):
 for q in [p,*p.parents]:
  need(not q.is_symlink() and (not q.exists() or not getattr(q.lstat(),'st_file_attributes',0)&0x400),'REGULAR_CONFIRMATION_SOURCE_REQUIRED')
 need(p.is_file() and p.resolve(strict=True)==p,'REGULAR_CONFIRMATION_FILE_REQUIRED');return p
def prepare(kind,project,reference):
 v=catalog();need(kind in v['kindResults'],'EXACT_CONFIRMATION_KIND_REQUIRED');project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True);need(project!=reference and not project.is_relative_to(reference) and not reference.is_relative_to(project),'DISTINCT_CONFIRMATION_BUILD_COPY_REQUIRED');row=v['kindResults'][kind];plans=[]
 for rel,details in [(row['hook']['path'],None),*sorted(row['files'].items())]:
  target,origin=project/rel,reference/rel;regular(target);regular(origin);need(not target.samefile(origin),'DISTINCT_CONFIRMATION_FILES_REQUIRED');raw=origin.read_bytes();updated=transform_hook(raw) if details is None else transform_caller(raw,details);need(target.read_bytes()==raw,'CONFIRMATION_BUILD_COPY_DRIFT');plans.append((target,raw,updated,{'file':rel,'originalSHA256':digest(raw),'adaptedSHA256':digest(updated),'guardedCalls':0 if details is None else len(details['calls']),'controlFlowGuards':[] if details is None else [x['controlFlowGuard'] for x in extra_control_flow_patches(raw,details)]}))
 return plans,{'kind':kind,'catalogSHA256':CATALOG_SHA256,'originalHookSHA256':HOOK_SHA256,'activeCallCount':row['activeCallCount'],'callerFileCount':row['activeCallerFiles'],'allFilesPrevalidated':True,'files':[p[3] for p in plans],'codeZeroAndPlatform200NonFalseVoidAndDTOResultsPreserved':True,'cancellationAndAPIRejectionSettleFalse':True,'originalConfirmationTextOptionsAndAPIPayloadPreserved':True,'falseOrUnknownCodeHasNoSuccessOrCallerFollowup':True,'referenceChanged':False,'sourceFilesRestored':False}
def replace_owned(target,expected,desired):
 regular(target);need(target.read_bytes()==expected,'EXTERNAL_CONFIRMATION_EDIT_PRESERVED');temp=target.with_name(target.name+'.xnby-confirm-'+uuid.uuid4().hex+'.tmp')
 try:
  with temp.open('xb') as f:f.write(desired);f.flush();os.fsync(f.fileno())
  regular(target);need(target.read_bytes()==expected,'EXTERNAL_CONFIRMATION_EDIT_PRESERVED');os.replace(temp,target)
 finally:
  if temp.exists():need(temp.is_file() and not temp.is_symlink(),'OWN_CONFIRMATION_TEMP_ONLY');temp.unlink()
@contextmanager
def confirmed_operation_override(kind,project,reference):
 plans,receipt=prepare(kind,project,reference);applied=[]
 try:
  for target,raw,updated,row in plans:replace_owned(target,raw,updated);applied.append((target,raw,updated))
  yield receipt
 finally:
  errors=[]
  for target,raw,updated in reversed(applied):
   try:replace_owned(target,updated,raw)
   except Exception as error:errors.append({'file':str(target),'error':type(error).__name__})
  receipt['sourceFilesRestored']=not errors;receipt['externalEditsPreserved']=errors
  if errors:raise ValueError('EXTERNAL_CONFIRMATION_EDITS_PRESERVED:'+json.dumps(errors))
