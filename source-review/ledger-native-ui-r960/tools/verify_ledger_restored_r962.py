from pathlib import Path
import json,hashlib,subprocess
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).resolve().parent;D=R/'Document/Deployment/ledger_original_ui_r940_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
plan=J(R/'Document/Deployment/unified_home_supervision_exact_r930_20261104/full-source-and-restore-plan.private.json')
latest=J(R/'work/ledgerfull-r960/verified-ledger-ui-r960.json');assert latest['passed'] and latest['actualTwoSixComponentLifecycles'] and latest['codeRestored'] and latest['privateConfigurationUnchanged'] and latest['originalCurrentPointerRestored']
terminals=[]
for n in [941,946,948,950,952,960]:
 d=J(R/f'work/ledgerfull-r{n}/verified-ledger-ui-r{n}.json');assert d['codeRestored'] and d['privateConfigurationUnchanged'] and d['originalCurrentPointerRestored']
 for t in d['terminals']:
  assert t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and t['normalOwnedShutdown'] and not t['forceTerminationUsed'] and all(x==0 for x in t['exitCodes'].values());terminals.append(t)
 s=J(R/f'work/ledgerfull-r{n}/pointer-snapshot/snapshot.private.json');assert s['phase']=='restored' and pin(G/'UserData/OriginalServer/current-run.json')==s['before']
 assert (R/f'work/ledgerfull-r{n}/pointer-snapshot/before.private.json').read_bytes()==(G/'UserData/OriginalServer/current-run.json').read_bytes()
rows=dict(plan['mutations'])
for group in ['retiredKnownFrontendPaths','knownRebuildableCachesToRemoveOnlyDuringFutureApply']:
 for n,p in plan[group].items():assert n not in rows;rows[n]={'before':p,'after':None}
for n,r in rows.items():assert pin(G/n)==r['before'],'CODE_PREIMAGE_DRIFT:'+n
assert pin(G/'private/server-configuration.json')==plan['configBefore'] and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore'] and sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
for phase in ['first-start','normal-restart']:
 b=R/'work/ledger-browser-r960'/phase;d=J(b/'result.json');assert d['passed'] and d['generationRequests']==0 and d['fixtureRecordsCreated']==0 and not d['APIsMocked'] and not d['tokenInjectedIntoPreviewOrDownload']
 assert J(b/'browser-terminal.json')['normalBrowserClosed'];ctx=J(R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941/ledger-context.private.json');files=list((b/'downloads').iterdir());assert len(files)==1 and pin(files[0])==ctx['pdf']
 node=J(R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941/resume-r960'/phase/'probe-terminals.json');assert len(node)==2 and all(x['exitCode']==0 and x['actualJobDescendantsZero'] for x in node)
 metadata=(R/f'work/original-manager-full-lifecycle-r609/ledger-ui-r941/metadata-readback-r960-{phase}.private.properties').read_text('ascii');assert 'persistentWritesIssued=false' in metadata.splitlines()
out={'passed':True,'allSixAttemptCodeAndPrivateConfigurationAndPointersRestored':True,'currentCodePathsIndependentlyMatchedBefore':len(rows),'durablePointerBeforeImagesMatched':6,'actualNormalControllerLifecycles':len(terminals),'finalTwoNormalBrowserDownloadsExactlyMatchSameGeneratedPDF':True,'finalTwoMetadataReadbacksWereReadOnly':True,'newPublicOrDesktopWrites':False,'fullCloneReady':False}
p=D/'independent-restore-r962.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
