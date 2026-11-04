"""External anonymous HTTPS static checks against exact R45 decoded content; no auth or business writes."""
from pathlib import Path
import datetime,gzip,hashlib,http.client,importlib.util,json,socket,ssl,time,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent
ROOT=V/'public-r45-static-r862'
WRAPPER=Path('D:/Project/Zhumadian/Application/tools/deploy_original_bootstrap_r45.py')
HOST='www.joinlinksmart.com';ADDRESS='101.201.65.94'

def main():
 assert not ROOT.exists();ROOT.mkdir()
 assert hashlib.sha256(WRAPPER.read_bytes()).hexdigest()=='6dbaaeb40efed99acc5e12d41b0728bc1bbf11ccf458b54813843aec663fcc9d'
 spec=importlib.util.spec_from_file_location('r45_static_contract_r862',WRAPPER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 rows=[]
 def fetch(path,accept):
  assert path.startswith('/zhumadian/')and '?'not in path
  start=time.perf_counter();tls=ssl.create_default_context().wrap_socket(socket.create_connection((ADDRESS,443),timeout=20),server_hostname=HOST)
  c=http.client.HTTPConnection(HOST,timeout=30);c.sock=tls
  try:
   c.request('GET',path,headers={'Host':HOST,'Accept-Encoding':accept,'Connection':'close','User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0.0.0 Safari/537.36'})
   r=c.getresponse();first=time.perf_counter()-start;raw=r.read(4*1024**2+1);assert len(raw)<=4*1024**2
   return r.status,{k.lower():v for k,v in r.getheaders()},raw,first,time.perf_counter()-start
  finally:c.close()
 try:
  for path in m.STATIC_EXPECTED:
   for accept,encoding in [('gzip','gzip'),('gzip;q=0, *;q=1','identity')]:
    status,headers,body,ttfb,elapsed=fetch(path,accept)
    item=m.validate_static_response(path,encoding,status,headers,body)
    item.update(path=path,ttfbSeconds=round(ttfb,4),totalSeconds=round(elapsed,4),headers={k:headers.get(k)for k in ['content-type','content-encoding','cache-control','etag','vary']})
    decoded=gzip.decompress(body)if encoding=='gzip'else body;item['decodedSHA256']=hashlib.sha256(decoded).hexdigest();rows.append(item)
    (ROOT/'measurements.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8');print(json.dumps(item),flush=True)
  for path in ['/zhumadian/home','/zhumadian/emergency/home/index']:
   status,headers,body,ttfb,elapsed=fetch(path,'identity');assert status==200 and 'no-store'in headers.get('cache-control','')
   if path=='/zhumadian/home':assert b'xnby-workplace-period-736f7b07dd2c.css'in body
   else:assert b'wf-index-C_ZP3Pto.js'in body
   item={'path':path,'status':status,'htmlNoStoreVerified':True,'currentR45ReferenceVerified':True,'wireBytes':len(body),'ttfbSeconds':round(ttfb,4),'totalSeconds':round(elapsed,4)};rows.append(item);print(json.dumps(item),flush=True)
  proof={'passed':True,'measuredAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,
   'actualExternalHTTPS':True,'certificateHostnameVerified':HOST,'connectionAddress':ADDRESS,'DNSBypassedButTLSNotBypassed':True,
   'onlyAnonymousStaticGETs':True,'cookieOrAuthorizationSent':False,'businessAPIsOrRowsRead':False,
   'authenticatedUserExperienceOrBrowserWarmCacheAcceptanceClaimed':False,'publicMutation':False}
  (ROOT/'verified-result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print('EXTERNAL_R45_STATIC_12_CHECKS_PASSED',flush=True)
 except BaseException as e:
  (ROOT/'failure.json').write_text(json.dumps({'type':type(e).__name__,'completedRequests':len(rows),'publicMutation':False})+'\n',encoding='utf8');raise
if __name__=='__main__':main()
