"""Create and verify a private relocatable Reference-source business runtime.

Preparation consumes the already verified source selection. Verification uses
only an explicit manifest pin and files in the selected payload; no Reference,
source archive, database, network service or experimental receipts are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from urllib.parse import quote
import uuid
import zipfile

KIND='zhumadian.reference-business.portable.v1'
MANIFEST='portable_runtime.json'
REFERENCE_SHA='b48adb8d966fa55656757d182cdd6b64c409d151c3e30ee3cbc5ef0cb86e68d8'
SOURCE_SHA='abbb76588157cf9ad8e53f98033568bb4c58c1e36a2040e149688c8fcd945485'
MAX_PAYLOAD=1024**3
MAX_MANIFEST=2*1024**2


def require(value,code):
    if not value:raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def regular(path,directory=False):
    info=Path(path).lstat()
    require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'REGULAR_PAYLOAD_REQUIRED')
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode),'REGULAR_PAYLOAD_REQUIRED')
    return info


def relative(value):
    require(isinstance(value,str) and 0<len(value)<240 and not any(ord(c)<32 for c in value),'SAFE_RELATIVE_PAYLOAD_PATH_REQUIRED')
    p=PurePosixPath(value)
    require(value not in ('.','..') and not p.is_absolute() and p.as_posix()==value and '\\' not in value and ':' not in value and '..' not in p.parts,'SAFE_RELATIVE_PAYLOAD_PATH_REQUIRED')
    for part in p.parts:
        require(part not in ('.','..') and part.rstrip(' .')==part,'SAFE_RELATIVE_PAYLOAD_PATH_REQUIRED')
        require(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',part.split('.')[0].upper()),'WINDOWS_DEVICE_PATH_REFUSED')
    return value


def manifest_values(raw,enforce_fold=True):
    require(len(raw)<128*1024 and b'\0' not in raw,'JAR_MANIFEST_BOUND')
    if enforce_fold:require(all(len(line)<=70 for line in raw.replace(b'\r\n',b'\n').split(b'\n')),'JAR_MANIFEST_PHYSICAL_LINE_BOUND')
    values={};lines=[]
    for line in raw.replace(b'\r\n',b'\n').split(b'\n'):
        if not line:
            if lines:break
            continue
        if line.startswith(b' '):
            require(bool(lines),'JAR_MANIFEST_CONTINUATION');lines[-1]+=line[1:]
        else:lines.append(line)
    for line in lines:
        key,value=line.decode('utf-8').split(': ',1)
        require(key.casefold() not in {k.casefold() for k in values},'JAR_MANIFEST_DUPLICATE_HEADER')
        values[key]=value
    return values


def dependency_metadata(path,allowed_jars):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        require(len(names)==len(set(names)),'DEPENDENCY_DUPLICATE_ZIP_MEMBER')
        for name in names:
            if name.casefold() in ('meta-inf/manifest.mf','meta-inf/index.list'):
                require(name in ('META-INF/MANIFEST.MF','META-INF/INDEX.LIST'),'AMBIGUOUS_DEPENDENCY_METADATA_CASE')
        if 'META-INF/MANIFEST.MF' in names:
            # Signed jars can contain large per-entry digest sections. Only the
            # main section defines Class-Path; do not read the signature tail.
            main=bytearray()
            with archive.open('META-INF/MANIFEST.MF') as stream:
                while True:
                    line=stream.readline(65537)
                    require(len(line)<=65536 and len(main)+len(line)<128*1024,'DEPENDENCY_MAIN_MANIFEST_BOUND')
                    main.extend(line)
                    if not line or line in (b'\n',b'\r\n',b'\r'):break
            values=manifest_values(bytes(main),False)
            value=next((v for k,v in values.items() if k.casefold()=='class-path'),'')
            require(not value.strip(),'DEPENDENCY_SECONDARY_CLASSPATH_REFUSED')
        headers=[]
        if 'META-INF/INDEX.LIST' in names:
            require(archive.getinfo('META-INF/INDEX.LIST').file_size<2*1024**2,'DEPENDENCY_JAR_INDEX_BOUND')
            raw=archive.read('META-INF/INDEX.LIST').decode('utf-8').replace('\r\n','\n')
            groups=[g.strip().splitlines() for g in re.split(r'\n\s*\n',raw) if g.strip()]
            require(groups and re.fullmatch(r'JarIndex-Version:\s*1\.0',groups[0][0]) and len(groups)<1000,'DEPENDENCY_JAR_INDEX_FORMAT')
            headers=[g[0] for g in groups[1:]]
            require(all(h in allowed_jars for h in headers),'DEPENDENCY_JAR_INDEX_ESCAPES_PAYLOAD')
        return headers


def tree_files(root):
    files=set();pending=[root]
    while pending:
        folder=pending.pop();regular(folder,True)
        require(folder==root or folder==root/'lib','PORTABLE_DIRECTORY_SET_MISMATCH')
        for path in folder.iterdir():
            info=path.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'PAYLOAD_REPARSE_POINT_REFUSED')
            if stat.S_ISDIR(info.st_mode):pending.append(path)
            else:
                regular(path);files.add(path.relative_to(root).as_posix())
                require(len(files)<=300,'PAYLOAD_FILE_COUNT_BOUND')
    return files


def verify(manifest,expected_sha256):
    manifest=Path(manifest).absolute()
    require(manifest.name==MANIFEST and isinstance(expected_sha256,str) and re.fullmatch('[0-9a-f]{64}',expected_sha256),'EXPLICIT_PORTABLE_MANIFEST_PIN_REQUIRED')
    require(0<regular(manifest).st_size<=MAX_MANIFEST,'BOUNDED_PORTABLE_MANIFEST_REQUIRED')
    raw=manifest.read_bytes();require(hashlib.sha256(raw).hexdigest()==expected_sha256,'PORTABLE_MANIFEST_PIN_MISMATCH')
    def object_pairs(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'PORTABLE_JSON_DUPLICATE_KEY');result[key]=value
        return result
    spec=json.loads(raw,object_pairs_hook=object_pairs);root=manifest.parent;regular(root,True)
    require(spec.get('kind')==KIND and spec.get('referenceArchiveSHA256')==REFERENCE_SHA and spec.get('sourceArchiveSHA256')==SOURCE_SHA,'EXACT_REFERENCE_SOURCE_PROVENANCE_REQUIRED')
    require(spec.get('compiledClasses')==768 and spec.get('resourceCount')==97 and spec.get('dependencyCount')==220 and spec.get('sourceInputs')==863,'COMPLETE_REFERENCE_SOURCE_LAYOUT_REQUIRED')
    require(spec.get('privateRuntimeArtifact') is True and spec.get('originalConfigurationIncluded') is True,'PRIVATE_RUNTIME_ARTIFACT_REQUIRED')
    require(spec.get('originalClassesOrResourceBytesChanged') is False and spec.get('jarManifestOnlyChanged') is True,'ORIGINAL_APPLICATION_BYTES_MUST_BE_PRESERVED')
    require(isinstance(spec.get('ownerId'),str) and str(uuid.UUID(spec['ownerId']))==spec['ownerId'],'PORTABLE_OWNER_ID_REQUIRED')
    require(re.fullmatch('[0-9a-f]{64}',spec.get('sourceInputsSHA256','')) and re.fullmatch('[0-9a-f]{64}',spec.get('sourceFlatJarSHA256','')),'SOURCE_DERIVATION_DIGESTS_REQUIRED')
    records=spec.get('files');require(isinstance(records,list) and len(records)==221,'COMPLETE_PORTABLE_FILES_REQUIRED')
    names=[relative(r['path']) for r in records]
    require(len(set(n.casefold() for n in names))==len(names),'PORTABLE_PATH_COLLISION')
    require(names[0]=='application.jar' and all(re.fullmatch(r'lib/[A-Za-z0-9_.+-]+\.jar',n) for n in names[1:]),'PRIVATE_JAR_LAYOUT_REQUIRED')
    require(tree_files(root)==set(names)|{MANIFEST},'PORTABLE_FILE_SET_MISMATCH')
    total=0;index_files=0
    allowed_jars={PurePosixPath(name).name for name in names[1:]}
    for row in records:
        file=root/row['path'];info=regular(file)
        require(type(row.get('bytes')) is int and 0<row['bytes']<=MAX_PAYLOAD and info.st_size==row['bytes'],'PORTABLE_FILE_SIZE_MISMATCH')
        total+=info.st_size;require(total<=MAX_PAYLOAD,'PORTABLE_PAYLOAD_SIZE_BOUND')
        require(re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) and sha(file)==row['sha256'],'PORTABLE_FILE_SHA_MISMATCH')
        if row['path']!='application.jar':index_files+=bool(dependency_metadata(file,allowed_jars))
    with zipfile.ZipFile(root/'application.jar') as archive:
        infos=archive.infolist();members=[i.filename for i in infos]
        require(len(members)<=10000 and len(members)==len(set(members)) and sum(i.file_size for i in infos)<=128*1024**2,'PORTABLE_JAR_LAYOUT_BOUND')
        for info in infos:relative(info.filename.rstrip('/') if info.is_dir() else info.filename)
        expected=spec['applicationEntries'];require(isinstance(expected,list) and len(expected)==865,'COMPLETE_APPLICATION_ENTRIES_REQUIRED')
        wanted={relative(r['path']) for r in expected}
        require(len(wanted)==865 and {i.filename for i in infos if not i.is_dir()}==wanted|{'META-INF/MANIFEST.MF'},'PORTABLE_APPLICATION_ENTRY_SET_MISMATCH')
        directories={'META-INF/'}
        for name in wanted:
            parent=PurePosixPath(name).parent
            while str(parent)!='.':directories.add(parent.as_posix()+'/');parent=parent.parent
        require({i.filename for i in infos if i.is_dir()}==directories,'PORTABLE_EXPLICIT_PACKAGE_DIRECTORIES_REQUIRED')
        main=spec.get('mainClass')
        require(isinstance(main,str) and re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*',main) and main.replace('.','/')+'.class' in wanted,'PORTABLE_MAIN_CLASS_REQUIRED')
        for row in expected:
            data=archive.read(row['path']);require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'PORTABLE_APPLICATION_BYTES_MISMATCH')
        require(sum(r['path'].endswith('.class') for r in expected)==768,'PORTABLE_CLASS_COUNT_MISMATCH')
        values=manifest_values(archive.read('META-INF/MANIFEST.MF'))
        allowed={'Manifest-Version','Original-Main-Class','Class-Path','Created-By','Source-Archive-SHA256','Portable-Layout-Version'}
        require(set(values)==allowed and values.get('Original-Main-Class')==spec['mainClass'] and values.get('Source-Archive-SHA256')==SOURCE_SHA and values.get('Portable-Layout-Version')=='1','CONTROLLED_LAUNCH_MANIFEST_REQUIRED')
        require(values.get('Class-Path')==' '.join(quote(n,safe='/._-') for n in names[1:]),'PORTABLE_CLASSPATH_MISMATCH')
    return {'kind':KIND,'dependencyCount':220,'compiledClasses':768,'resourceCount':97,'payloadFiles':221,
        'payloadBytes':total,'manifestSHA256':expected_sha256,'privateRuntimeArtifact':True,
        'referenceOrSourceArchiveRequiredAtVerification':False,'allPayloadAndApplicationEntryBytesVerified':True,
        'controlledLauncherRequired':True,'directJarMainEntryProvided':False,
        'dependencyJarIndexFilesChecked':index_files,
        'applicationStarted':False,'databaseConnected':False,'publicDeployed':False,'fullCloneReady':False}


def source_plan(workspace,selection,selection_sha256):
    # Build-time proof is deliberately separate from standalone verification.
    from reference_business_runtime import select
    flat,proof=select(workspace,selection,selection_sha256)
    require(proof['mode']=='reference-source-rebuilt' and proof['dependencyCount']==220,'EXACT_REFERENCE_SOURCE_SELECTION_REQUIRED')
    spec=json.loads((flat/'receipt.json').read_bytes())
    names=[r['file'] for r in spec['dependencies']]
    require(len(names)==220 and len({n.casefold() for n in names})==220 and all(re.fullmatch(r'[A-Za-z0-9_.+-]+\.jar',n) for n in names),'PORTABLE_DEPENDENCY_NAMES_REQUIRED')
    for name in names:relative('lib/'+name)
    dependencies=[(flat/r['relativePath']).resolve(strict=True) for r in spec['dependencies']]
    for dep in dependencies:regular(dep);dependency_metadata(dep,set(names))
    required=sum(r['bytes'] for r in spec['dependencies'])+sum(r['bytes'] for r in spec['applicationEntries'])+2*1024**2
    require(required<MAX_PAYLOAD,'PORTABLE_GENERATION_SIZE_BOUND')
    return flat,proof,spec,dependencies,required


def prepare(workspace,selection,selection_sha256,output):
    workspace=Path(workspace).resolve(strict=True);output=Path(output).resolve()
    require(output.is_relative_to(workspace) and not output.exists(),'FRESH_PRIVATE_PORTABLE_OUTPUT_REQUIRED')
    flat,proof,spec,dependencies,required=source_plan(workspace,selection,selection_sha256)
    require(output.parent.exists() and shutil.disk_usage(output.parent).free>2*required+64*1024**2,'PORTABLE_SPACE_RESERVE_REQUIRED')
    from reference_flat_runtime import manifest_bytes
    output.mkdir();(output/'lib').mkdir();files=[]
    with zipfile.ZipFile(flat/'application.jar') as source,zipfile.ZipFile(output/'application.jar','x') as target:
        values=manifest_values(source.read('META-INF/MANIFEST.MF'))
        values['Original-Main-Class']=values.pop('Main-Class')
        values['Class-Path']=' '.join(quote('lib/'+r['file'],safe='/._-') for r in spec['dependencies'])
        values['Portable-Layout-Version']='1'
        for entry in source.infolist():
            target.writestr(entry,manifest_bytes(values) if entry.filename=='META-INF/MANIFEST.MF' else source.read(entry))
    files.append({'path':'application.jar','bytes':(output/'application.jar').stat().st_size,'sha256':sha(output/'application.jar')})
    for row,source in zip(spec['dependencies'],dependencies):
        dest=output/'lib'/row['file'];relative('lib/'+row['file']);regular(source)
        require(source.stat().st_size==row['bytes'] and sha(source)==row['sha256'],'SOURCE_DEPENDENCY_CHANGED')
        shutil.copyfile(source,dest)
        require(sha(dest)==row['sha256'],'COPIED_DEPENDENCY_BYTES_MISMATCH')
        files.append({'path':'lib/'+row['file'],'bytes':row['bytes'],'sha256':row['sha256']})
    portable={'kind':KIND,'ownerId':str(uuid.uuid4()),'referenceArchiveSHA256':REFERENCE_SHA,'sourceArchiveSHA256':SOURCE_SHA,
        'sourceFlatJarSHA256':spec['applicationJarSHA256'],'sourceInputsSHA256':proof['sourceInputsSHA256'],
        'sourceInputs':863,'compiledClasses':768,'resourceCount':97,'dependencyCount':220,'mainClass':spec['mainClass'],
        'applicationEntries':[{'path':r['file'],'bytes':r['bytes'],'sha256':r['sha256']} for r in spec['applicationEntries']],
        'files':files,'privateRuntimeArtifact':True,'originalConfigurationIncluded':True,
        'originalClassesOrResourceBytesChanged':False,'jarManifestOnlyChanged':True,
        'controlledLauncherRequired':True,'directJarMainEntryProvided':False,
        'conservativeGenerationBytes':required,'applicationStarted':False,'databaseConnected':False,
        'publicDeployed':False,'fullCloneReady':False}
    manifest=output/MANIFEST;manifest.write_text(json.dumps(portable,indent=2)+'\n',encoding='utf-8')
    result=verify(manifest,sha(manifest))
    # Verify immutable inputs once more after generating the private payload.
    for row,dep in zip(spec['dependencies'],dependencies):require(sha(dep)==row['sha256'],'SOURCE_DEPENDENCY_CHANGED')
    require(sha(flat/'application.jar')==spec['applicationJarSHA256'],'SOURCE_FLAT_JAR_CHANGED')
    return result


def select(manifest,expected_sha256):
    require(manifest is not None and expected_sha256 is not None,'PORTABLE_MANIFEST_AND_PIN_REQUIRED_TOGETHER')
    checked=verify(manifest,expected_sha256)
    manifest=Path(manifest).absolute();raw=manifest.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==expected_sha256,'PORTABLE_MANIFEST_CHANGED_AFTER_VERIFICATION')
    spec=json.loads(raw)
    return manifest.parent.resolve(strict=True),{
        'mode':'reference-source-portable','dependencyCount':220,'compiledClasses':768,
        'sourceArchiveSHA256':SOURCE_SHA,'referenceArchiveSHA256':REFERENCE_SHA,
        'selectionSHA256':expected_sha256,'sourceInputsSHA256':spec['sourceInputsSHA256'],
        'mainClass':spec['mainClass'],'controlledLauncherRequired':True,
        'businessSelectionReadReferenceOrBootArchive':False,'payloadBytes':checked['payloadBytes']}


def validate_launch_options(reference_manifest,reference_pin,portable_manifest,portable_pin,original_semantics):
    reference_requested=reference_manifest is not None or reference_pin is not None
    portable_requested=portable_manifest is not None or portable_pin is not None
    require(not (reference_requested and portable_requested),'BUSINESS_RUNTIME_SELECTORS_ARE_EXCLUSIVE')
    if portable_requested:
        require(portable_manifest is not None and portable_pin is not None,'PORTABLE_MANIFEST_AND_PIN_REQUIRED_TOGETHER')
        require(isinstance(portable_pin,str) and re.fullmatch('[0-9a-f]{64}',portable_pin),'EXPLICIT_PORTABLE_MANIFEST_PIN_REQUIRED')
        require(original_semantics is True,'PORTABLE_RUNTIME_REQUIRES_ORIGINAL_BUSINESS_SEMANTICS')
    elif reference_requested:
        require(original_semantics is True,'REFERENCE_SOURCE_RUNTIME_REQUIRES_ORIGINAL_BUSINESS_SEMANTICS')
    return portable_requested


def select_for_launch(workspace,reference_manifest=None,reference_pin=None,portable_manifest=None,portable_pin=None,original_semantics=False):
    portable=validate_launch_options(reference_manifest,reference_pin,portable_manifest,portable_pin,original_semantics)
    if portable:
        root,proof=select(portable_manifest,portable_pin)
        require(proof['mainClass']=='com.iemp.endanger.Application','PORTABLE_CONTROLLED_APPLICATION_MAIN_REQUIRED')
        return root,proof
    from reference_business_runtime import select as legacy
    return legacy(workspace,reference_manifest,reference_pin)


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    plan=sub.add_parser('plan');build=sub.add_parser('prepare')
    for p in [plan,build]:
        p.add_argument('--workspace',type=Path,required=True);p.add_argument('--selection',type=Path,required=True);p.add_argument('--selection-sha256',required=True)
    build.add_argument('--output',type=Path,required=True)
    check=sub.add_parser('verify');check.add_argument('--manifest',type=Path,required=True);check.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args()
    if args.command=='plan':
        _,_,spec,_,required=source_plan(args.workspace,args.selection,args.selection_sha256)
        result={'dependencyFiles':220,'dependencyBytes':sum(r['bytes'] for r in spec['dependencies']),
            'conservativeGenerationBytes':required,'newPayloadCreated':False,'privateRuntimeArtifact':True}
    elif args.command=='prepare':result=prepare(args.workspace,args.selection,args.selection_sha256,args.output)
    else:result=verify(args.manifest,args.manifest_sha256)
    print(json.dumps(result))


if __name__=='__main__':main()
