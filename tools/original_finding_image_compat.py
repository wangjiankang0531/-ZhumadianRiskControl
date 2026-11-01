"""Preserve mixed original finding image lists and block incomplete image saves.

Compose with the fixed unsaved-task guard; never modify Reference or a live page.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from original_finding_submit_guard import transform as guard,RELATIVE,PIN,regular

HELPERS='''const normalizeFindingImageList = files => {
  if (files == null) return [];
  if (!Array.isArray(files)) return files;
  return files.map(file => typeof file === "string" ? { name: file, url: file } : file);
};

const getFindingImageURLs = files => {
  if (files == null) return [];
  if (!Array.isArray(files)) return null;
  const urls = [];
  for (const file of files) {
    const url = typeof file === "string" ? file : file?.url;
    if (typeof url !== "string" || !url.trim() || /^(blob:|data:)/i.test(url)) return null;
    if (typeof file !== "string" && file.status != null && file.status !== "success") return null;
    urls.push(url);
  }
  return urls;
};

'''
ERROR='图片尚未上传完成或上传失败，请等待完成、重试或移除后再保存'
NORMALIZE='    if (el.fileList.some(file => !file.url)) el.fileList = el.fileList.map(file => ({ name: file, url: file }));'
OPEN='const handleRowSave = async row => {\n'
PARAMS='''  }).then(async () => {
    const params = JSON.parse(JSON.stringify(field.value));'''
URLS='    rowData.fileList = rowData.fileList.map(file => file?.url);'

def transform(raw):
    base,prior=guard(raw)
    nl='\r\n' if b'\r\n' in base else '\n';s=base.decode('utf-8').replace('\r\n','\n')
    for token in ['const handleCheck = async (item: CheckPlanItemsList) => {',NORMALIZE,OPEN,PARAMS,URLS]:
        if s.count(token)!=1:raise ValueError('EXACT_ORIGINAL_FINDING_IMAGE_BOUNDARY_REQUIRED')
    s=s.replace('const handleCheck = async (item: CheckPlanItemsList) => {',HELPERS+'const handleCheck = async (item: CheckPlanItemsList) => {',1)
    s=s.replace(NORMALIZE,'    el.fileList = normalizeFindingImageList(el.fileList);',1)
    check='  if (getFindingImageURLs(row?.fileList) === null) {\n    ElMessage.error("'+ERROR+'");\n    return;\n  }\n'
    s=s.replace(OPEN,OPEN+check,1)
    s=s.replace(PARAMS,'  }).then(async () => {\n    const imageURLs = getFindingImageURLs(row?.fileList);\n    if (imageURLs === null) {\n      ElMessage.error("'+ERROR+'");\n      return;\n    }\n    const params = JSON.parse(JSON.stringify(field.value));',1)
    s=s.replace(URLS,'    rowData.fileList = imageURLs;',1);out=s.replace('\n',nl).encode('utf-8')
    return out,{'file':RELATIVE,'originalSHA256':PIN,'requiredGuardedPreimageSHA256':sha256(base).hexdigest(),'adaptedSHA256':sha256(out).hexdigest(),'priorSubmitGuard':prior,'mixedExistingURLAndUploadObjectsPreserved':True,'incompleteOrFailedImagesBlockedBeforeConfirmationAndRequest':True,'invalidImagesNotSilentlyRemoved':True,'originalAPIRolesPayloadShapePreserved':True,'publicSave500CauseEstablished':False}

@contextmanager
def finding_image_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_FINDING_IMAGE_COPY_REQUIRED')
    target,origin=project/RELATIVE,reference/RELATIVE
    if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_FINDING_IMAGE_COPY_REQUIRED')
    raw=origin.read_bytes();base,_=guard(raw);updated,receipt=transform(raw)
    if target.read_bytes()!=base:raise ValueError('FINDING_IMAGE_GUARDED_PREIMAGE_DIFFERS')
    target.write_bytes(updated);receipt.update(referenceChanged=False,sourceFileRestored=False)
    try:yield receipt
    finally:
        if target.read_bytes()!=updated:raise ValueError('FINDING_IMAGE_EXTERNAL_EDIT_PRESERVED')
        target.write_bytes(base);receipt['sourceFileRestored']=True
