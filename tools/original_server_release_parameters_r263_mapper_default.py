"""Render frozen private original-system settings for distinct owned server ports.

No I/O, database connection, process launch, authentication, or default secrets.
"""
from pathlib import Path
import re,urllib.parse,uuid,json,hashlib

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

def runtime_temporary_path(application, runtime, side):
    app, run = Path(application), Path(runtime)
    if side not in ('platform', 'business'):
        raise ValueError('EXPLICIT_COMPONENT_REQUIRED')
    if app == Path('C:/inetpub/wwwroot/Zhumadian/Application'):
        if side == 'platform':
            if run.parent != app/'UserData/TianjinOriginalPlatform/runs' or not re.fullmatch(r'j[1-9][0-9]{0,3}', run.name):
                raise ValueError('OWNED_SERVER_RUNTIME_LAYOUT_REQUIRED')
            return app/'UserData/TianjinOriginalPlatform'/('t'+run.name[1:])
        if run.name != 'b' or run.parent.parent != app/'UserData/OriginalServer/runs' or not re.fullmatch(r'j[1-9][0-9]{0,3}', run.parent.name):
            raise ValueError('OWNED_SERVER_RUNTIME_LAYOUT_REQUIRED')
        return run/'t'
    # Keep installed QA layouts bounded when the monotone run counter gains digits.
    # The controller still validates all paths and creates these owned directories.
    if app.is_absolute():
        if side == 'platform' and run.parent == app/'UserData/TianjinOriginalPlatform/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name):
            return app/'UserData/TianjinOriginalPlatform'/('t'+run.name[1:])
        if side == 'business' and run.name == 'b' and run.parent.parent == app/'UserData/OriginalServer/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}', run.parent.name):
            return run/'t'
    return run/'tmp'

"""Pure numeric budgets for declared pools and the original JNPF generated primary."""
import re

CONNECTION_POOL_POLICY = {'revision':'pool-family-budget-v2','mysqlMinimum':24,'mysqlMaximum':256,'reservedConnections':12,'maximumSinglePool':128}

def _pool_integer(values,prefix,aliases,default=None,minimum=0,maximum=300000):
    selected=[]
    for alias in aliases:
        key=prefix+alias
        if key not in values:continue
        text=values[key]
        if not isinstance(text,str) or not re.fullmatch(r'[0-9]{1,6}',text):raise ValueError('POOL_INTEGER_REQUIRED')
        number=int(text)
        if not minimum<=number<=maximum:raise ValueError('POOL_INTEGER_OUT_OF_BOUNDS')
        selected.append(number)
    if len(set(selected))>1:raise ValueError('CONFLICTING_POOL_PROPERTY_ALIASES')
    return selected[0] if selected else default

def _pool_name(values,keys,default=None):
    selected=[values[k] for k in keys if k in values]
    if any(not isinstance(v,str) or not re.fullmatch('[A-Za-z0-9_-]{1,40}',v) for v in selected):raise ValueError('BOUNDED_POOL_NAME_REQUIRED')
    if len(set(selected))>1:raise ValueError('CONFLICTING_POOL_NAME_ALIASES')
    return selected[0] if selected else default

def _pool_layout(values,side):
    stem='spring.datasource.dynamic.datasource.'
    keys=[k for k in values if isinstance(k,str) and k.startswith(stem)]
    if any('.' not in k[len(stem):] for k in keys):raise ValueError('BOUNDED_DYNAMIC_POOL_LAYOUT_REQUIRED')
    names=sorted({k[len(stem):].split('.',1)[0] for k in keys})
    if any(not re.fullmatch('[A-Za-z0-9_-]{1,40}',n) for n in names):raise ValueError('BOUNDED_DYNAMIC_POOL_LAYOUT_REQUIRED')
    for name in names:
        url=values.get(stem+name+'.url')
        if not isinstance(url,str) or not url.strip():raise ValueError('EXPLICIT_POOL_URL_REQUIRED')
    primary=_pool_name(values,['spring.datasource.dynamic.primary'],'master')
    # MybatisPlusConfig.initDynamicDataSource recognizes an exact key, a primary_
    # group, or a DataSourceProperty.poolName alias before adding its own primary.
    covered=any(n==primary or n.startswith(primary+'_') or
        _pool_name(values,[stem+n+'.pool-name',stem+n+'.poolName'])==primary for n in names)
    implicit=None
    if side=='platform' and not covered:
        if not all(isinstance(values.get('spring.datasource.'+k),str) and values['spring.datasource.'+k].strip()
                   for k in ['host','db-name']):raise ValueError('ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED')
        implicit=primary;names=sorted([*names,primary])
    if not 1<=len(names)<=16:raise ValueError('BOUNDED_DYNAMIC_POOL_LAYOUT_REQUIRED')
    return names,implicit

