"""Build an exact single-source audit-submit guard atop the verified full workflow source."""
from pathlib import Path
import copy,hashlib,json,os,shutil
R=Path('D:/Project/Zhumadian');B=R/'work/user_feedback_20261031/emergency-workflow-source-r3';N=B.with_name('emergency-workflow-source-r4');T=R/'Application/tools';OVER=T/'frontend/emergency-workflow-approval-busy'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert read(B/'independent-build-verification.json')['undeclaredSourceDifferences']==0;assert not N.exists()
relative='src/components/workflow/components/auditForm.vue';origin=B/'source'/relative;raw=origin.read_bytes();text=raw.decode('utf-8');newline='\r\n'if'\r\n'in text else'\n';text=text.replace('\r\n','\n');before=text
pairs=[
 ('<el-button type="primary" :loading="isSubmit" @click="submitForm(ruleFormRef)">','<el-button type="primary" :loading="isSubmit" :disabled="isSubmit" @click="submitForm(ruleFormRef)">'),
 ('  if (!formEl) return;\n  await formEl.validate(async (valid: boolean) => {\n    if (valid) {\n      isSubmit.value = true;', '  if (!formEl || isSubmit.value) return;\n  isSubmit.value = true;\n  try {\n    const valid = await formEl.validate().catch(() => false);\n    if (valid) {'),
 ('    }\n  });\n};\n\nconst submitPort =', '    } else {\n      isSubmit.value = false;\n    }\n  } catch (error: any) {\n    isSubmit.value = false;\n    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");\n  }\n};\n\nconst submitPort ='),
 ('  } catch {\n    // The original request client owns error notifications; a rejected operation is not a success.','  } catch (error: any) {\n    // Keep server error notifications and add a fallback for transport failures without a response.\n    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");')]
for old,new in pairs:assert text.count(old)==1,'EXACT_KNOWN_AUDIT_COMPONENT_REQUIRED';text=text.replace(old,new,1)
reverse=text
for old,new in reversed(pairs):assert reverse.count(new)==1;reverse=reverse.replace(new,old,1)
assert reverse==before and reverse.replace('\n',newline).encode()==raw
# API selection, bodies, native action labels, permission/identity and preposition callback protocol are unchanged.
excluded={'node_modules','dist','.git','.cache','.vite','coverage'}
for folder,dirs,files in os.walk(B/'source',followlinks=False):
 dirs[:]=[n for n in dirs if n not in excluded]
 for name in dirs+files:assert not(Path(folder)/name).lstat().st_file_attributes&0x400
N.mkdir();shutil.copytree(B/'source',N/'source',copy_function=os.link,ignore=lambda folder,names:[n for n in names if n in excluded or'.timestamp-'in n]);target=N/'source'/relative;target.unlink();target.write_bytes(text.replace('\n',newline).encode());own=OVER/relative;own.parent.mkdir(parents=True,exist_ok=True)
if own.exists():assert own.read_bytes()==target.read_bytes(),'TRACKED_AUDIT_GUARD_DRIFT'
else:own.write_bytes(target.read_bytes())
assert sha(origin)==hashlib.sha256(raw).hexdigest()
manifest=copy.deepcopy(read(B/'source-closure.json'));manifest['runtimeSourceAdaptations']={relative:{'baseSourceSHA256':sha(origin),'adaptedSHA256':sha(target),'reverseByteExact':True,'declaredChanges':len(pairs),'synchronousLockBeforeValidation':True,'invalidValidationUnlocks':True,'failedTransportPreservesFormAndUnlocksWithFallback':True,'nativeBusinessBodiesActionListOrAuthChanged':False}};manifest['sourceRevision']='r4';(N/'source-closure.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('FULL_SOURCE_R4_SINGLE_AUDIT_COMPONENT_GUARD_PREPARED_NOT_INSTALLED')
