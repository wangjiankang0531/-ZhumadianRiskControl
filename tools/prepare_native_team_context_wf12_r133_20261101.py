from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';old=W/'emergency-workflow-source-r11';new=W/'emergency-workflow-source-r12';assert not new.exists()
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def load(name):
    spec=importlib.util.spec_from_file_location(name,T/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
detail=load('original_team_detail_members_compat');editor=load('original_team_editor_context_compat')
metadata=json.loads((old/'source-closure.json').read_bytes());changes={};adaptations={}
for rel,name,function in [(detail.REL,'original_team_detail_members_compat','transform'),(editor.EDITOR,'original_team_editor_context_compat','transform_editor'),(editor.PARENT,'original_team_editor_context_compat','transform_parent')]:
    original=(old/'source'/rel).read_bytes();module=detail if name.endswith('members_compat')else editor;after,receipt=getattr(module,function)(original)
    try:getattr(module,function)(original+b'\n')
    except ValueError:pass
    else:raise AssertionError('UNPINNED_ORIGINAL_ACCEPTED')
    stored=T/'frontend/emergency-team-native-context'/rel;assert not stored.exists();stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(after)
    key=rel.removeprefix('src/');metadata['sourceFiles'][key]={'source':str(stored),'sha256':sha(after),'bytes':len(after),'overlay':True};metadata['overlayFiles']=sorted(set(metadata['overlayFiles'])|{key})
    adaptations[key]={'beforeSHA256':sha(original),'afterSHA256':sha(after),'helper':name,'entry':function,'receipt':receipt};changes[rel]=after
metadata['nativeTeamContextAdaptations']=adaptations
assert shutil.disk_usage(W).free>1024**3
shutil.copytree(old/'source',new/'source',copy_function=os.link)
for rel,after in changes.items():p=new/'source'/rel;p.unlink();p.write_bytes(after)
differences=[]
for p in(old/'source').rglob('*'):
    if p.is_file()and p.read_bytes()!=(new/'source'/p.relative_to(old/'source')).read_bytes():differences.append(p.relative_to(old/'source').as_posix())
assert set(differences)==set(changes)
(new/'source-closure.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(new/'native-team-source-proof.json').write_text(json.dumps({'onlyChangedSources':sorted(changes),'allThreeExactRetainedGuardsReproduced':True,'allOtherWF11SourceBytesPreserved':True,'wrongOriginalPinsRefused':3,'backendOrSchemasChanged':False,'runtimeStillPending':True,'adaptations':adaptations},indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
    p=T/name;s=p.read_text(encoding='utf-8');a="'r9','r10','r11'";assert s.count(a)==1;s=s.replace(a,"'r9','r10','r11','r12'")
    if name.endswith('.py'):
        anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel";assert s.count(anchor)==1
        block=''' if rel in c.get('nativeTeamContextAdaptations',{}):
  import importlib.util
  entry=c['nativeTeamContextAdaptations'][rel]
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r11/source/src'/rel
  assert sha(origin)==entry['beforeSHA256']and expected in [entry['beforeSHA256'],entry['afterSHA256']]
  assert entry['helper'] in ['original_team_detail_members_compat','original_team_editor_context_compat']
  assert entry['entry'] in ['transform','transform_editor','transform_parent']
  spec=importlib.util.spec_from_file_location('independent_native_team',T/(entry['helper']+'.py'));helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  generated,receipt=getattr(helper,entry['entry'])(origin.read_bytes())
  assert receipt==entry['receipt']and hashlib.sha256(generated).hexdigest()==entry['afterSHA256']
  expected=entry['afterSHA256']
'''
        s=s.replace(anchor,block+anchor);ast.parse(s)
    p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'revision':'r12','threeRetainedTeamGuardsRestored':True,'sourceInputs':len(metadata['sourceFiles']),'overlays':len(metadata['overlayFiles']),'runtimeOrPublicChanged':False}))
