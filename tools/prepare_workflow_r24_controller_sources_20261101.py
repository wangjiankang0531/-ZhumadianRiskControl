from pathlib import Path
import ast, hashlib
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
updater=T/'original_public_test_update_r24_20261101.py';pin=hashlib.sha256(updater.read_bytes()).hexdigest()
def write(name,s):
    ast.parse(s);p=T/name;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
s=(T/'prepare_whole_controller_code_20261101.py').read_text(encoding='utf-8')
s=s.replace('work/r23gv-r1','work/r24gv-r1').replace("R/'_b'","R/'_f'")
s=s.replace('original_public_test_update_r23_graceful_20261101.py','original_public_test_update_r24_20261101.py')
s=s.replace('d500b5b591971532a74dd632d2cff7139474bd61986c01bc75b184017c143d41',pin)
s=s.replace('assert len(changes)==1183',"assert len(changes)==proof['candidateInstallPaths']")
s+='''
# Only this newly created synthetic code view may be moved to the short _f root.
destination=R/'_f'
assert not destination.exists() and app.resolve().parent==P.resolve() and P.resolve()==(R/'work/r24gv-r1').resolve()
assert app.resolve()==(P/'Application').resolve() and not(app/'UserData').exists()
assert not any(p.lstat().st_file_attributes&0x400 for p in [app,*app.rglob('*')])
destination.mkdir();app.rename(destination/'Application')
(destination/'own-fixture.json').write_text(json.dumps({'ownedSyntheticFixtureOnly':True,
    'purpose':'unified-r24-exact-controller-runtime','noInstalledPrivateConfigOrSeedRead':True}),encoding='utf-8')
root=R/'work/event_delivery_consistency_20261030/full-controller-r127';assert not root.exists();root.mkdir()
(root/'code-prepared.json').write_bytes((P/'controller-code-prepared.json').read_bytes())
print('OWN_R24_CODE_MOVED_ONLY_WITHIN_VERIFIED_NEW_FIXTURE_TO_F')
'''
write('prepare_unified_workflow_r24_controller_code_20261101.py',s)
java_out=T/'java/workflow_r24_fixture_r1';assert not java_out.exists();java_out.mkdir()
for name in ['OwnWorkflowPortalMenusFixture.java','OwnWorkflowFormStorageFixture.java']:
    raw=(T/'java/approval_ui_fixture_r1'/name).read_text(encoding='utf-8')
    assert '/_e/Application/UserData/OriginalServer/database/data'in raw
    raw=raw.replace('/_e/','/_f/').replace('owned _e synthetic','owned _f synthetic')
    (java_out/name).write_text(raw,encoding='utf-8',newline='\n')
s=(T/'prepare_approval_ui_controller_fixture_20261101.py').read_text(encoding='utf-8')
s=s.replace('/_e/','/_f/').replace("R/'_e/","R/'_f/")
s=s.replace('full-controller-r123','full-controller-r127').replace('java/approval_ui_fixture_r1/','java/workflow_r24_fixture_r1/')
assert '_e/'not in s
write('prepare_unified_workflow_r24_controller_fixture_20261101.py',s)
s=(T/'verify_whole_graceful_controller_20261101.py').read_text(encoding='utf-8')
s=s.replace('/_b/','/_f/').replace("R/'_b/","R/'_f/").replace('full-controller-r117','full-controller-r127')
s=s.replace("base=R/'work/event_delivery_consistency_20261030/full-controller-r127'", "base=R/'work/event_delivery_consistency_20261030/full-controller-r127'\nassert not(app.parent/'user-manual-protected.json').exists(),'USER_MANUAL_ROOT_MUST_NOT_BE_AUTOMATIC_TEST_FIXTURE'")
before="phase='checking-gateway-health';m.health(app,row,gateway_port=port)"
assert s.count(before)==1
s=s.replace(before,before+"\n        checks['actualR24WorkflowGuardRuntimePinsPassed']=m.workflow_ready(app,row) is not None")
s=s.replace('xnby.r23.whole-graceful-controller-check.v1','xnby.r24.whole-controller-check.v1')
write('verify_unified_workflow_r24_controller_lifecycle_20261101.py',s)
print('Prepared exact R24 code, synthetic R114-only dataset preparation, and whole-controller lifecycle drivers.')
