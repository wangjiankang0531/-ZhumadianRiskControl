"""Build one closed R48 R2 transport; no upload or server operation."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,sys,zipfile
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');R2=V/'r48-retained-preflight-r2-r1013'
OLD=R/'Document/Deployment/public_test_home_supervision_r47_20261104/delivery'
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105';DEL=D/'delivery'
J=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
assert not D.exists()
assert J(R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-real-files-r1018.json')['passed']
assert J(R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-sparse-code-recovery-r1022.json')['passed']
assert J(R/'Document/Deployment/event_r2_native_r1021_20261105/independent-restoration-r1023.json')['passed']
spec=importlib.util.spec_from_file_location('r48_transport_r1025',R2/'source/original_public_test_update.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);m=w.runtime()
sources=J(V/'r48-file-source-resolution-r1007.private.json')['newSources']
for rel in ['tools/original_public_test_update.py','tools/original_public_test_base_r46.py']:
 p=R2/'source'/Path(rel).name;sources[rel]={'source':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
plans={label:J(R2/('update-from-'+label+'.json'))for label in ['r45','r47']}
bases={};union={}
new=sha(R2/'candidate/release-manifest.json')
for label,plan in plans.items():
 old=next(iter(plan['acceptedOldReleases']));accepted=plan['acceptedOldReleases'][old]
 assert plan['newReleaseSHA256']==new and old in m.R48_BASES
 bases[old]={'label':label,'updateId':plan['updateId'],'manifestSHA256':sha(R2/('update-from-'+label+'.json')),
             'oldUpdaterSHA256':accepted['controllerFiles']['tools/original_public_test_update.py'],
             'writes':len(plan['files']),'removals':len(plan['removedFrontendFiles'])}
 for name,pin in plan['files'].items():
  assert name not in union or union[name]==pin,'CROSS_VARIANT_PAYLOAD_COLLISION'
  union[name]=pin
assert len(union)==187 and len(plans['r47']['files'])==180
D.mkdir();DEL.mkdir()
archive_name='Zhumadian_Event_Write_Results_20261105_R48.zip'
def put(z,name,raw):
 info=zipfile.ZipInfo(name,(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
 z.writestr(info,raw,compresslevel=9)
with zipfile.ZipFile(DEL/archive_name,'x')as z:
 put(z,'web.config',(OLD/'web.config').read_bytes())
 for label in plans:put(z,'variants/'+label+'/update-manifest.json',(R2/('update-from-'+label+'.json')).read_bytes())
 for name,pin in sorted(union.items()):
  p=R2/'candidate'/name if name in ['release-manifest.json','payload-manifest.json']else Path(sources[name]['source'])
  raw=p.read_bytes();assert len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'],name
  put(z,'payload/'+name,raw)
text=(OLD/'deploy_home_supervision_r47.py').read_text('utf8').replace('R47','R48').replace('r47','r48')
tree=ast.parse(text)
updates={'ARCHIVE_SHA':sha(DEL/archive_name),'ARCHIVE_NAME':archive_name,'NEW':new,
         'UPDATER_SHA':sha(R2/'source/original_public_test_update.py'),'BASES':bases,
         'CORE_SHA':sha(R2/'source/original_public_test_base_r46.py')}
lines=text.splitlines(keepends=True)
for node in reversed(tree.body):
 if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in updates:
  lines[node.lineno-1:node.end_lineno]=[node.targets[0].id+'='+repr(updates[node.targets[0].id])+'\n']
text=''.join(lines).replace("'ONLY_EXACT_R45_BASE'","'ONLY_EXACT_R45_OR_R47_BASE'")
start=text.index('def validate_archive(');end=text.index('\n\ndef write_scoped_result',start)
replacement='''def validate_archive(z,base):
    entries=z.infolist();names=[v.filename for v in entries]
    need(len(entries)<=512 and len(names)==len(set(names))==len({n.casefold()for n in names}) and sum(v.file_size for v in entries)<=40*1024**2,'CLOSED_TRANSPORT_BOUNDS')
    need(all(not v.is_dir()and not(v.flag_bits&1)and ((v.external_attr>>16)&0o170000)!=0o120000 for v in entries),'REGULAR_UNENCRYPTED_MEMBERS')
    for info in entries:
        rel=PurePosixPath(info.filename)
        need(str(rel)==info.filename and not rel.is_absolute()and all(p not in ('.','..')and not re.search(r'[\\\\:\\x00-\\x1f]',p)and not p.endswith((' ','.'))for p in rel.parts),'EXACT_RELATIVE_MEMBER')
    plans={};union={}
    for old,pin in BASES.items():
        raw=z.read('variants/'+pin['label']+'/update-manifest.json')
        need(hashlib.sha256(raw).hexdigest()==pin['manifestSHA256'],'FIXED_VARIANT_MANIFEST')
        plan=json.loads(raw)
        need(plan['updateId']==pin['updateId']and plan['newReleaseSHA256']==NEW and set(plan['acceptedOldReleases'])=={old},'FIXED_SINGLE_BASE_UPDATE_IDENTITY')
        need(plan['targetApplication']==APP.as_posix()and plan['gatewayPort']==18892,'EXACT_VARIANT_TARGET')
        need(len(plan['files'])==pin['writes']and len(plan['removedFrontendFiles'])==pin['removals'],'EXACT_VARIANT_WRITE_REMOVE_COUNTS')
        for name,row in plan['files'].items():
            need(name not in union or union[name]==row,'CROSS_VARIANT_PAYLOAD_COLLISION');union[name]=row
        plans[pin['label']]=plan
    need(set(names)=={'web.config'}|{'variants/'+v['label']+'/update-manifest.json'for v in BASES.values()}|{'payload/'+n for n in union},'EXACT_CLOSED_MEMBERS')
    need(z.read('web.config')==b'__DENY_BYTES__','EXACT_STAGE_HTTP_DENY_CONFIG')
    for name,pin in union.items():
        raw=z.read('payload/'+name)
        need(len(raw)==pin['bytes']and hashlib.sha256(raw).hexdigest()==pin['SHA256'],'EXACT_ARCHIVED_PAYLOAD_PIN:'+name)
    return plans[base['label']]

def extract_selected_archive(archive,stage,base):
    with zipfile.ZipFile(archive)as z:
        plan=validate_archive(z,base)
        stage=regular(stage);need(not stage.exists(),'NEW_OWN_STAGE_REQUIRED');stage.mkdir(parents=True)
        members=[('web.config','web.config'),('variants/'+base['label']+'/update-manifest.json','update-manifest.json')]+[('payload/'+n,'payload/'+n)for n in plan['files']]
        for origin,destination in members:
            dest=regular(stage.joinpath(*PurePosixPath(destination).parts));dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb')as target,z.open(origin)as stream:
                while True:
                    chunk=stream.read(65536)
                    if not chunk:break
                    target.write(chunk)
    need(sha(stage/'update-manifest.json')==base['manifestSHA256'],'EXACT_SELECTED_STAGE_MANIFEST')
    return plan
'''
replacement=replacement.replace("b'__DENY_BYTES__'",repr((OLD/'web.config').read_bytes()))
text=text[:start]+replacement+text[end:]
# Keep security resources exact; select actual new compiled emergency entry/CSS
# and event editor chunk, rather than hardcoding the old R47 hashed URL.
namespace={};oldtree=ast.parse((OLD/'deploy_home_supervision_r47.py').read_text('utf8'))
static=ast.literal_eval(next(n.value for n in oldtree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='STATIC_EXPECTED'))
static={k:v for k,v in static.items()if not k.startswith('/zhumadian/emergency/')}
dist=R/'work/event-result-full-r996/dist';html=(dist/'index.html').read_text('utf8')
public='/zhumadian/emergency/branding-20261025/'
entries=re.findall(r'(?:src|href)="('+re.escape(public)+r'assets/(?:js|css)/[^"?]+)"',html)
event=[n for n in J(R2/'candidate/payload-manifest.json')['files']if n.startswith('frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-')]
assert len(entries)==2 and len(event)==1
entries.append(public+event[0].removeprefix('frontend/emergency_pc/'))
for path in entries:
 p=dist/path.removeprefix(public);static[path]={'decodedBytes':p.stat().st_size,'decodedSHA256':sha(p)}
parsed=ast.parse(text);lines=text.splitlines(keepends=True)
node=next(n for n in parsed.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='STATIC_EXPECTED')
lines[node.lineno-1:node.end_lineno]=['STATIC_EXPECTED='+repr(static)+'\n'];text=''.join(lines)
ast.parse(text);(DEL/'deploy_event_write_results_r48.py').write_text(text,encoding='utf8')
for source,target in [('original_public_test_update.py','r48_update_runtime.py'),('original_public_test_base_r46.py','original_public_test_base_r46.py')]:
 (DEL/target).write_bytes((R2/'source'/source).read_bytes())
(DEL/'web.config').write_bytes((OLD/'web.config').read_bytes())
for name,mode in [('Check_Only_Event_Write_Results_R48.cmd',' --check-only'),('Deploy_Event_Write_Results_R48.cmd',''),('Recover_This_Event_Write_Results_R48.cmd',' --recover-this-update')]:
 raw='@echo off\r\n"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_event_write_results_r48.py"'+mode+'\r\n'
 (DEL/name).write_bytes(raw.encode('ascii'))
rows={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(DEL.iterdir())}
manifest={'schema':'xnby.public.r48.fixed-transport.v1','candidate':'R48-r2','newReleaseSHA256':new,
 'ftpDestination':'/Zhumadian/Zhumadian_Event_Write_Results_20261105_R48/','files':rows,
 'baseVariants':bases,'noDatabaseCredentialsUploadsGISOrUserBusinessRows':True,
 'uploadedOrDeployed':False,'actualPublicAcceptance':False}
(DEL/'delivery-manifest.json').write_bytes(enc(manifest))
out={'preparedOnly':True,'transportFiles':len(list(DEL.iterdir())),'transportBytes':sum(p.stat().st_size for p in DEL.iterdir()),
 'deliveryManifestSHA256':sha(DEL/'delivery-manifest.json'),'archiveSHA256':sha(DEL/archive_name),
 'newReleaseSHA256':new,'variants':bases,'actualServerOrTransportValidationPerformed':False,'publicUploaded':False}
(D/'prepared-transport-r1025.json').write_bytes(enc(out));print(json.dumps(out))
