"""Anonymous HTTPS/read-only discovery checks after an approved successful R51 operation."""
from pathlib import Path
import datetime,gzip,hashlib,json,re,sys,urllib.error,urllib.request
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_home_same_window_r51_20261112'
def main():
 assert len(sys.argv)==2 and sys.argv[1].isdigit();seq=int(sys.argv[1]);target=D/('external-https-r2427-'+str(seq)+'.json');assert not target.exists()
 rows=[];checks=[]
 def get(label,path,encoding='identity',local=False):
  url=('http://127.0.0.1:18767'+path)if local else('https://www.joinlinksmart.com'+path)
  headers={'Accept-Encoding':encoding,'Cache-Control':'no-cache'}
  if local:headers['Origin']='https://www.joinlinksmart.com'
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=20)as f:
    raw=f.read(4*1024**2+1);assert len(raw)<=4*1024**2;status=f.status;meta=dict(f.getheaders())
   row={'label':label,'HTTP':status,'bytes':len(raw)}
   if not local:row['sha256']=hashlib.sha256(raw).hexdigest()
   rows.append(row);return status,meta,raw
  except urllib.error.HTTPError as e:rows.append({'label':label,'HTTP':e.code});return e.code,{},b''
  except urllib.error.URLError as e:rows.append({'label':label,'errorType':type(e.reason).__name__});return None,{},b''
 def check(ok,name):
  if not ok:raise AssertionError(name)
  checks.append(name)
 failed=None
 try:
  code,headers,html=get('publicRoot','/zhumadian/');check(code==200,'public-root-HTTPS-200')
  entry='/zhumadian/branding-20261025/assets/js/index-BuFDAtvn.js';home='/zhumadian/branding-20261025/assets/js/index-ChrBvWBP.js'
  check(entry.encode()in html and b'index-BYnEbdB9.js'not in html,'public-html-references-R51-entry-not-R50-entry')
  code,_,body=get('R51Entry',entry);check(code==200 and b'index-ChrBvWBP.js'in body and b'index-w-VlSjlt.js'not in body,'public-entry-references-new-home')
  code,headers,body=get('R51Home',home);check(code==200 and len(body)==7834 and hashlib.sha256(body).hexdigest()=='c8c88dbff5acbed1739c94416fc10275dedb725fceab8709f3442a9afb0ae83c','public-served-home-matches-actual-original-nginx-proof')
  check(re.search(rb'\.push\("/sceneViewer"\)',body)is not None and b'window.open("/zhumadian/sceneViewer"'not in body and b'127.0.0.1:8767'not in body,'public-home-same-window-router-preserved')
  code,headers,zipped=get('R51HomeGzip',home,'gzip');check(code==200 and headers.get('Content-Encoding')=='gzip'and gzip.decompress(zipped)==body,'public-gzip-decodes-identically')
  check('immutable'in headers.get('Cache-Control','')and 'Accept-Encoding'in headers.get('Vary',''),'public-versioned-home-cache-and-vary')
  code,_,spa=get('homeRoute','/zhumadian/home');check(code==200 and spa==html,'public-home-route-current-HTML')
  code,_,spa=get('sceneViewerRoute','/zhumadian/sceneViewer');check(code==200 and spa==html,'public-scene-viewer-route-current-HTML')
  check(get('retiredR50Home','/zhumadian/branding-20261025/assets/js/index-w-VlSjlt.js')[0]==404,'public-retired-R50-home-404')
  code,_,raw=get('sceneHTML','/zhumadian/scene/index.html');check(code==200 and hashlib.sha256(raw).hexdigest()=='370aa6ce47b67b3919478af86046de49f2bce7d4043cf641da0d7921b23760ec','public-original-scene-HTML-kept')
  code,_,raw=get('originalLoginConfig','/zhumadian/api/jnpf/oauth/getLoginConfig');check(code==200 and json.loads(raw).get('code')==200,'public-original-login-configuration-available')
  code,_,raw=get('local250Discovery','/xnby-gis/v1/discovery',local=True);value=json.loads(raw)if code==200 else{}
  check(code==200 and(value.get('ready')is True or value.get('phase')=='ready'),'250-current-GIS-discovery-ready')
 except BaseException as e:failed={'type':type(e).__name__,'check':str(e)[:160]}
 result={'at':datetime.datetime.now().astimezone().isoformat(),'passed':failed is None,'failure':failed,'checks':checks,'observations':rows,'readOnly':True,'actualNormalLoginBrowserGISRenderingAnd252Accepted':False,'credentialsCookiesOrDiscoveryIdentifiersReadBack':False,'scope':'fixed R51 first external acceptance; user scene acceptance remains pending'}
 with target.open('x',encoding='utf8')as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result));raise SystemExit(0 if failed is None else 1)
if __name__=='__main__':main()
