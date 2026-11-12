from pathlib import Path
import hashlib,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_control_20261112';TARGET=A/'Packages/ResourceGISControlCandidate_20261112';D=R/'Document/Deployment/resource_gis_control_20261112'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert not TARGET.exists(),'Do not overwrite an existing candidate'
code=sorted((P/'code').glob('*.py'));assert len(code)==10
rows={}
for machine in ['250','252']:
 folder=TARGET/('client-'+machine);(folder/'code').mkdir(parents=True)
 for f in code:shutil.copyfile(f,folder/'code'/f.name)
 registration=A/('Packages/ResourceManagerCandidate_20261112/client-'+machine+'/registration.json')
 reg=json.loads(registration.read_text('utf-8'));assert reg['GISInstallSHA256']=='26342711ce4091661d71893ce43a1e0431417117ba9f9d522d3ce8ea738cac72'
 (folder/'registration.json').write_bytes(registration.read_bytes())
 files={f.relative_to(folder).as_posix():{'bytes':f.stat().st_size,'sha256':sha(f)}for f in [*sorted((folder/'code').glob('*.py')),folder/'registration.json']}
 doc={'schema':'xnby.client-resources.install.v1','version':'client-resources.20261112.2','files':files}
 (folder/'client-resources-install.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (P/'registrations').mkdir(exist_ok=True)
 for name in ['registration.json','client-resources-install.json']:(P/'registrations'/('client-'+machine+'-'+name)).write_bytes((folder/name).read_bytes())
 rows[machine]={'folder':str(folder.relative_to(R)),'fileCount':12,'ownQualifiedCodeFiles':10,'ownManifestSHA256':sha(folder/'client-resources-install.json'),'externalGIS953SHA256':reg['GISInstallSHA256'],'actualOwnManifestQualificationOnThisMachine':False,'activated':False,'copied252':False}
(D/'thin-delivery-map.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preparedThinPackages':rows,'newRuntimeOrGISCopies':0}))
