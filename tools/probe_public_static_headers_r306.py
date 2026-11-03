from pathlib import Path
import datetime,http.client,json,ssl,time
HOST='www.joinlinksmart.com';V=Path(__file__).resolve().parent
paths=['/zhumadian/home','/zhumadian/branding-20261025/assets/js/index-DOC7mNwT.js','/zhumadian/branding-20261025/assets/css/index-ClWHaJx5.css']
rows=[]
for path in paths:
    client=http.client.HTTPSConnection(HOST,timeout=6,context=ssl.create_default_context());started=time.monotonic()
    try:
        client.request('HEAD',path,headers={'Accept-Encoding':'gzip','Connection':'close'})
        response=client.getresponse();h={k.lower():v for k,v in response.getheaders()}
        rows.append({'path':path,'status':response.status,'elapsedSeconds':round(time.monotonic()-started,3),
          'contentEncoding':h.get('content-encoding'),'cacheControl':h.get('cache-control'),
          'vary':h.get('vary'),'contentLength':h.get('content-length'),'redirectPresent':'location'in h})
    except Exception as e:rows.append({'path':path,'requestFailed':True,'exceptionType':type(e).__name__,'elapsedSeconds':round(time.monotonic()-started,3)})
    finally:client.close()
report={'at':datetime.datetime.now().astimezone().isoformat(),'host':HOST,'anonymousHEADOnly':True,
 'TLSVerificationEnabled':True,'accountSessionCookiesCredentialsOrBusinessResponsesRead':False,
 'exactDeployedReleaseIdentityNotEstablishedByThisProbe':True,'observations':rows}
(V/'public-static-headers-r306.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))
