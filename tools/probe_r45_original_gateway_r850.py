"""Anonymous real-gateway static responses from the exact live owned R44 only."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from pathlib import Path
import hashlib,http.client,json,time,zlib
O=Path('D:/Project/Zhumadian/work/original-backend-full-r850')
def children_exited():return True # This helper creates no child process.
class Links(HTMLParser):
 def __init__(self):super().__init__();self.js=[];self.css=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='script'and a.get('src'):self.js.append(a['src'])
  if tag=='link'and a.get('rel')=='stylesheet'and a.get('href'):self.css.append(a['href'])
def run_probe(row,label,gateway_port,fixture_nonce):
 assert label in ['first-start','normal-restart']and row['ready']and row['gatewayPort']==gateway_port
 assert 1024<gateway_port<65536 and gateway_port not in [18891,8767]
 base='http://127.0.0.1:'+str(gateway_port);results=[]
 def get(path,encoding):
  u=urlsplit(urljoin(base,path));assert u.scheme=='http'and u.netloc=='127.0.0.1:'+str(gateway_port)and u.path.startswith('/zhumadian/')and not u.query
  start=time.perf_counter();client=http.client.HTTPConnection('127.0.0.1',gateway_port,timeout=20)
  try:
   client.request('GET',u.path,headers={'Accept-Encoding':encoding})
   response=client.getresponse();raw=response.read(8*1024**2+1);assert len(raw)<=8*1024**2
   assert response.status==200,'OWN_STATIC_STATUS_REQUIRED'
   headers={k.lower():response.getheader(k)for k in ['Content-Type','Content-Encoding','Cache-Control','Vary']}
  finally:client.close()
  if headers['content-encoding']=='gzip':
   decoder=zlib.decompressobj(16+zlib.MAX_WBITS);body=decoder.decompress(raw,16*1024**2+1)
   assert len(body)<=16*1024**2 and decoder.eof and not decoder.unconsumed_tail
  else:assert headers['content-encoding']in [None,'identity'];body=raw
  return body,{'path':u.path,'requestedEncoding':encoding,'wireBytes':len(raw),'decodedBytes':len(body),'decodedSHA256':hashlib.sha256(body).hexdigest(),'headers':headers,'elapsedSeconds':round(time.perf_counter()-start,4)}
 for entry in ['/zhumadian/home','/zhumadian/emergency/home/index']:
  body,html=get(entry,'gzip');assert 'no-store'in html['headers']['cache-control'];results.append(html)
  links=Links();links.feed(body.decode('utf8'))
  def local_asset(value):
   u=urlsplit(urljoin(base+entry,value));return u.scheme=='http'and u.netloc=='127.0.0.1:'+str(gateway_port)and '/assets/'in u.path and u.path.startswith('/zhumadian/')
  localJS=[x for x in links.js if local_asset(x)];localCSS=[x for x in links.css if local_asset(x)];assert localJS and localCSS
  for name in [localJS[0],localCSS[0]]:
   path=urljoin(base+entry,name);compressed,gzipRow=get(path,'gzip');identity,plainRow=get(path,'identity')
   assert compressed==identity and gzipRow['headers']['content-encoding']=='gzip'
   assert gzipRow['wireBytes']<plainRow['wireBytes']
   assert all(x in gzipRow['headers']['cache-control']for x in ['public','max-age=31536000','immutable'])
   assert 'accept-encoding'in gzipRow['headers']['vary'].lower()
   results.extend([gzipRow,plainRow])
 proof={'passed':True,'phase':label,'rows':results,'actualFullCandidateGatewayResponses':True,'decodedIdentityAndGzipBytesEqual':True,
 'hashedJSCSSImmutableAndHTMLNoStore':True,'noAuthCookiesOrBusinessRowsRequested':True,'actualIISOrHTTPSOrPublicAccepted':False,
 'actualBrowserColdWarmOrAuthenticatedModuleTimingsAccepted':False,'fullCloneReady':False}
 (O/(label+'-static-result.json')).write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');return proof
