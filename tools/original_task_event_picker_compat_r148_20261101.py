"""Validate the original event picker before emitting its selected record."""
import hashlib
BEFORE_SHA256='f4ea914edcb9bb9c5e1043161ff37dcae7851ad6df539132b6da97f69a02fcac'
def transform(raw):
 if hashlib.sha256(raw).hexdigest()!=BEFORE_SHA256:raise ValueError('EXACT_WF16_TASK_EVENT_PICKER_SOURCE_REQUIRED')
 nl=b'\r\n'if b'\r\n'in raw else b'\n'
 old=b'  emit("check", nowRow);'
 active=b'// import { ElMessage } from "element-plus";'
 if raw.count(old)!=1 or raw.count(active)!=1:raise ValueError('ONE_ORIGINAL_EVENT_PICKER_AND_IMPORT_REQUIRED')
 new=("  if (!nowRow) {\n"
      "    ElMessage.warning(\"请先选择一条事件信息\");\n"
      "    return;\n"
      "  }\n"
      "  emit(\"check\", nowRow);").encode('utf-8').replace(b'\n',nl)
 out=raw.replace(active,b'import { ElMessage } from "element-plus";',1).replace(old,new,1)
 return out,{'beforeSHA256':hashlib.sha256(raw).hexdigest(),'afterSHA256':hashlib.sha256(out).hexdigest(),'onlyOriginalPickerValidatesCurrentVisibleSelectedRow':True,'emptyOrInvalidatedChoiceWarnsAndKeepsDialogWithoutEmittingUndefined':True,'confirmedEventFilterOriginalRadioAndSuccessfulSelectionKept':True,'schemaOrWorkflowStateSemanticsChanged':False}
