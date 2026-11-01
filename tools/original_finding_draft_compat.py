"""Retain sibling finding edits when one saved finding reloads the original form.

Compose after the immutable image/submit adapters; never patch Reference or a live page.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from original_finding_image_compat import transform as images, RELATIVE, regular

HELPER='''const retainFindingSiblingEdits = (current, refreshed, savedRow) => {
  if (!savedRow) return refreshed;
  if (!current?.id || current.id !== refreshed?.id || !Array.isArray(current.checkPlanItemsList) ||
      !Array.isArray(refreshed.checkPlanItemsList)) return null;
  const replacements = [];
  for (const previousItem of current.checkPlanItemsList) {
    if (!Array.isArray(previousItem?.checkHiddenDangerList)) return null;
    const siblings = previousItem.checkHiddenDangerList.filter(danger => danger && danger !== savedRow &&
      (!savedRow.id || danger.id !== savedRow.id));
    if (!siblings.length) continue;
    const nextItem = refreshed.checkPlanItemsList.find(item => item?.id === previousItem.id);
    if (!previousItem.id || !nextItem || !Array.isArray(nextItem.checkHiddenDangerList)) return null;
    const nextRows = [...nextItem.checkHiddenDangerList];
    for (const sibling of siblings) {
      if (sibling.id) {
        const index = nextRows.findIndex(danger => danger?.id === sibling.id);
        if (index < 0) return null;
        nextRows[index] = sibling;
      } else if (!nextRows.includes(sibling)) {
        nextRows.push(sibling);
      }
    }
    replacements.push([nextItem, nextRows]);
  }
  for (const [item, rows] of replacements) item.checkHiddenDangerList = rows;
  return refreshed;
};

'''
OLD_RELOAD='''    await getData();
    const checkObj = field.value.checkPlanItemsList!.find(item => item.id == checkData.value.id);
    handleCheck(checkObj!);'''
NEW_RELOAD='''    if (!(await getData(row))) return;
    const checkObj = field.value.checkPlanItemsList!.find(item => item.id == checkData.value.id);
    if (checkObj) await handleCheck(checkObj, true);'''
OLD_LOAD='''const getData = async () => {
  if (!route.query.id) return;
  const res: any = await details({ id: route.query.id });
  field.value = res.data;
  await checkDepartmentChange(res.data.checkDepartmentId);
};'''
NEW_LOAD='''const getData = async (savedRow = undefined) => {
  if (!route.query.id) return false;
  const requestedId = route.query.id;
  const res: any = await details({ id: requestedId });
  if (route.query.id !== requestedId) return false;
  const refreshed = retainFindingSiblingEdits(field.value, res.data, savedRow);
  if (!refreshed) {
    ElMessage.error("隐患已保存，但其它排查内容已发生变化。当前填写内容已保留，请先复制未保存内容，再刷新核对刚保存的隐患。");
    return false;
  }
  field.value = refreshed;
  await checkDepartmentChange(refreshed.checkDepartmentId);
  return true;
};'''

def transform(raw):
 base,prior=images(raw);nl='\r\n' if b'\r\n' in base else '\n';s=base.decode('utf-8').replace('\r\n','\n')
 old_select='const handleCheck = async (item: CheckPlanItemsList) => {';new_select='const handleCheck = async (item: CheckPlanItemsList, refreshingSavedRow = false) => {'
 old_validation='  if (checkData.value.id && formItemRef.value) {';new_validation='  if (!refreshingSavedRow && checkData.value.id && formItemRef.value) {'
 for token in [old_select,old_validation,OLD_RELOAD,OLD_LOAD]:
  if s.count(token)!=1:raise ValueError('EXACT_FINDING_DRAFT_BOUNDARIES_REQUIRED')
 out=s.replace(old_select,HELPER+new_select,1).replace(old_validation,new_validation,1).replace(OLD_RELOAD,NEW_RELOAD,1).replace(OLD_LOAD,NEW_LOAD,1).replace('\n',nl).encode('utf-8')
 reverse=out.decode('utf-8').replace('\r\n','\n').replace(HELPER,'',1).replace(new_select,old_select,1).replace(new_validation,old_validation,1).replace(NEW_RELOAD,OLD_RELOAD,1).replace(NEW_LOAD,OLD_LOAD,1).replace('\n',nl).encode('utf-8');assert reverse==base
 return out,{'file':RELATIVE,'originalSHA256':sha256(raw).hexdigest(),'requiredImagesPreimageSHA256':sha256(base).hexdigest(),'adaptedSHA256':sha256(out).hexdigest(),'priorImageCompatibility':prior,'siblingDraftAndPersistedEditReferencesRetained':True,'savedRowExcludedFromRetention':True,'serverReloadStillProvidesSavedIdentity':True,'latestEditsCollectedAfterDetailsResponse':True,'taskMismatchMissingItemOrMissingSiblingRefusesReplacement':True,'routeChangedDuringReloadRefusesReplacement':True,'onlyOneOriginalRowSaveRequest':True,'realRoleBusinessAcceptance':False,'publicSave500CauseEstablished':False}

@contextmanager
def finding_draft_override(project,reference):
 project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
 if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_FINDING_DRAFT_COPY_REQUIRED')
 target,origin=project/RELATIVE,reference/RELATIVE
 if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_FINDING_DRAFT_COPY_REQUIRED')
 raw=origin.read_bytes();base,_=images(raw);updated,receipt=transform(raw)
 if target.read_bytes()!=base:raise ValueError('FINDING_DRAFT_IMAGE_PREIMAGE_DIFFERS')
 target.write_bytes(updated);receipt.update(referenceChanged=False,sourceFileRestored=False)
 try:yield receipt
 finally:
  if target.read_bytes()!=updated:raise ValueError('FINDING_DRAFT_EXTERNAL_EDIT_PRESERVED')
  target.write_bytes(base);receipt['sourceFileRestored']=True
