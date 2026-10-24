"""Prepare a loopback-only original-frontend gateway; contains no business API.

Static roots are referenced, never copied. Upstreams are either explicitly
unavailable (503), or explicit loopback ports of isolated local services.
This is a local integration candidate, not a public production configuration.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

def quoted(path):
    value=Path(path).resolve().as_posix()
    if any(c in value for c in ('"','\n','\r','$',';','{','}')):
        raise ValueError('Unsupported nginx path characters')
    return '"'+value+'"'

def checked_port(port):
    if isinstance(port,bool) or not isinstance(port,int) or not 1024<=port<=65535:
        raise ValueError('Explicit nonprivileged local port required')
    return port

def checked_base_path(value):
    if not isinstance(value,str) or len(value)>128 or not re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',value):
        raise ValueError('Explicit same-origin application base without trailing slash required')
    return value


def prepare(output, runtime, roots, port, business_port=None, platform_port=None, base_path='/tianjinrisk'):
    output=Path(output).resolve();runtime=Path(runtime).resolve()
    checked_port(port)
    base_path=checked_base_path(base_path)
    if (business_port is None)!=(platform_port is None):
        raise ValueError('Both isolated upstreams must be provided together')
    if business_port is not None:
        checked_port(business_port);checked_port(platform_port)
        if port in (business_port,platform_port):raise ValueError('Gateway cannot proxy to itself')
    if output.exists():raise ValueError('Fresh gateway output required')
    if set(roots)!={'security_pc','emergency_pc','mobile','bigscreen','tiles'}:
        raise ValueError('All original static roots required')
    for kind,path in roots.items():
        path=Path(path).resolve()
        if not path.is_dir() or (kind!='tiles' and not (path/'index.html').is_file()):
            raise ValueError('Missing original static root: '+kind)
        if output.is_relative_to(path) or path.is_relative_to(output):
            raise ValueError('Gateway output must not overlap static roots')
        quoted(path)
    if not (runtime/'nginx.exe').is_file() or not (runtime/'conf/mime.types').is_file():
        raise ValueError('Explicit verified nginx distribution required')
    lines=['daemon off;','master_process on;','worker_processes 1;','worker_shutdown_timeout 3s;',
           'pid '+quoted(output/'nginx.pid')+';',
           'error_log '+quoted(output/'error.log')+' crit;',
           'events { worker_connections 256; }','http {',
           ' include '+quoted(runtime/'conf/mime.types')+';',
           ' default_type application/octet-stream;',
           " log_format without_query '$request_method $uri $status';",
           ' access_log '+quoted(output/'access.log')+' without_query;',
           " map $http_upgrade $connection_upgrade { default upgrade; '' close; }",
           ' server {',' listen 127.0.0.1:'+str(port)+';',
           ' server_name 127.0.0.1 localhost;',' server_tokens off;',' autoindex off;',
           ' client_max_body_size 100m;',
           ' location = / { return 302 '+base_path+'/home; }',
           *([' location = /zhumadian/ { return 302 /tianjinrisk/home; }'] if base_path=='/tianjinrisk' else []),
           ' location = '+base_path+' { return 302 '+base_path+'/home; }']
    lines+=[' location = '+base_path+'/api { return 404; }',
            ' location ^~ '+base_path+'/api/ { return 404; }']
    for external,upstream,target,timeout in (
            (base_path+'/api/jnpf/',platform_port,'/api/',15),
            (base_path+'/api/serv/websocket/',business_port,'/websocket/',300),
            (base_path+'/api/serv/',business_port,'/',15)):
        lines+=[' location ^~ '+external+' {']
        if upstream is None:
            lines+=['  add_header X-Original-Backend unavailable always;','  return 503;']
        else:
            lines+=['  proxy_pass http://127.0.0.1:'+str(upstream)+target+';',
                    '  proxy_http_version 1.1;',
                    '  proxy_set_header Host $http_host;',
                    '  proxy_set_header X-Forwarded-Proto $scheme;',
                    '  proxy_set_header X-Real-IP $remote_addr;',
                    '  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
                    '  proxy_set_header Upgrade $http_upgrade;',
                    '  proxy_set_header Connection $connection_upgrade;',
                    '  proxy_connect_timeout 15s;','  proxy_read_timeout '+str(timeout)+'s;',
                    '  proxy_send_timeout '+str(timeout)+'s;']
        lines+=[' }']
    mounts=[(base_path+'/emergency/','emergency_pc'),(base_path+'/h5/','mobile'),
            ('/reference-bigscreen/','bigscreen'),(base_path+'/','security_pc')]
    for mount,kind in mounts:
        # Original portal menus use the bare emergency path. With a static
        # root/rewrite mount nginx does not add the proxy_pass slash redirect.
        if kind!='security_pc':
            lines+=[' location = '+mount.rstrip('/')+' { return 301 '+mount+'$is_args$args; }']
        # Serving a directory through try_files $uri/ would cause nginx's
        # index module to redirect to /index.html after the prefix rewrite.
        lines+=[' location = '+mount+' {',
                '  root '+quoted(roots[kind])+';',
                '  try_files /index.html =404;',' }']
        name='spa_'+kind
        lines+=[' location ^~ '+mount+' {',
                '  rewrite ^'+mount+'(.*)$ /$1 break;',
                '  root '+quoted(roots[kind])+';',
                '  try_files $uri $uri/ @'+name+';',' }',
                ' location @'+name+' {',
                '  if ($uri ~ "\\.[^/]+$") { return 404; }',
                '  root '+quoted(roots[kind])+';',
                '  try_files /index.html =404;',' }']
    for mount in (base_path+'/map/',base_path+'/api/map/'):
        lines+=[' location ^~ '+mount+' {',
                '  rewrite ^'+mount+'(.*)$ /$1 break;',
                '  root '+quoted(roots['tiles'])+';','  try_files $uri =404;',' }']
    lines+=[' location / { return 404; }',' }','}']
    output.mkdir(parents=True)
    (output/'logs').mkdir()
    (output/'temp').mkdir()
    config=output/'nginx.conf'
    config.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    receipt={'bind':'127.0.0.1','port':port,'appBasePath':base_path,'backendMode':'unavailable' if business_port is None else 'isolated-loopback',
             'businessPort':business_port,'platformPort':platform_port,
             'roots':{k:str(Path(v).resolve()) for k,v in roots.items()},
             'nginxExecutableSHA256':hashlib.sha256((runtime/'nginx.exe').read_bytes()).hexdigest(),
             'configSHA256':hashlib.sha256(config.read_bytes()).hexdigest(),
             'businessAPISynthesized':False,'staticResourcesCopied':False,'publicProductionReady':False,
             'notes':['/reference-bigscreen/ is a local QA mount. The observed original command link targets the desktop component on 127.0.0.1:18080/daping/index.html; that integration remains unverified.',
                      'The selected application base is a local integration candidate; public production mapping remains unverified.']}
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--port',type=int,required=True)
    for kind in ('security_pc','emergency_pc','mobile','bigscreen','tiles'):ap.add_argument('--'+kind.replace('_','-'),type=Path,required=True)
    ap.add_argument('--business-port',type=int);ap.add_argument('--platform-port',type=int)
    ap.add_argument('--base-path',default='/tianjinrisk')
    a=ap.parse_args();r=prepare(a.output,a.runtime,{k:getattr(a,k) for k in ('security_pc','emergency_pc','mobile','bigscreen','tiles')},a.port,a.business_port,a.platform_port,a.base_path)
    print(json.dumps({k:r[k] for k in ('bind','port','backendMode','businessAPISynthesized','staticResourcesCopied','publicProductionReady')}))

if __name__=='__main__':main()
