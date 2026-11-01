"""Reconcile uncertain native operations from original detail and own pending list."""
from pathlib import Path
import copy,hashlib,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';B=R/'work/user_feedback_20261031/emergency-workflow-source-r5';N=B.with_name('emergency-workflow-source-r6')
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(B/'independent-build-verification.json')['undeclaredSourceDifferences']==0 and not N.exists()
excluded={'node_modules','dist','.git','.cache','.vite','coverage'}
for folder,dirs,files in os.walk(B/'source',followlinks=False):
 dirs[:]=[n for n in dirs if n not in excluded]
 for name in dirs+files:assert not(Path(folder)/name).lstat().st_file_attributes&0x400
N.mkdir();shutil.copytree(B/'source',N/'source',copy_function=os.link,ignore=lambda folder,names:[n for n in names if n in excluded or '.timestamp-'in n])
metadata=copy.deepcopy(read(B/'source-closure.json'));adaptations={}
def change(relative,pairs):
 origin=B/'source'/relative;raw=origin.read_bytes();s=raw.decode();nl='\r\n'if'\r\n'in s else'\n';s=s.replace('\r\n','\n');before=s
 for old,new in pairs:assert s.count(old)==1,'EXACT_RECONCILE_SOURCE_REQUIRED:'+relative;s=s.replace(old,new,1)
 inverse=s
 for old,new in reversed(pairs):assert inverse.count(new)==1;inverse=inverse.replace(new,old,1)
 assert inverse==before and inverse.replace('\n',nl).encode()==raw
 target=N/'source'/relative;target.unlink();target.write_bytes(s.replace('\n',nl).encode());own=T/'frontend/emergency-workflow-reconcile'/relative;own.parent.mkdir(parents=True,exist_ok=True);assert not own.exists();own.write_bytes(target.read_bytes())
 adaptations[relative]={'baseSourceSHA256':sha(origin),'adaptedSHA256':sha(target),'declaredChanges':len(pairs),'reverseByteExact':True,'nativePOSTBodiesOrAuthenticationChanged':False,'noOperateAuthUsedAsApprovalPermission':False}

helper='''const pendingSignature = (data: any) => (Array.isArray(data.flowTaskOperatorRecordList) ? data.flowTaskOperatorRecordList : [])
  .filter((item: any) => Number(item.handleStatus) === 18)
  .map((item: any) => [item.taskOperatorId, item.taskNodeId, item.handleId, item.operatorId, item.nodeCode].map(value => String(value ?? "")).join("|"))
  .sort().join(";");
const initialPendingSignature = ref("");
const hasOwnPendingFlow = async (taskId: string) => {
  const deadline = Date.now() + 15000;
  let currentPage = 1, seen = 0;
  for (;;) {
    const result: any = await flowBefore1({ currentPage, pageSize: 100 });
    const list = result?.list, total = Number(result?.pagination?.total);
    if (!Array.isArray(list) || !Number.isFinite(total) || total < 0) throw new Error("PENDING_STATE_UNCONFIRMED");
    if (list.some((item: any) => String(item.id) === taskId || String(item.processInstanceId) === taskId)) return true;
    seen += list.length;
    if (seen >= total) return false;
    if (!list.length || Date.now() >= deadline) throw new Error("PENDING_STATE_UNCONFIRMED");
    currentPage++;
  }
};
const reconcileOutcome = async () => {
  const data: any = await readWorkData();
  if (!data?.flowTaskInfo?.id || String(data.flowTaskInfo.id) !== workflowTaskId.value || data.flowTaskInfo.status === undefined || data.flowTaskInfo.status === null) throw new Error("FLOW_STATE_UNCONFIRMED");
  const running = String(data.flowTaskInfo.status) === "1";
  if (props.auditType === "待办事宜" && running) {
    const pending = await hasOwnPendingFlow(String(data.flowTaskInfo.id));
    const signature = pendingSignature(data);
    if (pending && signature && signature === initialPendingSignature.value) return true;
  } else if (props.auditType === "我发起的" && running && data.approversProperties?.hasRevokeBtn !== false) {
    const signature = pendingSignature(data);
    if (signature && signature === initialPendingSignature.value) return true;
  }
  applyWorkData(data);
  auditFormIsShow.value = false;
  return false;
};
const getWorkData = async () => applyWorkData(await readWorkData());
'''
change('src/components/workflow/info.vue',[
 ('<businessForm :component-url="flowFormInfo.urlAddress" :workflow-task-id="workflowTaskId"></businessForm>','<businessForm :key="workflowTaskId + \':\' + businessRevision" :component-url="flowFormInfo.urlAddress" :workflow-task-id="workflowTaskId"></businessForm>'),
 ('const workflowTaskId = ref("");','const workflowTaskId = ref("");\nconst businessRevision = ref(0);'),
 ('import { flowInfo } from "@/api/workFlow";','import { flowInfo, flowBefore1 } from "@/api/workFlow";'),
 ('            :form-data="formData"','            :form-data="formData"\n            :reconcile-outcome="reconcileOutcome"'),
 ('const getWorkData = async () => {','const readWorkData = async () => {'),
 ('  const res: any = await flowInfo(route.query.id as string, params);','  return await flowInfo(route.query.id as string, params);\n};\nconst applyWorkData = (res: any) => {\n  initialPendingSignature.value = pendingSignature(res);\n  businessRevision.value++;'),
 ('onMounted(() => {\n  getWorkData();',helper+'\nonMounted(() => {\n  getWorkData();')])
