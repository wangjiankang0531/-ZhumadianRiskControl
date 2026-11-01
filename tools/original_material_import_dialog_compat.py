"""Derive a material-only import dialog with response and request identity checks."""
from contextlib import contextmanager
from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian')
ROOT='src/views/emergencyResources/materials/index.vue'
DIALOG='src/components/ImportExcel/index.vue'
ADAPTED='src/components/ImportExcel/OriginalMaterialExcelImport.vue'
PINS={ROOT:'5fac9639d7634049e5aabb86fb913ae208409a5ca141bdbaaaeb04dd36ec872a',DIALOG:'83fa2468d61028eea168ee8092d84ddc19a0e0654d1254903a775167f72d7c81'}
def sha(b):return hashlib.sha256(b).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('EXACT_MATERIAL_IMPORT_PATCH_REQUIRED:'+a[:50])
 return s.replace(a,b,1)
def confirmed_root(raw):
 from original_confirmed_operation_compat import catalog,transform_caller
 if sha(raw)!=PINS[ROOT]:raise ValueError('PINNED_MATERIAL_ROOT_BEFORE_CONFIRMATION_REQUIRED')
 return transform_caller(raw,catalog()['kindResults']['emergency_pc']['files'][ROOT])
def transform(kind,raw):
 if kind not in PINS:raise ValueError('PINNED_ORIGINAL_MATERIAL_IMPORT_REQUIRED')
 if sha(raw)!=PINS[kind]:
  if kind!=ROOT or raw!=confirmed_root((reference()/ROOT).read_bytes()):raise ValueError('PINNED_ORIGINAL_MATERIAL_IMPORT_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';s=raw.decode('utf8').replace('\r\n','\n')
 if kind==ROOT:
  s=one(s,'import ImportExcel from "@/components/ImportExcel/index.vue";','import ImportExcel from "@/components/ImportExcel/OriginalMaterialExcelImport.vue";')
 else:
  s=one(s,':destroy-on-close="true" width="580px"',':destroy-on-close="true" :before-close="beforeClose" width="580px"')
  s=one(s,'import { ref } from "vue";','import { ref, onBeforeUnmount } from "vue";')
  s=one(s,'          :on-success="excelUploadSuccess"\n','');s=one(s,'          :on-error="excelUploadError"\n','')
  s=one(s,'const acceptParams = (params: ExcelParameterProps) => {','''let dialogEpoch = 0;
let requestSerial = 0;
let currentRequest = 0;
let mounted = true;
const pendingRequests = new Map<number, number>();
onBeforeUnmount(() => {
  mounted = false;
  dialogEpoch++;
});
const beforeClose = (done: () => void) => {
  if (Array.from(pendingRequests.values()).includes(dialogEpoch)) {
    ElNotification({ title: "温馨提示", message: "导入请求仍在处理，关闭窗口不会撤回已提交的请求。", type: "info" });
  }
  dialogEpoch++;
  currentRequest = 0;
  done();
};
const acceptParams = (params: ExcelParameterProps) => {
  dialogEpoch++;
  currentRequest = 0;''')
  s=one(s,'''  let excelFormData = new FormData();
  excelFormData.append("file", param.file);
  // excelFormData.append("isCover", isCover.value as unknown as Blob);
  await parameter.value.importApi!(excelFormData);
  parameter.value.getTableList && parameter.value.getTableList();
  dialogVisible.value = false;''','''  const target = { ...parameter.value };
  const epoch = dialogEpoch;
  const request = ++requestSerial;
  currentRequest = request;
  pendingRequests.set(request, epoch);
  const isCurrent = () => mounted && epoch === dialogEpoch && request === currentRequest;
  const excelFormData = new FormData();
  excelFormData.append("file", param.file);
  try {
    const response: any = await target.importApi!(excelFormData);
    const confirmed = response == null || response === "" ||
      (typeof response === "object" && response.code === 0 && response.data !== false);
    if (!confirmed) throw new Error("物资导入未确认成功。");
    if (mounted) target.getTableList && target.getTableList();
    if (isCurrent()) {
      dialogVisible.value = false;
      dialogEpoch++;
      excelUploadSuccess(target.title);
    }
    return response;
  } catch (error) {
    if (isCurrent()) excelUploadError(target.title);
    throw error;
  } finally {
    pendingRequests.delete(request);
  }''')
  s=one(s,'const excelUploadError = () => {','const excelUploadError = (title: string) => {')
  s=one(s,'message: `批量添加${parameter.value.title}失败，请您重新上传！`,','message: `批量添加${title}未确认完成，请先核对导入结果，再决定是否重新上传。`,')
  s=one(s,'const excelUploadSuccess = () => {','const excelUploadSuccess = (title: string) => {')
  s=one(s,'message: `批量添加${parameter.value.title}成功！`,','message: `批量添加${title}成功！`,')
 out=s.replace('\n',nl).encode('utf8');return out,{'source':kind,'destination':ROOT if kind==ROOT else ADAPTED,'originalSHA256':PINS[kind],'inputSHA256':sha(raw),'adaptedSHA256':sha(out),'materialOnly':True,'retainedConfirmationCallerPreserved':kind!=ROOT or raw==confirmed_root((reference()/ROOT).read_bytes()),'legacyVoidResponseSupported':True,'closedOrNewerDialogNotClosedByOldRequest':True}
def reference():return Path(json.loads((R/'Document/Deployment/emergency_plan_report_20261030/frontend-build-config-v2.json').read_bytes())['reference'])
def prepare(output):
 output=Path(output);assert output.is_dir();receipts=[]
 for kind,name in [(ROOT,'materials.vue'),(DIALOG,'OriginalMaterialExcelImport.vue')]:
  raw=(reference()/kind).read_bytes();data,receipt=transform(kind,confirmed_root(raw) if kind==ROOT else raw);p=output/name;assert not p.exists();p.write_bytes(data);receipts.append(receipt)
 from original_confirmed_operation_compat import transform_hook
 hook=output/'useHandleData.ts';assert not hook.exists();hook.write_bytes(transform_hook((reference()/'src/hooks/useHandleData.ts').read_bytes()))
 (output/'receipt.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return receipts
@contextmanager
def material_import_dialog_override(project,origin):
 project=Path(project).resolve(strict=True);origin=Path(origin).resolve(strict=True)
 if project==origin or project.is_relative_to(origin) or origin.is_relative_to(project):raise ValueError('DISTINCT_BUILD_COPY_REQUIRED')
 old=project/ROOT;new=project/ADAPTED;raw=confirmed_root((origin/ROOT).read_bytes())
 if old.read_bytes()!=raw or old.is_symlink() or getattr(old.lstat(),'st_file_attributes',0)&0x400 or old.samefile(origin/ROOT) or old.resolve(strict=True)!=old or new.exists() or new.is_symlink():raise ValueError('FRESH_MATERIAL_DIALOG_BUILD_REQUIRED')
 root,rr=transform(ROOT,raw);dialog,dr=transform(DIALOG,(origin/DIALOG).read_bytes());old.write_bytes(root);new.write_bytes(dialog);receipt={'files':[rr,dr],'genericImportComponentUnchanged':True,'originalSourcesRestored':False}
 try:yield receipt
 finally:
  if old.read_bytes()!=root or new.read_bytes()!=dialog:raise ValueError('EXTERNAL_MATERIAL_DIALOG_EDIT_PRESERVED')
  old.write_bytes(raw);new.unlink();receipt['originalSourcesRestored']=True
