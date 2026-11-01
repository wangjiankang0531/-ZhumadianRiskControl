"""Add a pinned original certificate-name rule matching MySQL varchar(16).

Build-copy only; retain the original component, required fields, date rules,
dictionary, attachment control and callback shape. Never change Reference.
"""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

RELATIVE='src/views/safetyBasic/thirdPartyUnitInfo/components/List1/FormDialog.vue'
PIN='1cf19ad6707ee25fbcafe57365ec8ab8a55bef2fb06d1521dba0a988b3057681'

def transform(raw):
    if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_THIRD_PARTY_FORM_REQUIRED')
    newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8').replace('\r\n','\n')
    old='    { el: "input", prop: "licenceName", label: "证书名称", required: true },'
    new='''    {
      el: "input",
      prop: "licenceName",
      label: "证书名称",
      required: true,
      attrs: { placeholder: "最多16个字符" },
      rules: [
        {
          validator: (_rule, value, callback) => {
            if (typeof value === "string" && Array.from(value).length > 16) {
              callback(new Error("证书名称不能超过16个字符"));
            } else {
              callback();
            }
          },
          trigger: ["blur", "change"]
        }
      ]
    },'''
    if text.count(old)!=1:raise ValueError('EXACT_CERTIFICATE_NAME_FIELD_REQUIRED')
    out=text.replace(old,new,1).replace('\n',newline).encode('utf-8')
    return out,{'file':RELATIVE,'originalSHA256':PIN,'adaptedSHA256':sha256(out).hexdigest(),'maximumUnicodeCodePoints':16,'noSilentTruncation':True,'originalRequiredDateDictionaryAttachmentAndCallbackPreserved':True}

def regular(p):return p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400 and p.resolve(strict=True)==p

@contextmanager
def third_party_credentials_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):raise ValueError('DISTINCT_THIRD_PARTY_BUILD_COPY_REQUIRED')
    target,origin=project/RELATIVE,reference/RELATIVE
    if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DISTINCT_REGULAR_THIRD_PARTY_FILES_REQUIRED')
    raw=origin.read_bytes();adapted,receipt=transform(raw)
    if target.read_bytes()!=raw:raise ValueError('THIRD_PARTY_BUILD_COPY_DRIFT')
    target.write_bytes(adapted);receipt.update(referenceChanged=False,sourceFileRestored=False)
    try:yield receipt
    finally:
        if target.read_bytes()!=adapted:raise ValueError('THIRD_PARTY_EXTERNAL_EDIT_PRESERVED')
        target.write_bytes(raw);receipt['sourceFileRestored']=True
