from pathlib import Path
import datetime,gzip,hashlib,http.client,io,json,ssl,time
V=Path(__file__).resolve().parent;host='www.joinlinksmart.com'
path='/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js'
client=http.client.HTTPSConnection(host,timeout=12,context=ssl.create_default_context());start=time.monotonic()
report={'at':datetime.datetime.now().astimezone().isoformat(),'host':host,'path':path,'anonymousStaticGETOnly':True,'TLSVerificationEnabled':True,'requestAcceptEncoding':'gzip','accountSessionCookiesCredentialsOrBusinessRowsRead':False,'exactDeployedReleaseNotEstablished':True}
try:
    client.request('GET',path,headers={'Accept-Encoding':'gzip','Connection':'close'})
    response=client.getresponse();body=response.read(4*1024**2+1);assert len(body)<=4*1024**2
    headers={k.lower():v for k,v in response.getheaders()}
    if headers.get('content-encoding')=='gzip':
        with gzip.GzipFile(fileobj=io.BytesIO(body))as stream:decoded=stream.read(4*1024**2+1)
    else:decoded=body
    assert len(decoded)<=4*1024**2
    report.update(status=response.status,wireBytes=len(body),decodedBytes=len(decoded),decodedSHA256=hashlib.sha256(decoded).hexdigest(),
      contentEncoding=headers.get('content-encoding'),cacheControl=headers.get('cache-control'),vary=headers.get('vary'),
      decodedMatchesKnownUnchangedSecurityBundle=hashlib.sha256(decoded).hexdigest()=='3fda69730a678c07a2c83117eae03796f9fd3ef5d34a5928cc578a8c957806df')
except Exception as e:report.update(requestFailed=True,exceptionType=type(e).__name__)
finally:client.close()
report['elapsedSeconds']=round(time.monotonic()-start,3)
(V/'public-static-get-r307.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
