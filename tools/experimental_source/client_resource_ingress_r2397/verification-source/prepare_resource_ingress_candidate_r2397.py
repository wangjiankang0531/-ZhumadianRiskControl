"""Compose an independently versioned resource ingress candidate, never install."""
from pathlib import Path
import ast,hashlib,json

R=Path('D:/Project/Zhumadian');A=R/'Application'
OLD=A/'tools/experimental_source/client_resource_worker_r2369/package'
DEST=A/'tools/experimental_source/client_resource_ingress_r2397'
SUPPORT=R/'work/public-same-window-r2330/bundle/payload/tools/original_spatial_sync_release_support.py'


def need(value,code):
    if not value:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def replace_once(source,before,after):
    need(source.count(before)==1,'EXACT_SOURCE_ANCHOR_REQUIRED:'+before[:40]);return source.replace(before,after,1)


VALIDATOR='''def checked_client_resources(value, local_sources):
    """Trusted project allowlist, optional and validated before any startup."""
    item = value.get('clientResources')
    if 'clientResources' not in value:
        return None
    need(isinstance(item, dict) and set(item) == {'schema', 'allowedInstallations'}
         and item['schema'] == 'xnby.client-resources.server-settings.v1', 'EXACT_CLIENT_RESOURCE_SETTINGS_REQUIRED')
    rows = item['allowedInstallations']
    need(isinstance(rows, list) and 1 <= len(rows) <= 16, 'BOUNDED_CLIENT_RESOURCE_INSTALLATIONS_REQUIRED')
    fields = ('installationIdentity', 'sourceRuntimeIdentity', 'sourceIndexIdentity')
    supported = {(r['sourceRuntimeIdentity'], r['sourceIndexIdentity']) for r in local_sources}
    seen = set()
    for row in rows:
        need(isinstance(row, dict) and set(row) == set(fields)
             and all(isinstance(row[k], str) and re.fullmatch('[a-f0-9]{64}', row[k]) for k in fields),
             'EXACT_CLIENT_RESOURCE_INSTALLATION_REQUIRED')
        key = tuple(row[k] for k in fields)
        need(key not in seen, 'DUPLICATE_CLIENT_RESOURCE_INSTALLATION_REFUSED')
        seen.add(key)
        need((row['sourceRuntimeIdentity'], row['sourceIndexIdentity']) in supported,
             'CLIENT_RESOURCE_SOURCE_NOT_DECLARED_FOR_PROJECT')
    return item


'''


