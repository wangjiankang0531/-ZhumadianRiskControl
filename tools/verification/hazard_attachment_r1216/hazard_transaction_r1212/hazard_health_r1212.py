from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';D=R/'Document/Deployment/hazard_attachment_transaction_r1212_20261106'
def profile():
 p=D/'full-source-and-restore-plan.private.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='9fc421adb10e4f9f97b7c319095400c52761e490aafbc6bb7a23969c38d8c9ff'
 plan=json.loads(p.read_bytes());source=Path('D:\\CodexData\\home\\visualizations\\2026\\10\\28\\01a1836e-e4ee-7fb0-be6f-b24f2e2672e4\\tencent-feedback-20261031\\original_public_test_update_r45_bootstrap_r847.py')
 assert hashlib.sha256(source.read_bytes()).hexdigest()=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
 s=importlib.util.spec_from_file_location('hazard_r45_original_health',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return plan,m,None
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G;plan,m,_=profile();assert hashlib.sha256((G/'release-manifest.json').read_bytes()).hexdigest()==plan['candidateReleaseSHA256']
 m.health(G,row,True,gateway_port=gateway_port);return {'originalR45OtherBackendHealthPreserved':True,'hazardSourceBackendReplaced':True,'publicAccepted':False}
