from pathlib import Path
import ast,base64,hashlib,json,zlib
V=Path(__file__).parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_native_history_r36_20261103';J=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
fixed='06c2351a7771ac6280fa5212d09698347bc89699b2b792ca401a6a12fe417a26'
result=J(D/'public-ui-r212/result.json');outer=J(D/'public-ui-r212-outer-terminal.json')
assert result['passed'] and result['normalChromeExitCode']==0 and outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose'] and len(result['checks'])==37
details={x['case'].split('public-native-detail-and-approval-area-',1)[1]:x for x in result['checks'] if x['case'].startswith('public-native-detail-and-approval-area-')}
assert set(details)=={'pending','handled','initiated'} and all(x['passed'] and x['detailExercised'] and x['businessFormPresent'] and x['readOnlyFields'] for x in details.values())
alias={'passed':True,'actualNormalLoginAndThreePersonalWorkflowListsAndDetailsPassed':True,'pendingHandledInitiatedDetailsExercised':True,'actualBrowserChecks':37,'normalBrowserExitZeroAndActualDescendantsZero':True,'businessOperationsSubmitted':False,'credentialsTokensOrBusinessRowsExported':False,'fullNativeNangangAcceptanceClaimed':False}
(D/'public-authenticated-personal-workflow-verification.json').write_text(json.dumps(alias,indent=2)+'\n',encoding='utf-8')
assert J(D/'server-deployment-summary.json')['passed'] and J(D/'public-https-verification.json')['allPassed']
delivery=J(D/'delivery-manifest.json');old=J(R/'Document/Deployment/public_test_personal_workflow_r35_20261103/delivery-manifest.json')
known=[{'ftpName':'Zhumadian_Personal_Workflow_20261103_R35','manifestSHA256':'ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3','updateManifestSHA256':old['updateManifestSHA256'],'releaseSHA256':old['newReleaseSHA256']},{'ftpName':'Zhumadian_Native_History_20261103_R36','manifestSHA256':fixed,'updateManifestSHA256':delivery['updateManifestSHA256'],'releaseSHA256':delivery['newReleaseSHA256']}]
s=(V/'r35-retention-executed-source.py').read_text(encoding='utf-8-sig')
for a,b in [('Zhumadian_Personal_Workflow_20261103_R35','Zhumadian_Native_History_20261103_R36'),('ccede060e9c329d44e65aef3200d86f8666c73d071d743cc1535031ab15d0ca4',delivery['newReleaseSHA256']),('ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3',fixed),('20261103-R35-personal-workflow-from-exact-R34','20261103-R36-native-history-from-exact-R35'),('r35-deployment-summary','r36-deployment-summary'),('r35-retention','r36-retention'),('xnby.public.r35','xnby.public.r36'),("'R35'","'R36'"),('originalTenReadinessAndControllerUnchanged=True','originalTenPlusHistoryElevenReadinessAndControllerUnchanged=True')]:s=s.replace(a,b)
kn=next(n for n in ast.parse(s).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='known');assert kn.lineno==kn.end_lineno
lines=s.splitlines(keepends=True);lines[kn.lineno-1]='known='+repr(known)+'\n';s=''.join(lines);ast.parse(s)
(V/'r36-retention-executed-source.py').write_text(s,encoding='utf-8');compressed=base64.b64encode(zlib.compress(s.encode(),9)).decode();pins={}
for mode in ['inspect','apply']:
 ps="$ErrorActionPreference='Stop'\n$python='C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe'\n$text= & $python -I -B -c \"import base64,zlib;exec(zlib.decompress(base64.b64decode('"+compressed+"')))\" "+mode+"\nif($LASTEXITCODE -ne 0){throw 'R36_RETENTION_REFUSED_NO_UNVERIFIED_DELETE'}\n$value=$text|ConvertFrom-Json\nif($value.activeRelease -ne 'R36' -or -not $value.passed){throw 'R36_RETENTION_RESULT_REFUSED'}\n$json=$value|ConvertTo-Json -Depth 6 -Compress\nSet-Clipboard -Value $json\nWrite-Output $json\n"
 (V/('r36-retention-'+mode+'-command-source.ps1')).write_text(ps,encoding='utf-8-sig');cmd='powershell.exe -NoProfile -NonInteractive -EncodedCommand '+base64.b64encode(ps.encode('utf-16-le')).decode();(V/('r36-retention-'+mode+'-command.txt')).write_text(cmd,encoding='ascii');pins[mode]=hashlib.sha256(cmd.encode()).hexdigest()
(V/'r36-retention-command-pins.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
for oldname,newname in [('submit_r35_retention.ps1','submit_r36_retention.ps1'),('collect_r35_retention.ps1','collect_r36_retention.ps1')]:
 code=(V/oldname).read_text(encoding='utf-8-sig')
 for a,b in [('public_test_personal_workflow_r35_20261103','public_test_native_history_r36_20261103'),('user-approval-r197-20261103.json','user-approval-r210-20261103.json'),('r35','r36'),('R35','R36')]:code=code.replace(a,b)
 (V/newname).write_text(code,encoding='utf-8-sig')
(D/'retention-command-pins.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(s.encode()).hexdigest(),'commandPins':pins,'oldKnownAndCurrentReleaseManifestsFixed':known,'requiresExactActiveR36NormalReadinessNoReferencesAndNoReparse':True,'inspectBeforeApplyRequired':True,'originalDataUploadsConfigurationIISKept':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'retentionPrepared':True,'activeR36Kept':True,'onlyExactRetiredR35AndStoppedCodeRuns':True,'actualPublicReadOnlyThreeListsDetailsHTTPSPassed':True}))
