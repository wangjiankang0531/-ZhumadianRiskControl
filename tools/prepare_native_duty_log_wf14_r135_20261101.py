"""Prepare one additional native log guard after the real delayed-request reproduction."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';old=W/'emergency-workflow-source-r13';new=W/'emergency-workflow-source-r14';assert not new.exists()
proof=json.loads((R/'work/event_delivery_consistency_20261030/full-controller-r135/r10/duty-browser/pending-log-options-proof.json').read_bytes());assert proof['actualOwnGetListRequestPausedNoResponseReplaced']and proof['inputRetained']and proof['stillOnEditRoute']and proof['updateRequestsBeforeOptionsReady']==0 and not proof['loadingOrReselectionNoticeVisible']
spec=importlib.util.spec_from_file_location('duty_log_context',T/'original_duty_log_personnel_context_compat.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
before=(old/'source'/module.REL).read_bytes();after,receipt=module.transform(before)
try:module.transform(before+b'\n')
except ValueError:pass
else:raise AssertionError('UNPINNED_DUTY_LOG_ACCEPTED')
metadata=json.loads((old/'source-closure.json').read_bytes());key=module.REL.removeprefix('src/');stored=T/'frontend/emergency-duty-log-context'/module.REL;assert not stored.exists();stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(after)
metadata['overlayFiles']=sorted(set(metadata['overlayFiles'])|{key});metadata['nativeDutyLogPersonnelGuard']={'path':key,'receipt':receipt,'storedSource':str(stored)}
assert not(old/'source/node_modules').exists()and shutil.disk_usage(W).free>1024**3
for p in(old/'source').rglob('*'):assert not p.is_symlink()
shutil.copytree(old/'source',new/'source',copy_function=os.link);p=new/'source'/module.REL;p.unlink();p.write_bytes(after)
changes=[p.relative_to(old/'source').as_posix()for p in(old/'source').rglob('*')if p.is_file()and p.read_bytes()!=(new/'source'/p.relative_to(old/'source')).read_bytes()];assert changes==[module.REL]
(new/'source-closure.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(new/'native-duty-log-source-proof.json').write_text(json.dumps({'onlyChangedSources':changes,'allOtherWF13SourceBytesPreserved':True,'receipt':receipt,'actualDelayedOriginalRequestReproduced':True,'runtimeBackendSchemasOrPublicChanged':False},indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
    p=T/name;s=p.read_text(encoding='utf-8');a="'r11','r12','r13'";assert s.count(a)==1;s=s.replace(a,"'r11','r12','r13','r14'")
    if name.endswith('.py'):
        anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert s.count(anchor)==1
        block=""" if rel==c.get('nativeDutyLogPersonnelGuard',{}).get('path'):
  import importlib.util
  entry=c['nativeDutyLogPersonnelGuard']
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r13/source/src'/rel
  spec=importlib.util.spec_from_file_location('independent_native_duty_log',T/'original_duty_log_personnel_context_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=helper.transform(origin.read_bytes())
  assert receipt==entry['receipt']and expected in [receipt['beforeSHA256'],receipt['afterSHA256']]
  expected=receipt['afterSHA256']
"""
        s=s.replace(anchor,block+anchor);ast.parse(s)
    p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'revision':'r14','sourceInputs':len(metadata['sourceFiles']),'sourceOverlays':len(metadata['overlayFiles']),'onlyLogSourceAddedToPickerFix':True,'runtimeOrPublicInstalled':False}))
