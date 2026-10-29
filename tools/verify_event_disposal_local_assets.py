"""Read all current PC assets and removed old paths through the actual local gateway."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse,datetime,hashlib,importlib.util,json,time,urllib.error,urllib.parse,urllib.request,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');B=R/'work/event_disposal_update_20261029';NEW='9fbc1db40a205414f0788c21d109ba966196ad178c04bb60195f46f99a0631b3';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);report=parser.parse_args().report;assert not report.exists();plan=read(B/'update-manifest.json');release=read(Q/'release-manifest.json');assert sha((Q/'release-manifest.json').read_bytes())==plan['newReleaseSHA256']==NEW and sha((Q/'payload-manifest.json').read_bytes())==release['payloadManifestSHA256'];payload=read(Q/'payload-manifest.json')
 spec=importlib.util.spec_from_file_location('event_owned_project_branding',Q/'tools/original_project_branding.py');branding=importlib.util.module_from_spec(spec);spec.loader.exec_module(branding);pairs=[];decoder=json.JSONDecoder()
 for line in branding.static_directives(branding.PROJECT_NAME):
  if line.startswith('sub_filter '):old,end=decoder.raw_decode(line[len('sub_filter '):]);new,_=decoder.raw_decode(line[len('sub_filter '):][end:].lstrip());pairs.append((old.encode(),new.encode()))
 from original_confirmed_operation_compat import NOTICE
 headerPath=Q/'tools/original_header_branding.py';assert sha(headerPath.read_bytes())==release['controllerFiles']['tools/original_header_branding.py'];headerSpec=importlib.util.spec_from_file_location('exact_owned_header_alias',headerPath);header=importlib.util.module_from_spec(headerSpec);headerSpec.loader.exec_module(header);iconPath=Path(header.checked_icon(Q/'deploy/branding/zhumadian-emergency.svg'));icon=iconPath.read_bytes();assert sha(icon)==header.ICON_SHA256
 from run_original_inventory_ownership_probe import state
 config=(Path(state()['run'])/'gateway/nginx.conf').read_text(encoding='utf8');exact='location = '+header.HEADER_PATH+' {\n  alias \"'+iconPath.as_posix()+'\";';assert config.count(exact)==1,'ACTUAL_EXACT_HEADER_ALIAS_REQUIRED'
 tasks=[];messageChunks={};counts={};eventChunks=[]
 from original_event_operations_frontend_compat import NOTICE as EVENT_NOTICE
 def route(name):
  kind,rel=name.split('/',2)[1:];mount={'security_pc':'/zhumadian/','emergency_pc':'/zhumadian/emergency/'}[kind];assert '..' not in Path(rel).parts and '\\' not in rel and ':' not in rel;return mount+(branding.ASSET_VERSION+'/' if rel.startswith('assets/') else '')+rel
 for kind,count in [('security_pc',835),('emergency_pc',204)]:
  active={n:v for n,v in payload['files'].items() if n.startswith('frontend/'+kind+'/')};assert len(active)==count;chunks=[]
  for name,row in active.items():
   raw=(Q/name).read_bytes();assert sha(raw)==row['sha256'] and len(raw)==row['bytes'];expected=raw
   if name.endswith('.js'):
    assert b'ownConfirmedFixture' not in raw and b'OWN_SYNTHETIC_ROW' not in raw,'SYNTHETIC_FIXTURE_IN_PRODUCTION'
    if NOTICE.encode() in raw:chunks.append({'path':name,'occurrences':raw.count(NOTICE.encode())})
    if EVENT_NOTICE.encode() in raw:eventChunks.append({'path':name,'occurrences':raw.count(EVENT_NOTICE.encode())})
   if Path(name).suffix in ('.js','.json','.html'):
    for old,new in pairs:expected=expected.replace(old,new)
   if name=='frontend/security_pc/assets/png/logo-CQaY_L7K.png':assert '/zhumadian/'+name.split('/',2)[2]==header.HEADER_PATH;expected=icon
   tasks.append((name,route(name),200,expected))
  assert len(chunks)==1 and chunks[0]['occurrences']==1;messageChunks[kind]=chunks;counts[kind]=count
 assert len(eventChunks)==3 and sum(v['occurrences'] for v in eventChunks)==4
 for name in plan['removedFrontendFiles']:assert not (Q/name).exists();tasks.append((name,route(name),404,None))
 def fetch(item):
  name,path,want,expected=item;request=urllib.request.Request('http://127.0.0.1:18891'+urllib.parse.quote(path,safe='/'),headers={'Accept-Encoding':'identity','User-Agent':'Zhumadian-event-disposal-readonly-static-check'});opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  try:
   try:
    with opener.open(request,timeout=12) as response:status=response.status;raw=response.read(16*1024**2+1)
   except urllib.error.HTTPError as e:status=e.code;raw=e.read(1024)
   return {'path':name,'HTTPPath':path,'status':status,'expectedStatus':want,'bytes':len(raw),'matches':status==want and (expected is None or raw==expected),'actualSHA256':sha(raw) if status==200 else None,'expectedSHA256':sha(expected) if expected is not None else None}
  except Exception as e:return {'path':name,'matches':False,'errorType':type(e).__name__}
 start=time.monotonic();rows=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(fetch,t) for t in tasks]):rows.append(f.result())
 failures=[x for x in rows if not x['matches']];result={'at':datetime.datetime.now().astimezone().isoformat(),'releaseSHA256':NEW,'activeAssets':counts,'obsoleteAssets':len(plan['removedFrontendFiles']),'requests':len(rows),'matched':len(rows)-len(failures),'results':sorted(rows,key=lambda x:x['path']),'failures':failures,'confirmationMessageChunks':messageChunks,'eventOperationMessageChunks':eventChunks,'brandingRulesAppliedToExpectedText':True,'existingExactHeaderAliasMatchedPinnedIcon':True,'fixtureMarkersAbsentInProduction':True,'durationSeconds':time.monotonic()-start,'authenticationOrBusinessAPIsUsed':False,'actualLoggedInPageOrRolesAccepted':False,'publicChanged':False,'fullCloneReady':False};report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='results'}));assert not failures
if __name__=='__main__':main()
