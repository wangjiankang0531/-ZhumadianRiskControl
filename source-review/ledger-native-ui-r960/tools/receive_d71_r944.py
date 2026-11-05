from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,datetime
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
M=R/'Document/Coordination/交接消息';p=M/'驻马店三维账号编辑会话组件_给驻马店3_20261104_d71.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads(p.read_bytes());assert not m['publicChanges'] and not m['publicInstallRequested']
for name in ['sourceArchive','runtimeArchive']:
 assert sha(Path(m[name]).read_bytes())==m[name+'SHA256']
 with zipfile.ZipFile(m[name]) as z:
  names=z.namelist();assert len(names)==len(set(names));assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and '\\' not in n for n in names)
  if name=='runtimeArchive':
   for n,pin in m['runtimePins'].items():
    b=z.read(n);assert len(b)==pin['bytes'] and sha(b)==pin['sha256']
  else:
   for n,pin in m['sourcePins'].items():
    assert sha(z.read('Application/'+n))==pin and sha((R/'Application'/n).read_bytes())==pin
out={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维','receivedAt':datetime.datetime.now().astimezone().isoformat(),
 'messageSHA256':sha(p.read_bytes()),'sourceArchiveSHA256Verified':m['sourceArchiveSHA256'],'runtimeArchiveSHA256Verified':m['runtimeArchiveSHA256'],
 'runtimePinsIndependentlyVerified':len(m['runtimePins']),'declaredWorkingAndArchivedSourcePinsVerified':len(m['sourcePins']),
 'sender245TestsIndependentlyRerun':False,'archivesExecutedOrInstalled':False,'publicInstallRequested':False,'publicChangedByReceiver':False,
 'R47UploadedAndReadbackVerified':True,'R47ServerPreflightOrDeployResultReceived':False,'lastVerifiedPublicVersion':'R45',
 'normalLoginUIToOwnerMemoryHandoffStillPending':True,'actualNewNativeEXELaunchAndAccountSwitchStillPending':True,
 'firstActualUserLayerInitializationStillNeedsReview':True,'originalSixComponentAndJobHelperMustRemainUnchanged':True,
 'componentMustStayInVersionedNestedPrivateNamespace':True,'noManualTokenPasteOrJWTCommandArguments':True,
 'trustedCurrentUserIdentityMustPrecedeRunDirectoryAndChildCreation':True,'noSharedRecentProjectOrSamplePublishing':True,
 'actualIISPublicTLSAndLocal252AcceptanceStillPending':True,'futureIntegrationMustDiscoverFreshRuntimeAndFilePreimages':True,
 'directThreadMessageOrWakeupClaimed':False,'fullCloneReady':False}
q=M/'驻马店3已读D71账号编辑组件_20261104_r944.json';assert not q.exists();q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(V/'d71-receiver-ack-r944.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=True))
