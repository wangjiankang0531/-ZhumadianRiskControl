"""Load original team detail and linked members together, with current-record checks."""
from pathlib import Path
from contextlib import contextmanager
import hashlib,json
REL='src/views/emergencyResources/firstAidTeams/info/detail.vue';PIN='ece90a6dc068207d4495cfaf6c1a0eccf664c4db5bd1f13767541df469788eb9'
def sha(b):return hashlib.sha256(b).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('EXACT_ORIGINAL_TEAM_DETAIL_REQUIRED')
 return s.replace(a,b,1)
def transform(raw):
 if sha(raw)!=PIN:raise ValueError('PINNED_ORIGINAL_TEAM_DETAIL_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';s=raw.decode().replace('\r\n','\n');s=one(s,'import { ref, onMounted } from "vue";','import { ref, watch, onBeforeUnmount } from "vue";')
 s=one(s,'<template>','''<template>
  <el-alert v-if="loadState === 'error'" title="队伍详情未加载完成，请重新加载。" type="error" :closable="false" show-icon />
  <el-button v-if="loadState === 'error'" @click="loadDetail">重新加载</el-button>
  <div v-if="loadState === 'loading'" role="status">正在加载队伍详情</div>
  <div v-if="loadState === 'ready'">''');s=one(s,'</template>','  </div>\n</template>')
 start=s.index('onMounted(async () => {');end=s.index('\n});',start)+len('\n});')
 s=s[:start]+'''const loadState = ref<"loading" | "ready" | "error">("loading");
let generation = 0;
let mounted = true;
const loadDetail = async () => {
  const epoch = ++generation;
  const id = typeof route.query.id === "string" ? route.query.id : "";
  field.value = {};
  list.value = [];
  loadState.value = "loading";
  if (!id) { loadState.value = "error"; return; }
  const current = () => mounted && epoch === generation && route.query.id === id;
  try {
    const response: any = await getById({ id });
    if (!current()) return;
    const data = response?.data;
    if (response?.code !== 0 || !data?.teams || String(data.teams.id) !== id || !Array.isArray(data.members) || data.members.some(row => !row || String(row.teamId) !== id)) throw new Error("TEAM_DETAIL_NOT_CONFIRMED");
    field.value = { ...data.teams };
    list.value = data.members.map(row => ({ ...row }));
    loadState.value = "ready";
  } catch {
    if (current()) loadState.value = "error";
  }
};
watch(() => route.query.id, loadDetail, { immediate: true });
onBeforeUnmount(() => { mounted = false; generation++; });'''+s[end:]
 out=s.replace('\n',nl).encode();return out,{'path':REL,'originalSHA256':PIN,'adaptedSHA256':sha(out),'teamAndMembersSetFromSameConfirmedResponse':True,'currentIdAndMemberTeamIdsChecked':True,'failedOrLateResponseCannotDisplayOldTeamOrMembers':True,'originalReadonlyListFieldsMapAndApiPreserved':True}
def prepare(output):
 p=Path(output)/'detail.vue';data,row=transform(p.read_bytes());p.write_bytes(data);(Path(output)/'detail-members-receipt.json').write_bytes((json.dumps(row,ensure_ascii=False,indent=2)+'\n').encode());return row
@contextmanager
def team_detail_override(project,reference):
 project=Path(project).resolve(strict=True);reference=Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_TEAM_DETAIL_BUILD_COPY_REQUIRED')
 p=project/REL;origin=reference/REL
 if p.resolve(strict=True)!=p or p.is_symlink() or p.samefile(origin) or getattr(p.lstat(),'st_file_attributes',0)&0x400 or p.read_bytes()!=origin.read_bytes():raise ValueError('EXACT_DISTINCT_TEAM_DETAIL_SOURCE_REQUIRED')
 raw=p.read_bytes();data,row=transform(raw);p.write_bytes(data);result={'files':[row],'originalSourcesRestored':False}
 try:yield result
 finally:
  if p.read_bytes()!=data:raise ValueError('EXTERNAL_TEAM_DETAIL_EDIT_PRESERVED')
  p.write_bytes(raw);result['originalSourcesRestored']=True
