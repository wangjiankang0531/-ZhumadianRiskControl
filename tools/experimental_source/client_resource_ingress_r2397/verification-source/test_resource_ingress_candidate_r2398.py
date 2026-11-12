"""Qualify exact route generation/config assembly and actual nginx syntax only."""
from pathlib import Path
from types import SimpleNamespace
import ast,hashlib,importlib.util,itertools,json,re,subprocess,sys,tempfile

R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
C=A/'tools/experimental_source/client_resource_ingress_r2397';P=C/'package'
OLD=A/'tools/experimental_source/client_resource_worker_r2369/package'
Q=Path(tempfile.gettempdir())/'xnby-resource-ingress-r2398'


def need(value,code):
    if not value:raise ValueError(code)
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    assert not Q.exists();Q.mkdir()
    before=sha(OLD/'package-manifest.json');sys.path.insert(0,str(P))
    from tools.layer_sync_supervisor import verify_package
    record=json.loads((C/'prepared.json').read_bytes());pin=record['packageManifestSHA256']
    assert len(verify_package(P,pin)['inputs'])==44
    new=load('new_resources_route',P/'tools/layer_sync_gateway_transaction.py')
    old=load('old_resources_route',OLD/'tools/layer_sync_gateway_transaction.py')
    base=b'daemon off;\nmaster_process on;\nworker_processes 1;\nevents{worker_connections 32;}\nhttp{\n server{\n listen 127.0.0.1:18974;\n location ^~ /zhumadian/api/serv/ {return 503;}\n location / {return 404;}\n }\n}\n'
    checks=[]
    def check(value,label):
        assert value,label;checks.append(label)
    def rejects(call,label,code):
        try:call()
        except ValueError as e:check(str(e)==code,label)
        else:raise AssertionError(label+'_ACCEPTED')
    for flags in itertools.product((False,True),repeat=4):
        kwargs=dict(zip(['project_files','project_scenes','project_models','local_gis'],flags))
        prior=old.route_candidate(base,18973,'a'*32,**kwargs)
        check(new.route_candidate(base,18973,'a'*32,**kwargs)==prior,'default-off-original-byte-identical-'+''.join(str(int(x))for x in flags))
    enabled=new.route_candidate(base,18973,'a'*32,local_gis=True,client_resources=True)
    text=enabled.decode()
    check(text.count('location = /zhumadian/api/spatial-sync/v2/client-resources/')==2,'only-two-exact-resource-POST-locations')
    for route in ['grants','grants/consume']:
        block=re.search(r'location = /zhumadian/api/spatial-sync/v2/client-resources/'+route+r' \{([^}]+)\}',text).group(1)
        check('client_max_body_size 8k;'in block and 'limit_except POST'in block and 'proxy_next_upstream off;'in block and 'proxy_intercept_errors off;'in block,'bounded-no-replay-no-error-rewrite-'+route.replace('/','-'))
    for value in [None,0,1,'true',[],{}]:
        rejects(lambda v=value:new.route_candidate(base,18973,'a'*32,client_resources=v),'strict-resource-flag-'+repr(value),'EXPLICIT_CLIENT_RESOURCE_MODE_REQUIRED')
    support=(C/'original_spatial_sync_release_support.py').read_text('utf-8');tree=ast.parse(support)
    validator=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='checked_client_resources')
    ns={'need':need,'re':re};exec(compile(ast.Module(body=[validator],type_ignores=[]),'actual_product_resource_validator','exec'),ns)
    validate=ns['checked_client_resources'];source={'sourceRuntimeIdentity':'a'*64,'sourceIndexIdentity':'b'*64,'budgetMiB':2048}
    row={'installationIdentity':'c'*64,**{k:source[k]for k in ['sourceRuntimeIdentity','sourceIndexIdentity']}}
    good={'schema':'xnby.client-resources.server-settings.v1','allowedInstallations':[row]}
    check(validate({},[source])is None,'absent-resource-settings-no-activation')
    check(validate({'clientResources':good},[source])==good,'exact-declared-project-installation-accepted')
    for value in [None,True,{},dict(good,unknown=True)]:
        rejects(lambda v=value:validate({'clientResources':v},[source]),'resource-settings-invalid-'+repr(value),'EXACT_CLIENT_RESOURCE_SETTINGS_REQUIRED')
    for rows in [[],[row]*17]:
        rejects(lambda v=rows:validate({'clientResources':dict(good,allowedInstallations=v)},[source]),'bounded-installations-'+str(len(rows)),'BOUNDED_CLIENT_RESOURCE_INSTALLATIONS_REQUIRED')
    rejects(lambda:validate({'clientResources':dict(good,allowedInstallations=[row,row])},[source]),'duplicate-manager-installation-refused','DUPLICATE_CLIENT_RESOURCE_INSTALLATION_REFUSED')
    rejects(lambda:validate({'clientResources':dict(good,allowedInstallations=[dict(row,sourceIndexIdentity='d'*64)])},[source]),'manager-source-not-in-project-refused','CLIENT_RESOURCE_SOURCE_NOT_DECLARED_FOR_PROJECT')
    rejects(lambda:validate({'clientResources':dict(good,allowedInstallations=[dict(row,installationIdentity=True)])},[source]),'boolean-manager-identity-refused','EXACT_CLIENT_RESOURCE_INSTALLATION_REQUIRED')
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='SpatialRuntime')
    start=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='start')
    begin=next(i for i,n in enumerate(start.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='worker_config'for t in n.targets))
    end=next(i for i,n in enumerate(start.body)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Attribute)and t.attr=='config_raw'for t in n.targets))
    block=ast.Module(body=start.body[begin:end],type_ignores=[])
    for optional in [None,good]:
        settings={'sceneLibrary':None,'sceneModels':None,'localGIS':{'schema':'xnby.local-gis.server-settings.v1','allowedSources':[source]},'clientResources':optional}
        runtime=SimpleNamespace(platform_port=18971,gateway_port=18974,settings=settings)
        env={'self':runtime,'port':18973,'value':{'access':{},'projectFilesRoot':'D:/Temp/own-QA'}}
        exec(compile(block,'actual_product_worker_config_assembly','exec'),env)
        output=env['worker_config']
        check(('clientResources'in output)==(optional is not None)and output.get('clientResources')==optional,'actual-worker-config-optional-copy-'+str(optional is not None))
    configure=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='configure_gateway')
    script_assign=next(n for n in configure.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='script'for t in n.targets))
    script=ast.literal_eval(script_assign.value);ast.parse(script)
    for flag in ['0','1']:
        child=subprocess.Popen([sys.executable,'-I','-B','-c',script,str(P),pin,'18973','a'*32,'0','0',flag],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        out,err=child.communicate(base);check(child.returncode==0,'actual-pinned-44-source-route-inspector-exit-zero-'+flag)
        check((b'v2/client-resources/grants'in out)==(flag=='1'),'actual-controller-argv-enables-exact-resource-routes-'+flag)
    nginx=R/'_g/Application/runtime/nginx/nginx.exe'
    check(sha(nginx)=='c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44','exact-existing-original-nginx-image')
    (Q/'logs').mkdir();config=Q/'nginx.conf';config.write_bytes(enabled)
    child=subprocess.Popen([str(nginx),'-p',str(Q)+'/', '-c',str(config),'-t'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    stdout,stderr=child.communicate();check(child.returncode==0,'actual-original-nginx-generated-resource-route-syntax')
    check(sha(OLD/'package-manifest.json')==before,'previous-worker44-package-not-modified')
    result={'passed':True,'checks':checks,'count':len(checks),'packageManifestSHA256':pin,
        'actualNginxSyntaxExitCode':child.returncode,'nginxListenerOrApplicationOrDatabaseNotStarted':True,
        'fullOriginalIISLifecycleAndNormalLoginStillPending':True,'R51AndPublicNotChanged':True}
    (Q/'verification.json').write_text(json.dumps(result,indent=2)+'\n','utf-8');print(json.dumps({k:v for k,v in result.items()if k!='checks'}))


if __name__=='__main__':main()
