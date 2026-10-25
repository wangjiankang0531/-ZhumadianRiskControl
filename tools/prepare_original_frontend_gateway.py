"""Prepare a loopback-only original-frontend gateway; contains no business API.

Static roots are referenced, never copied. Upstreams are either explicitly
unavailable (503), or explicit loopback ports of isolated local services.
An explicit canonical HTTPS origin supports an existing TLS frontend. This
does not configure TLS or make the gateway a complete production deployment.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
from urllib.parse import urlsplit

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


def checked_public_origin(value):
    if value is None:
        return None
    if not isinstance(value,str) or len(value)>320 or not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?/?',value):
        raise ValueError('Explicit canonical HTTPS DNS origin required')
    parsed=urlsplit(value)
    host=parsed.hostname
    try:
        port=parsed.port
    except ValueError as error:
        raise ValueError('Valid canonical HTTPS port required') from error
    if (not host or len(host)>253 or '.' not in host or
        not re.search(r'[a-z]',host.rsplit('.',1)[1]) or
        any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',label) for label in host.split('.')) or
        port is not None and not 1<=port<=65535):
        raise ValueError('Explicit canonical HTTPS DNS origin required')
    return 'https://'+host+(':'+str(port) if port not in (None,443) else '')


def forwarding_headers(origin):
    if origin is None:
        return ['  proxy_set_header Host $http_host;',
                '  proxy_set_header X-Forwarded-Proto $scheme;']
    parsed=urlsplit(origin)
    return ['  proxy_set_header Host '+parsed.netloc+';',
            '  proxy_set_header X-Forwarded-Host '+parsed.netloc+';',
            '  proxy_set_header X-Forwarded-Proto https;',
            '  proxy_set_header X-Forwarded-Port '+str(parsed.port or 443)+';',
            '  proxy_set_header Forwarded "";',
            '  proxy_set_header X-Forwarded-Prefix "";',
            '  proxy_set_header X-Forwarded-Server "";']


def prepare(output, runtime, roots, port, business_port=None, platform_port=None, base_path='/tianjinrisk',admin_frontend_port=None,public_origin=None,project_name=None):
    output=Path(output).resolve();runtime=Path(runtime).resolve()
    checked_port(port)
    base_path=checked_base_path(base_path)
    public_origin=checked_public_origin(public_origin)
    if (business_port is None)!=(platform_port is None):
        raise ValueError('Both isolated upstreams must be provided together')
    if business_port is not None:
        checked_port(business_port);checked_port(platform_port)
        if port in (business_port,platform_port):raise ValueError('Gateway cannot proxy to itself')
    if admin_frontend_port is not None:
        checked_port(admin_frontend_port)
        if admin_frontend_port in (port,business_port,platform_port):raise ValueError('Admin static service must be a distinct loopback port')
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
           *([' absolute_redirect off;'] if public_origin is not None else []),
           ' client_max_body_size 100m;',
           ' location = / { return 302 '+base_path+'/home; }',
           *([' location = /zhumadian/ { return 302 /tianjinrisk/home; }'] if base_path=='/tianjinrisk' else []),
           ' location = '+base_path+' { return 302 '+base_path+'/home; }']
    lines+=[' location = '+base_path+'/api { return 404; }',
            ' location ^~ '+base_path+'/api/ { return 404; }']
    if admin_frontend_port is not None:lines+=[' location = '+base_path+'/admin/api { return 404; }']
    proxies=[
            (base_path+'/api/jnpf/',platform_port,'/api/',15),
            (base_path+'/api/serv/websocket/',business_port,'/websocket/',300),
            (base_path+'/api/serv/',business_port,'/',15)]
    if admin_frontend_port is not None:proxies.append((base_path+'/admin/api/',platform_port,'/api/',300))
    for external,upstream,target,timeout in proxies:
        lines+=[' location ^~ '+external+' {']
        if upstream is None:
            lines+=['  add_header X-Original-Backend unavailable always;','  return 503;']
        else:
            lines+=['  proxy_pass http://127.0.0.1:'+str(upstream)+target+';',
                    '  proxy_http_version 1.1;',
                    *forwarding_headers(public_origin),
                    '  proxy_set_header X-Real-IP $remote_addr;',
                    '  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
                    '  proxy_set_header Upgrade $http_upgrade;',
                    '  proxy_set_header Connection $connection_upgrade;',
                    '  proxy_connect_timeout 15s;','  proxy_read_timeout '+str(timeout)+'s;',
                    '  proxy_send_timeout '+str(timeout)+'s;']
        lines+=[' }']
    if admin_frontend_port is not None:
        admin_mount=base_path+'/admin/'
        lines+=[' location = '+admin_mount.rstrip('/')+' { return 301 '+admin_mount+'$is_args$args; }',
                ' location ^~ '+admin_mount+' {',
                '  proxy_pass http://127.0.0.1:'+str(admin_frontend_port)+admin_mount+';',
                '  proxy_http_version 1.1;',*forwarding_headers(public_origin),
                '  proxy_connect_timeout 5s;','  proxy_read_timeout 15s;',
                ' }']
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
    config_text='\n'.join(lines)+'\n'
    branding=None
    if project_name is not None:
        from original_project_branding import brand_static_config
        config_text,branding=brand_static_config(config_text,project_name)
    config.write_text(config_text,encoding='utf-8')
    receipt={'bind':'127.0.0.1','port':port,'appBasePath':base_path,'backendMode':'unavailable' if business_port is None else 'isolated-loopback',
             'businessPort':business_port,'platformPort':platform_port,'adminFrontendPort':admin_frontend_port,
             'adminBasePath':base_path+'/admin' if admin_frontend_port is not None else None,
             'canonicalPublicOrigin':public_origin,
             'projectBranding':branding,
             'nginxRedirectsRelative':public_origin is not None,
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
    ap.add_argument('--admin-frontend-port',type=int)
    ap.add_argument('--public-origin',help='Canonical HTTPS origin of the existing TLS frontend; does not expose a listener')
    ap.add_argument('--project-name',help='Explicit project display name for static responses')
    a=ap.parse_args();r=prepare(a.output,a.runtime,{k:getattr(a,k) for k in ('security_pc','emergency_pc','mobile','bigscreen','tiles')},a.port,a.business_port,a.platform_port,a.base_path,a.admin_frontend_port,a.public_origin,a.project_name)
    print(json.dumps({k:r[k] for k in ('bind','port','backendMode','businessAPISynthesized','staticResourcesCopied','publicProductionReady')}))

if __name__=='__main__':main()
