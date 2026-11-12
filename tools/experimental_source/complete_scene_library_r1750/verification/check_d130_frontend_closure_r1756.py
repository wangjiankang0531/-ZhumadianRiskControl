"""Verify the distinct frontend manifest and inspect merge boundaries, without installing it."""
from pathlib import Path
import hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/d130_source_receiver_r1754_20261107';V=Path(__file__).parent
prior=json.loads((D/'received-d130.json').read_bytes());assert prior['passed']and prior['archiveFilesMatchedGit']==316
zpath=R/'Document/Deployment/scene_model_sync_20261107/source.zip';assert hashlib.sha256(zpath.read_bytes()).hexdigest()==prior['sourceArchiveSHA256']
with zipfile.ZipFile(zpath)as z:
 prefix='tools/experimental_source/scene_model_overlay_20261106/';manifest=json.loads(z.read(prefix+'source-pins.json'));pins=manifest['files'];assert len(pins)==273
 for n,h in pins.items():assert hashlib.sha256(z.read(prefix+'candidate/'+n)).hexdigest()==h
 client=z.read(prefix+'candidate/web/src/cloud_layer_client.js').decode('utf8')
 assert 'readSceneModels'in client and 'writeSceneModels'in client
 assert not any(n in client for n in ['listSceneFiles','readSceneFile','saveSceneFile'])
 own=(R/'work/scene-file-frontend-r1735/source/web/src/cloud_layer_client.js').read_text('utf8');assert all(n in own for n in ['listSceneFiles','readSceneFile','saveSceneFile'])
 api=(R/'work/d130-source-receiver-r1754/scene_model_sync/api.py').read_text('utf8');assert "origins!=[ORIGIN]"in api and "ORIGIN='https://www.joinlinksmart.com'"in api
proof={'passed':True,'D130AllArchiveFilesPreviouslyMatchedGit':316,'D130FrontendCandidatePinsVerified':273,'D130BackendPinsPreviouslyVerified':4,'bothClientsMustBeMergedNotOverwritten':True,'receiverNamedSceneFileMethods':['listSceneFiles','readSceneFile','saveSceneFile'],'senderLiveModelMethods':['readSceneModels','writeSceneModels'],'senderAPICanonicalProductionOriginPinned':True,'futureOriginalOwnedLoopbackMustBindExplicitTrustedOriginWithoutBlanketCORS':True,'receiverAuthRetirementPrivateAssetFetcherMustRemain':True,'senderRuntimeChecksNotClaimedAsReceiverRuntimeChecks':True,'installedOrMerged':False,'publicChanged':False}
p=D/'frontend-closure-and-merge-boundaries-r1756.json';assert not p.exists();p.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ack={'schema':'xnby.coordination.D130.receiver-source-check.v1','sender':'驻马店3','recipient':'驻马店三维','stage':'R1756','D130GitSourceArchiveFilesVerified':316,'backendPinsVerified':4,'frontendPinsVerified':273,'D131InProgressNotClaimedReceived':True,'receiverWholeSceneSnapshotFirstOriginalSaveAndRefreshFivePassed':True,'receiverWholeSceneOriginalRestartReadOnlyStillRunning':True,'mergeBoundary':proof,'peer8803OrSourcesChanged':False,'publicUpdated':False,'sharedRecordNotRealtimeAck':True}
p=R/'Document/Coordination/交接消息/驻马店3已核收D130源码及双库接线边界_r1756_20261107.json';assert not p.exists();p.write_text(json.dumps(ack,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
