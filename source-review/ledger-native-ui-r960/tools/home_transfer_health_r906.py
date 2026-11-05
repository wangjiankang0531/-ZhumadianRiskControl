from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
 pins=json.loads((V/'ledger-source-pins-r960.json').read_bytes());assert sha(D/'full-source-and-restore-plan.private.json')==pins['candidatePlanSHA256']
 plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes());assert plan['target']==str(G)and plan['exactPublicR47ProgramAndControllerBytes']and plan['onlyPrivateConfigurationManifestPinAdapted']
 release=json.loads((D/'candidate/release-manifest.json').read_bytes());assert sha(D/'candidate/release-manifest.json')==plan['candidateReleaseSHA256']
 source=Path(plan['sources']['tools/original_public_test_update.py']['source']);assert sha(source)==release['controllerFiles']['tools/original_public_test_update.py']
 spec=importlib.util.spec_from_file_location('exact_r47_updater_r931',source);wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper);assert wrapper.declared(release)
 runtime=wrapper.runtime();return plan,runtime,wrapper
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G;plan,runtime,wrapper=profile()
 assert sha(G/'release-manifest.json')==plan['candidateReleaseSHA256']
 p=G/'private/server-configuration.json';assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['configBefore']
 result=runtime.health(G,row,True,gateway_port=gateway_port);assert result and result['supervisionReady']
 return {'exactR47UpdaterAndCoreUsed':True,'originalReleaseHealthRetained':True,'supervisionReadinessRequired':True,'privateApplicationSettingsChanged':False,'publicIISOrTLSAccepted':False}
