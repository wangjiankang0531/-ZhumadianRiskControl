"""Prepare one callback plan only from a verified live owned G controller.

The full parent owns resource gates and actual child Job handles. This helper
does not start services or create the full attempt marker. No credentials here.
"""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');APP=R/'_g/Application';ATTEMPT=R/'work/original-manager-full-lifecycle-r609';T=R/'Application/tools';V=Path(__file__).resolve().parent
UPDATER=T/'original_public_test_update_r42_mapper_equivalence_r457.py'
UPDATER_SHA='5e63e0f3e1f7d1064b5ae1276bfee56d51ce58b0e0ea64f59e30238c1c2d8b30'
J=lambda p:json.loads(p.read_bytes())
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,message):
    if not v:raise ValueError(message)
def plain(p):
    p=Path(p).absolute();need(p.resolve()==p and'..'not in p.parts,'EXACT_OWN_CALLBACK_PATH_REQUIRED')
    for q in [p,*p.parents]:
        need(not q.is_symlink()and(not q.exists()or not(q.lstat().st_file_attributes&0x400)),'OWN_CALLBACK_REPARSE_REFUSED')
    return p
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def marker():
    plain(ATTEMPT)
    need(ATTEMPT.is_dir()and(ATTEMPT/'own-normal-manager-test.marker').is_file(),'FULL_MANAGER_ATTEMPT_MARKER_REQUIRED')
    need((ATTEMPT/'own-normal-manager-test.marker').read_bytes()==b'own-original-manager-full-lifecycle-r609\n','FULL_MANAGER_ATTEMPT_MARKER_REQUIRED')
    need(J(APP.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']is True and not(APP.parent/'user-manual-protected.json').exists(),'ONLY_OWN_SYNTHETIC_G_ALLOWED')
def source_rows(business_port):
    helper=T/'prepare_owned_callback_rows_r653.py'
    fixed=J(R/'Document/Deployment/owned_callback_sql_r657_20261104/source-pins-r657.json')['files']
    for name in ['prepare_owned_callback_rows_r653.py','prepare_owned_callback_sql_input_r649.py']:
        pin=next(x for x in fixed if x['path']=='tools/'+name);need(sha(T/name)==pin['sha256'],'PINNED_CALLBACK_ROW_BUILDER_REQUIRED')
    m=load('owned_runtime_rows_r663',helper)
    p=R/'work/original-manager-bindings-r602/owned-binding-plan.private.json'
    need(sha(p)==J(R/'Document/Deployment/original_manager_bindings_r602_20261104/verified-binding-metadata-r602.json')['privateBindingPlanSHA256'],'ORIGINAL_CALLBACK_BINDING_PACKET_DRIFT')
    f=R/'work/original-manager-http-definitions-r615/native-definitions.private.json'
    g=R/'work/original-manager-graph-r466/clone-graphs.private.json'
    s=R/'work/callback-config-read-r654/original-callback-configs.private.json'
    for path,digest in [(f,'539b57deffd8710dc633cd401f81898440d82ff5e7b7f8f1cbfe86cc55595660'),
                        (g,'14854a91ca1541548b5a3dde89ee6d128a81151451bb8417fbed223070a2948f'),
                        (s,'232fb979bcf834c4c596adc297a328b0f251e875b54527be9a7eddb1df760d9f')]:need(sha(path)==digest,'ORIGINAL_CALLBACK_FIXED_INPUT_DRIFT')
    return m.rows_for_owned_port(J(p),J(f),J(g),J(s),business_port)
def prepare_runtime_plan(stage,attempt_id,release_sha256,*,gateway_port,controller_process):
    need(stage in ['first-start','normal-restart','after-submit-r889'],'EXACT_MANAGER_CALLBACK_STAGE_REQUIRED')
    marker();root=ATTEMPT/'feedback-r880'/stage;plain(root)
    need(root.is_dir()and(root/'own-normal-manager-test.marker').read_bytes()==b'own-original-manager-full-lifecycle-r609\n','OWN_STAGE_PARENT_MARKER_REQUIRED')
    need(sha(UPDATER)==UPDATER_SHA and sha(APP/'release-manifest.json')==release_sha256,'ORIGINAL_HELPER_AND_RELEASE_PIN_REQUIRED')
    runtime=load('manager_callback_owned_runtime_r769',UPDATER);row=runtime.owned_ready(APP,release_sha256,gateway_port=gateway_port)
    need(row['persistent']is True and row['callbackProjectionEnabled']is True and controller_process.pid==row['controllerPID']and controller_process.poll()is None,'ACTUAL_LIVE_OWN_PARENT_REQUIRED')
    observer=load('manager_callback_actual_windows_r769',V.parent/'attest_owned_windows_process_r746.py')
    identity=observer.attest(controller_process,APP/'runtime/python/python.exe',controller_process.args[1:])
    previousRoot=ATTEMPT/'feedback-r880/normal-restart'if stage=='after-submit-r889'else ATTEMPT/'task-ui-r806/normal-restart'if stage=='first-start'else ATTEMPT/'feedback-r880/first-start'
    previousPlan=previousRoot/'callback-normal-restart-plan.private.json';previousJournal=previousRoot/'callback-normal-restart-journal.private.properties'
    previousResult=previousRoot/'callback-r777-result.json'
    previous=J(plain(previousPlan));receipt=J(plain(previousResult))
    if stage=='first-start':need(sha(previousJournal)=='6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98','PINNED_PREDECESSOR_JOURNAL_REQUIRED')
    if stage=='after-submit-r889':need(sha(previousJournal)=='234781eb7e322f9395bd0533f87acd0bd0440a5964bba71a1e20c2a533825bbc','PINNED_CREATED_TASK_PREDECESSOR_REQUIRED')
    need(receipt['passed']and sha(previousJournal)==receipt['journalSHA256'],'VERIFIED_PREVIOUS_CALLBACK_JOURNAL_REQUIRED')
    lines=previousJournal.read_text('ascii').splitlines()
    need('phase=readback-verified'in lines and 'planSHA256='+sha(previousPlan)in lines,'EXACT_VERIFIED_CALLBACK_PLAN_JOURNAL_BINDING_REQUIRED')
    need(previous['attemptId']==attempt_id and previous['databaseUUID']==row['databaseUUID']and previous['releaseSHA256']==('e957cf851cb253d4ac020ef04711ebd6e9f066bfc1471002b10d53c88de71db2'if stage=='first-start'else'eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93')and release_sha256=='eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93','EXACT_PREVIOUS_OWN_CALLBACK_CHAIN_REQUIRED')
    before=previous['afterRows'];need(before==source_rows(previous['businessPort']),'EXACT_PREVIOUS_ORIGINAL_CALLBACK_ROWS_REQUIRED')
    plan={'schema':'xnby.owned-original-callback-plan.r662.v1','application':str(APP),'attempt':str(root),'onlyOwnedRuntimeFixture':True,'attemptId':attempt_id,'stage':'normal-restart',
          'releaseSHA256':release_sha256,'currentRunSHA256':sha(APP/'UserData/OriginalServer/current-run.json'),**{k:row[k]for k in ['controllerPID','databaseUUID','databasePort','businessPort','gatewayPort']},
          'beforeRows':before,'afterRows':source_rows(row['businessPort']),'previousBusinessPort':previous['businessPort'],'controllerWindowsIdentity':identity}
    need(runtime.owned_ready(APP,release_sha256,gateway_port=gateway_port)==row,'OWN_CONTROLLER_CHANGED_DURING_PLAN')
    target=plain(root/'callback-normal-restart-plan.private.json');need(not target.exists(),'EXISTING_CALLBACK_STAGE_REFUSE_NO_RETRY')
    raw=(json.dumps(plan,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();need(len(raw)<1048576,'BOUNDED_CALLBACK_PLAN_REQUIRED')
    with target.open('xb')as out:out.write(raw);out.flush();os.fsync(out.fileno())
    need(sha(target)==hashlib.sha256(raw).hexdigest(),'PLAN_READBACK_FAILED')
    return {'plan':target,'planSHA256':sha(target),'databasePort':row['databasePort'],'journal':root/'callback-normal-restart-journal.private.properties','attempt':root}
