"""Team editor only: retain R6 result contract; confirm current record and one in-flight save."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json
R=Path('D:/Project/Zhumadian');EDITOR='src/views/emergencyResources/firstAidTeams/info/addOrEdit.vue';PARENT='src/views/emergencyResources/firstAidTeams/info/index.vue';BASE_EDITOR='b882af48e47e2ff01314e313b2ad4a5123e011840cfafd753503037a3eed4c70';PARENT_PIN='afd5665bd8c5468bc5b80398327ccde9bb31db3b0153cb13ad6a07dc95e1cab0'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('EXACT_TEAM_EDITOR_SOURCE_REQUIRED')
 return s.replace(a,b,1)
STATE='''const loadState = ref<"loading" | "ready" | "error">("loading");
const loadError = ref("");
const isSubmitting = ref(false);
let mounted = true;
let generation = 0;
let loadedKey = "";
const context = () => {
  const type = route.query.type;
  const id = typeof route.query.id === "string" ? route.query.id : "";
  if ((type !== "add" && type !== "edit") || (type === "edit" && !id)) return null;
  return { type, id: type === "edit" ? id : "", actor: userStore.info?.userId, department: userStore.info?.departmentId };
};
const keyOf = (value: ReturnType<typeof context>) => value ? JSON.stringify([value.type, value.id, value.actor ?? null, value.department ?? null]) : "";
const current = (epoch: number, key: string) => mounted && epoch === generation && key !== "" && key === keyOf(context());
const canSubmit = computed(() => mounted && loadState.value === "ready" && loadedKey === keyOf(context()) && !isSubmitting.value && !!form1Ref.value);
const loadCurrent = async () => {
  const epoch = ++generation;
  const value = context();
  const key = keyOf(value);
  loadedKey = "";
  field.value = {};
  list.value = [];
  loadError.value = "";
  loadState.value = "loading";
  if (!value) {
    loadState.value = "error";
    loadError.value = "队伍标识或操作方式无效，请返回列表重新选择。";
    return;
  }
  if (value.type === "add") { loadedKey = key; loadState.value = "ready"; return; }
  try {
    const response = await getById({ id: value.id });
    if (!current(epoch, key)) return;
    const data = response?.data;
    if (response?.code !== 0 || !data?.teams || String(data.teams.id) !== value.id || !Array.isArray(data.members) || data.members.some(row => !row || String(row.teamId) !== value.id)) throw new Error("TEAM_DETAIL_NOT_CONFIRMED");
    field.value = { ...data.teams };
    list.value = data.members.map(row => ({ ...row }));
    loadedKey = key;
    loadState.value = "ready";
  } catch {
    if (!current(epoch, key)) return;
    loadState.value = "error";
    loadError.value = "队伍信息加载未完成，请重新加载后再编辑。";
  }
};
'''
SUBMIT='''const handleSubmit = async () => {
  if (!canSubmit.value) return;
  const value = context();
  if (!value) return;
  const epoch = generation;
  const key = keyOf(value);
  isSubmitting.value = true;
  try {
    const valid = await form1Ref.value!.validate();
    if (!valid || !current(epoch, key) || loadedKey !== key) return;
    const payload = { ...field.value };
    if (value.type === "edit") {
      if (String(payload.id) !== value.id) return;
      payload.id = value.id;
      payload.updatedBy = value.actor;
    } else {
      delete payload.id;
      payload.createdBy = value.actor;
      payload.createDept = value.department;
    }
    const members = list.value.map(row => ({ ...row }));
    if (value.type === "edit" && members.some(row => row.teamId != null && String(row.teamId) !== value.id)) return;
    const response = await (value.type === "edit" ? updateById : save)({ teams: payload, members });
    if (!current(epoch, key)) return;
    if (response?.code !== 0 || response?.data !== true) {
      ElMessage.error("保存未完成，请保留当前内容，核对队伍状态后重试。");
      return;
    }
    ElMessage.success(value.type === "edit" ? "编辑成功！" : "新增成功！");
    await router.push({ path: "/emergencyResources/firstAidTeams" });
  } catch {
    // The retained request layer reports transport/business errors; keep current inputs.
    return;
  } finally {
    isSubmitting.value = false;
  }
};

'''
def transform_editor(raw):
 if sha(raw)!=BASE_EDITOR:raise ValueError('EXACT_R6_RESULT_PROTECTED_TEAM_EDITOR_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';s=raw.decode().replace('\r\n','\n');s=one(s,'import { ref, onMounted } from "vue";','import { ref, computed, watch, onBeforeUnmount } from "vue";')
 s=one(s,'  <MyForm ref="form1Ref" :field="field" :columns="columns1">','''  <el-alert v-if="loadState === 'error'" type="error" :title="loadError" :closable="false" show-icon />
  <el-button v-if="loadState === 'error'" @click="loadCurrent">重新加载</el-button>
  <div v-if="loadState === 'loading'" role="status">正在加载队伍信息</div>
  <MyForm v-show="loadState === 'ready'" ref="form1Ref" :field="field" :columns="columns1" :disabled="loadState !== 'ready' || isSubmitting">''')
 s=one(s,'  <List v-model:data="list" />','  <fieldset v-if="loadState === \'ready\'" :disabled="isSubmitting" style="border:0;padding:0;margin:0"><List :key="generation" v-model:data="list" /></fieldset>')
 anchor='const handleSubmit = async () => {';start=s.index(anchor);end=s.index('const router = useRouter();',start);s=s[:start]+STATE+SUBMIT+s[end:]
 start=s.index('onMounted(async () => {');end=s.index('\n\ndefineExpose({',start);s=s[:start]+'''watch(() => [route.query.type, route.query.id, userStore.info?.userId, userStore.info?.departmentId], loadCurrent, { immediate: true });
onBeforeUnmount(() => { mounted = false; generation++; loadedKey = ""; });'''+s[end:]
 oldmap='    callback: val => (field.value.coordinate = val)'
 newmap='    callback: val => { if (current(epoch, key) && loadState.value === "ready" && !isSubmitting.value && loadedKey === key) field.value.coordinate = val; }'
 s=one(s,'const openMapDialog = () => {','const openMapDialog = () => {\n  if (!canSubmit.value) return;\n  const epoch = generation;\n  const key = keyOf(context());');s=one(s,oldmap,newmap)
 s=one(s,'  submit: handleSubmit' ,'  submit: handleSubmit,\n  canSubmit,\n  isSubmitting');out=s.replace('\n',nl).encode();return out,{'path':EDITOR,'inputSHA256':BASE_EDITOR,'adaptedSHA256':sha(out),'originalFieldsValidationApiAndResultContractPreserved':True,'currentIdModeAndActorReloaded':True,'oneInFlightSavePerMountedEditor':True,'lateCompletionDoesNotNavigateNewOrUnmountedEditor':True}
def transform_parent(raw):
 if sha(raw)!=PARENT_PIN:raise ValueError('EXACT_ORIGINAL_TEAM_INFO_PARENT_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';s=raw.decode().replace('\r\n','\n');s=one(s,'import { ref } from "vue";','import { computed, ref } from "vue";\nimport { ElMessage } from "element-plus";');s=one(s,'const type = route.query.type as string;','const type = computed(() => typeof route.query.type === "string" ? route.query.type : "");')
 s=one(s,'<el-button type="primary" v-if="[\'add\', \'edit\'].includes(type)" @click="addOrEditRef?.submit">提交</el-button>','''<el-button type="primary" v-if="['add', 'edit'].includes(type)" :disabled="!addOrEditRef?.canSubmit" :loading="addOrEditRef?.isSubmitting" @click="addOrEditRef?.submit">提交</el-button>''')
 s=one(s,'const handleCancel = () => {','''const handleCancel = () => {
  if (addOrEditRef.value?.isSubmitting) ElMessage.warning("正在处理的保存请求不会自动撤回，请返回列表核对结果。");''');out=s.replace('\n',nl).encode();return out,{'path':PARENT,'inputSHA256':PARENT_PIN,'adaptedSHA256':sha(out),'nativeInfoViewFooterAndCancelNavigationPreserved':True,'reactiveModeAndSubmitState':True}
def prepare(output):
 output=Path(output);rows=[]
 for name,fn in [('addOrEdit.vue',transform_editor),('Info.vue',transform_parent)]:
  p=output/name;data,receipt=fn(p.read_bytes());p.write_bytes(data);rows.append(receipt)
 (output/'identity-editor-receipt.json').write_bytes((json.dumps(rows,ensure_ascii=False,indent=2)+'\n').encode());return rows

@contextmanager
def team_editor_override(project,reference):
 from original_emergency_team_frontend_compat import transform
 project=Path(project).resolve(strict=True);reference=Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_TEAM_EDITOR_BUILD_COPY_REQUIRED')
 originals={};adapted={};receipts=[]
 for relative,fn in [(EDITOR,transform_editor),(PARENT,transform_parent)]:
  p=project/relative;origin=reference/relative;raw=transform(origin.read_bytes())[0] if relative==EDITOR else origin.read_bytes()
  if p.read_bytes()!=raw or p.resolve(strict=True)!=p or origin.resolve(strict=True)!=origin or p.samefile(origin) or p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400:raise ValueError('EXACT_RETAINED_TEAM_BUILD_SOURCE_REQUIRED')
  data,receipt=fn(raw);originals[p]=raw;adapted[p]=data;receipts.append(receipt)
 for p,data in adapted.items():p.write_bytes(data)
 result={'files':receipts,'originalSourcesRestored':False}
 try:yield result
 finally:
  for p,data in adapted.items():
   if p.read_bytes()!=data:raise ValueError('EXTERNAL_TEAM_EDITOR_CHANGE_PRESERVED')
  for p,raw in originals.items():p.write_bytes(raw)
  result['originalSourcesRestored']=True
