"""Read the fixed R16 asset set over TLS, or prove expected responses against local parity first."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,datetime,hashlib,importlib.util,json,sys,time,urllib.error,urllib.parse,urllib.request
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';ROOT=R/'work/public_test_update_20261029_r16';C=R/'Application/Packages/candidates/Confirmed_Operations_Result_20261029_Preview';Q=Path('D:/Zqa20261025/Application');NEW='0c588bf53e265e81f18048ec89b044edb9c1f727845b2481be300283b085acab';PLAN='233099c3effca0c54a1caaf774c5f368a7510cdb9949de758e9babcbedfd1e71';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def load(p,name):s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);parser.add_argument('--local-parity',action='store_true');args=parser.parse_args();out=args.report;assert not out.exists();bundle=ROOT/'from-r15/bundle';assert sha((bundle/'update-manifest.json').read_bytes())==PLAN;plan=read(bundle/'update-manifest.json');release=read(bundle/'payload/release-manifest.json');payload=read(bundle/'payload/payload-manifest.json');assert sha((bundle/'payload/release-manifest.json').read_bytes())==plan['newReleaseSHA256']==NEW and sha((bundle/'payload/payload-manifest.json').read_bytes())==release['payloadManifestSHA256'];assert sha((C/'manifest.json').read_bytes())=='161a11c06e34390d2b29580b520a586889856076f2757da353e8716019e19bad'
 for name in ['original_project_branding.py','original_header_branding.py']:assert sha((Q/'tools'/name).read_bytes())==release['controllerFiles']['tools/'+name]
 branding=load(Q/'tools/original_project_branding.py','r16_pinned_project_branding');header=load(Q/'tools/original_header_branding.py','r16_pinned_exact_header_alias');icon=Path(header.checked_icon(Q/'deploy/branding/zhumadian-emergency.svg')).read_bytes();assert sha(icon)==header.ICON_SHA256;pairs=[];decoder=json.JSONDecoder()
 for line in branding.static_directives(branding.PROJECT_NAME):
  if line.startswith('sub_filter '):old,end=decoder.raw_decode(line[len('sub_filter '):]);new,_=decoder.raw_decode(line[len('sub_filter '):][end:].lstrip());pairs.append((old.encode(),new.encode()))
 tasks=[]
 def route(name):
  kind,rel=name.split('/',2)[1:];assert '..' not in Path(rel).parts and '\\' not in rel and ':' not in rel;mount={'security_pc':'/zhumadian/','emergency_pc':'/zhumadian/emergency/'}[kind];return mount+(branding.ASSET_VERSION+'/' if rel.startswith('assets/') else '')+rel
 for kind,count in [('security_pc',835),('emergency_pc',204)]:
  entries={n:v for n,v in payload['files'].items() if n.startswith('frontend/'+kind+'/')};assert len(entries)==count
  for name,row in entries.items():
   raw=(Q/name).read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['bytes'];expected=raw
   if Path(name).suffix in ('.js','.json','.html'):
    for old,new in pairs:expected=expected.replace(old,new)
   if name=='frontend/security_pc/assets/png/logo-CQaY_L7K.png':assert '/zhumadian/'+name.split('/',2)[2]==header.HEADER_PATH;expected=icon
   tasks.append((name,route(name),200,expected))
 for name in plan['removedFrontendFiles']:tasks.append((name,route(name),404,None))
 assert len(tasks)==1108;origin='http://127.0.0.1:18891' if args.local_parity else 'https://www.joinlinksmart.com'
 def fetch(item):
  name,path,want,expected=item;url=origin+urllib.parse.quote(path,safe='/');request=urllib.request.Request(url,headers={'Accept-Encoding':'identity','User-Agent':'Zhumadian-R16-read-only-static-verification'});opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  try:
   try:
    with opener.open(request,timeout=15) as response:
     final=urllib.parse.urlsplit(response.url);assert final.netloc==urllib.parse.urlsplit(origin).netloc and final.scheme==urllib.parse.urlsplit(origin).scheme,'UNEXPECTED_REDIRECT';status=response.status;raw=response.read(16*1024**2+1)
   except urllib.error.HTTPError as error:status=error.code;raw=error.read(1024)
   assert len(raw)<=16*1024**2;return {'path':name,'HTTPPath':path,'status':status,'expectedStatus':want,'bytes':len(raw),'expectedSHA256':sha(expected) if expected is not None else None,'actualSHA256':sha(raw) if status==200 else None,'matches':status==want and (expected is None or raw==expected)}
  except Exception as error:return {'path':name,'HTTPPath':path,'matches':False,'errorType':type(error).__name__}
 start=time.monotonic();rows=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(fetch,t) for t in tasks]):rows.append(f.result())
 failures=[row for row in rows if not row['matches']];result={'at':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':sha(Path(__file__).read_bytes()),'baseURL':origin,'mode':'local-parity' if args.local_parity else 'public-HTTPS','expectedPublicReleaseSHA256':NEW,'activeSecurityFiles':835,'activeEmergencyFiles':204,'obsoletePaths':69,'requests':len(rows),'matched':len(rows)-len(failures),'failures':failures,'results':sorted(rows,key=lambda r:r['path']),'durationSeconds':time.monotonic()-start,'existingProjectNameAndExactHeaderAliasesApplied':True,'TLSVerificationDisabled':False,'publicHTTPSAssetVerificationPassed':not args.local_parity and not failures,'publicReleaseMetadataOrAccountBusinessAcceptanceProven':False,'authenticationOrBusinessMethodsUsed':False,'runtimeChanged':False,'fullCloneReady':False};out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='results'}));assert not failures
if __name__=='__main__':main()