reconcile='''const outcomeUncertain = ref(false);
const reconcileUncertainOutcome = async () => {
  outcomeUncertain.value = true;
  try {
    if (typeof props.reconcileOutcome !== "function") throw new Error("FLOW_STATE_UNCONFIRMED");
    const mayRetry = await props.reconcileOutcome();
    if (mayRetry !== true && mayRetry !== false) throw new Error("FLOW_STATE_UNCONFIRMED");
    outcomeUncertain.value = false;
    if (mayRetry) ElMessage.error("提交失败，请重试");
    else ElMessage.info("流程状态已更新，请查看最新待办和审批记录");
  } catch {
    ElMessage.warning("暂时无法确认提交结果，请先核对流程状态");
  } finally {
    isSubmit.value = false;
  }
};
'''
change('src/components/workflow/components/auditForm.vue',[
 ('@click="submitForm(ruleFormRef)"> 提交 </el-button>','@click="submitForm(ruleFormRef)"> {{ outcomeUncertain ? "核对提交结果" : "提交" }} </el-button>'),
 ('  isEnablePrepositionCancel: {','  reconcileOutcome: { type: Function },\n  isEnablePrepositionCancel: {'),
 ('const isSubmit = ref(false);','const isSubmit = ref(false);\n'+reconcile),
 ('  isSubmit.value = true;\n  try {\n    const valid','  isSubmit.value = true;\n  if (outcomeUncertain.value) {\n    await reconcileUncertainOutcome();\n    return;\n  }\n  try {\n    const valid'),
 ('    // Keep server error notifications and add a fallback for transport failures without a response.\n    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");','    // Preserve the draft until the original service confirms whether this operation is still pending.\n    await reconcileUncertainOutcome();')])
metadata['runtimeSourceAdaptations'].update(adaptations);metadata['uncertainOutcomeAdaptations']=adaptations;metadata['sourceRevision']='r6';(N/'source-closure.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
p=T/'build_emergency_workflow_source_20261101.mjs';s=p.read_bytes().decode();old="['r1','r2','r3','r4','r5']";assert s.count(old)==1;p.write_bytes(s.replace(old,"['r1','r2','r3','r4','r5','r6']").encode())
p=T/'verify_emergency_workflow_source_20261101.py';s=p.read_bytes().decode();assert s.count(old)==1;s=s.replace(old,"['r1','r2','r3','r4','r5','r6']");old="'taskStateDisplayDeclaredChangedFiles':len(c.get('taskStateDisplayAdaptations',{}))";assert s.count(old)==1;s=s.replace(old,old+",'uncertainOutcomeDeclaredChangedFiles':len(c.get('uncertainOutcomeAdaptations',{}))");p.write_bytes(s.encode())
print('WF6_TWO_SOURCE_NATIVE_OUTCOME_RECONCILIATION_PREPARED_NOT_INSTALLED')
