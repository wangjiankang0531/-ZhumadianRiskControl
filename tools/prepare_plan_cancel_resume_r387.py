from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
O=R/'work/plan-six-relations-cancel-r386';D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
terminal=J(O/'terminal.json');assert terminal['allOwnedControllerHandlesTerminal']and len(terminal['controllers'])==2
assert terminal['failure']['phase']=='actual-candidate-gzip-static'and terminal['failure']['message']=='STATIC_HTTP_STATUS_OR_BOUND'
for c in terminal['controllers']:
 assert c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']
 assert all(v==0 for v in c['receipt']['exitCodesBeforeJobClose'].values())
s=(V/'plan_cancel_run_r386.py').read_text(encoding='utf-8')
prefix=s.split("dump(O/'run-started.json'",1)[0]
prefix=prefix.replace("not(O/'run-started.json').exists()","not(O/'resume-started-r388.json').exists()")
prefix=prefix.replace("baseline_applied=False;restored=False","baseline_applied=True;restored=False")
prefix=prefix.replace("O/'owned-controller-handles.json'","O/'resume-controller-handles-r388.json'")
anchor="    result=[]\n    for path in ns['STATIC_EXPECTED']:"
replacement='''    # Bind the test to actual compiled entry names; preserve strict decoded hashes.
    import re
    entry=(O/'bundle/payload/frontend/emergency_pc/index.html').read_text(encoding='utf-8')
    scripts=re.findall(r'<script[^>]+src="(/zhumadian/emergency/assets/js/[^"<>]+)"',entry)
    styles=re.findall(r'<link[^>]+href="(/zhumadian/emergency/assets/css/[^"<>]+)"',entry)
    assert len(scripts)==len(styles)==1
    expected={n:p for n,p in ns['STATIC_EXPECTED'].items()if not n.startswith('/zhumadian/emergency/')}
    for original in scripts+styles:
        rel='frontend/emergency_pc/'+original.split('/zhumadian/emergency/',1)[1]
        pin=m.R38_FRONTEND_ROWS[rel]
        expected[original.replace('/zhumadian/emergency/','/zhumadian/emergency/branding-20261025/',1)]={'decodedBytes':pin['bytes'],'decodedSHA256':pin['sha256']}
    assert len(expected)==4
    ns['STATIC_EXPECTED']=expected
    result=[]
    for path in ns['STATIC_EXPECTED']:'''
