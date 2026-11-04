"""Correct one stale diagnostic fixture reference; preserve the failed R883 scope."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;S=V/'event_picker_r883';D=V/'event_picker_r884';R=Path('D:/Project/Zhumadian')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();old=json.loads((S/'event-picker-source-pins-r883.json').read_bytes())['files']
 assert all(sha(Path(n))==pin for n,pin in old.items())
 prior=json.loads((R/'work/ep883/verified-event-picker-r883.json').read_bytes())
 assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
 assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(v==0 for v in t['exitCodes'].values()) for t in prior['terminals'])
 assert not(R/'work/event-picker-browser-r883').exists()
 D.mkdir();files=[]
 for name in ['event_picker_browser_r883.mjs','event_picker_probe_r883.py','run_event_picker_full_r883.py']:
  s=(S/name).read_text('utf8').replace('r883','r884')
  if name.startswith('event_picker_probe_'):
   a="W=R/'work/original-manager-full-lifecycle-r609/task-ui-r806'";assert s.count(a)==1;s=s.replace(a,"W=R/'work/original-manager-full-lifecycle-r609/feedback-r880'")
  if name.startswith('run_'):
   a="prior=J(R/'work/fb880/verified-feedback-chain-r880.json')";assert s.count(a)==1;s=s.replace(a,"prior=J(R/'work/ep883/verified-event-picker-r883.json')")
   a="prior['taskConfigurationRestoredBeforeCode']";assert s.count(a)==1;s=s.replace(a,"prior['privateConfigurationUnchanged']")
   assert "Z=R/'work/ep883'" in s;s=s.replace("Z=R/'work/ep883'","Z=R/'work/ep884'")
  q=D/name.replace('r883','r884');q.write_text(s,encoding='utf8');files.append(q)
  if q.suffix=='.py':ast.parse(s)
  else:assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(q)],capture_output=True).returncode==0
 (D/'event-picker-source-pins-r884.json').write_text(json.dumps({'files':{str(p):sha(p)for p in files}},indent=2)+'\n',encoding='utf8')
 (D/'r883-prior-refusal.json').write_text(json.dumps({'reason':'Diagnostic probe retained old task-ui-r806 flight while parent used feedback-r880; nonce guard refused before browser allocation','browserWasNotStarted':True,'priorNormalStopCodeConfigPointerRestored':True,'newScopeFixesFixtureReferenceAndOwnOutputsOnly':True})+'\n',encoding='utf8')
 print('R884_REFERENCE_FIXED_OLD_FAILURE_RETAINED')
if __name__=='__main__':main()