def main():
    need(not DEST.exists(),'NEW_VERSIONED_CANDIDATE_REQUIRED')
    old=json.loads((OLD/'package-manifest.json').read_bytes())
    need(digest((OLD/'package-manifest.json').read_bytes())=='e8aca5df66078aecba8414fbfff1e4249ec77a4a898cd55e0411b6d358deb8a6','EXACT_ORIGINAL_44_PACKAGE_REQUIRED')
    files={}
    for name,row in old['inputs'].items():
        raw=(OLD/name).read_bytes();need(len(raw)==row['bytes']and digest(raw)==row['sha256'],'ORIGINAL_44_SOURCE_DRIFT');files[name]=raw
    name='tools/layer_sync_gateway_transaction.py';s=files[name].decode('utf-8')
    s=replace_once(s,'project_models=False,local_gis=False):','project_models=False,local_gis=False,client_resources=False):')
    s=replace_once(s,"    if type(local_gis)is not bool:raise ValueError('EXPLICIT_LOCAL_GIS_MODE_REQUIRED')", "    if type(local_gis)is not bool:raise ValueError('EXPLICIT_LOCAL_GIS_MODE_REQUIRED')\n    if type(client_resources)is not bool:raise ValueError('EXPLICIT_CLIENT_RESOURCE_MODE_REQUIRED')")
    anchor="    if local_gis:routes.extend([('=', 'v2/local-gis/grants','POST'),('=', 'v2/local-gis/grants/consume','POST')])"
    s=replace_once(s,anchor,anchor+"\n    if client_resources:routes.extend([('=', 'v2/client-resources/grants','POST'),('=', 'v2/client-resources/grants/consume','POST')])")
    s=replace_once(s,"'8k' if route.startswith('v2/local-gis/') else '16m'", "'8k' if route.startswith(('v2/local-gis/','v2/client-resources/')) else '16m'")
    files[name]=s.encode();ast.parse(s)
    package=DEST/'package';package.mkdir(parents=True)
    for name,raw in files.items():
        target=package/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    manifest=dict(old,inputs={n:{'bytes':len(raw),'sha256':digest(raw)}for n,raw in files.items()},sourceBytes=sum(map(len,files.values())),
        sourceFiles=44,ingressResourceRoutesCandidate=True,original44PackageManifestSHA256=digest((OLD/'package-manifest.json').read_bytes()))
    (package/'package-manifest.json').write_bytes(encoded(manifest));pin=digest((package/'package-manifest.json').read_bytes())
    s=SUPPORT.read_text('utf-8-sig');base=s
    s=replace_once(s,"PACKAGE_PIN = '1466135ce821d0ebc871fcabfb542ae9505e639ca1f35b15d15a80f797b99509'", "PACKAGE_PIN = '"+pin+"'")
    s=replace_once(s,"len(manifest.get('inputs', {})) == 41", "len(manifest.get('inputs', {})) == 44")
    s=replace_once(s,"def preflight(application, release, *, gateway_port=None):",VALIDATOR+"def preflight(application, release, *, gateway_port=None):")
    s=replace_once(s,"'sceneModelsCatalogSHA256'}) and (value['schema']", "'sceneModelsCatalogSHA256', 'clientResources'}) and (value['schema']")
    s=replace_once(s,"    need(scene_rows is not None and scene_library is not None and (model_library is not None), 'SERVER_MODELS_AND_SCENE_LIBRARIES_REQUIRED')",
        "    resources = checked_client_resources(value, sources)\n    need(scene_rows is not None and scene_library is not None and (model_library is not None), 'SERVER_MODELS_AND_SCENE_LIBRARIES_REQUIRED')")
    s=replace_once(s,"return {'sceneModels': model_library, 'sceneLibrary': scene_library, 'localGIS': local_gis,", "return {'clientResources': resources, 'sceneModels': model_library, 'sceneLibrary': scene_library, 'localGIS': local_gis,")
    s=replace_once(s,"        worker_config['localGIS'] = self.settings['localGIS']", "        worker_config['localGIS'] = self.settings['localGIS']\n        if self.settings['clientResources'] is not None:\n            worker_config['clientResources'] = self.settings['clientResources']")
    s=replace_once(s,"local_gis=True))\"", "local_gis=True,client_resources=sys.argv[7]=='1'))\"")
    s=replace_once(s,"'1' if self.settings['sceneModels'] is not None else '0'], stdin=", "'1' if self.settings['sceneModels'] is not None else '0', '1' if self.settings['clientResources'] is not None else '0'], stdin=")
    anchor="        self.gateway_verified = True"
    inserted='''        if self.settings['clientResources'] is not None:
            for suffix, expected_status in [('grants', 401), ('grants/consume', 403)]:
                conn = http.client.HTTPConnection('127.0.0.1', self.gateway_port, timeout=3)
                try:
                    conn.request('POST', '/zhumadian/api/spatial-sync/v2/client-resources/' + suffix,
                                 body=b'{}', headers={'Content-Type': 'application/json', 'Origin': 'https://www.joinlinksmart.com'})
                    response = conn.getresponse(); body = response.read(4097)
                    need(response.status == expected_status and len(body) <= 4096
                         and response.getheader('X-XNBY-Layer-Sync-Deployment') == self.route_nonce,
                         'CLIENT_RESOURCE_GATEWAY_ROUTE_NOT_VERIFIED')
                    code = loads(body).get('code')
                    need(code == ('RESOURCE_AUTHORIZATION_INVALID' if suffix == 'grants' else 'RESOURCE_GRANT_REJECTED'),
                         'CLIENT_RESOURCE_ANONYMOUS_GUARD_NOT_VERIFIED')
                finally:
                    conn.close()
        self.gateway_verified = True'''
    s=replace_once(s,anchor,inserted)
    ast.parse(s)
    (DEST/'original_spatial_sync_release_support.py').write_text(s,'utf-8')
    a=ast.parse(base);b=ast.parse(s)
    def functions(tree):
        out={}
        for n in tree.body:
            if isinstance(n,ast.FunctionDef):out[n.name]=ast.dump(n)
            if isinstance(n,ast.ClassDef):
                for f in n.body:
                    if isinstance(f,ast.FunctionDef):out[n.name+'.'+f.name]=ast.dump(f)
        return out
    oldfn=functions(a);newfn=functions(b);changed=[n for n in oldfn if oldfn[n]!=newfn[n]]
    need(set(changed)=={'preflight','SpatialRuntime.start','SpatialRuntime.configure_gateway','SpatialRuntime.verify_gateway'},'ONLY_EXPLICIT_RESOURCE_ASSEMBLY_METHODS_MAY_CHANGE')
    record={'prepared':True,'packageSourceFiles':44,'packageManifestSHA256':pin,'changedPackageFiles':['tools/layer_sync_gateway_transaction.py'],
       'baseSupportSHA256':digest(SUPPORT.read_bytes()),'candidateSupportSHA256':digest((DEST/'original_spatial_sync_release_support.py').read_bytes()),
       'changedOriginalFunctions':changed,'newPureValidator':'checked_client_resources',
       'originalStopHandleRecoveryAndOwnershipASTRetained':True,'fullApplicationOrServerInstallationNotExecuted':True,
       'R51FixedTransportAndPublicNotChanged':True,'privateSettingsNotCreatedOrChanged':True}
    (DEST/'prepared.json').write_bytes(encoded(record));print(json.dumps(record))


if __name__=='__main__':main()
