"""Full original online-workflow frontend, with a measured hard build budget.

Same nine source adapters, four final source differences and original Vite recipe
as R525. R525's conservative preflight is kept unchanged as historical source.
This entry uses a 3-GiB process-tree commit limit plus a 2-GiB physical reserve;
the separate six-component application lifecycle still has its own 6-GiB gate.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
sys.path.insert(0,str(T))
from bounded_build_job_r671 import BoundedBuildJob,memory_snapshot
D=R/'Document/Deployment/original_online_workflow_integration_r475_20261104'
S=R/'Document/Deployment/authenticated_installer_map_r828_20261104'
W=R/'work/authenticated-installer-map-r828'
P=R/'work/user_feedback_20261031/event-research-level-r418/source'
ORIGIN=R/'work/user_feedback_20261031/emergency-workflow-source-r17/source'
DEPS=R/'Application/work/tianjin_native_20261023/emergency_pc/node_modules'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
CAP=3*1024**3;PHYSICAL_RESERVE=2*1024**3;COMMIT_RESERVE=1024**3
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
assert not W.exists(),'EXISTING_BUILD_HANDLE_OR_TERMINAL_MUST_BE_AUDITED_NO_RESTART'
assert J(D/'browser-result-r482.json')['passed']and J(D/'browser-outer-terminal-r482.json')['actualDescendantsZero']
policyProof=J(V/'bounded-job-r672-r2/verified-bounded-job-r672.json')
assert policyProof['passed']and len(policyProof['cases'])==5 and policyProof['sourceSHA256']==sha(V/'bounded_build_job_r671.py')
memory=memory_snapshot();S.mkdir(exist_ok=True)
plan={'runner':'run_bounded_online_full_build_r673.py','sameCompleteR525SourceAndViteRecipeWithOnlyDeferredGlobalInstaller':True,'jobCommitLimitBytes':CAP,
      'nodeHeapLimitMiB':2048,'minimumUnallocatedPhysicalReserveBytes':PHYSICAL_RESERVE,'minimumCommitReserveBytes':COMMIT_RESERVE,
      'memoryBefore':memory,'conservativeAdditionalDiskPeakBytes':512*1024**2,'minimumDiskReserveBytes':2*1024**3,
      'originalR525SixGiBEntryUnmodified':True,'sixComponentLifecycleGateNotChanged':True,'noUserApplicationsToBeClosed':True,
      'budgetPolicyWasVerifiedAgainstActualWindowsKernel':True}
(S/'resource-plan-r673.json').write_bytes(enc(plan))
if not args.run or memory['availablePhysicalBytes']<CAP+PHYSICAL_RESERVE or memory['availableCommitBytes']<CAP+COMMIT_RESERVE:
    proof={'started':False,'reason':'EXPLICIT_RUN_OR_BOUNDED_RESOURCE_RESERVE_REQUIRED','resourcePlan':plan,'buildRootAllocated':False,'sourceOverridesOrNodeStarted':False}
    (S/'not-started-r673.json').write_bytes(enc(proof));print(json.dumps(proof));raise SystemExit(2)
assert shutil.disk_usage(R).free>2*1024**3+512*1024**2
assert not(P/'node_modules').exists()and not(P/'node_modules').is_symlink()and not(P/'node_modules').is_junction()
assert(DEPS/'vite/dist/node/index.js').is_file()
import build_avatar_full_r157_20261102 as base
from original_header_avatar_compat import header_avatar_override
from original_project_header_home_r167_20261102 import project_header_override
from original_workflow_pending_visibility_r178 import pending_visibility_override
from original_personal_workflow_routes_r195 import personal_workflow_override
from original_plan_exercise_retained_r221 import retained_plan_exercise_override
from original_task_attachment_guard_r224 import task_attachment_override
from original_plan_resource_cancel_compat_r376 import resource_cancel_override
from original_event_research_level_r418 import research_level_override
from original_online_workflow_integration_r483 import online_workflow_override
from original_authenticated_installer_r817 import authenticated_installer_override,GLOBAL,GUARD,EXTRA
before=base.inventory(P);assert before==base.inventory(ORIGIN)
jobSource=R/'_g/Application/tools/original_server_windows_job.py';assert sha(jobSource)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
spec=importlib.util.spec_from_file_location('bounded_full_build_jobs_r673',jobSource);jobs=importlib.util.module_from_spec(spec);spec.loader.exec_module(jobs)
W.mkdir();(S/'source-and-bootstrap-pins-r673.json').write_bytes(enc({'originalNodeRecipeSHA256':sha(T/'build_online_workflow_integration_r525.mjs'),'legacyPythonRecipeSHA256':sha(T/'build_online_workflow_integration_r525.py'),
    'boundedBootstrapSHA256':sha(V/'build_authenticated_installer_bootstrap_r828.mjs'),'runnerSHA256':sha(Path(__file__)),'budgetHelperSHA256':sha(V/'bounded_build_job_r671.py')}))
process=None;job=None;policy=None;released=False;terminal=None;failure=None;samples=[];changed=set();junctionRecovered=False
def stop_wait_gate():
    global terminal
    if terminal is not None:return
    if process is None:return
    if process.stdin is not None and not process.stdin.closed:
        process.stdin.write(b'ABORT_BEFORE_BUILD\n');process.stdin.close()
    while process.poll()is None:
        try:process.wait(timeout=15)
        except subprocess.TimeoutExpired:print('OWN_FULL_BUILD_HANDLE_STILL_LIVE_NO_FORCE_OR_RESTART',flush=True)
    if job is None:raise RuntimeError('BUILD_JOB_EXIT_PROOF_MISSING_NO_RESTORE')
    while job.active_processes():time.sleep(.1)
    if policy is not None:samples.append({'at':time.time(),'job':policy.metrics(),'memory':memory_snapshot()})
    job.close();terminal={'nodeExitCode':process.returncode,'actualJobDescendantsZeroBeforeClose':True,'forceTerminationUsed':False,'gateReleased':released}
    (W/'build-terminal.json').write_bytes(enc(terminal))
def remove_only_owned_dependency_junction():
    global junctionRecovered
    link=P/'node_modules'
    if link.exists()or link.is_symlink()or link.is_junction():
        assert released and job is not None and process.poll()is not None and job.active_processes()==0
        assert link.is_junction()and link.resolve()==DEPS.resolve()and link.parent==P
        # Nonrecursive removal of this exact link, never the dependency target.
        link.rmdir();assert not link.exists();junctionRecovered=True
try:
    env={k:v for k,v in os.environ.items()if k.upper()not in ['NODE_OPTIONS','BROWSER','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS']};env['BROWSER']='none'
    with(W/'build.private.log').open('xb')as log:
        process=subprocess.Popen(['D:/Program Files/nodejs/node.exe','--max-old-space-size=2048',str(V/'build_authenticated_installer_bootstrap_r828.mjs')],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW|0x4000)
        job=jobs.OwnedWindowsJob(process);policy=BoundedBuildJob(job,CAP)
        (W/'live-build-handle.private.json').write_bytes(enc(dict(pid=process.pid,gateNotYetReleased=True,actualJobOwned=True,commitBudgetBytes=CAP)))
        samples.append({'at':time.time(),'job':policy.metrics(),'memory':memory_snapshot()})
        with(header_avatar_override(P)as avatar,project_header_override(P)as project,pending_visibility_override(P)as pending,
             personal_workflow_override(P)as workflow,retained_plan_exercise_override(P)as retained,task_attachment_override(P)as task,
             resource_cancel_override(P)as cancelled,research_level_override(P)as researched,online_workflow_override(P)as online,authenticated_installer_override(P)as lazy):
            try:
                actual=base.inventory(P);old=J(R/'work/user_feedback_20261031/event-research-level-r418/build/actual-compiled-source-files.json')
                changed={n for n in set(old)|set(actual)if old.get(n)!=actual.get(n)}
                expected=set(J(D/'prepared-candidate-r481.json')['candidatePins'])|{GLOBAL,GUARD,EXTRA};assert changed==expected and len(changed)==7
                for n in changed:
                    raw=(P/n).read_bytes();assert (hashlib.sha256(raw).hexdigest()==lazy['files'][n]['after'] if n in [GLOBAL,GUARD,EXTRA] else {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==J(D/'prepared-candidate-r481.json')['candidatePins'][n])
                    out=W/'compiled-inputs'/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
                base.dump(W/'actual-compiled-source-files.json',actual)
                latest=memory_snapshot();assert latest['availablePhysicalBytes']>=CAP+PHYSICAL_RESERVE and latest['availableCommitBytes']>=CAP+COMMIT_RESERVE,'RESOURCE_RESERVE_CHANGED_BEFORE_GATE'
                process.stdin.write(b'XNBY_FULL_BUILD_R673\n');process.stdin.flush();process.stdin.close();released=True
                print(json.dumps(dict(fullBuildStarted=True,pid=process.pid,completeSourceDiffs=7,processTreeCommitCapBytes=CAP,availableBeforeGate=latest['availablePhysicalBytes'])),flush=True)
                while process.poll()is None:
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        sample={'at':time.time(),'job':policy.metrics(),'memory':memory_snapshot()};samples.append(sample)
                        print(json.dumps({'fullBuildStillLive':True,'activeOwnedProcesses':sample['job']['activeProcesses'],'reportedPeakJobMiB':round(sample['job']['reportedPeakJobMemoryBytes']/1024**2,1)}),flush=True)
                stop_wait_gate();remove_only_owned_dependency_junction()
            finally:
                stop_wait_gate();remove_only_owned_dependency_junction()
        assert all([avatar['originalSourcesRestored'],project['sourceRestored'],pending['sourceRestored'],workflow['sourceRestored'],retained['sourceRestored'],task['sourceRestored'],cancelled['sourceRestored'],researched['sourceRestored'],online['sourceRestored'],lazy['sourceRestored']])
except Exception as e:failure={'type':type(e).__name__,'reason':str(e)}
finally:
    if terminal is None and process is not None:stop_wait_gate();remove_only_owned_dependency_junction()
    restored=base.inventory(P)==base.inventory(ORIGIN)==before
    telemetry={'samples':samples,'maximumReportedJobMemoryBytes':max((s['job']['reportedPeakJobMemoryBytes']for s in samples),default=0),'privateCommitNotRSS':True}
    (W/'build-budget-telemetry-r673.json').write_bytes(enc(telemetry))
    proof={'passed':failure is None and released and terminal is not None and terminal['nodeExitCode']==0 and restored,
           'failure':failure,'runner':'run_bounded_online_full_build_r673.py','completeBuildExecuted':released,
           'changedSources':sorted(changed),'allOtherActualR418CompilerInputsRetained':len(changed)==7,
           'tenOverrideLayersRestored':restored,'originalBuildAndReferenceSourceTreesUnchanged':restored,'terminal':terminal,
           'jobCommitLimitBytes':CAP,'maximumReportedJobMemoryBytes':telemetry['maximumReportedJobMemoryBytes'],
           'ownedDependencyJunctionRecoveredAfterChildExit':junctionRecovered,'sourceRestored':restored,
           'userProcessesOrGlobalMemorySettingsChanged':False,'actualNativeSDKOrManagerWorkflowAccepted':False,
           'publicInstalledOrGDatabaseOrDesktopChanged':False,'fullCloneReady':False}
    if proof['passed']:
        proof['files']=base.inventory(W/'dist');proof['compiledFiles']=len(proof['files']);assert proof['files']and(W/'dist/index.html').is_file()
    (W/'verified-bounded-full-build-r673.json').write_bytes(enc(proof));(S/'verified-bounded-full-build-r673.json').write_bytes(enc(proof))
    if proof['passed']:(S/'verified-full-build-r828.json').write_bytes(enc(proof))
print(json.dumps({k:v for k,v in proof.items()if k!='files'}));raise SystemExit(0 if proof['passed']else 1)
