"""Copy or verify the complete supplied Tianjin projects without patching them.

No package scripts, service startup, database access, or publication occurs.
The source packages, runtime binaries and test data require separate release
approval; this tool's manifest contains paths and hashes, not their contents.
"""
from pathlib import Path
import argparse,hashlib,json,shutil

BASE='02安全风险管控平台/代码及开发环境搭建移交资料/源码包'
PROJECTS={
    'security_pc':BASE+'/安全风险管控平台前台代码/security-risk-web',
    'emergency_pc':BASE+'/敏捷应急管理前台代码/agile-emergency-response-dev',
    'mobile':BASE+'/移动端前端代码whwly-mobile/whwly-mobile',
    'bigscreen':'03敏捷应急大屏/tjwhbigscreen',
    'business_java':BASE+'/后端代码/后端源码-maven/cloud-endanger',
    'bigscreen_java':'03敏捷应急大屏/大屏后台tjwhyq-svc/tjwhyq-svc',
}
EXCLUDED={'.git','.hg','.svn','node_modules','dist','target','__MACOSX'}
BUILD_OUTPUTS={'native-build-phase1'}


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as source:
        while block:=source.read(1048576):value.update(block)
    return value.hexdigest()


def inputs(root,excluded):
    for folder,dirs,names in root.walk():
        dirs[:]=[name for name in dirs if name not in excluded]
        for name in names:
            # Windows directory junctions may be returned as filenames.
            if name in excluded:continue
            path=folder/name
            if path.is_symlink():raise ValueError('Unexpected source file link: '+str(path))
            yield path.relative_to(root).as_posix(),path


def prepare(reference,output,verify_only=False):
    reference=Path(reference).resolve();output=Path(output).resolve()
    if not reference.is_dir() or reference==output or reference.is_relative_to(output) or output.is_relative_to(reference):
        raise ValueError('Reference and independent output must be distinct, nonoverlapping roots')
    if verify_only:
        if not output.is_dir():raise ValueError('Verification output is missing')
    else:
        if output.exists():raise ValueError('Fresh output required; existing files will not be overwritten')
        output.mkdir(parents=True)
    projects={}
    for name,relative in PROJECTS.items():
        origin=reference/relative;target=output/name
        if not origin.is_dir():raise ValueError('Missing original project: '+name)
        if not verify_only:target.mkdir()
        files=[]
        for rel,source in sorted(inputs(origin,EXCLUDED)):
            destination=target/rel;digest=sha(source)
            if not verify_only:
                destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
            if not destination.is_file() or sha(destination)!=digest:raise ValueError('Original source mismatch: '+name+'/'+rel)
            files.append(dict(path=rel,bytes=source.stat().st_size,sha256=digest))
        actual={rel for rel,_ in inputs(target,EXCLUDED|BUILD_OUTPUTS)}
        if actual!={row['path'] for row in files}:raise ValueError('Unexpected/missing input files in '+name)
        projects[name]=dict(reference=str(origin),output=str(target),fileCount=len(files),files=files)
    return dict(schema='xnby.tianjin-native-source.v1',projects=projects,
                totalFiles=sum(p['fileCount'] for p in projects.values()),
                verifiedOriginalBytes=True,referenceModified=False,sourceLogicPatched=False,
                verifyOnly=verify_only,servicesStarted=False,dataCaptured=False,publicDeployed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if args.manifest.exists():raise ValueError('Fresh manifest path required; prior evidence will not be overwritten')
    if args.manifest.resolve().is_relative_to(args.reference.resolve()):raise ValueError('Manifest must not modify the reference tree')
    result=prepare(args.reference,args.output,args.verify_only)
    args.manifest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('totalFiles','verifiedOriginalBytes','verifyOnly','servicesStarted','dataCaptured','publicDeployed')}))


if __name__=='__main__':main()
