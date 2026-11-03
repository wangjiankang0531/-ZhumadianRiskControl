"""Read public HTML and static-resource timings only; no login, cookies, tokens or business API calls."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
import datetime,gzip,http.client,json,ssl,time
HOST='www.joinlinksmart.com';ROOT='https://'+HOST
OUT=Path(__file__).resolve().parent/'public-initial-performance-r228'
OUT.mkdir(exist_ok=False)
context=ssl.create_default_context()
def get(path,encoding='gzip',etag=None):
    assert path.startswith('/zhumadian/') and '/api/'not in path
    conn=http.client.HTTPSConnection(HOST,timeout=25,context=context)
    start=time.perf_counter();conn.connect();connected=time.perf_counter()
    headers={'Accept-Encoding':encoding,'User-Agent':'XNBY-Static-Performance-Probe/1.0','Connection':'close'}
    if etag:headers['If-None-Match']=etag
    try:
        conn.request('GET',path,headers=headers);sent=time.perf_counter();r=conn.getresponse();first=time.perf_counter()
        raw=r.read(32*1024*1024+1);end=time.perf_counter();assert len(raw)<=32*1024*1024,'BOUNDED_PUBLIC_STATIC_BODY_REQUIRED'
        selected={k:r.getheader(k)for k in ['Content-Type','Content-Length','Content-Encoding','Cache-Control','ETag','Last-Modified','Vary','Server']}
        row={'path':path,'requestEncoding':encoding,'conditionalRequest':bool(etag),'status':r.status,
             'connectMs':round((connected-start)*1000,2),'ttfbAfterSendMs':round((first-sent)*1000,2),
             'bodyMs':round((end-first)*1000,2),'totalMs':round((end-start)*1000,2),'wireBodyBytes':len(raw),'headers':selected}
        body=gzip.decompress(raw)if selected['Content-Encoding']=='gzip'else raw
        row['decodedBytes']=len(body)
        return row,body
    finally:conn.close()
class Links(HTMLParser):
    def __init__(self):super().__init__();self.assets=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='script'and a.get('src'):self.assets.append(('script',a['src']))
        if tag=='link'and a.get('href')and a.get('rel')in ['stylesheet','modulepreload']:self.assets.append((a['rel'],a['href']))
pages=['/zhumadian/','/zhumadian/home','/zhumadian/emergency/','/zhumadian/emergency/home/index']
with ThreadPoolExecutor(max_workers=4)as pool:initial=list(pool.map(get,pages))
rows=[];assets={}
for path,(row,body)in zip(pages,initial):
    rows.append(row)
    if row['status']==200 and'html'in(row['headers']['Content-Type']or''):
        parser=Links();parser.feed(body.decode('utf-8'))
        for kind,href in parser.assets[:16]:
            u=urlsplit(urljoin(ROOT+path,href))
            if u.hostname==HOST and u.path.startswith('/zhumadian/')and'/api/'not in u.path:assets[u.path]=kind
with ThreadPoolExecutor(max_workers=4)as pool:downloads=list(pool.map(get,assets))
for path,(row,body)in zip(assets,downloads):row['kind']=assets[path];rows.append(row)
largest=sorted([x for x in rows if x.get('kind')=='script'and x['status']==200],key=lambda x:x['decodedBytes'],reverse=True)[:2]
for row in largest:
    identity,_=get(row['path'],'identity');identity['comparison']='identity';rows.append(identity)
    if row['headers']['ETag']:
        conditional,_=get(row['path'],'gzip',row['headers']['ETag']);conditional['comparison']='conditional-etag';rows.append(conditional)
proof={'at':datetime.datetime.now().astimezone().isoformat(),'scope':'public-unauthenticated-static-resources-only',
       'cookiesCredentialsSessionsOrBusinessAPIsAccessed':False,'desktopOrServerConfigurationChanged':False,
       'actualAuthenticatedHomeOrModuleRenderTimeMeasured':False,'rows':rows}
(OUT/'result.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'publicHTMLAndStaticRequests':len(rows),'rows':[{k:x.get(k)for k in ['path','kind','status','wireBodyBytes','decodedBytes','totalMs','comparison','headers']}for x in rows]},ensure_ascii=True))
