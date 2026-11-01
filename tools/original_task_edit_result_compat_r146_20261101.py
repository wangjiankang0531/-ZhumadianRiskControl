"""Keep the original task editor open unless its real API saved a row."""
import hashlib
BEFORE_SHA256='ce86172624cf32082cc993bbbde0a7aabe14b5c6c0121db8877ce3e4aeba09b3'
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF15_TASK_EDIT_SOURCE_REQUIRED')
 nl=b'\r\n'if b'\r\n'in raw else b'\n'
 old=b'    await api({ ...field.value, uploadUrl });'
 new=("    const result = await api({ ...field.value, uploadUrl });\n"
      "    if (result.data !== true) {\n"
      "      ElMessage.error(\"任务未保存，请刷新核对后重试\");\n"
      "      return false;\n"
      "    }").encode('utf-8').replace(b'\n',nl)
 if raw.count(old)!=1:raise ValueError('ONE_ORIGINAL_TASK_SAVE_REQUIRED')
 out=raw.replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalBooleanSaveResultChecked':True,'falseResultKeepsEditorAndDoesNotNavigateOrReportSuccess':True,'normalTrueResultValidationBusyAndNavigationKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