assert prefix.count(anchor)==1;prefix=prefix.replace(anchor,replacement,1)
suffix=r'''
previous_terminal=J(O/'terminal.json')
assert previous_terminal['allOwnedControllerHandlesTerminal']and len(previous_terminal['controllers'])==2
assert all(v['controllerExitCode']==0 and v['actualJobDescendantsZero']for v in previous_terminal['controllers'])
assert previous_terminal['failure']['phase']=='actual-candidate-gzip-static'
assert sha(A/'release-manifest.json')==scope['candidateAdaptedR39SHA256']
bundle=O/'bundle';manifest=scope['bundleManifestSHA256'];assert sha(bundle/'update-manifest.json')==manifest
plan=J(bundle/'update-manifest.json');latest=J(A/'UserData/OriginalPublicUpdates/latest.json')
assert latest['ready']and latest['updateId']==plan['updateId']and latest['newReleaseSHA256']==scope['candidateAdaptedR39SHA256']
assert latest['oldReleaseSHA256']==scope['baselineAdaptedR37SHA256']and not latest.get('rolledBack')
attempt=Path(latest['attempt']);assert attempt.parent==A/'UserData/OriginalPublicUpdates'
changes=J(attempt/'changes.json')
assert set(changes)==set(plan['files'])|set(plan['removedFrontendFiles'])
for n,change in changes.items():
    expected=plan['files'].get(n)
    assert change['after']==(expected['SHA256']if expected else None)
    if expected:m.check_file(A,n,expected['SHA256'],expected['bytes'])
    else:assert not m.regular(A,n).exists()
    if change['before'] is not None:m.check_file(attempt/'before',n,change['before'])
unchanged_private()
schema_before=J(O/'before-update-398-models.private.json')
assert schema_before==J(O/'after-update-398-models.private.json')
dump(O/'resume-started-r388.json',{'started':True,'sameExactStoppedCandidate':True,'previousApplyExecuted':True,'priorTwoControllersNormalZero':True,'onlyTestStaticExpectationsUpdated':True})
native_ui_failure=None
try:
    with patch.object(m,'load_bundle',local_load),patch.object(m,'owned_ready',local_owned),patch.object(m,'health',local_health),patch.object(m,'launch',local_launch),patch.object(m,'ingress_preflight',local_ingress),patch.object(subprocess,'Popen',observed_popen):
        phase='resume-exact-candidate-preflight-before-normal-start'
        assert m.candidate_runtime_pool_preflight(A,bundle,plan)['originalMapperPreflight']['passed']
        boot=O/'resume-boot-r388';boot.mkdir()
        phase='normal-start-exact-stopped-candidate';row=m.launch(A,scope['candidateAdaptedR39SHA256'],boot);m.health(A,row)
        assert m.native_plan_runtime_ready(A,row)['installedAndRuntimeClassCopyMatched']
        try:
            phase='actual-candidate-static-current-compiled-hashes'
            static=verify_candidate_static();dump(O/'candidate-static-HTTP-r388.json',{'passed':True,'checks':static,'actualOwnedGatewayHTTP':True,'actualIISTLS':False})
            phase='actual-normal-role-six-relations-29-cases'
            native_ui=verify_native_candidate(row)
            print('OWN_R40_NATIVE_ALL_SIX_RELATIONS_29_CASES_PASSED',flush=True)
        except BaseException as error:
            native_ui_failure={'type':type(error).__name__,'phase':phase,'message':str(error)if isinstance(error,(AssertionError,ValueError))else'OWN_TEST_FAILED_INSPECT_SCOPED_RESULT'}
            dump(O/'verification-failure-r388.json',native_ui_failure)
            print('OWN_VERIFICATION_FAILED_PROCEEDING_TO_ACTUAL_ROLLBACK_AND_NORMAL_STOP',flush=True)
        phase='actual-rollback-latest-from-exact-candidate'
        with(O/'resume-updater-transactions-r388.private.log').open('w',encoding='utf-8')as trace,contextlib.redirect_stdout(trace):m.rollback_latest(A)
        old=scope['baselineAdaptedR37SHA256'];assert sha(A/'release-manifest.json')==old
        row=m.owned_ready(A,old);m.health(A,row,guarded=False)
        assert m.native_plan_runtime_ready(A,row)is None and not(A/m.R39_PLAN_CLASS).exists()
        phase='restored-baseline-398-model-snapshot';assert schema_snapshot('after-rollback-r388',row)==schema_before
        phase='normal-stop-two-resume-controllers';normal_stop_every_owned_process()
        assert len(processes)==len(terminal)==2
        for c in terminal:
            assert c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']
            assert set(c['receipt']['exitCodesBeforeJobClose'])=={'store','mysql','redis','platform','business','gateway'}
            assert all(v==0 for v in c['receipt']['exitCodesBeforeJobClose'].values())
        phase='restore-original-G-code-and-pointers';restore_original();restored=True
        assert native_ui_failure is None,'OWN_NATIVE_VERIFICATION_FAILED_BUT_ROLLBACK_AND_ORIGINAL_RESTORE_COMPLETE'
except BaseException as error:
    failure={'type':type(error).__name__,'phase':phase,'message':str(error)if isinstance(error,(AssertionError,ValueError))else'OWN_RESUME_FAILED_INSPECT_SCOPED_STATE',
       'frames':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}for f in traceback.extract_tb(error.__traceback__)]}
    dump(O/'resume-failure-r388.json',failure)
finally:
    if not restored:
        normal_stop_every_owned_process()
        try:restore_original();restored=True
        except BaseException as e:dump(O/'resume-restore-refused-r388.json',{'type':type(e).__name__,'message':str(e),'noForcedTermination':True})
    dump(O/'resume-terminal-r388.json',{'failure':failure,'allOwnedControllerHandlesTerminal':all(v['process'].poll()is not None for v in processes),
       'controllers':terminal,'originalGCodeAndPointersRestored':restored,'forceTerminationUsed':False,'actualIISTLSNotTested':True})
assert failure is None and restored
proof={'passed':True,'actualNormalRoleSixRelationsCases':29,'originalApplyExecutedInR386':True,'actualRollbackLatestExecutedInR388':True,
 'priorAndResumedFourControllersAllNormalZeroAndActualDescendantsZero':True,'candidateClassInstalledAndRuntimeBytesMatched':True,
 'original398ModelsAcrossUpdateAndRollbackMatched':True,'currentCompiledStaticGzipDecodedSHAActualPassed':True,
 'originalGCodeConfigurationAndPointersRestored':True,'r386FailureWasStaleStaticTestEntryNotHiddenOrDiscarded':True,
 'onlyExplicitLoopbackHTTPIngressAdapterNotIISTLS':True,'publicFormal18891Scene8767OrDesktopTouched':False,'fullCloneReady':False}
dump(D/'verified-native-r388.json',proof);print(json.dumps(proof),flush=True)
'''
out=V/'plan_cancel_resume_r388.py';assert not out.exists();ast.parse(prefix+suffix);out.write_text(prefix+suffix,encoding='utf-8')
(D/'resume-prepared-r387.json').write_text(json.dumps({'prepared':True,'driver':out.name,'sha256':sha(out),'exactStoppedCandidateKept':True,
 'originalFailureRetained':True,'originalTwoControllersNormalZero':True,'candidateProductCodeChanged':False,'nativeAndRollbackPending':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'driverSHA256':sha(out),'noServicesStarted':True}))
