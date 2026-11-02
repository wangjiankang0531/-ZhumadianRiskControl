"""Match both the current process and the exact operator carried by the original route."""
from pathlib import Path
from contextlib import contextmanager
from original_workflow_pending_visibility_r177 import transform as initial_transform, digest, RELATIVE

def transform(raw):
    changed, proof = initial_transform(raw)
    text = changed.decode('utf-8')
    def once(before, after):
        nonlocal text
        if text.count(before) != 1:
            raise ValueError('EXACT_PENDING_OPERATOR_ANCHOR_REQUIRED')
        text = text.replace(before, after, 1)
    once('const hasOwnPendingFlow = async (taskId: string) => {',
         'const hasOwnPendingFlow = async (taskId: string, operatorId?: string) => {')
    once('if (list.some((item: any) => String(item.id) === taskId || String(item.processInstanceId) === taskId)) return true;',
         'if (list.some((item: any) => (String(item.id) === taskId || String(item.processInstanceId) === taskId) && (!operatorId || String(item.id) === operatorId))) return true;')
    once('const taskId = String(data.flowTaskInfo?.id || "");',
         'const taskId = String(data.flowTaskInfo?.id || "");\n      const operatorId = typeof route.query.id === "string" ? route.query.id : "";')
    once('if (!running || !taskId) {', 'if (!running || !taskId || !operatorId) {')
    once('const pending = await hasOwnPendingFlow(taskId);', 'const pending = await hasOwnPendingFlow(taskId, operatorId);')
    result = text.encode('utf-8')
    proof.update(afterSHA256=digest(result), exactOriginalOperatorAndProcessMembershipChecked=True)
    return result, proof

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
