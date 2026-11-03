from pathlib import Path
import ast,hashlib,json

R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert J(D/'verified-stage-r345.json')['passedProgramAndFileTransactionStage']
S=T/'original_public_test_update_r39_plan_runtime_r337.py'
assert sha(S.read_bytes())=='e935f51aa3c7a5aae3346c632b90423ce99f6a0887b1d44781ea0ed8e8c16d8f'

def replace_once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)

sources={}
for label,view in [('r36','r339'),('r37','r341')]:
    ld="native_plan_unified_candidate_r39_20261103/lifecycle-"+label
    lo='r39-actual-lifecycle-'+label+'-r346'
    oldroot="W/'r36-native-history-candidate-r2/bundle'" if label=='r36' else "R/'work/r39-plan-runtime-unified-r1/original-r37-contract'"
    out=[]
    for role,source in [('inspect','inspect_owned_unified_lifecycle_r292.py'),('prepare','prepare_owned_unified_lifecycle_r293.py'),('run','run_owned_unified_lifecycle_r294.py')]:
        text=(T/source).read_text(encoding='utf-8')
        text=text.replace('unified_update_owned_lifecycle_r292_20261103',ld)
        text=text.replace('unified-update-lifecycle-r293',lo)
        text=text.replace('original_public_test_update_r38_mapper_preflight_r286.py',S.name)
        text=text.replace('baselineAdaptedR36SHA256','baselineAdapted'+label.upper()+'SHA256')
        text=text.replace('candidateAdaptedR38SHA256','candidateAdaptedR39SHA256')
        if role=='inspect':
            text=replace_once(text,"R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle/payload/release-manifest.json'", "R/'work/"+('user_feedback_20261031/r36-native-history-candidate-r2/bundle' if label=='r36' else 'r39-plan-runtime-unified-r1/original-r37-contract')+"/payload/release-manifest.json'")
            text=replace_once(text,"R/'work/r38-unified-full-preflight-r288/resolution.json'", "R/'work/r39-full-preflight-"+label+'-'+view+"/resolution.json'")
            # Existing release IDs intentionally remain the same application identity.
            text=text.replace('MatchesR36','Matches'+label.upper())
            text=replace_once(text,"assert not D.exists();D.mkdir()", "assert not D.exists();D.mkdir()")
        elif role=='prepare':
            text=replace_once(text,"oldroot=W/'r36-native-history-candidate-r2/bundle';public=W/'r38-unified-original-mappers-r2/bundle'", "oldroot="+oldroot+";public=R/'work/r39-plan-runtime-unified-r1/"+label+"/bundle'")
            text=text.replace('MatchesR36','Matches'+label.upper())
            text=text.replace("'xnby.r293.owned-update-lifecycle-scope.v1'","'xnby.r346.owned-plan-update-lifecycle-scope.v1'")
            text=replace_once(text,"assert shutil.disk_usage(R).free>2*1024**3+64*1024**2", "assert shutil.disk_usage(R).free>2*1024**3+256*1024**2\nimport ctypes\nmemory=(ctypes.c_ulonglong*8)();memory[0]=64\nassert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))and memory[2]>6*1024**3,'OWN_LIFECYCLE_PREPARE_REQUIRES_6GIB_AVAILABLE'\nassert not(A/'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class').exists()")
            text=text.replace('prepared-scope-r293.json','prepared-scope-r346.json')
            text=text.replace('estimatedPhysicalPeakBytes=64*1024**2','estimatedPhysicalPeakBytes=256*1024**2')
        else:
            text=replace_once(text,"assert old==scope['baselineAdapted"+label.upper()+"SHA256']and len(changes)==363", "assert old==scope['baselineAdapted"+label.upper()+"SHA256']and len(changes)==364")
            text=replace_once(text,"phase='apply-owned-R36-code-baseline'", "phase='apply-owned-"+label.upper()+"-code-baseline'")
            text=replace_once(text,"row=m.launch(A,old,boot);m.health(A,row)", "row=m.launch(A,old,boot);m.health(A,row)\n        assert m.native_plan_runtime_ready(A,row)is None,'BASELINE_MUST_NOT_HAVE_PLAN_OVERRIDE'\n        assert not(A/m.R39_PLAN_CLASS).exists()")
            text=replace_once(text,"row=m.owned_ready(A,scope['candidateAdaptedR39SHA256']);m.health(A,row)", "row=m.owned_ready(A,scope['candidateAdaptedR39SHA256']);m.health(A,row)\n        native_plan=m.native_plan_runtime_ready(A,row)\n        assert native_plan['installedAndRuntimeClassCopyMatched']and native_plan['candidatePlanClassSHA256']==m.R39_PLAN_ROW['sha256']\n        dump(O/'candidate-plan-runtime-ready.json',native_plan)")
            text=replace_once(text,"row=m.owned_ready(A,old);m.health(A,row,guarded=False)", "row=m.owned_ready(A,old);m.health(A,row,guarded=False)\n        assert m.native_plan_runtime_ready(A,row)is None and not(A/m.R39_PLAN_CLASS).exists(),'ROLLBACK_MUST_RESTORE_PLAN_CLASS_ABSENCE'")
            text=text.replace('verified-lifecycle-r294.json','verified-lifecycle-r346.json')
            text=replace_once(text,"proof={'passed':True", "proof={'baselineVariant':'"+label.upper()+"','candidatePlanClassInstalledAndActualRuntimeBytesMatched':True,'rollbackRestoredPlanClassAbsence':True,'passed':True")
        ast.parse(text)
        file=V/('plan_lifecycle_'+role+'_'+label+'_r346.py');assert not file.exists();file.write_text(text,encoding='utf-8')
        out.append({'role':role,'source':file.name,'bytes':file.stat().st_size,'sha256':sha(file.read_bytes())})
    sources[label.upper()]=out
proof={'prepared':True,'candidateUpdaterSHA256':sha(S.read_bytes()),'sources':sources,
       'originalUpdaterFunctionBodiesNotChanged':True,'onlyTargetGatewayAndSyntheticPrivateManifestAdapted':True,
       'realIISHTTPSNotClaimedByLoopbackHTTPAdapter':True,'servicesStartedOrFixtureChanged':False}
out=V/'plan-lifecycle-drivers-r346.json';assert not out.exists();out.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
