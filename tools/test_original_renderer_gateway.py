"""Check optional original-renderer routing using existing private fixtures, without starting applications."""
import argparse,hashlib,json,os,pathlib,re,subprocess,sys
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=pathlib.Path,required=True)
parser.add_argument('--output',type=pathlib.Path,required=True)
args=parser.parse_args()
W=args.workspace.resolve(strict=True);A=W.parents[1];candidate=pathlib.Path(__file__).parent.resolve();out=args.output.resolve()
assert A.name=='Application' and candidate==A/'tools'
assert out.is_relative_to(W) and not out.exists()
out.mkdir();sys.path.insert(0,str(candidate))
import prepare_original_bigscreen_gateway as gateway
from serve_original_bigscreen_candidate import closed_normally
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
probe=W/'own-original-renderer-252-probe-r1/receipt.json';actual=gateway.load_renderer_probe(W,probe,sha(probe));assert actual['sdkSHA256']==gateway.ORIGINAL_RENDERER_SDK_SHA256
checks=1
for endpoint in ['127.0.0.1:8080','8.8.8.8:8080','0.0.0.0:8080','169.254.0.1:8080','224.0.0.1:8080','192.168.0.107:80','192.168.0.107:08080','192.168.0.107:8080/path','user@192.168.0.107:8080','192.168.0.107:8080;return 200;']:
 try:gateway.checked_renderer_upstream(endpoint)
 except ValueError:checks+=1
 else:raise AssertionError('BAD_ENDPOINT_ACCEPTED')
record=json.loads(probe.read_bytes())
for i,changes in enumerate([{'status':404},{'bytes':1},{'sha256':'0'*64},{'cookiesOrAuthorizationSent':True},{'url':'http://8.8.8.8:8080/libac'},{'url':'http://192.168.0.107:8080/libac?token=secret'},{'url':'http://user:secret@192.168.0.107:8080/libac'},{'url':'http://192.168.0.107:8080/elsewhere'}]):
 file=out/f'invalid-{i}.json';file.write_text(json.dumps(dict(record,**changes)),encoding='utf-8')
 try:gateway.load_renderer_probe(out,file,sha(file))
 except ValueError:checks+=1
 else:raise AssertionError('BAD_PROBE_ACCEPTED')
for workspace,file,pin in [(W,probe,'0'*64),(out,probe,sha(probe))]:
 try:gateway.load_renderer_probe(workspace,file,pin)
 except ValueError:checks+=1
 else:raise AssertionError('BAD_PIN_OR_SCOPE_ACCEPTED')
def run(command,name,valid=True):
 r=subprocess.run(list(map(str,command)),capture_output=True,timeout=30,env=dict(os.environ,PYTHONPATH=str(A/'tools')),creationflags=subprocess.CREATE_NO_WINDOW);(out/(name+'.private.log')).write_bytes(r.stdout+r.stderr);assert (r.returncode==0)==valid,name
base=['D:/Program Files/nodejs/node.exe',candidate/'prepare_original_bigscreen_config.mjs','--source',W/'bigscreen/public/config.js','--parser',W/'security_pc/node_modules/@babel/parser/lib/index.js','--parser-sha256','82d72e197e27bf909ae10ffc8d1a969aeb94fe96ec96c4e9cb685a0a8229e40c','--origin','http://127.0.0.1:18893']
run([*base,'--output',out/'default-runtime'],'default-runtime');baseline=(W/'own-bigscreen-j3/runtime/config.js').read_bytes();assert not re.search(rb'\binteractWsAddress\s*:',baseline);expected,count=re.subn(rb'(\bvar\s+config\s*=\s*\{)',lambda match:match[1]+b'\n    interactWsAddress: "ws://127.0.0.1:18893/zhumadian/api/bigscreen/interact",',baseline,count=1);assert count==1 and (out/'default-runtime/config.js').read_bytes()==expected;checks+=1
assert b'interactWsAddress' in expected and b'ws://127.0.0.1:18893/zhumadian/api/bigscreen/interact' in expected;checks+=1
run([*base,'--renderer-sdk-sha256',gateway.ORIGINAL_RENDERER_SDK_SHA256,'--output',out/'renderer-runtime'],'renderer-runtime');assert (out/'renderer-runtime/config.js').read_bytes()==(out/'default-runtime/config.js').read_bytes().replace(b'/zhumadian/unavailable-renderer/libac',b'/zhumadian/renderer/libac');checks+=1
run([*base,'--renderer-sdk-sha256','0'*64,'--output',out/'bad-sdk'],'bad-sdk',False);assert not (out/'bad-sdk').exists();checks+=1
runtime=W/'local-gateway-runtime_20261024/nginx-1.31.8';dist=W/'own-bigscreen-local-build-r1/dist';public=W/'bigscreen/public'
for name,upstream in [('default',None),('renderer',actual['upstream'])]:
 destination=out/(name+'-gateway');prepared=gateway.prepare(destination,runtime,dist,public,out/(name+'-runtime/config.js'),18893,18891,18895,18896,upstream)
 run([runtime/'nginx.exe','-p',str(destination)+'/', '-c',destination/'nginx.conf','-t'],name+'-nginx-check');checks+=1
 config=(destination/'nginx.conf').read_text('utf-8')
 if upstream:
  assert config.count('proxy_pass http://'+upstream)==2 and 'location = /player {' in config and 'location = /zhumadian/renderer/libac {' in config
  for route in ['/player','/zhumadian/renderer/libac']:
   block=config.split('location = '+route+' {',1)[1].split(' }',1)[0]
   assert all('proxy_set_header '+header+' "";' in block for header in ['Authorization','Cookie','Referer'])
  assert prepared['rendererEndpointConfigured'] and not prepared['originalRendererAvailable'];checks+=1
 else:assert 'location = /player {' not in config and not prepared['rendererEndpointConfigured'];checks+=1
badOutput=out/'bad-gateway'
try:gateway.prepare(badOutput,runtime,dist,public,out/'renderer-runtime/config.js',18893,18891,18895,18896,'8.8.8.8:8080')
except ValueError:assert not badOutput.exists();checks+=1
else:raise AssertionError('BAD_GATEWAY_CREATED')
run([sys.executable,'-B',candidate/'serve_original_bigscreen_candidate.py','--help'],'controller-help');checks+=1
classified={name:closed_normally(json.loads((W/name/'receipt.json').read_bytes())) for name in ['own-bigscreen-j1','own-bigscreen-j2','own-bigscreen-j3']};assert classified=={'own-bigscreen-j1':False,'own-bigscreen-j2':False,'own-bigscreen-j3':True};checks+=3
receipt={'checks':checks,'defaultRuntimeOnlyMissingInteractionEndpointAdded':True,'sourceInteractionEndpointWasMissing':True,'interactionEndpointSameOriginInBothModes':True,'onlyEnabledRuntimeSDKEndpointChanged':True,'actualOriginalSDKProbeValidated':True,'unavailableDefaultPreserved':True,'anonymousSDKPinRequired':True,'rendererCredentialsStrippedForBothRoutes':True,'bothActualNginxConfigurationChecksPassed':True,'oldActualClosureClassificationsPreserved':True,'rendererOrBusinessApplicationStarted':False,'sourceFiles':{name:sha(candidate/name) for name in ['prepare_original_bigscreen_config.mjs','prepare_original_bigscreen_gateway.py','serve_original_bigscreen_candidate.py']}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
