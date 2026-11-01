"""Prepare WF13 from the pinned WF12 source only after actual native empty-picker reproduction."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';old=W/'emergency-workflow-source-r12';new=W/'emergency-workflow-source-r13'
assert not new.exists()
reproduction=R/'work/event_delivery_consistency_20261030/full-controller-r135/r8/duty-browser/empty-person-picker-proof.json'
proof=json.loads(reproduction.read_bytes());assert proof['dialogStillOpen']and proof['noMemberAdded']and not proof['selectionNoticeVisible']
spec=importlib.util.spec_from_file_location('duty_picker_guard',T/'original_duty_picker_selection_compat.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
metadata=json.loads((old/'source-closure.json').read_bytes());before=(old/'source'/module.REL).read_bytes();after,receipt=module.transform(before)
try:module.transform(before+b'\n')
except ValueError:pass
else:raise AssertionError('UNPINNED_DUTY_PICKER_ACCEPTED')
stored=T/'frontend/emergency-duty-native-picker'/module.REL;assert not stored.exists();stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(after)
key=module.REL.removeprefix('src/');metadata['sourceFiles'][key]={'source':str(stored),'sha256':hashlib.sha256(after).hexdigest(),'bytes':len(after),'overlay':True};metadata['overlayFiles']=sorted(set(metadata['overlayFiles'])|{key});metadata['nativeDutyPickerGuard']={'path':key,'receipt':receipt}
assert not(old/'source/node_modules').exists()and shutil.disk_usage(W).free>1024**3
for p in(old/'source').rglob('*'):assert not p.is_symlink(),'REDIRECTED_SOURCE_NOT_ALLOWED'
shutil.copytree(old/'source',new/'source',copy_function=os.link)
p=new/'source'/module.REL;p.unlink();p.write_bytes(after)
changes=[]
for p in(old/'source').rglob('*'):
    if p.is_file()and p.read_bytes()!=(new/'source'/p.relative_to(old/'source')).read_bytes():changes.append(p.relative_to(old/'source').as_posix())
assert changes==[module.REL]
(new/'source-closure.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(new/'native-duty-picker-source-proof.json').write_text(json.dumps({'onlyChangedSources':changes,'allOtherWF12SourceBytesPreserved':True,'actualBaselineEmptyPickerProof':str(reproduction),'wrongOriginalPinRefused':True,'backendOrSchemasOrRuntimeChanged':False,'receipt':receipt},indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
    p=T/name;s=p.read_text(encoding='utf-8');a="'r10','r11','r12'";assert s.count(a)==1;s=s.replace(a,"'r10','r11','r12','r13'")
    if name.endswith('.py'):
        anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert s.count(anchor)==1
        block=""" if rel==c.get('nativeDutyPickerGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeDutyPickerGuard']
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r12/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_duty_picker',T/'original_duty_picker_selection_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes())
  assert receipt==entry['receipt']and expected==hashlib.sha256(generated).hexdigest()
"""
        s=s.replace(anchor,block+anchor);ast.parse(s)
    p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'revision':'r13','sourceInputs':len(metadata['sourceFiles']),'sourceOverlays':len(metadata['overlayFiles']),'onlyDutyPickerSourceChanged':True,'runtimeOrPublicInstalled':False}))
