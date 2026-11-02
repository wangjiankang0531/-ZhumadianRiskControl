"""Gate the original approval form with the authenticated user's current pending list."""
from contextlib import contextmanager
from pathlib import Path
import hashlib

RELATIVE = 'src/components/workflow/info.vue'
INPUT_SHA256 = '684931ff67987b44de0db116b94797fd67fcee56ade316c8a2252190b9ec9dcf'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def transform(raw):
    if digest(raw) != INPUT_SHA256:
        raise ValueError('EXACT_RETAINED_WORKFLOW_INFO_REQUIRED')
    text = raw.decode('utf-8')
    def once(before, after):
        nonlocal text
        if text.count(before) != 1:
            raise ValueError('EXACT_WORKFLOW_PENDING_ANCHOR_REQUIRED')
        text = text.replace(before, after, 1)
    once('import { ref, onMounted } from "vue";', 'import { ref, onMounted, onBeforeUnmount } from "vue";')
    once('const auditFormIsShow = ref(true);', '''const auditFormIsShow = ref(false);
const pendingCheckMessage = ref("");
let detailLoadVersion = 0;''')
    once('''        </div>
      </div>
    </el-scrollbar>''', '''        </div>
        <div class="audit-content" v-else-if="pendingCheckMessage" role="status" aria-live="polite">
          <el-alert :title="pendingCheckMessage" type="info" :closable="false" show-icon />
        </div>
      </div>
    </el-scrollbar>''')
    once('const getWorkData = async () => applyWorkData(await readWorkData());', '''const getWorkData = async () => {
  const version = ++detailLoadVersion;
  auditFormIsShow.value = false;
  pendingCheckMessage.value = "";
  try {
    const data: any = await readWorkData();
    if (version !== detailLoadVersion) return;
    applyWorkData(data);
    const running = String(data.flowTaskInfo?.status) === "1";
    if (props.auditType === "待办事宜") {
      const taskId = String(data.flowTaskInfo?.id || "");
      if (!running || !taskId) {
        pendingCheckMessage.value = "当前任务暂不可审批，请在待办列表中查看最新状态";
        return;
      }
      pendingCheckMessage.value = "正在核实待办状态";
      const pending = await hasOwnPendingFlow(taskId);
      if (version !== detailLoadVersion) return;
      auditFormIsShow.value = pending;
      pendingCheckMessage.value = pending ? "" : "当前任务暂不可审批，请在待办列表中查看最新状态";
    } else if (props.auditType === "我发起的") {
      auditFormIsShow.value = running && data.approversProperties?.hasRevokeBtn !== false;
    }
  } catch {
    if (version !== detailLoadVersion) return;
    auditFormIsShow.value = false;
    pendingCheckMessage.value = "暂时无法核实待办状态，请刷新后重试";
  }
};
onBeforeUnmount(() => { detailLoadVersion++; });''')
    changed = text.encode('utf-8')
    return changed, {'path': RELATIVE, 'beforeSHA256': digest(raw), 'afterSHA256': digest(changed),
                     'originalAuthenticationAndAuditAPIsRetained': True,
                     'originalInitiatorAndHistoryModesRetained': True}

@contextmanager
def pending_visibility_override(project):
    project = Path(project).absolute()
    root = Path('D:/Project/Zhumadian/work/user_feedback_20261031')
    if project.resolve() != project or not project.is_relative_to(root):
        raise ValueError('ONLY_ISOLATED_WORKFLOW_BUILD_COPY')
    target = project / RELATIVE
    for p in [target, *target.parents]:
        if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('WORKFLOW_BUILD_REPARSE_REFUSED')
    before = target.read_bytes()
    after, proof = transform(before)
    proof['sourceRestored'] = False
    try:
        target.write_bytes(after)
        yield proof
    finally:
        if target.read_bytes() not in [before, after]:
            raise ValueError('FOREIGN_WORKFLOW_BUILD_EDIT_REFUSED_RESTORE')
        target.write_bytes(before)
        proof['sourceRestored'] = target.read_bytes() == before
