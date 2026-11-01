"""Explain every wire-byte difference using only the exact retained gateway source; no acceptance exceptions."""
from pathlib import Path
import datetime,hashlib,http.client,importlib.util,json,re,ssl
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_r24_20261101';S=R/'work/user_feedback_20261031/r24-unified-candidate-r1'
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest()
source=S/'sparse-graceful-update-preparation-r1/bundle/payload';release=read(source/'release-manifest.json');payload=read(source/'payload-manifest.json')
raw_check=read(D/'public-https-verification.json');records=read(D/'public-static-file-verification.json')
assert len(records)==1174 and len(raw_check['staticFileFailures'])==13
resolution=read(R/'work/r23pv-r1/dependency-resolution.json')
def retained(name):
 row=resolution['controllers'][name];p=Path(row['source']);assert digest(p.read_bytes())==row['sha256']==release['controllerFiles'][name]
 spec=importlib.util.spec_from_file_location('retained_'+p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
branding=retained('tools/original_project_branding.py');header=retained('tools/original_header_branding.py')
decoder=json.JSONDecoder();pairs=[]
for line in branding.static_directives('驻马店重大风险防控'):
 if not line.startswith('sub_filter '):continue
 text=line[len('sub_filter '):];old,end=decoder.raw_decode(text);text=text[end:].lstrip();new,end=decoder.raw_decode(text)
 assert text[end:]==';';pairs.append((old.encode(),new.encode()))
lookup={a.lower():b for a,b in pairs};pattern=re.compile(b'|'.join(re.escape(a)for a,_ in pairs),re.I)
icon_name='deploy/branding/zhumadian-emergency.svg';icon_row=resolution['programs'][icon_name];icon=Path(icon_row['source']).read_bytes()
assert digest(icon)==icon_row['sha256']==payload['files'][icon_name]['sha256']==header.ICON_SHA256
def original(name):
 p=source/name
 if not p.exists():p=S/'payload'/name
 if not p.exists():p=Path(resolution['programs'][name]['source'])
 raw=p.read_bytes();assert digest(raw)==payload['files'][name]['sha256'];return raw
expected={};changed={}
for name,pin in payload['files'].items():
 if name.startswith('frontend/security_pc/'):url='/zhumadian/'+name.removeprefix('frontend/security_pc/')
 elif name.startswith('frontend/emergency_pc/'):url='/zhumadian/emergency/'+name.removeprefix('frontend/emergency_pc/')
 else:continue
 raw=original(name)
 if url==header.HEADER_PATH:value=icon
 elif name.endswith(('.js','.html','.json')):value=pattern.sub(lambda m:lookup[m.group().lower()],raw)
 else:value=raw
 expected[url]=value
 if value!=raw:changed[url]={'expectedBytes':len(value),'expectedSHA256':digest(value)}
assert set(changed)=={r['path']for r in raw_check['staticFileFailures']},'UNEXPLAINED_OR_UNTESTED_STATIC_DIFFERENCE'
for row in records:
 assert row['status']==200
 if row['path']not in changed:assert row['shaMatches']and digest(expected[row['path']])==payload['files'][('frontend/emergency_pc/'+row['path'].removeprefix('/zhumadian/emergency/'))if row['path'].startswith('/zhumadian/emergency/')else('frontend/security_pc/'+row['path'].removeprefix('/zhumadian/'))]['sha256']
context=ssl.create_default_context();connection=http.client.HTTPSConnection('www.joinlinksmart.com',context=context,timeout=25);checked=[]
def fetch(url,body):
 connection.request('GET',url,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});response=connection.getresponse();actual=response.read()
 assert response.status==200 and actual==body,'RETAINED_GATEWAY_OUTPUT_NOT_BYTE_EXACT:'+url
 checked.append({'path':url,'status':response.status,'bytes':len(actual),'expectedSHA256':digest(body),'exactExpectedGatewayBytes':True})
for url in sorted(changed):fetch(url,expected[url])
# Verify the actual branded asset URLs emitted in both HTML entries, plus all four workflow facade URLs.
versioned=set()
for url in ['/zhumadian/index.html','/zhumadian/emergency/index.html']:
 for asset in re.findall(rb'''(?:src|href)=["']([^"']+)["']''',expected[url]):
  a=asset.decode('utf-8')
  if '/branding-20261025/assets/'in a:versioned.add(a)
routes=read(R/'work/user_feedback_20261031/emergency-workflow-source-r6/independent-build-verification.json')['actualFourWorkflowRouteFacadesVerified']
for rel in routes.values():versioned.add('/zhumadian/emergency/branding-20261025/'+rel)
for url in sorted(versioned):fetch(url,expected[url.replace('/branding-20261025/','/')])
connection.close()
proof={'schema':'xnby.r24.retained-gateway-wire-verification.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'allPassed':True,'totalStaticFilesVerified':1174,'unchangedWireFiles':1161,'exactRetainedGatewayDifferencesVerified':13,
 'retainedProjectBrandingSHA256':release['controllerFiles']['tools/original_project_branding.py'],
 'retainedHeaderBrandingSHA256':release['controllerFiles']['tools/original_header_branding.py'],
 'projectIconAliasUsesPinnedSVG':True,'brandedEntryAndFourWorkflowFacadeAssetURLsVerified':len(versioned),
 'rawByteMismatchDiagnosticPreserved':True,'arbitraryMismatchExceptionsOrProductChanges':False,'actualAuthenticatedPublicBusinessFlowAccepted':False,
 'checks':checked,'tlsDefaultCertificateVerificationEnabled':True}
(D/'public-retained-gateway-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items()if k!='checks'},ensure_ascii=False))
