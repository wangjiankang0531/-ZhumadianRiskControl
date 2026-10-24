"""Prepare an independent loopback gateway for the original bigscreen UI and three original backends."""
import hashlib,ipaddress,json,pathlib,re,urllib.parse
from prepare_original_frontend_gateway import quoted,checked_port

ORIGINAL_RENDERER_SDK_SHA256='b5afbd97aca400f69aee22a0f4d959d5b97dd5def92d95c9338ae7c37f6712a1'

def checked_renderer_upstream(value):
 if not isinstance(value,str) or not re.fullmatch(r'[0-9.]+:[0-9]+',value):raise ValueError('EXPLICIT_PRIVATE_IPV4_RENDERER_REQUIRED')
 host,number=value.split(':');address=ipaddress.IPv4Address(host);port=int(number);checked_port(port)
 if not address.is_private or address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified or address.is_reserved:raise ValueError('EXPLICIT_PRIVATE_IPV4_RENDERER_REQUIRED')
 if value!=str(address)+':'+str(port):raise ValueError('CANONICAL_PRIVATE_RENDERER_ENDPOINT_REQUIRED')
 return value

def load_renderer_probe(workspace,probe,expected_sha256):
 workspace=pathlib.Path(workspace).resolve(strict=True);probe=pathlib.Path(probe).resolve(strict=True)
 if not probe.is_relative_to(workspace) or not probe.is_file() or not 0<probe.stat().st_size<=16384:raise ValueError('BOUNDED_OWN_RENDERER_PROBE_REQUIRED')
 raw=probe.read_bytes()
 if not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256) or hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('RENDERER_PROBE_SHA256_MISMATCH')
 record=json.loads(raw);url=urllib.parse.urlsplit(record['url'])
 if url.scheme!='http' or url.username or url.password or url.path!='/libac' or url.query or url.fragment:raise ValueError('EXACT_ORIGINAL_SDK_PROBE_URL_REQUIRED')
 endpoint=checked_renderer_upstream(url.netloc)
 if record.get('status')!=200 or record.get('bytes')!=321959 or record.get('sha256')!=ORIGINAL_RENDERER_SDK_SHA256 or record.get('cookiesOrAuthorizationSent') is not False:raise ValueError('SUCCESSFUL_PINNED_ANONYMOUS_RENDERER_PROBE_REQUIRED')
 return {'upstream':endpoint,'sdkSHA256':ORIGINAL_RENDERER_SDK_SHA256,'probeSHA256':expected_sha256}