def connection_pool_budget(spec):
    configuration=spec.get('configuration')
    if not isinstance(configuration,dict):raise ValueError('EXPLICIT_POOL_CONFIGURATION_REQUIRED')
    rows=[]
    for side in ['platform','business']:
        values=configuration.get(side)
        if not isinstance(values,dict):raise ValueError('BOTH_COMPONENT_POOL_CONFIGURATIONS_REQUIRED')
        names,implicit=_pool_layout(values,side)
        stem='spring.datasource.dynamic.';druid=stem+'druid.';hikari=stem+'hikari.'
        dmax=_pool_integer(values,druid,['max-active','maxActive'],None,1,128)
        dmin=_pool_integer(values,druid,['min-idle','minIdle'],None,0,128)
        dwait=_pool_integer(values,druid,['max-wait','maxWait'],None)
        hmax=_pool_integer(values,hikari,['max-pool-size','maximum-pool-size','maxPoolSize','maximumPoolSize'],None,1,128)
        hmin=_pool_integer(values,hikari,['min-idle','minimum-idle','minIdle','minimumIdle'],None,0,128)
        hwait=_pool_integer(values,hikari,['connection-timeout','connectionTimeout'],None,250)
        for name in names:
            base=stem+'datasource.'+name+'.';pd=base+'druid.';ph=base+'hikari.'
            # Generated DataSourceProperty has no per-name Hikari binder entry.
            # It receives the original global settings through the creator.
            local={} if name==implicit else values
            pdmax=_pool_integer(local,pd,['max-active','maxActive'],None,1,128)
            pdmin=_pool_integer(local,pd,['min-idle','minIdle'],None,0,128)
            pdwait=_pool_integer(local,pd,['max-wait','maxWait'],None)
            effective_dmax=pdmax if pdmax is not None else(dmax if dmax is not None else 8)
            effective_dmin=pdmin if pdmin is not None else(dmin if dmin is not None else 0)
            if effective_dmin>effective_dmax:raise ValueError('DRUID_MINIMUM_EXCEEDS_MAXIMUM')
            effective_hmax=_pool_integer(local,ph,['max-pool-size','maximum-pool-size','maxPoolSize','maximumPoolSize'],None,1,128)
            if effective_hmax is None:effective_hmax=next((v for v in [hmax,pdmax,dmax] if v is not None),10)
            effective_hmin=_pool_integer(local,ph,['min-idle','minimum-idle','minIdle','minimumIdle'],None,0,128)
            if effective_hmin is None:effective_hmin=next((v for v in [hmin,pdmin,dmin] if v is not None),effective_hmax)
            if effective_hmin>effective_hmax:raise ValueError('POOL_MINIMUM_EXCEEDS_MAXIMUM')
            effective_hwait=_pool_integer(local,ph,['connection-timeout','connectionTimeout'],None,250)
            if effective_hwait is None:effective_hwait=next((v for v in [hwait,pdwait,dwait] if v is not None and v>=250),30000)
            rows.append({'side':side,'name':name,'hikariMaximum':effective_hmax,'hikariMinimumIdle':effective_hmin,'hikariConnectionTimeoutMillis':effective_hwait,'druidMaximum':effective_dmax,'maximumBudget':max(effective_dmax,effective_hmax)})
    total=sum(row['maximumBudget'] for row in rows)
    maximum=max(CONNECTION_POOL_POLICY['mysqlMinimum'],total+CONNECTION_POOL_POLICY['reservedConnections'])
    if maximum>CONNECTION_POOL_POLICY['mysqlMaximum']:raise ValueError('CONNECTION_BUDGET_EXCEEDS_BOUNDED_SERVER_LIMIT')
    return {'policy':dict(CONNECTION_POOL_POLICY),'datasources':rows,'maximumPoolConnections':total,'reservedConnections':CONNECTION_POOL_POLICY['reservedConnections'],'mysqlMaxConnections':maximum}

