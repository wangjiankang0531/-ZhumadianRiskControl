from pathlib import Path
import ast,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent;S=R/'work/user_feedback_20261031/r37-static-performance-r1';D=R/'Document/Deployment/public_test_static_performance_r37_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
full=J(D/'full-program-preflight.json');tx=J(D/'composition-and-recovery.json');assert full['allPassed']and tx['passed']and len(tx['normalAndFaultRecoveryCases'])==8
transport=J(V/'static-transport-r230/verified-result.json');browser=J(V/'static-transport-r231/verified-result.json');assert transport['passed']and browser['passed'];assert J(V/'static-proxy-boundaries-r232/transport/receipt.json')['checks']==13
source=T/'original_public_test_update_r37_static_20261103.py';assert sha(source)==full['newUpdaterSHA256']==tx['newUpdaterSHA256']
delivery=D/'delivery';assert not delivery.exists();delivery.mkdir()
plan=J(S/'bundle/update-manifest.json');archive=delivery/'Zhumadian_Static_Performance_20261103_R37.zip';deny=b'<?xml version="1.0" encoding="utf-8"?><configuration><system.webServer><security><authorization><clear/><add accessType="Deny" users="*"/></authorization></security></system.webServer></configuration>\r\n'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED)as z:
 z.writestr('web.config',deny);z.writestr('update-manifest.json',(S/'bundle/update-manifest.json').read_bytes())
 for n,pin in plan['files'].items():
  raw=(S/'bundle/payload'/n).read_bytes();assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'];z.writestr('payload/'+n,raw)