def prepare(output,runtime,build,public,runtime_config,port,business_gateway_port,bigscreen_port,mock_port,renderer_upstream=None):
 output=pathlib.Path(output).resolve();runtime=pathlib.Path(runtime).resolve(strict=True);build=pathlib.Path(build).resolve(strict=True);public=pathlib.Path(public).resolve(strict=True);runtime_config=pathlib.Path(runtime_config).resolve(strict=True)
 for number in (port,business_gateway_port,bigscreen_port,mock_port):checked_port(number)
 if len({port,business_gateway_port,bigscreen_port,mock_port})!=4:raise ValueError('DISTINCT_OWN_LOOPBACK_PORTS_REQUIRED')
 if renderer_upstream is not None:renderer_upstream=checked_renderer_upstream(renderer_upstream)
 if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (build,public,runtime_config)):raise ValueError('FRESH_SEPARATE_GATEWAY_ROOT_REQUIRED')
 if hashlib.sha256((runtime/'nginx.exe').read_bytes()).hexdigest()!='c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44':raise ValueError('EXISTING_FIXED_OFFICIAL_NGINX_REQUIRED')
 if not (build/'index.html').is_file() or not (build/'static').is_dir() or not runtime_config.is_file():raise ValueError('PREPARED_ORIGINAL_UI_AND_CONFIG_REQUIRED')
 mount='/zhumadian/bigscreen/';lines=['daemon off;','master_process on;','worker_processes 1;','worker_shutdown_timeout 3s;','pid '+quoted(output/'nginx.pid')+';','error_log '+quoted(output/'error.log')+' warn;','events { worker_connections 256; }','http {',' include '+quoted(runtime/'conf/mime.types')+';',' default_type application/octet-stream;',' sendfile on;',' client_body_temp_path '+quoted(output/'temp/body')+';',' proxy_temp_path '+quoted(output/'temp/proxy')+';'," log_format own '$request_method $status';",' access_log '+quoted(output/'access.log')+' own;'," map $http_upgrade $connection_upgrade { default upgrade; '' close; }",' server {',' listen 127.0.0.1:'+str(port)+';',' server_name 127.0.0.1 localhost;',' server_tokens off;',' autoindex off;',' client_max_body_size 10m;'," add_header Content-Security-Policy \"default-src 'self' data: blob:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' ws://127.0.0.1:"+str(port)+"; frame-src 'self'; object-src 'none'; base-uri 'self'\" always;",' add_header Referrer-Policy no-referrer always;',' location = / { return 302 '+mount+'; }',' location = '+mount.rstrip('/')+' { return 301 '+mount+'$is_args$args; }']
 for path,file in [(mount,build/'index.html'),(mount+'index.html',build/'index.html'),(mount+'config.js',runtime_config)]:lines+=[' location = '+path+' {','  root '+quoted(file.parent)+';','  try_files /'+file.name+' =404;',' }']
 lines+=[' location ^~ '+mount+' {','  rewrite ^'+mount+'(.*)$ /$1 break;','  root '+quoted(build)+';','  try_files $uri @original_bigscreen_public;',' }',' location @original_bigscreen_public {','  root '+quoted(public)+';','  try_files $uri =404;',' }']
 for path,target,upstream,drop in [('/zhumadian/api/reference-mock/','/zhumadian/api/reference-mock/',mock_port,True),('/zhumadian/api/bigscreen/','/',bigscreen_port,False),('/zhumadian/api/serv/','/zhumadian/api/serv/',business_gateway_port,False),('/zhumadian/api/jnpf/','/zhumadian/api/jnpf/',business_gateway_port,False)]:
  lines+=[' location ^~ '+path+' {','  proxy_pass http://127.0.0.1:'+str(upstream)+target+';','  proxy_http_version 1.1;','  proxy_set_header Host $http_host;','  proxy_set_header Upgrade $http_upgrade;','  proxy_set_header Connection $connection_upgrade;','  proxy_connect_timeout 3s;','  proxy_read_timeout 60s;','  proxy_send_timeout 15s;']
  if drop:lines+=['  proxy_set_header Authorization "";','  proxy_set_header Cookie "";','  proxy_set_header Referer "";']
  lines+=[' }']
 if renderer_upstream is not None:
  for path,target in [('/zhumadian/renderer/libac','/libac'),('/player','/player')]:
   lines+=[' location = '+path+' {','  proxy_pass http://'+renderer_upstream+target+';','  proxy_http_version 1.1;','  proxy_set_header Host $proxy_host;','  proxy_set_header Upgrade $http_upgrade;','  proxy_set_header Connection $connection_upgrade;','  proxy_set_header Authorization "";','  proxy_set_header Cookie "";','  proxy_set_header Referer "";','  proxy_connect_timeout 4s;','  proxy_read_timeout 150s;','  proxy_send_timeout 15s;',' }']
 lines+=[' location ^~ /zhumadian/unavailable-renderer/ { return 503; }',' location ^~ /zhumadian/unavailable/ { return 503; }',' location / { return 404; }',' }','}']
 output.mkdir();(output/'logs').mkdir();(output/'temp').mkdir();config=output/'nginx.conf';config.write_text('\n'.join(lines)+'\n',encoding='utf-8');receipt={'bind':'127.0.0.1','port':port,'portalMount':mount,'businessGatewayPort':business_gateway_port,'bigscreenPort':bigscreen_port,'mockPort':mock_port,'runtimeConfigSHA256':hashlib.sha256(runtime_config.read_bytes()).hexdigest(),'nginxConfigSHA256':hashlib.sha256(config.read_bytes()).hexdigest(),'staticResourcesCopied':False,'credentialHeadersToMockStripped':True,'rendererEndpointConfigured':renderer_upstream is not None,'credentialHeadersToRendererStripped':renderer_upstream is not None,'rendererSDKExpectedSHA256':ORIGINAL_RENDERER_SDK_SHA256 if renderer_upstream else None,'originalRendererAvailable':False,'businessAPISynthesized':False,'pathsQueriesOrCredentialsLogged':False,'publicProductionReady':False};(output/'preparation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt
