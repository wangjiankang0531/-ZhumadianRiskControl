from pathlib import Path
import hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/event_crud_native_r1004_20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile():
 pins=json.loads((V/'event-source-pins-r1004.json').read_bytes());assert sha(D/'full-source-and-restore-plan.private.json')==pins['candidatePlanSHA256']
 plan=json.loads((D/'full-source-and-restore-plan.private.json').read_bytes());assert plan['target']==str(G)and plan['exactPreparedR48ProgramAndControllerBytes']and plan['onlySixOwnedDockReceiverURLsAndPrivateManifestPinsAdapted']
 release=json.loads((D/'candidate/release-manifest.json').read_bytes());assert sha(D/'candidate/release-manifest.json')==plan['candidateReleaseSHA256']
 source=Path(plan['sources']['tools/original_public_test_update.py']['source']);assert sha(source)==release['controllerFiles']['tools/original_public_test_update.py']
 spec=importlib.util.spec_from_file_location('exact_r47_updater_r931',source);wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper);assert wrapper.declared(release)
 runtime=wrapper.runtime();return plan,runtime,wrapper
def health(app,row,*,gateway_port):
 assert Path(app).absolute()==G;plan,runtime,wrapper=profile()
 assert sha(G/'release-manifest.json')==plan['candidateReleaseSHA256']
 p=G/'private/server-configuration.json';assert {'bytes':p.stat().st_size,'sha256':sha(p)}==plan['configAfter']
 result=runtime.health(G,row,True,gateway_port=gateway_port);assert result and result['supervisionReady']
 return {'exactPreparedR48UpdaterAndCoreUsed':True,'originalReleaseHealthRetained':True,'supervisionReadinessRequired':True,'onlySixOwnLoopbackNotificationSettingsChanged':True,'publicIISOrTLSAccepted':False}
