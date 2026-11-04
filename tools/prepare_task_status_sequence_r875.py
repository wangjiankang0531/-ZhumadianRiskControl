"""Use the actual R850 restoration proof field; preserve the refused R874 attempt."""
from pathlib import Path
import ast, hashlib, json, subprocess
V=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    old=json.loads((V/'task-status-source-pins-r874.json').read_bytes())
    for name,pin in old['files'].items(): assert sha(Path(name))==pin
    R=Path('D:/Project/Zhumadian')
    assert not (R/'work/task-status-full-r874').exists()
    assert not (R/'work/original-manager-full-lifecycle-r609/task-status-sequence-r874').exists()
    prior=json.loads((R/'work/original-backend-full-r850/verified-component-bootstrap-r850.json').read_bytes())
    assert prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
    files=[]
    for name in ['verify_task_status_sequence_browser_r874.mjs','probe_task_status_sequence_r874.py','run_task_status_sequence_r874.py']:
      s=(V/name).read_text('utf8').replace('r874','r875')
      if name.startswith('run_'):
        old="assert prior['passed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']"
        assert s.count(old)==1
        s=s.replace(old,"assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']")
      p=V/name.replace('r874','r875'); assert not p.exists(); p.write_text(s,encoding='utf8'); files.append(p)
      if p.suffix=='.py':ast.parse(s)
      else:assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True).returncode==0
    pins={'files':{str(p):sha(p)for p in [*files,Path(__file__)]},'businessWritesIntended':False,'newNativeBuildOrRun':False}
    (V/'task-status-source-pins-r875.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
    (V/'task-status-r874-refused-before-allocation.json').write_text(json.dumps({'failure':'KeyError:taskConfigurationRestoredBeforeCode','actualPriorSchemaField':'privateConfigurationUnchanged','newR875FixesOnlyPriorEvidenceFieldAndOwnOutputScope':True,'R874AttemptNotAllocated':True,'R874GCodeNotChanged':True,'R874ServicesNotStarted':True})+'\n',encoding='utf8')
    print('R875_PREPARED_PRIOR_RESTORE_PROOF_MATCHED')
if __name__=='__main__':main()
