"""Prepare a loopback-only original-frontend gateway; contains no business API.

Static roots are referenced, never copied. Upstreams are either explicitly
unavailable (503), or explicit loopback ports of isolated local services.
This is a local integration candidate, not a public production configuration.
"""
from pathlib import Path
import argparse
import hashlib
import json

def quoted(path):
    value=Path(path).resolve().as_posix()
    if any(c in value for c in ('"','\n','\r','$',';','{','}')):
        raise ValueError('Unsupported nginx path characters')
    return '"'+value+'"'

def checked_port(port):
    if isinstance(port,bool) or not isinstance(port,int) or not 1024<=port<=65535:
        raise ValueError('Explicit nonprivileged local port required')
    return port

def prepare(output, runtime, roots, port, business_port=None, platform_port=None):
    output=Path(output).resolve();runtime=Path(runtime).resolve()
    checked_port(port)
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
           ' location = / { return 302 /tianjinrisk/home; }',
           ' location = /zhumadian/ { return 302 /tianjinrisk/home; }',
           ' location = /tianjinrisk { return 302 /tianjinrisk/home; }']
    lines+=[' location = /tianjinrisk/api { return 404; }',
            ' location ^~ /tianjinrisk/api/ { return 404; }']
    for external,upstream,target,timeout in (
            ('/tianjinrisk/api/jnpf/',platform_port,'/api/',15),
            ('/tianjinrisk/api/serv/websocket/',business_port,'/websocket/',300),
            ('/tianjinrisk/api/serv/',business_port,'/',15)):
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
    mounts=[('/tianjinrisk/emergency/','emergency_pc'),('/tianjinrisk/h5/','mobile'),
            ('/reference-bigscreen/','bigscreen'),('/tianjinrisk/','security_pc')]
    for mount,kind in mounts:
        name='spa_'+kind
        lines+=[' location ^~ '+mount+' {',
                '  rewrite ^'+mount+'(.*)$ /$1 break;',
                '  root '+quoted(roots[kind])+';',
                '  try_files $uri $uri/ @'+name+';',' }',
                ' location @'+name+' {',
                '  if ($uri ~ "\\.[^/]+$") { return 404; }',
                '  root '+quoted(roots[kind])+';',
                '  try_files /index.html =404;',' }']
    for mount in ('/tianjinrisk/map/','/tianjinrisk/api/map/'):
        lines+=[' location ^~ '+mount+' {',
                '  rewrite ^'+mount+'(.*)$ /$1 break;',
                '  root '+quoted(roots['tiles'])+';','  try_files $uri =404;',' }']
    lines+=[' location / { return 404; }',' }','}']
    output.mkdir(parents=True)
    (output/'logs').mkdir()
    (output/'temp').mkdir()
    config=output/'nginx.conf'
    config.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    receipt={'bind':'127.0.0.1','port':port,'backendMode':'unavailable' if business_port is None else 'isolated-loopback',
             'businessPort':business_port,'platformPort':platform_port,
             'roots':{k:str(Path(v).resolve()) for k,v in roots.items()},
             'nginxExecutableSHA256':hashlib.sha256((runtime/'nginx.exe').read_bytes()).hexdigest(),
             'configSHA256':hashlib.sha256(config.read_bytes()).hexdigest(),
             'businessAPISynthesized':False,'staticResourcesCopied':False,'publicProductionReady':False,
             'notes':['/reference-bigscreen/ is an explicit local QA mount; the original portal target is not yet verified.',
                      '/zhumadian/ is a local redirect only; public /zhumadian deployment mapping remains unverified.']}
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--runtime',type=Path,required=True)
    ap.add_argument('--port',type=int,required=True)
    for kind in ('security_pc','emergency_pc','mobile','bigscreen','tiles'):ap.add_argument('--'+kind.replace('_','-'),type=Path,required=True)
    ap.add_argument('--business-port',type=int);ap.add_argument('--platform-port',type=int)
    a=ap.parse_args();r=prepare(a.output,a.runtime,{k:getattr(a,k) for k in ('security_pc','emergency_pc','mobile','bigscreen','tiles')},a.port,a.business_port,a.platform_port)
    print(json.dumps({k:r[k] for k in ('bind','port','backendMode','businessAPISynthesized','staticResourcesCopied','publicProductionReady')}))

if __name__=='__main__':main()
