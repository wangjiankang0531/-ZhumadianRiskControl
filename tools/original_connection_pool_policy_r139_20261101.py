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
