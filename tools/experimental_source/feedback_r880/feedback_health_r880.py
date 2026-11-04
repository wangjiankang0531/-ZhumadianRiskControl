from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent;D=V
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
 plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes())
 assert plan['runtimeCandidateReleaseSHA256']=='eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93'
 p=V.parent/'original_public_test_update_r45_bootstrap_r847.py'
 assert sha(p)=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
 s=importlib.util.spec_from_file_location('feedback_original_runtime_r880',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 return plan,m,None
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G
 plan,runtime,_=profile();assert sha(G/'release-manifest.json')==plan['runtimeCandidateReleaseSHA256']
 p=G/'private/server-configuration.json';assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['runtimeConfigurationAfterPin']
 runtime.health(G,row,True,gateway_port=gateway_port)
 return {'originalR45ReleaseHealthRetained':True,'onlyOwnedTaskFlowCodeConfigured':True,'publicAccepted':False}
