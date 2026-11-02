from pathlib import Path
import ast,json,subprocess
V=Path(__file__).parent
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b)
p=V/'verify_native_addsign_browser_r172_20261102.mjs';s=p.read_text(encoding='utf-8')
old="  if(!nativeRecords.some(x=>x.handleOpinion==='OWN_R172_ADDSIGN_OPERATOR'&&x.handleTime&&String(x.userName).includes('own_reviewer_b')))throw Error('ORIGINAL_TRANSFER_RECORD_ACTOR_TIME_AND_OPINION_REQUIRED');"
new=r'''  const added=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_operator-added'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  const final=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-final'&&x.handleTime&&String(x.userName).includes('own_operator_a'));
  if(added.length!==1||final.length!==1||Number(added[0].handleTime)>Number(final[0].handleTime))throw Error('ORIGINAL_ADDED_AND_FINAL_REVIEW_RECORDS_AND_ORDER_REQUIRED');
  if(wire.addsignType==='1'){
   const original=nativeRecords.filter(x=>x.handleOpinion==='OWN_R165_reviewer-after-added'&&x.handleTime&&String(x.userName).includes('own_reviewer_b'));
   if(original.length!==1||Number(added[0].handleTime)>Number(original[0].handleTime)||Number(original[0].handleTime)>Number(final[0].handleTime))throw Error('ADDSIGN_BEFORE_ADDED_THEN_ORIGINAL_THEN_FINAL_ORDER_REQUIRED');
  }
  const independentAddsignOpinionRetained=nativeRecords.some(x=>x.handleOpinion==='OWN_R172_ADDSIGN_OPERATOR'&&x.handleTime&&String(x.userName).includes('own_reviewer_b'));
  await fs.writeFile(O+'/addsign-sequence-and-opinion-observation.json',JSON.stringify({addsignType:wire.addsignType,actualAddedAndFinalReviewRecordsAndOrderMatched:true,originalReviewerAfterAddedVerified:wire.addsignType==='1',independentAddsignOpinionRetained,opinionRetentionGapRemains:!independentAddsignOpinionRetained,completeAddsignAcceptance:independentAddsignOpinionRetained},null,2));
  cases.push({case:'actual-addsign-mode-sequence-and-distinct-approval-records-preserved',passed:true,addsignType:wire.addsignType,independentAddsignOpinionRetained});'''
s=once(s,old,new);p.write_text(s,encoding='utf-8')
p=V/'verify_full_controller_addsign_r172_20261102.py';s=p.read_text(encoding='utf-8')
s=once(s,"parser.add_argument('--resubmit-returned',action='store_true');options=parser.parse_args()","parser.add_argument('--resubmit-returned',action='store_true');parser.add_argument('--completed-addsign-readback',action='store_true');options=parser.parse_args()")
s=once(s,'if options.closed_readback_only or options.return_existing_pending or options.resubmit_returned:', 'if options.closed_readback_only or options.return_existing_pending or options.resubmit_returned or options.completed_addsign_readback:')
s=once(s,"assert options.attempt in ['r72','r73']", "assert options.attempt in ['r72','r73','r74']")
s=once(s,"add_type='1' if options.attempt=='r72' else '2'","add_type='1' if options.attempt in ['r72','r74'] else '2'")
s=once(s,"        state_source=R/", "        if options.completed_addsign_readback:\n            assert options.attempt=='r74'\n            phases=[('operator-completed-readback','own_operator_a','operator',False,False)]\n        state_source=R/")
s=once(s,"'actualAddsignAndRemainingReviewsCompleted':True", "'actualAddsignAndRemainingReviewsCompleted':not options.completed_addsign_readback,'onlyPreviouslyCompletedAddsignReadbackExecuted':options.completed_addsign_readback")
ast.parse(s);p.write_text(s,encoding='utf-8')
p=V/'run_addsign_r172_20261102.py';s=p.read_text(encoding='utf-8');s=once(s,"assert attempt in ['r72','r73'];","assert attempt in ['r72','r73','r74'];")
s=once(s,"'--event-dictionaries'],stdout=log", "'--event-dictionaries',*(['--completed-addsign-readback']if attempt=='r74'else[])],stdout=log")
ast.parse(s);p.write_text(s,encoding='utf-8')
r=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(V/'verify_native_addsign_browser_r172_20261102.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
print(json.dumps({'observerAssumptionCorrected':True,'originalR72FailedEvidencePreserved':True,'actualApprovalSequenceAssertionsAdded':True,'independentOpinionGapStillRecorded':True,'productOrConfigChanged':False}))