wrapper=(R/'Document/Deployment/public_test_native_history_r36_20261103/delivery/deploy_native_history_r36.py').read_text(encoding='utf-8');tree=ast.parse(wrapper);constants={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
old=next(iter(plan['acceptedOldReleases']));oldUpdater=plan['acceptedOldReleases'][old]['controllerFiles']['tools/original_public_test_update.py']
values={'ARCHIVE_SHA':sha(archive),'MANIFEST_SHA':sha(S/'bundle/update-manifest.json'),'OLD':old,'NEW':plan['newReleaseSHA256'],'UPDATE':plan['updateId'],'UPDATER_SHA':sha(source),'OLD_UPDATER_SHA':oldUpdater};lines=wrapper.splitlines(keepends=True)
for k,v in values.items():n=constants[k];assert n.lineno==n.end_lineno;lines[n.lineno-1]=k+'='+repr(v)+'\n'
wrapper=''.join(lines).replace('Zhumadian_Native_History_20261103_R36.zip',archive.name).replace('r36_update_runtime.py','r37_update_runtime.py').replace('fixed_r36_updater','fixed_r37_updater').replace('FIXED_R36','FIXED_R37').replace('R36_','R37_').replace('EXACT_R35_BASE','EXACT_R36_BASE').replace('EXACT_R35_RUNTIME','EXACT_R36_RUNTIME')
expected={}
for role,path in [('security-js','/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js'),('emergency-js','/zhumadian/emergency/branding-20261025/assets/js/wf-index-DxxdT4hP.js'),('security-css','/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css'),('emergency-css','/zhumadian/emergency/branding-20261025/assets/css/index-D0NHlCez.css')]:
 row=next(x for x in J(V/'static-transport-r230/baseline/results.json')['cases']if x['name']==role);expected[path]={'decodedBytes':row['decodedBytes'],'decodedSHA256':row['decodedSHA256']}
probe='\nSTATIC_EXPECTED = '+repr(expected)+'\n'+r'''
def validate_static_response(path,encoding,status,headers,body):
    import gzip,io
    need(status==200 and len(body)<=4*1024*1024,'STATIC_HTTP_STATUS_OR_BOUND')
    need(headers.get('cache-control')=='public, max-age=31536000, immutable','STATIC_HASH_CACHE_POLICY')
    expected=STATIC_EXPECTED[path]
    if encoding=='gzip':
        need(headers.get('content-encoding')=='gzip' and 'accept-encoding' in [v.strip().lower()for v in headers.get('vary','').split(',')],'STATIC_GZIP_AND_VARY')
        with gzip.GzipFile(fileobj=io.BytesIO(body))as stream:decoded=stream.read(4*1024*1024+1)
    else:
        need(not headers.get('content-encoding'),'STATIC_EXPLICIT_ZERO_MUST_REMAIN_IDENTITY');decoded=body
    need(len(decoded)==expected['decodedBytes']and hashlib.sha256(decoded).hexdigest()==expected['decodedSHA256'],'STATIC_DECODED_CONTENT_IDENTITY')
    return {'status':status,'wireBytes':len(body),'decodedBytes':len(decoded),'gzip':encoding=='gzip','hashCacheVerified':True,'decodedContentMatched':True}

def verify_static_gateway_and_iis(m,root,checked):
    import http.client,socket,ssl
    # A new exact proxy pin is used only after apply_update has completed normally.
    changed=dict(checked);changed['iisProxySHA256']=m.R37_STATIC_CONTRACT['files']['iis/App_Code/XnbyReferenceProxy.cs']['sha256']
    ingress,address=m.ingress_preflight(APP,changed,{})
    def fetch(channel,path,accept):
        if channel=='gateway':c=http.client.HTTPConnection('127.0.0.1',18892,timeout=20)
        else:
            secure=ssl.create_default_context().wrap_socket(socket.create_connection((address,443),timeout=20),server_hostname='www.joinlinksmart.com')
            c=http.client.HTTPConnection('www.joinlinksmart.com',timeout=20);c.sock=secure
        try:
            c.request('GET',path,headers={'Host':'www.joinlinksmart.com','Accept-Encoding':accept,'Connection':'close'});r=c.getresponse();b=r.read(4*1024*1024+1)
            need(len(b)<=4*1024*1024,'STATIC_RESPONSE_BOUND')
            return r.status,{k.lower():v for k,v in r.getheaders()},b
        finally:c.close()
    rows=[]
    for channel in ['gateway','iis-tls']:
        for path in STATIC_EXPECTED:
            code,headers,body=fetch(channel,path,'gzip');r=validate_static_response(path,'gzip',code,headers,body);r.update(channel=channel,resource=path);rows.append(r)
        path=next(iter(STATIC_EXPECTED));code,headers,body=fetch(channel,path,'gzip;q=0, *;q=1');r=validate_static_response(path,'identity',code,headers,body);r.update(channel=channel,explicitGzipZero=True);rows.append(r)
        for path in ['/zhumadian/home','/zhumadian/emergency/home/index']:
            code,headers,body=fetch(channel,path,'identity');need(code==200 and 'no-store'in headers.get('cache-control',''),'HTML_ENTRY_MUST_NOT_BE_LONG_CACHED');rows.append({'channel':channel,'resource':path,'status':code,'htmlNoStoreVerified':True})
    result={'passed':True,'checks':rows,'realGatewayAndLocalIISTLS':True,'businessRecordsOrCredentialsRead':False,'publicExternalOrAuthenticatedTimingAccepted':False}
    m.write_json(root/'server-static-performance-result.json',result)
    print('R37_STATIC_GZIP_CACHE_HTML_AND_DECODED_BYTES_PASSED_GATEWAY_AND_IIS_TLS',flush=True)

'''
wrapper=wrapper.replace('def main():',probe+'def main():')
needle="    m.apply_update(APP,stage,MANIFEST_SHA)";assert wrapper.count(needle)==1
wrapper=wrapper.replace(needle,needle+"\n    verify_static_gateway_and_iis(m,root,checked)");ast.parse(wrapper)
put(delivery/'deploy_static_performance_r37.py',wrapper.replace('\r\n','\n').replace('\n','\r\n').encode());put(delivery/'r37_update_runtime.py',source.read_bytes());put(delivery/'web.config',deny)
for label,flag in [('Check_Only','--check-only'),('Deploy',''),('Recover_This','--recover-this-update')]:put(delivery/(label+'_Static_Performance_R37.cmd'),('@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_static_performance_r37.py" '+flag+'\r\n').encode('ascii'))
entries={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in delivery.iterdir()if p.is_file()}
maxpath=max(len(plan['targetApplication']+'/UserData/OriginalPublicUpdates/staging/'+'f'*32+'/payload/'+n)for n in plan['files']);assert maxpath<260
manifest={'revision':'R37-static-initial-load-performance','targetFTP':'/Zhumadian/Zhumadian_Static_Performance_20261103_R37/','targetApplication':plan['targetApplication'],'files':entries,'oldReleaseSHA256':old,'oldUpdaterSHA256':oldUpdater,'newReleaseSHA256':plan['newReleaseSHA256'],'newUpdaterSHA256':sha(source),'updateManifestSHA256':sha(S/'bundle/update-manifest.json'),'writes':6,'removedFiles':0,'newDeclaredControlFiles':22,'oldReadinessReports':11,'newReadinessReports':11,'fixedCompositionNegativeCases':31,'recoveryScenarios':8,'fullProgramFilesVerified':full['fullProgramFilesVerified'],'normalStopLaunchBackupReplaceRestoreAndRecoveryASTUnchanged':True,'applyUpdateOnlyAddsAccurateIISFileReceiptFlag':True,'actualNginxAspNetTransportCasesEachMode':18,'originalProxyTransportSecurityCasesPassed':13,'quarantined23GzipUnitCasesExecuted':False,'actualChromeAnonymousColdWarmBothPortalsPassed':True,'maximumExtractionPathCharacters':maxpath,'bothFrontendsBusinessJarsAuthHistoryDatabasePrivateConfigUploadAndIISMappingRetained':True,'onlyActualIISProxySourceAddedToPinnedControls':True,'publicDeployed':False,'actualServerIISPreflightAndExternalUserTimingPending':True,'newPublicGitIncluded':False,'fullCloneReady':False}
put(D/'delivery-manifest.json',enc(manifest));put(delivery/'delivery-manifest.json',enc(manifest))
proof={'prepared':True,'transportFiles':len(list(delivery.iterdir())),'transportBytes':sum(p.stat().st_size for p in delivery.iterdir()),'manifestSHA256':sha(D/'delivery-manifest.json'),'writes':6,'removals':0,'actualPublicDeployPassed':False}
put(D/'preparation-result.json',enc(proof));print(json.dumps(proof))
