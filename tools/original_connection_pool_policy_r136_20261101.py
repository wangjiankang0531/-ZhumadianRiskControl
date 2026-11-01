"""Resolve bounded numeric pool settings without changing or returning private configuration."""
import re

CONNECTION_POOL_POLICY = {'revision':'pool-family-budget-v1','mysqlMinimum':24,'mysqlMaximum':256,'reservedConnections':12,'maximumSinglePool':128}

def _pool_integer(values,prefix,aliases,default=None,minimum=0,maximum=300000):
    selected=[]
    for alias in aliases:
        key=prefix+alias
        if key not in values:continue
        text=values[key]
        if not isinstance(text,str)or not re.fullmatch(r'[0-9]{1,6}',text):raise ValueError('POOL_INTEGER_REQUIRED')
        number=int(text)
        if not minimum<=number<=maximum:raise ValueError('POOL_INTEGER_OUT_OF_BOUNDS')
        selected.append(number)
    if len(set(selected))>1:raise ValueError('CONFLICTING_POOL_PROPERTY_ALIASES')
    return selected[0]if selected else default

def connection_pool_budget(spec):
    configuration=spec.get('configuration')
    if not isinstance(configuration,dict):raise ValueError('EXPLICIT_POOL_CONFIGURATION_REQUIRED')
    rows=[]
    for side in ['platform','business']:
        values=configuration.get(side)
        if not isinstance(values,dict):raise ValueError('BOTH_COMPONENT_POOL_CONFIGURATIONS_REQUIRED')
        stem='spring.datasource.dynamic.'
        names=sorted({k[len(stem+'datasource.'):-len('.url')]for k in values if k.startswith(stem+'datasource.')and k.endswith('.url')})
        if not 1<=len(names)<=16 or any(not re.fullmatch('[A-Za-z0-9_-]{1,40}',n)for n in names):raise ValueError('BOUNDED_DYNAMIC_POOL_LAYOUT_REQUIRED')
        druid=stem+'druid.';hikari=stem+'hikari.'
        dmax=_pool_integer(values,druid,['max-active','maxActive'],None,1,128)
        dmin=_pool_integer(values,druid,['min-idle','minIdle'],None,0,128)
        dwait=_pool_integer(values,druid,['max-wait','maxWait'],None)
        hmax=_pool_integer(values,hikari,['max-pool-size','maximum-pool-size','maxPoolSize','maximumPoolSize'],None,1,128)
        hmin=_pool_integer(values,hikari,['min-idle','minimum-idle','minIdle','minimumIdle'],None,0,128)
        hwait=_pool_integer(values,hikari,['connection-timeout','connectionTimeout'],None,250)
        for name in names:
            base=stem+'datasource.'+name+'.';pd=base+'druid.';ph=base+'hikari.'
            pdmax=_pool_integer(values,pd,['max-active','maxActive'],None,1,128)
            pdmin=_pool_integer(values,pd,['min-idle','minIdle'],None,0,128)
            pdwait=_pool_integer(values,pd,['max-wait','maxWait'],None)
            effective_dmax=pdmax if pdmax is not None else(dmax if dmax is not None else 8)
            effective_hmax=_pool_integer(values,ph,['max-pool-size','maximum-pool-size','maxPoolSize','maximumPoolSize'],None,1,128)
            if effective_hmax is None:effective_hmax=next((v for v in [hmax,pdmax,dmax]if v is not None),10)
            effective_hmin=_pool_integer(values,ph,['min-idle','minimum-idle','minIdle','minimumIdle'],None,0,128)
            if effective_hmin is None:effective_hmin=next((v for v in [hmin,pdmin,dmin]if v is not None),effective_hmax)
            if effective_hmin>effective_hmax:raise ValueError('POOL_MINIMUM_EXCEEDS_MAXIMUM')
            effective_hwait=_pool_integer(values,ph,['connection-timeout','connectionTimeout'],None,250)
            if effective_hwait is None:effective_hwait=next((v for v in [hwait,pdwait,dwait]if v is not None and v>=250),30000)
            rows.append({'side':side,'name':name,'hikariMaximum':effective_hmax,'hikariMinimumIdle':effective_hmin,'hikariConnectionTimeoutMillis':effective_hwait,'druidMaximum':effective_dmax,'maximumBudget':max(effective_dmax,effective_hmax)})
    total=sum(row['maximumBudget']for row in rows)
    maximum=max(CONNECTION_POOL_POLICY['mysqlMinimum'],total+CONNECTION_POOL_POLICY['reservedConnections'])
    if maximum>CONNECTION_POOL_POLICY['mysqlMaximum']:raise ValueError('CONNECTION_BUDGET_EXCEEDS_BOUNDED_SERVER_LIMIT')
    return {'policy':dict(CONNECTION_POOL_POLICY),'datasources':rows,'maximumPoolConnections':total,'reservedConnections':CONNECTION_POOL_POLICY['reservedConnections'],'mysqlMaxConnections':maximum}

def runtime_pool_properties(spec,side):
    if side not in ['platform','business']:raise ValueError('EXPLICIT_POOL_COMPONENT_REQUIRED')
    plan=connection_pool_budget(spec);values={}
    for row in plan['datasources']:
        if row['side']!=side:continue
        base='spring.datasource.dynamic.datasource.'+row['name']+'.hikari.'
        for key,value in [('max-pool-size',row['hikariMaximum']),('min-idle',row['hikariMinimumIdle']),('connection-timeout',row['hikariConnectionTimeoutMillis'])]:values[base+key]=str(value)
    return values
