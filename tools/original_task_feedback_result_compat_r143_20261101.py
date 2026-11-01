"""Preserve native task disposal input when the original update API saved no row."""
import hashlib
BEFORE_SHA256='3a1e8ab2918d225f660d21bfe29d5ffe66450fe23fc80eb937064ba2158baed5'
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF14_TASK_DISPOSAL_SOURCE_REQUIRED')
 nl=b'\r\n'if b'\r\n'in raw else b'\n'
 old=b'    await updateById(fieldJudge.value);'
 new=("    const result = await updateById(fieldJudge.value);\n"
      "    if (result.data !== true) {\n"
      "      ElMessage.error(\"任务未保存，请刷新核对后重试\");\n"
      "      return false;\n"
      "    }").encode('utf-8').replace(b'\n',nl)
 if raw.count(old)!=1:raise ValueError('ONE_NATIVE_TASK_DISPOSAL_UPDATE_REQUIRED')
 out=raw.replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalBooleanSaveResultChecked':True,'falseResultKeepsFeedbackAndDoesNotNavigateOrReportSuccess':True,'normalTrueResultValidationBusyAndNavigationKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
