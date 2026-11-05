"""Build a separate R48 third draft only after real-apply/recovery acceptance."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import zipfile

R=Path('D:/Project/Zhumadian')
V=Path(__file__).resolve().parent
OLD=R/'Document/Deployment/public_test_event_write_results_r48_20261105/delivery'
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'
OUT=D/'delivery'
ARCHIVE='Zhumadian_Event_Write_Results_20261105_R48_R3.zip'
FIXED=V/'static-control-bridge-r1046/r48_update_runtime.py'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(raw):return json.loads(raw)
def encode(data):return(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def pin(raw):return {'bytes':len(raw),'sha256':sha(raw)}
def replace_assignment(source,name,value):
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets)]
    assert len(nodes)==1
    node=nodes[0];lines=source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno-1])+name+'='+repr(value)+'\n'+''.join(lines[node.end_lineno:])

def main():
    accepted=read((R/'work/ua1049/verified-real-apply-r1049.json').read_bytes())
    first_terminal=read((R/'work/ua1049/actual-parent-terminal-r1049.json').read_bytes())
    terminal=read((R/'work/ua1049/actual-parent-terminal-r1053.json').read_bytes())
    assert accepted['passed']and accepted['codeRestored']and accepted['pointerRestored']and accepted['metadataRestored']
    assert first_terminal['harnessExitCode']==1 and first_terminal['actualJobDescendantsZero']
    assert accepted['initialHarnessKeyErrorRetained']and accepted['applyUpdateNotRepeated']
    assert terminal['harnessExitCode']==0 and terminal['actualJobDescendantsZero']
    assert sha(FIXED.read_bytes())=='81cc5e3d27062002bc18b142b577530ac940800b9e75dbc7c268f74d246a3211'
    assert not D.exists()
    original_manifest=read((OLD/'delivery-manifest.json').read_bytes())
    assert sha((OLD/'delivery-manifest.json').read_bytes())=='ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a'
    with zipfile.ZipFile(OLD/'Zhumadian_Event_Write_Results_20261105_R48.zip')as archive:
        members={item.filename:archive.read(item.filename)for item in archive.infolist()}
    before_members={name:sha(raw)for name,raw in members.items()}
    members['payload/tools/original_public_test_update.py']=FIXED.read_bytes()
    payload=read(members['payload/payload-manifest.json'])
    payload['files']['tools/original_public_test_update.py']=pin(FIXED.read_bytes())
    members['payload/payload-manifest.json']=encode(payload)
    release=read(members['payload/release-manifest.json'])
    release['controllerFiles']['tools/original_public_test_update.py']=sha(FIXED.read_bytes())
    release['payloadManifestSHA256']=sha(members['payload/payload-manifest.json'])
    members['payload/release-manifest.json']=encode(release)
    new=sha(members['payload/release-manifest.json'])
    constants=ast.parse((OLD/'deploy_event_write_results_r48.py').read_text('utf-8-sig'))
    base_nodes=[node for node in constants.body if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='BASES'for t in node.targets)]
    bases=ast.literal_eval(base_nodes[0].value)
    for old,row in bases.items():
        path='variants/'+row['label']+'/update-manifest.json'
        plan=read(members[path])
        for name in ['tools/original_public_test_update.py','payload-manifest.json','release-manifest.json']:
            raw=members['payload/'+name]
            plan['files'][name]={'bytes':len(raw),'SHA256':sha(raw)}
        plan['newReleaseSHA256']=new
        plan['newPayloadManifestSHA256']=sha(members['payload/payload-manifest.json'])
        assert len(plan['files'])==row['writes']and len(plan['removedFrontendFiles'])==row['removals']
        members[path]=encode(plan);row['manifestSHA256']=sha(members[path])
    changed={name for name,raw in members.items()if before_members[name]!=sha(raw)}
    assert changed=={'payload/tools/original_public_test_update.py','payload/payload-manifest.json','payload/release-manifest.json',
        'variants/r45/update-manifest.json','variants/r47/update-manifest.json'}
    D.mkdir();OUT.mkdir()
    with zipfile.ZipFile(OUT/ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
        for name,raw in members.items():archive.writestr(name,raw)
    wrapper=(OLD/'deploy_event_write_results_r48.py').read_text('utf-8-sig')
    for key,value in {'ARCHIVE_NAME':ARCHIVE,'ARCHIVE_SHA':sha((OUT/ARCHIVE).read_bytes()),
        'NEW':new,'UPDATER_SHA':sha(FIXED.read_bytes()),'BASES':bases}.items():wrapper=replace_assignment(wrapper,key,value)
    ast.parse(wrapper)
    # Only fixed data bindings change in the transport wrapper. Its lifecycle,
    # extraction, postchecks and recovery functions are exact retained ASTs.
    before=ast.parse((OLD/'deploy_event_write_results_r48.py').read_text('utf-8-sig'))
    funcs=lambda tree:{n.name:ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert funcs(before)==funcs(ast.parse(wrapper))
    (OUT/'deploy_event_write_results_r48.py').write_text(wrapper,encoding='utf-8',newline='\n')
    shutil.copyfile(FIXED,OUT/'r48_update_runtime.py')
    for name in ['original_public_test_base_r46.py','web.config']:shutil.copyfile(OLD/name,OUT/name)
    python='"C:\\inetpub\\wwwroot\\Zhumadian\\Application\\runtime\\python\\python.exe" -I -B "%~dp0deploy_event_write_results_r48.py"'
    for filename,mode in [('Check_Only_Event_Write_Results_R48_R3.cmd',' --check-only'),('Deploy_Event_Write_Results_R48_R3.cmd',''),('Recover_This_Event_Write_Results_R48_R3.cmd',' --recover-this-update')]:
        # The user may double-click in Explorer; preserve the final output so
        # an early exception cannot disappear in an automatically closed window.
        raw='@echo off\r\n'+python+mode+'\r\nset "xnby_r48r3_exit=%errorlevel%"\r\necho R48_R3_COMMAND_FINISHED_EXIT_CODE=%xnby_r48r3_exit%\r\npause\r\nexit /b %xnby_r48r3_exit%\r\n'
        (OUT/filename).write_bytes(raw.encode('ascii'))
    manifest=copy.deepcopy(original_manifest)
    manifest.update(candidate='R48-third-draft-static-control-bridge',ftpDestination='/Zhumadian/Zhumadian_Event_Write_Results_20261105_R48_R3/',
        newReleaseSHA256=new,baseVariants=bases,uploadedOrDeployed=False)
    manifest['files']={p.name:pin(p.read_bytes())for p in sorted(OUT.iterdir())}
    assert len(manifest['files'])==8
    (OUT/'delivery-manifest.json').write_bytes(encode(manifest))
    proof={'prepared':True,'files':9,'bytes':sum(p.stat().st_size for p in OUT.iterdir()),
        'deliveryManifestSHA256':sha((OUT/'delivery-manifest.json').read_bytes()),'newReleaseSHA256':new,
        'runtimeSHA256':sha(FIXED.read_bytes()),'onlyFiveArchiveMembersChanged':sorted(changed),
        'frontendBusinessAndDataBytesUnchangedFromFixedR48':True,
        'transportWrapperAllFunctionASTsRetained':True,'exactCandidateRuntimeExercisedByActualApplyTest':True,
        'realIISPublicTLSAndUserUIAcceptance':False,'uploadedOrDeployed':False,'fullCloneReady':False}
    (D/'prepared-r1051.json').write_bytes(encode(proof))
    print(json.dumps(proof,ensure_ascii=False))

if __name__=='__main__':main()
