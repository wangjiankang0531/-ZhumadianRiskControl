"""Render frozen private original-system settings for distinct owned server ports.

No I/O, database connection, process launch, authentication, or default secrets.
"""
from pathlib import Path
import re,urllib.parse,uuid

def checked_uuid(value):
    if not isinstance(value,str) or str(uuid.UUID(value))!=value:raise ValueError('EXPLICIT_CANONICAL_OWNER_UUID_REQUIRED')
    return value

def properties_ascii(values):
    """Java Properties syntax, including UTF-16 surrogate pairs for non-BMP text."""
    def escape(value,key=False):
        out=[]
        for i,c in enumerate(value):
            if c in '\\=:' or key and c in ' #!' or i==0 and c==' ':out.append('\\'+c)
            elif c in '\n\r\t\f':out.append({'\n':'\\n','\r':'\\r','\t':'\\t','\f':'\\f'}[c])
            elif ord(c)<32 or ord(c)>126:
                raw=c.encode('utf-16-be')
                out.extend('\\u%04x'%int.from_bytes(raw[j:j+2],'big') for j in range(0,len(raw),2))
            else:out.append(c)
        return ''.join(out)
    if not isinstance(values,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in values.items()):raise ValueError('STRING_PROPERTIES_REQUIRED')
    return ''.join(escape(k,True)+'='+escape(v)+'\n' for k,v in sorted(values.items())).encode('ascii')

def materialize(spec,*,side,application,platform_run,business_run,platform_data_owner,run_owner,database_uuid,database_port,redis_port,object_port,database_password,redis_password,object_access,object_secret,platform_port=None):
    if side not in ('platform','business'):raise ValueError('EXPLICIT_COMPONENT_REQUIRED')
    for value in (platform_data_owner,run_owner,database_uuid):checked_uuid(value)
    ports=[database_port,redis_port,object_port]+([] if side=='platform' else [platform_port])
    if any(type(v)!=int or not 1024<=v<=65535 for v in ports) or len(set(ports))!=len(ports):raise ValueError('DISTINCT_OWNED_LOOPBACK_PORTS_REQUIRED')
    for secret in (database_password,redis_password,object_access,object_secret):
        if not isinstance(secret,str) or not secret or any(c in secret for c in '\r\n\0'):raise ValueError('EXPLICIT_PRIVATE_RUNTIME_SECRET_REQUIRED')
    app=Path(application);p=Path(platform_run);b=Path(business_run)
    if any('..' in q.parts for q in (app,p,b)) or not app.is_absolute() or app.name!='Application' or p.parent!=app/'UserData/TianjinOriginalPlatform/runs' or not b.is_relative_to(app/'UserData') or not re.fullmatch(r'j[1-9][0-9]{0,3}',p.name):raise ValueError('OWNED_SERVER_RUNTIME_LAYOUT_REQUIRED')
    if len(str(p/'tmp'))>80 or len(str(b/'tmp'))>80:raise ValueError('SHORT_WINDOWS_RUNTIME_PATH_REQUIRED')
    tokens={'APP':app.as_posix(),'PLATFORM_RUN':p.as_posix(),'BUSINESS_RUN':b.as_posix(),'PLATFORM_DATA':(app/'UserData/TianjinOriginalPlatform').as_posix()}
    def render(value):
        for key,new in tokens.items():value=value.replace('${'+key+'}',new)
        if any('${'+key+'}' in value for key in tokens):raise ValueError('UNRENDERED_RUNTIME_PATH')
        return value
    values={k:render(v) for k,v in spec['configuration'][side].items()}
    root=p if side=='platform' else b
    def jdbc(value):
        value=re.sub(r'jdbc:mysql://(?:127\.0\.0\.1|localhost):[0-9]+/',f'jdbc:mysql://127.0.0.1:{database_port}/',value)
        value=re.sub(r'([?&]serverRSAPublicKeyFile=)[^&]*',lambda m:m[1]+urllib.parse.quote((p/'own-mysql-public-key.pem').as_posix(),safe=''),value)
        return value
    if side=='platform':
        values.update({'spring.datasource.host':'127.0.0.1','spring.datasource.port':str(database_port),'spring.datasource.username':'root','spring.datasource.password':database_password,'spring.redis.host':'127.0.0.1','spring.redis.port':str(redis_port),'spring.redis.password':redis_password,'spring.redis.database':'0'})
        for k in list(values):
            if k.startswith('spring.datasource.') and ('url' in k):values[k]=jdbc(values[k])
        base='config.file-storage.minio[0].'
        values[base+'access-key']=object_access;values[base+'secret-key']=object_secret
        old=urllib.parse.urlsplit(values[base+'end-point']);new=f'http://127.0.0.1:{object_port}'
        if old.hostname!='127.0.0.1':raise ValueError('PREPARED_OWNED_OBJECT_ENDPOINT_REQUIRED')
        previous=old.scheme+'://'+old.netloc
        for k in list(values):
            if k.startswith(base):values[k]=values[k].replace(previous,new)
    else:
        old_base=next(v.split('=',1)[1] for v in spec['businessArguments'] if v.startswith('-Down.internal.platform.base='))
        if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{4,5}',old_base):raise ValueError('PREPARED_OWNED_PLATFORM_BASE_REQUIRED')
        for k in list(values):values[k]=values[k].replace(old_base,f'http://127.0.0.1:{platform_port}')
        values.update({'spring.data.redis.host':'127.0.0.1','spring.data.redis.port':str(redis_port),'spring.data.redis.password':redis_password,'spring.data.redis.database':'0','minio.url':'127.0.0.1','minio.port':str(object_port),'minio.secure':'false','minio.accessKey':object_access,'minio.secretKey':object_secret})
        for name in ['master','tow']:
            base='spring.datasource.dynamic.datasource.'+name+'.'
            values[base+'url']=jdbc(values[base+'url']);values[base+'username']='root';values[base+'password']=database_password
    values['server.address']='127.0.0.1';values['server.port']='0'
    overrides={'own.candidate.root':root.as_posix(),'own.server.lifecycle':'persistent','own.server.owner':run_owner,'own.expected.database.uuid':database_uuid,'own.expected.database.port':str(database_port),'own.expected.redis.port':str(redis_port),'own.internal.object-store.base':f'http://127.0.0.1:{object_port}','own.allowed.loopback.ports':','.join(map(str,ports)),'spring.config.location':(root/'application.properties').as_uri()}
    if side=='platform':overrides.update({'own.platform.data.owner':platform_data_owner,'own.platform.data.root':(app/'UserData/TianjinOriginalPlatform').as_posix()})
    else:overrides['own.internal.platform.base']=f'http://127.0.0.1:{platform_port}'
    omit={'own.candidate.maximum-seconds','own.platform.file-probe.owner','own.platform.file-probe.recover','own.object-store.probe.owner','own.joint.root','own.startup.observation','own.startup.bean.definitions','own.startup.lifecycle.directory'}
    result=[]
    for arg in spec[side+'Arguments']:
        if arg.startswith('-D'):
            key=arg[2:].split('=',1)[0]
            if key in overrides or key in omit:continue
        result.append(render(arg))
    result[0:0]=['-D'+k+'='+v for k,v in overrides.items()]
    return {'configuration':values,'properties':properties_ascii(values),'arguments':result,'side':side,'runtime':root.as_posix(),'containsPrivateValues':True}
