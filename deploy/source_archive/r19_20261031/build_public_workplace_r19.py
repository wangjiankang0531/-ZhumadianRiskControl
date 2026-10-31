from pathlib import Path
import ast,copy,datetime,hashlib,importlib.util,json,sys,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
W=R/'work/user_feedback_20261031';D=R/'Document/Deployment/public_test_workplace_r19_20261031'
PRE=R/'Document/Deployment/public_test_home_viewport_r18_20261031_r2'
M=R/'Document/Deployment/server_directory_migration_20261030_r17d/delivery/payload/tools/original_public_test_update.py'
BASE=W/'workplace-security-build-r1';DIST=BASE/'build/dist'
OLD='2eb15cf467f00acc615ac39b9a6cc5deaa5413c5642e44234783b22a0b1e2c35'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_bytes())
def enc(value):return(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def put(path,raw):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
def main():
    sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
    assert not D.exists()
    assert read(BASE/'compiled-static-verification.json')['allFilesExactSHA256Verified']==836
    assert read(W/'workplace-chart-r1/browser-proof-r3/result.json')['passed']
    before=PRE/'delivery/bundle/payload'
    assert sha(before/'release-manifest.json')==OLD
    old=read(before/'release-manifest.json');payload=read(before/'payload-manifest.json')
    assert digest(enc(payload))==old['payloadManifestSHA256']
    new=copy.deepcopy(payload);prefix='frontend/security_pc/'
    desired=read(BASE/'candidate-result.json')['fullFrontendFiles']
    new['files']={n:v for n,v in new['files'].items()if not n.startswith(prefix)}
    new['files'].update({prefix+n:v for n,v in desired.items()})
    assert {n:v for n,v in payload['files'].items()if not n.startswith(prefix)}=={n:v for n,v in new['files'].items()if not n.startswith(prefix)}
    new.setdefault('frontendUpdate',{})['workplaceViewport']={'revision':'20261031-r1','feedbackCells':['G3','G4','G5'],'componentBrowserProofSHA256':sha(W/'workplace-chart-r1/browser-proof-r3/result.json'),'compiledStaticProofSHA256':sha(BASE/'compiled-static-verification.json'),'originalTaskAndStatisticsScriptPreserved':True}
    bodies={prefix+n:(DIST/n).read_bytes()for n,v in desired.items()if payload['files'].get(prefix+n)!=v}
    assert all(digest(bodies[n])==new['files'][n]['sha256']for n in bodies)
    css=prefix+'xnby-home-viewport-97d8e3adeed9.css'
    assert new['files'][css]==payload['files'][css]
    removed={n:{'bytes':v['bytes'],'SHA256':v['sha256']}for n,v in payload['files'].items()if n.startswith(prefix)and n not in new['files']}
    release=copy.deepcopy(old)
    global_path='iis/Global.asax';assert global_path not in old['controllerFiles']
    global_source=A/'deploy/iis_canonical_home/Global.asax'
    assert sha(global_source)=='694ef766a4c998e750142d8687f36473fcb45557529d5865102de3d1dcac041b'
    assert read(W/'canonical-home-compile-r3/result.json')['actualASPNetSitePrecompilationPassed']
    bodies[global_path]=global_source.read_bytes();release['controllerFiles'][global_path]=sha(global_source)
    updater='tools/original_public_test_update.py';assert sha(M)==old['controllerFiles'][updater]
    bodies[updater]=M.read_bytes()
    bodies['payload-manifest.json']=enc(new)
    release.update(payloadManifestSHA256=digest(bodies['payload-manifest.json']),
        publicTestRevision='20261031-R19-workplace-and-canonical-root',
        workplaceViewportRevision='container-resize-statistics-grid-table-header-v1',
        canonicalHomeRootRevision='exact-https-project-root-301-v1',publicAccepted=False)
    bodies['release-manifest.json']=enc(release)
    plan=read(PRE/'delivery/bundle/update-manifest.json')
    plan.update(updateId='20261031-R19-workplace-and-canonical-root-from-R18',
        acceptedOldReleases={OLD:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
        basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],
        newReleaseSHA256=digest(bodies['release-manifest.json']),
        oldPayloadFiles={n:payload['files'][n]for n in bodies if n in payload['files']},
        legacyEntrySHA256={},removedFrontendFiles=removed,
        files={n:{'bytes':len(b),'SHA256':digest(b)}for n,b in bodies.items()})
    assert len(bodies)<=1000 and sum(map(len,bodies.values()))<=32*1024**2
    bundle=D/'bundle';delivery=D/'delivery'
    for n,b in bodies.items():put(bundle/'payload'/n,b)
    put(bundle/'update-manifest.json',enc(plan));pin=sha(bundle/'update-manifest.json')
    deny=b'<?xml version="1.0" encoding="utf-8"?><configuration><system.webServer><security><authorization><clear/><add accessType="Deny" users="*"/></authorization></security></system.webServer></configuration>\r\n'
    put(delivery/'web.config',deny)
    archive=delivery/'Zhumadian_Workplace_20261031_R19.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
        z.writestr('update-manifest.json',enc(plan));z.writestr('web.config',deny)
        for n,b in bodies.items():z.writestr('payload/'+n,b)
    wrapper=(V/'workplace_r19_transport.py.in').read_text(encoding='utf-8')
    for token,value in [('__ARCHIVE_SHA__',sha(archive)),('__MANIFEST_SHA__',pin),('__OLD__',OLD),('__NEW__',plan['newReleaseSHA256'])]:wrapper=wrapper.replace(token,value)
    ast.parse(wrapper);put(delivery/'deploy_workplace_r19.py',wrapper.encode())
    for label,arg in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:
        put(delivery/(label+'_Workplace_R19.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_workplace_r19.py" '+arg+'\r\n').encode())
    spec=importlib.util.spec_from_file_location('retained_transaction_r19',M);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    old_security=A/'Packages/candidates/Confirmed_Operations_Result_20261029_Preview/compiled-security'
    baseline={}
    for n in set(bodies)|set(removed):
        if n in ('release-manifest.json','payload-manifest.json'):baseline[n]=(before/n).read_bytes()
        elif n==updater:baseline[n]=M.read_bytes()
        elif n.startswith(prefix):
            p=before/n
            if p.exists():baseline[n]=p.read_bytes()
            elif n in payload['files']:baseline[n]=(old_security/n.removeprefix(prefix)).read_bytes()
    changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(b)}for n,b in bodies.items()}
    changes.update({n:{'before':row['SHA256'],'after':None}for n,row in removed.items()})
    tests=[]
    for fault in [False,True]:
        case=W/('r19-fourth-write'if fault else'r19-normal-restore');app=case/'Application';assert not case.exists()
        for n,b in baseline.items():put(app/n,b)
        m.backup_code(app,case/'backup',changes);count=[0];caught=False
        def after(name):
            count[0]+=1
            if fault and count[0]==4:raise RuntimeError('OWN_R19_FOURTH_WRITE')
        try:m.replace_code(app,bundle,changes,after_each=after)
        except RuntimeError as error:assert fault and str(error)=='OWN_R19_FOURTH_WRITE';caught=True
        assert caught==fault
        m.restore_code(app,case/'backup',changes)
        assert all((app/n).read_bytes()==b for n,b in baseline.items())
        assert all(not(app/n).exists()for n in changes if n not in baseline)
        tests.append({'fourthWriteFault':fault,'allOldBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)})
    guard=next(n for n in ast.parse(wrapper).body if isinstance(n,ast.FunctionDef)and n.name=='recovery_guard')
    g={'need':lambda v,t:None if v else(_ for _ in()).throw(ValueError(t)),'Path':Path,'APP':Path('C:/inetpub/wwwroot/Zhumadian/Application'),'OLD':OLD,'NEW':plan['newReleaseSHA256'],'UPDATE':plan['updateId']}
    exec(compile(ast.Module(body=[guard],type_ignores=[]),'generated-guard','exec'),g)
    good={'updateId':plan['updateId'],'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],'attempt':'C:/inetpub/wwwroot/Zhumadian/Application/UserData/OriginalPublicUpdates/own'}
    g['recovery_guard'](good)
    for k,v in [('updateId','other'),('oldReleaseSHA256','0'*64),('newReleaseSHA256','1'*64),('attempt','C:/other/own')]:
        bad=dict(good);bad[k]=v
        try:g['recovery_guard'](bad)
        except ValueError:pass
        else:raise AssertionError('UNRELATED_RECOVERY_ACCEPTED')
    put(D/'transaction-verification.json',enc({'actualRetainedUpdater':True,'scenarios':tests,'generatedRecoveryOwnershipCases':5,'realRuntimeStartedOrStopped':False}))
    listed={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(delivery.iterdir())if p.is_file()}
    manifest={'revision':'R19-workplace-and-canonical-root','targetFTP':'/Zhumadian/Zhumadian_Workplace_20261031_R19/',
        'files':listed,'payloadTransportFiles':len(listed),'payloadTransportBytes':sum(x['bytes']for x in listed.values()),
        'oldReleaseSHA256':OLD,'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':pin,
        'replacementPaths':len(bodies),'obsoleteFrontendPaths':len(removed),'totalInstallPaths':len(changes),
        'containsCompiledFrontendIISSourceAndInternalPaths':True,'containsCredentialsBusinessRowsOrRawLogs':False,
        'allExistingBackendAuthIISMappingAndControllersUnchanged':True,'addsOnlyIISGlobalAsaxController':True}
    put(D/'delivery-manifest.json',enc(manifest));put(delivery/'delivery-manifest.json',enc(manifest))
    scope={'at':datetime.datetime.now().astimezone().isoformat(),'manifestSHA256':sha(D/'delivery-manifest.json'),
        'transportFilesIncludingManifest':len(listed)+1,'transportBytesIncludingManifest':manifest['payloadTransportBytes']+(D/'delivery-manifest.json').stat().st_size,
        'replacementPaths':len(bodies),'obsoleteFrontendPaths':len(removed),'totalInstallPaths':len(changes),
        'sourceAndComponentAndFullCompiledGraphAndTransactionsVerified':True,'publicDeployed':False,'approvalGranted':False}
    put(D/'preparation-result.json',enc(scope));print(json.dumps(scope))
if __name__=='__main__':main()
