from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
def put(name,s):
    p=V/name;assert not p.exists();p.write_text(s,encoding='utf-8')
    if p.suffix=='.py':ast.parse(s)
for name in ['build_pending_visibility_r177.py','build_pending_visibility_r177.mjs']:
    s=(V/name).read_text(encoding='utf-8').replace('workflow-pending-visibility-r177','workflow-pending-visibility-r178').replace('build_pending_visibility_r177.mjs','build_pending_visibility_r178.mjs').replace('original_workflow_pending_visibility_r177 import','original_workflow_pending_visibility_r178 import').replace('WorkflowInfoPendingVisibilityR177.vue','WorkflowInfoPendingVisibilityR178.vue')
    put(name.replace('r177','r178'),s)
for name in ['prepare_pending_visibility_runtime_r177.py','restore_pending_visibility_runtime_r177.py']:
    s=(V/name).read_text(encoding='utf-8').replace('workflow-pending-visibility-r177','workflow-pending-visibility-r178').replace('r77','r78').replace('r177-restore','r178-restore')
    put(name.replace('r177','r178'),s)
host=(V/'verify_full_controller_pending_visibility_r177_20261102.py').read_text(encoding='utf-8').replace('verify_native_pending_visibility_r177_20261102.mjs','verify_native_pending_visibility_r178_20261102.mjs')
host=once(host,"options.attempt=='r77'","options.attempt=='r78'")
host=once(host,"('reviewer-early-probe','own_reviewer_b','reviewer',False,False),('operator-membership-unavailable'","('reviewer-early-probe','own_reviewer_b','reviewer',False,False),('operator-other-node-link','own_operator_a','reviewer',False,False),('operator-membership-unavailable'")
host=once(host,"'injectMembershipFailure':label=='operator-membership-unavailable'","'injectMembershipFailure':label=='operator-membership-unavailable','probeWrongOperator':label=='operator-other-node-link'")
host=once(host,"['reviewer-addsign','reviewer-early-probe','operator-membership-unavailable','operator-added','reviewer-after-added']","['reviewer-addsign','reviewer-early-probe','operator-other-node-link','operator-membership-unavailable','operator-added','reviewer-after-added']")
host=host.replace('xnby.r177.pending-visibility-native-controller-check.v1','xnby.r178.exact-pending-operator-native-controller-check.v1')
put('verify_full_controller_pending_visibility_r178_20261102.py',host)
s=(V/'verify_native_pending_visibility_r177_20261102.mjs').read_text(encoding='utf-8')
s=once(s,"'operator-membership-unavailable'].includes(wire.phaseName)","'operator-membership-unavailable','operator-other-node-link'].includes(wire.phaseName)")
s=once(s,'if(wire.probeEarlyApproval){','if(wire.probeEarlyApproval||wire.probeWrongOperator){')
s=once(s,"if(wire.account!=='own_reviewer_b'||wire.phaseName!=='reviewer-early-probe'||!context.originalReviewerRoute)","if((wire.probeWrongOperator?(wire.account!=='own_operator_a'||wire.phaseName!=='operator-other-node-link'):(wire.account!=='own_reviewer_b'||wire.phaseName!=='reviewer-early-probe'))||!context.originalReviewerRoute)")
needle="  const originalRoute=new URL(context.originalReviewerRoute,wire.base);"
s=once(s,needle,"  if(wire.probeWrongOperator&&!found)throw Error('OWN_ACTIVE_ADDED_REVIEWER_MUST_HAVE_SAME_PROCESS_PENDING');\n"+needle)
s=once(s,"const observation={earlyApprovalIncorrectlyAccepted:false,","const observation={sameProcessDifferentOperatorLinkChecked:!!wire.probeWrongOperator,earlyApprovalIncorrectlyAccepted:false,")
put('verify_native_pending_visibility_r178_20261102.mjs',s)
runner=(V/'run_pending_visibility_r177_20261102.py').read_text(encoding='utf-8').replace("attempt='r77'","attempt='r78'").replace('verify_full_controller_pending_visibility_r177_20261102.py','verify_full_controller_pending_visibility_r178_20261102.py').replace('restore_pending_visibility_runtime_r177.py','restore_pending_visibility_runtime_r178.py')
put('run_pending_visibility_r178_20261102.py',runner)
r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_pending_visibility_r178_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode()
print(json.dumps({'prepared':True,'positiveSameProcessOtherOperatorRegressionAdded':True,'stages':10,'noRuntimeChanges':True}))
