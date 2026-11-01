"""Anonymous HTTPS byte verification of the fixed public frontend; no login or business reads."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,http.client,json,queue,ssl,threading,time,urllib.parse
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_r24_20261101';S=R/'work/user_feedback_20261031/r24-unified-candidate-r1'
read=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((D/'delivery-manifest.json').read_bytes())=='0a6d7682ba9d0b39611ad91ed1dea01c9eafd5c44d246d8873048a00260567e6'
stage=read(D/'server-deployment-summary.json');assert stage['passed']and stage['exitCode']==0
payload=read(S/'sparse-graceful-update-preparation-r1/bundle/payload/payload-manifest.json')
HOST='www.joinlinksmart.com';context=ssl.create_default_context();jobs=queue.Queue();results=[];failures=[];lock=threading.Lock()
for name,pin in payload['files'].items():
 if name.startswith('frontend/security_pc/'):path='/zhumadian/'+name.removeprefix('frontend/security_pc/')
 elif name.startswith('frontend/emergency_pc/'):path='/zhumadian/emergency/'+name.removeprefix('frontend/emergency_pc/')
 else:continue
 jobs.put((path,pin))
assert jobs.qsize()==1174
def worker():
 connection=None
 try:
  while True:
   try:path,pin=jobs.get_nowait()
   except queue.Empty:break
   record=None
   for attempt in range(2):
    try:
     if connection is None:connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
     connection.request('GET',urllib.parse.quote(path,safe='/._-~')+'?r24verify=20261101',headers={'Accept-Encoding':'identity','Cache-Control':'no-cache','User-Agent':'Zhumadian-approved-R24-static-verifier'})
     response=connection.getresponse();body=response.read(pin['bytes']+1024)
     record={'path':path,'status':response.status,'bytes':len(body),'expectedBytes':pin['bytes'],'shaMatches':sha(body)==pin['sha256']}
     if response.will_close:connection.close();connection=None
     break
    except Exception as e:
     if connection:connection.close()
     connection=None
     if attempt:record={'path':path,'exceptionType':type(e).__name__}
   with lock:
    results.append(record)
    if record.get('status')!=200 or not record.get('shaMatches')or record.get('bytes')!=pin['bytes']:failures.append(record)
   jobs.task_done()
 finally:
  if connection:connection.close()
start=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:list(pool.map(lambda _:worker(),range(4)))
special=[];connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
for path,expected in [('/zhumadian',301),('/zhumadian/',200),('/zhumadian/home',200),('/zhumadian/emergency/',200),('/zhumadian/api/jnpf/oauth/getLoginConfig',200),('/zhumadian/api/serv/checkInventory/page?current=1&size=1',200)]:
 connection.request('GET',path,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});response=connection.getresponse();body=response.read(2*1024**2)
 row={'path':path,'status':response.status,'expectedStatus':expected}
 if path=='/zhumadian':row['location']=response.getheader('Location');assert row['location']in ['/zhumadian/','https://www.joinlinksmart.com/zhumadian/']
 if path.endswith('getLoginConfig'):row['businessCode']=json.loads(body)['code'];assert row['businessCode']==200
 if 'checkInventory' in path:
  data=json.loads(body);row.update(businessCode=data.get('code'),noData=data.get('data')is None);assert row['businessCode']==600 and row['noData']
 assert response.status==expected
 special.append(row)
 if response.will_close:connection.close();connection=http.client.HTTPSConnection(HOST,context=context,timeout=25)
connection.close()
proof={'schema':'xnby.r24.public-anonymous-https.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'allPassed':not failures,'staticFiles':len(results),'staticBytesMatched':sum(x['bytes']for x in results if x.get('shaMatches')),
 'staticFileFailures':failures,'specialChecks':special,'tlsDefaultCertificateVerificationEnabled':True,
 'elapsedSeconds':round(time.monotonic()-start,2),'actualPublicLoginRoleBusinessWriteOrApprovalAccepted':False,
 'credentialsCookiesTokensAccountsSessionsBusinessRowsOrRawLogsRead':False}
(D/'public-https-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'public-static-file-verification.json').write_text(json.dumps(sorted(results,key=lambda x:x['path']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,ensure_ascii=False));assert not failures,'PUBLIC_STATIC_BYTES_MISMATCH'
