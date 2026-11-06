"""Exact existing local branches, both original diagnosis and candidate evidence."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent;D=R/'Document/Deployment/hazard_attachment_transaction_r1214_20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(repo,*args):return subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True).stdout.decode().strip()
parents={'application':'fb3b2161341b3f5faf44e30181680b579435d221','engine':'3be7748e5c34c0c76ead3f911291b1bb6ae158ff'}
branches={'application':'review/workplace-r19-live-local-20261031','engine':'review/workplace-r19-live-progress-local-20261031'}
for kind,repo in [('application',A),('engine',E)]:assert git(repo,'rev-parse','refs/heads/'+branches[kind])==parents[kind],'LOCAL_REF_DRIFT_REFUSE'
assert not(D/'local-git-completed-r1219.json').exists()
scopes=[json.loads(p.read_bytes())for p in [R/'Document/Deployment/hazard_attachment_original_r1207_20261106/local-source-files-r1216.json',D/'local-source-files-r1218.json']]
files={kind:sorted(set(p for s in scopes for p in s[kind]))for kind in ['application','engine']}
dest=A/'tools/verification/hazard_attachment_r1218/commit_hazard_attachment_r1219.py';assert not dest.exists();dest.write_bytes(Path(__file__).read_bytes());files['application'].append(dest.relative_to(A).as_posix())
for kind,repo in [('application',A),('engine',E)]:
 for rel in files[kind]:
  p=repo/rel
  if p.suffix=='.py':ast.parse(p.read_text('utf8'),filename=str(p))
  elif p.suffix=='.json':json.loads(p.read_bytes())
  elif p.suffix=='.mjs':subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(p)],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
held=sha(A/'native/main.cpp');s=importlib.util.spec_from_file_location('hazard_attachment_local_commit',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h);receipt={}
for kind,repo in [('application',A),('engine',E)]:receipt[kind]=h.commit(repo,parents[kind],branches[kind],files[kind],kind+'-hazard-attachment-r1219',message_override='Reproduce original hazard attachment loss on failed save; verify minimal service candidate through ordinary upload, failed edit, corrected retry and normal restart; retain late-insert transaction and public gaps',update_existing=True)
assert sha(A/'native/main.cpp')==held
receipt.update({'formalHeadsAndIndexesUnchanged':True,'onlyExistingLocalBranches':True,'heldNativeUnchanged':True,'publicPushedOrDeployed':False,'originalAttachmentLossReproduced':True,'candidateOriginalUIFailureRetryAndRestartAccepted':True,'laterAttachmentInsertFailureOrWholeNangangAccepted':False,'SSHAuthenticationAccepted':False})
(D/'local-source-files-r1219.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(D/'local-git-completed-r1219.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,ensure_ascii=False))
