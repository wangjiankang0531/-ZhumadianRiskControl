"""Exact original R45 backend, no supervision module or private setting change."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/r45_owned_backend_r848_20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
    pins=json.loads((V/'r45-compatibility-source-pins-r850.json').read_bytes())
    assert sha(D/'full-source-and-restore-plan.private.json')==pins['candidatePlanSHA256']
    plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes())
    assert plan['target']==str(G)and plan['schema']=='xnby.r45-original-backend.owned-full-candidate.plan.v1'
    assert plan['onlyExistingOwnedSyntheticFixture']and plan['onlyPrivateConfigurationManifestPinAdapted']
    assert sha(D/'candidate/release-manifest.json')==plan['candidateReleaseSHA256']
    release=json.loads((D/'candidate/release-manifest.json').read_bytes())
    assert 'businessSupervisionPdf'not in release
    runtimePath=V/'original_public_test_update_r45_bootstrap_r847.py'
    assert sha(runtimePath)=='d5af4267715b5b4fdcd740c27cdadf3742d5dfc5a8f3f7d06cc84b6ddac0c9df'
    s=importlib.util.spec_from_file_location('r45_original_runtime_health',runtimePath);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return plan,m,None
def health(app,row,*,gateway_port):
    assert Path(app).absolute()==G
    plan,runtime,_=profile()
    assert sha(G/'release-manifest.json')==plan['candidateReleaseSHA256']
    p=G/'private/server-configuration.json'
    assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['configBefore']
    runtime.health(G,row,True,gateway_port=gateway_port)
    return {'originalReleaseHealthRetained':True,'newBackendOrSupervisionModulePresent':False,
        'privateApplicationSettingsChanged':False,'publicIISOrTLSAccepted':False}
