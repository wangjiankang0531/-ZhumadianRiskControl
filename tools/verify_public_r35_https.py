"""Anonymous deployed byte verification against exact retained gateway transforms, no login/rows."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,http.client,importlib.util,json,queue,re,ssl,threading,time,urllib.parse
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_personal_workflow_r35_20261103';W=R/'work/user_feedback_20261031';S=W/'r35-personal-workflow-candidate-r1';BASE=W/'r24-unified-candidate-r1'
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest()
assert digest((D/'delivery-manifest.json').read_bytes())=='ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3'
assert read(D/'server-deployment-summary.json')['passed']
source=S/'bundle/payload';assert digest((source/'release-manifest.json').read_bytes())=='ccede060e9c329d44e65aef3200d86f8666c73d071d743cc1535031ab15d0ca4';release=read(source/'release-manifest.json');payload=read(source/'payload-manifest.json');resolution=read(R/'work/r23pv-r1/dependency-resolution.json')
def retained(name):
    row=resolution['controllers'][name];p=Path(row['source']);assert digest(p.read_bytes())==row['sha256']==release['controllerFiles'][name]
    spec=importlib.util.spec_from_file_location('retained_'+p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
branding=retained('tools/original_project_branding.py');header=retained('tools/original_header_branding.py')
decoder=json.JSONDecoder();pairs=[]
for line in branding.static_directives('驻马店重大风险防控'):
    if not line.startswith('sub_filter '):continue
    text=line[len('sub_filter '):];old,end=decoder.raw_decode(text);text=text[end:].lstrip();new,end=decoder.raw_decode(text);assert text[end:]==';';pairs.append((old.encode(),new.encode()))
lookup={a.lower():b for a,b in pairs};pattern=re.compile(b'|'.join(re.escape(a)for a,_ in pairs),re.I)
icon_name='deploy/branding/zhumadian-emergency.svg';ip=resolution['programs'][icon_name];icon=Path(ip['source']).read_bytes();assert digest(icon)==ip['sha256']==payload['files'][icon_name]['sha256']==header.ICON_SHA256
expected={};declared={};changed={}
for name,pin in payload['files'].items():
    if name.startswith('frontend/security_pc/'):url='/zhumadian/'+name.removeprefix('frontend/security_pc/')
    elif name.startswith('frontend/emergency_pc/'):url='/zhumadian/emergency/'+name.removeprefix('frontend/emergency_pc/')
    else:continue
    if name.startswith('frontend/security_pc/'):p=W/'avatar-full-r157/security_pc/build/dist'/name.removeprefix('frontend/security_pc/')
    else:p=W/'personal-workflow-routes-r195/dist'/name.removeprefix('frontend/emergency_pc/')
    raw=p.read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
    if url==header.HEADER_PATH:body=icon
    elif name.endswith(('.js','.html','.json')):body=pattern.sub(lambda m:lookup[m.group().lower()],raw)
    else:body=raw
    expected[url]=body;declared[url]=pin
    if body!=raw:changed[url]={'originalSHA256':pin['sha256'],'expectedRetainedGatewaySHA256':digest(body)}
assert len(expected)==1176
jobs=queue.Queue();results=[];failures=[];lock=threading.Lock();context=ssl.create_default_context();HOST='www.joinlinksmart.com'
for url,body in expected.items():jobs.put((url,body))
def worker(_):
    connection=None
    try:
        while True:
            try:url,wanted=jobs.get_nowait()
            except queue.Empty:break
            record=None
            for attempt in range(2):
                try:
                    if connection is None:connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
                    connection.request('GET',urllib.parse.quote(url,safe='/._-~')+'?r35verify=20261102',headers={'Accept-Encoding':'identity','Cache-Control':'no-cache','User-Agent':'Zhumadian-authorized-R35-static-verifier'})
                    response=connection.getresponse();body=response.read(len(wanted)+1024)
                    record={'path':url,'status':response.status,'bytes':len(body),'shaMatchesOriginal':digest(body)==declared[url]['sha256'],'exactExpectedRetainedGatewayBytes':body==wanted}
                    if response.will_close:connection.close();connection=None
                    break
                except Exception as e:
                    if connection:connection.close()
                    connection=None
                    if attempt:record={'path':url,'exceptionType':type(e).__name__}
            with lock:
                results.append(record)
                if record.get('status')!=200 or not record.get('exactExpectedRetainedGatewayBytes'):failures.append(record)
            jobs.task_done()
    finally:
        if connection:connection.close()
start=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(worker,range(4)))
special=[];connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
for path,status in [('/zhumadian',301),('/zhumadian/',200),('/zhumadian/home',200),('/zhumadian/emergency/',200),('/zhumadian/emergency/home',200),('/zhumadian/emergency/home/index',200),('/zhumadian/emergency/emergencyResources/materials',200),('/zhumadian/emergency/emergencyResources/firstAidTeams',200),('/zhumadian/emergency/dutyManage/dutyPersonnel',200),('/zhumadian/emergency/dutyManage/dutySchedule',200),('/zhumadian/emergency/dutyManage/dutyLog',200),('/zhumadian/api/jnpf/oauth/getLoginConfig',200)]:
    connection.request('GET',path,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});response=connection.getresponse();body=response.read(2*1024**2);record={'path':path,'status':response.status,'expectedStatus':status};assert response.status==status
    if path=='/zhumadian':record['location']=response.getheader('Location');assert record['location']in ['/zhumadian/','https://www.joinlinksmart.com/zhumadian/']
    if path.endswith('getLoginConfig'):record['businessCode']=json.loads(body)['code'];assert record['businessCode']==200
    if 'checkInventory'in path:
        data=json.loads(body);record.update(businessCode=data.get('code'),noData=data.get('data')is None);assert record['businessCode']==600 and record['noData']
    special.append(record)
    if response.will_close:connection.close();connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
versioned=set()
for url in ['/zhumadian/index.html','/zhumadian/emergency/index.html']:
    for asset in re.findall(rb'''(?:src|href)=["']([^"']+)["']''',expected[url]):
        value=asset.decode()
        if '/branding-20261025/assets/'in value:versioned.add(value)
branded=[]
for url in sorted(versioned):
    connection.request('GET',url,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});response=connection.getresponse();body=response.read();wanted=expected[url.replace('/branding-20261025/','/')];assert response.status==200 and body==wanted,'BRANDED_OR_WORKFLOW_ENTRY_DRIFT:'+url
    branded.append({'path':url,'status':response.status,'expectedSHA256':digest(wanted),'exactExpectedGatewayBytes':True})
connection.close()
assert{r['path']for r in results if not r.get('shaMatchesOriginal')}==set(changed),'UNEXPLAINED_RAW_DIFFERENCE'
proof={'schema':'xnby.r35.public-retained-gateway-https.v1','at':datetime.datetime.now().astimezone().isoformat(),'allPassed':not failures,'staticFiles':len(results),
    'unchangedWireFiles':sum(r.get('shaMatchesOriginal',False)for r in results),'exactRetainedGatewayDifferences':len(changed),'staticFileFailures':failures,
    'allWireDifferencesDerivedFromExactRetainedBrandingOrIconAlias':True,'retainedProjectBrandingSHA256':release['controllerFiles']['tools/original_project_branding.py'],
    'retainedHeaderBrandingSHA256':release['controllerFiles']['tools/original_header_branding.py'],'specialChecks':special,'brandedEntryAndWorkflowFacadeChecks':branded,
    'tlsDefaultCertificateVerificationEnabled':True,'elapsedSeconds':round(time.monotonic()-start,2),'actualAuthenticatedPublicBusinessFlowAccepted':False,
    'credentialsCookiesTokensAccountsSessionsBusinessRowsOrRawLogsRead':False,'publicApplicationCodeChangedByVerifier':False}
(D/'public-https-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(D/'public-static-file-verification.json').write_text(json.dumps(sorted(results,key=lambda r:r['path']),indent=2)+'\n',encoding='utf-8')
(D/'public-expected-gateway-differences.json').write_text(json.dumps(changed,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items()if k not in ['brandedEntryAndWorkflowFacadeChecks']},ensure_ascii=False));assert not failures,'PUBLIC_STATIC_BYTES_MISMATCH'