def runtime_pool_properties(spec,side):
    if side not in ['platform','business']:raise ValueError('EXPLICIT_POOL_COMPONENT_REQUIRED')
    plan=connection_pool_budget(spec);_,implicit=_pool_layout(spec['configuration'][side],side);values={}
    for row in plan['datasources']:
        if row['side']!=side:continue
        base='spring.datasource.dynamic.'+('hikari.' if row['name']==implicit else 'datasource.'+row['name']+'.hikari.')
        for key,value in [('max-pool-size',row['hikariMaximum']),('min-idle',row['hikariMinimumIdle']),('connection-timeout',row['hikariConnectionTimeoutMillis'])]:values[base+key]=str(value)
    return values


def original_business_mapper_defaults(values):
    """Resolve original XML resources when no explicit MybatisPlus location is configured."""
    explicit = any(re.fullmatch(r'mybatisplusmapperlocations(?:\[[0-9]+\])?', re.sub(r'[-_.]', '', key).lower()) for key in values)
    if not explicit:
        values['mybatis-plus.mapper-locations'] = 'classpath*:/xml/**/*.xml'

def materialize(spec,*,side,application,platform_run,business_run,platform_data_owner,run_owner,database_uuid,database_port,redis_port,object_port,database_password,redis_password,object_access,object_secret,platform_port=None,business_port=None,callback_pins=None):
    if side not in ('platform','business'):raise ValueError('EXPLICIT_COMPONENT_REQUIRED')
    for value in (platform_data_owner,run_owner,database_uuid):checked_uuid(value)
    if callback_pins is not None and business_port is None:raise ValueError('CALLBACK_BUSINESS_PORT_REQUIRED')
    if business_port is not None and (type(business_port)!=int or not 1024<=business_port<=65535 or business_port in (database_port,redis_port,object_port,platform_port)):raise ValueError('DISTINCT_OWN_CALLBACK_BUSINESS_PORT_REQUIRED')
    if side=='platform' and business_port is not None and callback_pins is None:raise ValueError('EXPLICIT_CALLBACK_ROUTE_PINS_REQUIRED')
    ports=[database_port,redis_port,object_port]+([] if side=='platform' else [platform_port])
    if side=='platform' and business_port is not None:ports.append(business_port)
    if any(type(v)!=int or not 1024<=v<=65535 for v in ports) or len(set(ports))!=len(ports):raise ValueError('DISTINCT_OWNED_LOOPBACK_PORTS_REQUIRED')
    for secret in (database_password,redis_password,object_access,object_secret):
        if not isinstance(secret,str) or not secret or any(c in secret for c in '\r\n\0'):raise ValueError('EXPLICIT_PRIVATE_RUNTIME_SECRET_REQUIRED')
    app=Path(application);p=Path(platform_run);b=Path(business_run)
    if any('..' in q.parts for q in (app,p,b)) or not app.is_absolute() or app.name!='Application' or p.parent!=app/'UserData/TianjinOriginalPlatform/runs' or not b.is_relative_to(app/'UserData') or not re.fullmatch(r'j[1-9][0-9]{0,3}',p.name):raise ValueError('OWNED_SERVER_RUNTIME_LAYOUT_REQUIRED')
    platform_tmp=runtime_temporary_path(app,p,'platform');business_tmp=runtime_temporary_path(app,b,'business')
    if len(str(platform_tmp))>80 or len(str(business_tmp))>80:raise ValueError('SHORT_WINDOWS_RUNTIME_PATH_REQUIRED')
    tokens={'APP':app.as_posix(),'PLATFORM_RUN':p.as_posix(),'BUSINESS_RUN':b.as_posix(),'PLATFORM_DATA':(app/'UserData/TianjinOriginalPlatform').as_posix()}
    def render(value):
        for key,new in tokens.items():value=value.replace('${'+key+'}',new)
        if any('${'+key+'}' in value for key in tokens):raise ValueError('UNRENDERED_RUNTIME_PATH')
        return value
    values={k:render(v) for k,v in spec['configuration'][side].items()}
    if side=='business':original_business_mapper_defaults(values)
    values.update(runtime_pool_properties(spec,side))
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
    values['server.address']='127.0.0.1';values['server.port']=str(business_port) if side=='business' and business_port is not None else '0'
    callback_bytes=None
    overrides={'java.io.tmpdir':(platform_tmp if side=='platform' else business_tmp).as_posix(),'own.candidate.root':root.as_posix(),'own.server.lifecycle':'persistent','own.server.owner':run_owner,'own.expected.database.uuid':database_uuid,'own.expected.database.port':str(database_port),'own.expected.redis.port':str(redis_port),'own.internal.object-store.base':f'http://127.0.0.1:{object_port}','own.allowed.loopback.ports':','.join(map(str,ports)),'spring.config.location':(root/'application.properties').as_uri()}
    if side=='platform':overrides.update({'own.platform.data.owner':platform_data_owner,'own.platform.data.root':(app/'UserData/TianjinOriginalPlatform').as_posix()})
    else:overrides['own.internal.platform.base']=f'http://127.0.0.1:{platform_port}'
    if side=='platform' and business_port is not None:
        if not isinstance(callback_pins,dict) or len(callback_pins)!=7:raise ValueError('EXACT_SEVEN_CALLBACK_ROUTE_PINS_REQUIRED')
        selected={}
        for ident,pin in callback_pins.items():
            if not isinstance(ident,str) or not re.fullmatch('[0-9a-f]{64}',ident) or not isinstance(pin,dict):raise ValueError('CALLBACK_ROUTE_PIN_SHAPE')
            value={key:pin.get(key) for key in ('hostSHA256','pathSHA256','configSHA256','port')}
            if any(not isinstance(value[key],str) or not re.fullmatch('[0-9a-f]{64}',value[key]) for key in ('hostSHA256','pathSHA256','configSHA256')) or type(value['port'])!=int or not 1024<=value['port']<=65535:raise ValueError('CALLBACK_ROUTE_PIN_SHAPE')
            selected[ident]=value
        callback_bytes=(json.dumps(selected,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')
        overrides.update({'own.internal.business.base':f'http://127.0.0.1:{business_port}','own.callback.routes.path':(p/'callback-route-pins.json').as_posix(),'own.callback.routes.sha256':hashlib.sha256(callback_bytes).hexdigest()})
        initializer='xnby.platform.OriginalCallbackRoutesInitializer'
        current=values.get('context.initializer.classes','').split(',')
        values['context.initializer.classes']=','.join([item for item in current if item and item!=initializer]+[initializer])
    if side=='business' and business_port is not None:overrides.update({'server.port':str(business_port),'server.address':'127.0.0.1','own.expected.business.listen.port':str(business_port)})
    omit={'own.expected.business.listen.port','own.internal.business.base','own.callback.routes.path','own.callback.routes.sha256','own.candidate.maximum-seconds','own.platform.file-probe.owner','own.platform.file-probe.recover','own.object-store.probe.owner','own.joint.root','own.startup.observation','own.startup.bean.definitions','own.startup.lifecycle.directory'}
    result=[]
    for arg in spec[side+'Arguments']:
        if arg.startswith('-D'):
            key=arg[2:].split('=',1)[0]
            if key in overrides or key in omit:continue
        result.append(render(arg))
    result[0:0]=['-D'+k+'='+v for k,v in overrides.items()]
    rendered={'configuration':values,'properties':properties_ascii(values),'arguments':result,'side':side,'runtime':root.as_posix(),'containsPrivateValues':True}
    if callback_bytes is not None:rendered['callbackRoutingPinsBytes']=callback_bytes
    return rendered
