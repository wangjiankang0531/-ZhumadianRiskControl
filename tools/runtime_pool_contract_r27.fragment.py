def runtime_pool_declared(release):
    controls=release['controllerFiles']
    if R27_POOL_FIELD not in release:
        require(controls.get(R23_CONTROLLER)!=R27_POOL_PINS[R23_CONTROLLER]['sha256']
                and controls.get(R24_PARAMETER)!=R27_POOL_PINS[R24_PARAMETER]['sha256'], 'EXPLICIT_POOL_POLICY_REQUIRED')
        return False
    require(release[R27_POOL_FIELD]==R27_POOL_POLICY,'EXACT_POOL_POLICY_REQUIRED')
    require(all(controls.get(n)==p['sha256']for n,p in R27_POOL_PINS.items()),'EXACT_POOL_CONTROL_DECLARATIONS_REQUIRED')
    return True

def workflow_contract_for(release):
    return R27_POOL_WORKFLOW_CONTRACT if runtime_pool_declared(release)else R24_WORKFLOW_CONTRACT

def parameter_pin_for(release):
    return R27_POOL_PINS[R24_PARAMETER]if runtime_pool_declared(release)else R24_PARAMETER_PIN

def controller_pin_for(release):
    return R27_POOL_PINS[R23_CONTROLLER]['sha256']if runtime_pool_declared(release)else R23_CONTROLLER_SHA

def runtime_pool_bundle_contract(app,bundle,plan,old,release,payload):
    if not runtime_pool_declared(release):
        require(R27_POOL_FIELD not in old,'RETAINED_POOL_POLICY_CANNOT_BE_DROPPED')
        return False
    fresh=R27_POOL_FIELD not in old
    prior={R23_CONTROLLER:R23_CONTROLLER_SHA,R24_PARAMETER:R24_PARAMETER_PIN['sha256']}if fresh else{n:p['sha256']for n,p in R27_POOL_PINS.items()}
    if not fresh:require(runtime_pool_declared(old),'EXACT_RETAINED_POOL_POLICY_REQUIRED')
    require(all(old['controllerFiles'].get(n)==p for n,p in prior.items()),'EXACT_PREVIOUS_POOL_CONTROL_SOURCES_REQUIRED')
    require(old.get(R24_WORKFLOW_FIELD)==workflow_contract_for(old),'POOL_REQUIRES_PREVIOUS_WORKFLOW_DESCRIPTOR')
    allowed=set(R27_POOL_PINS)|{'tools/original_public_test_update.py'}
    require({n:p for n,p in release['controllerFiles'].items()if n not in allowed}=={n:p for n,p in old['controllerFiles'].items()if n not in allowed},'POOL_OTHER_CONTROLLERS_MUST_BE_RETAINED')
    if fresh:require(set(R27_POOL_PINS).issubset(plan['files']),'COMPLETE_POOL_CONTROL_TRANSPORT_REQUIRED')
    previous=read(check_file(app,'payload-manifest.json',old['payloadManifestSHA256']))
    retained=lambda rows:{n:p for n,p in rows.items()if not n.startswith('frontend/emergency_pc/')}
    require(retained(previous['files'])==retained(payload['files']),'POOL_NON_EMERGENCY_PAYLOAD_MUST_BE_RETAINED')
    for n,pin in R27_POOL_PINS.items():
        if n in plan['files']:require(plan['files'][n]=={'bytes':pin['bytes'],'SHA256':pin['sha256']},'EXACT_POOL_TRANSPORT_PIN_REQUIRED')
        check_file(bundle/'payload'if n in plan['files']else app,n,pin['sha256'],pin['bytes'])
    return True

def runtime_pool_ready(app,row):
    release=read(regular(app,'release-manifest.json'))
    if not runtime_pool_declared(release):return None
    require(workflow_ready(app,row)is not None,'POOL_RETAINED_WORKFLOW_RUNTIME_REQUIRED')
    for n,pin in R27_POOL_PINS.items():check_file(app,n,pin['sha256'],pin['bytes'])
    run=regular(app,Path(row['run']).absolute().relative_to(app).as_posix())
    require(run.parent==app/'UserData/OriginalServer/runs'and re.fullmatch(r'j[1-9][0-9]{0,3}',run.name),'OWNED_POOL_RUNTIME_REQUIRED')
    report=regular(run,'connection-budget.json');require(report.is_file()and report.stat().st_size<=16384,'BOUNDED_POOL_REPORT_REQUIRED');value=read(report)
    require(set(value)=={'policy','datasources','maximumPoolConnections','reservedConnections','mysqlMaxConnections'}and value['policy']==R27_POOL_POLICY,'EXACT_POOL_REPORT_FIELDS_REQUIRED')
    rows=value['datasources'];require(isinstance(rows,list)and 2<=len(rows)<=32,'BOUNDED_POOL_DATASOURCE_REPORT_REQUIRED');seen=set();total=0
    for item in rows:
        require(isinstance(item,dict)and set(item)=={'side','name','hikariMaximum','hikariMinimumIdle','hikariConnectionTimeoutMillis','druidMaximum','maximumBudget'},'EXACT_POOL_DATASOURCE_FIELDS_REQUIRED')
        require(item['side']in ['platform','business']and isinstance(item['name'],str)and re.fullmatch('[A-Za-z0-9_-]{1,40}',item['name']),'POOL_DATASOURCE_IDENTITY_REQUIRED')
        key=(item['side'],item['name']);require(key not in seen,'DUPLICATE_POOL_DATASOURCE_REFUSED');seen.add(key)
        require(all(type(item[k])is int for k in ['hikariMaximum','hikariMinimumIdle','hikariConnectionTimeoutMillis','druidMaximum','maximumBudget']),'POOL_REPORT_INTEGER_REQUIRED')
        require(1<=item['hikariMaximum']<=128 and 0<=item['hikariMinimumIdle']<=item['hikariMaximum']and 250<=item['hikariConnectionTimeoutMillis']<=300000 and 1<=item['druidMaximum']<=128,'POOL_REPORT_BOUNDS_REQUIRED')
        require(item['maximumBudget']==max(item['hikariMaximum'],item['druidMaximum']),'POOL_DATASOURCE_BUDGET_MISMATCH');total+=item['maximumBudget']
    require({x[0]for x in seen}=={'platform','business'},'BOTH_COMPONENT_POOL_REPORTS_REQUIRED')
    require(type(value['maximumPoolConnections'])is int and value['maximumPoolConnections']==total and type(value['reservedConnections'])is int and value['reservedConnections']==12 and type(value['mysqlMaxConnections'])is int and value['mysqlMaxConnections']==max(24,total+12)<=256,'POOL_TOTAL_BUDGET_MISMATCH')
    return {'poolPolicyAndExactRuntimeSourcesMatched':True,'datasources':len(rows),'mysqlMaxConnections':value['mysqlMaxConnections'],'accountsSessionsBusinessRowsOrCredentialsRead':False}
