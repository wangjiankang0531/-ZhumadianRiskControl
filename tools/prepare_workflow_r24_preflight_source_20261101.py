from pathlib import Path
import ast, hashlib, json, shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';root=R/'work/r24gv-r1'
assert not root.exists()
p=R/'work/r23gv-r1/dependency-resolution.json';resolution=json.loads(p.read_bytes())
assert resolution['allResolved']and not resolution['realPrivateConfigurationRead']and not resolution['realSeedOrBusinessDataRead']
assert len(resolution['programs'])==15408 and len(resolution['controllers'])==19
for collection in ['programs','controllers']:
    for name,row in resolution[collection].items():
        s=row['source'].replace('\\','/').lower()
        assert not any('/'+n+'/'in s for n in ['_c','_d','_e'])
        assert not name.startswith(('private/','seed/','UserData/'))
free=shutil.disk_usage(R).free;assert free>2*1024**3
root.mkdir();(root/'dependency-resolution.json').write_bytes(p.read_bytes())
s=(T/'verify_unified_graceful_full_preflight_20261101.py').read_text(encoding='utf-8')
s=s.replace('r23-unified-candidate-r1','r24-unified-candidate-r1').replace("'r23gv-'","'r24gv-'")
s=s.replace('original_public_test_update_r23_graceful_20261101.py','original_public_test_update_r24_20261101.py')
s=s.replace('d500b5b591971532a74dd632d2cff7139474bd61986c01bc75b184017c143d41',hashlib.sha256((T/'original_public_test_update_r24_20261101.py').read_bytes()).hexdigest())
s=s.replace('len(changes)==1183',"len(changes)==len(public_plan['files'])+len(public_plan['removedFrontendFiles'])")
s=s.replace('xnby.r23.full-program-preflight.v1','xnby.r24.full-program-preflight.v1')
before="(app/helper).unlink();cases.append({'case':'unexpected-new-helper-path-refused','passed':True})"
assert s.count(before)==1
s=s.replace(before,before+'''
task=m.R24_TASK_CLASS;assert not(app/task).exists()
m.atomic(app/task,b'own unexpected task overlay\\n')
try:m.load_bundle(app,bundle,bundle_pin,expected_target=app)
except ValueError as error:assert str(error)=='NEW_PATH_ALREADY_EXISTS:'+task
else:raise AssertionError('PREEXISTING_TASK_CLASS_ACCEPTED')
(app/task).unlink();cases.append({'case':'unexpected-new-task-class-refused','passed':True})
''')
ast.parse(s);out=T/'verify_unified_workflow_r24_full_preflight_20261101.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
(root/'allocation-plan.json').write_text(json.dumps({'freeBytesBefore':free,'logicalProgramBytes':resolution['resolvedProgramBytes'],
    'programFilesAreHardlinksExceptMutableIndependentCopies':True,'additionalAllocatedBytesUpperBound':512*1024**2,
    'realPrivateSeedOrProtectedUserPreviewSources':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'root':str(root),'programFiles':15408,'logicalBytes':resolution['resolvedProgramBytes'],
                  'estimatedAdditionalAllocatedBytesUpperBound':512*1024**2,'freeBytesBefore':free}))
