"""New attempt after verified terminal/recovery, retaining product candidate bytes."""
from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';D=R/'Document/Deployment/supervision_current_full_r920_20261104'
OLD=V/'supervision_full_r921';H=V/'supervision_full_r925'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
assert not H.exists()and not(R/'work/sv925').exists()
proof=J(D/'conditional-pointer-recovery-r923.json');assert proof['passedAsScopedRecovery']and proof['noActiveGProcessReferencesBeforeOrAfter']and proof['durableOriginalPointerBeforeImageRestored']
assert J(V/'ready-observation-r924-result.json')['passed']
H.mkdir();(H/'classes').mkdir()
for p in OLD.rglob('*'):
 if p.is_file()and p.name!='current-supervision-source-pins-r921.json':
  dest=H/p.relative_to(OLD)
  if p.suffix in ['.py','.mjs']:
   text=p.read_text('utf8').replace('current-supervision-r921','current-supervision-r925').replace('current-supervision-browser-r921','current-supervision-browser-r925').replace('work/sv921','work/sv925').replace("R/'work/sv921'","R/'work/sv925'").replace('current-supervision-source-pins-r921.json','current-supervision-source-pins-r925.json').replace('verified-current-supervision-r921.json','verified-current-supervision-r925.json').replace('current-supervision-full-result-r921.json','current-supervision-full-result-r925.json')
   if p.name=='run_home_transfer_full_r906.py':
    text=once(text,"assert sha(D/'full-source-and-restore-plan.private.json')", "assert J(D/'conditional-pointer-recovery-r923.json')['passedAsScopedRecovery']\nready_observer=load('ready_observer_r924',V/'owned_ready_observation_r924.py')\nassert sha(D/'full-source-and-restore-plan.private.json')")
    text=once(text,"    record['row']=runtime.owned_ready(G,manifest,gateway_port=port);return record", "    record['row']=ready_observer.observe_ready(runtime,G,manifest,record,lambda value:save(label+'/observed-ready.private.json',value),gateway_port=port);return record")
    text=once(text,"receiptPath,receipt=terminal_helper.receipt_for_run(G,Path(stopped[0]['run']),proc.pid)","receiptPath,receipt=terminal_helper.receipt_for_run(G,Path(stopped[0]['run']),proc.pid,record.get('observedReady'))")
    text=once(text,"ownedRow=processes[-1]['row']if processes else None", "ownedRow=(processes[-1]['row']or processes[-1].get('observedReady'))if processes else None")
    funcs=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
    old,new=funcs(p.read_text('utf8')),funcs(text);assert old.keys()==new.keys()and [n for n in old if old[n]!=new[n]]==['start','stop']
   if p.suffix=='.py':ast.parse(text)
   dest.write_text(text,encoding='utf8')
  else:dest.write_bytes(p.read_bytes())
(H/'owned_ready_observation_r924.py').write_bytes((V/'owned_ready_observation_r924.py').read_bytes())
deps=['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in deps})
(H/'current-supervision-source-pins-r925.json').write_text(json.dumps({'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':pins},indent=2)+'\n',encoding='utf8')
report={'prepared':True,'productCandidateBytesUnchanged':True,'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'previousRunActuallyTerminalAndRecovered':True,
 'changedHarnessFunctions':['start','stop'],'originalIdentityValidatorRetained':True,'onlySameLiveHandleAndExactPointerMayRetryTimeout':True,'maxIdentityQueries':3,
 'durableObservedReadyBoundToExactRunReceiptBeforePointerRestore':True,'syntheticObserverChecks':8,'servicesDatabaseDesktopOrPublicChanged':False}
(D/'prepared-retry-r925.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report))
