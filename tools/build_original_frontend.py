"""Build supplied frontends with explicit deployment paths; never patch source.

Uses existing locked dependencies, direct Vite/uni CLI, and a fresh output.
This does not connect a backend, import data, launch a browser or publish.
"""
from pathlib import Path
from urllib.parse import urlsplit
from datetime import datetime
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import shutil
from contextlib import nullcontext
from original_frontend_deployment_assets import local_command_override, mobile_entry_url, replace_output_mobile_qr

KINDS = {'security_pc': '/tianjinrisk/', 'emergency_pc': '/tianjinrisk/emergency/',
         'mobile': '/tianjinrisk/h5/'}
EXCLUDED = {'node_modules', '.git', '.hg', '.svn', 'dist', 'target', 'native-build-phase1', '__MACOSX'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def route(value, trailing):
    if not re.fullmatch(r'/[A-Za-z0-9_/-]*', value) or '//' in value or '/..' in value:
        raise ValueError('Expected an absolute same-origin URL path without query, traversal or credentials')
    if value.endswith('/') != trailing or value == '/':
        raise ValueError('Unexpected route trailing slash or root scope')
    return value

def baseline_files(manifest, kind):
    project = manifest['projects'][kind]
    result = {}
    for row in project['files']:
        rel = row['path']
        if rel.startswith(('/', '\\')) or '\\' in rel or any(p in ('', '.', '..') for p in rel.split('/')) or ':' in rel:
            raise ValueError('Invalid relative source path')
        if rel in result or not re.fullmatch('[a-f0-9]{64}', row['sha256']):
            raise ValueError('Invalid source manifest entry')
        result[rel] = row['sha256']
    if not result:
        raise ValueError('Empty source manifest')
    return result

def verify_inputs(project, expected):
    for rel, digest in expected.items():
        p = project / rel
        if p.is_symlink() or not p.is_file() or sha(p) != digest:
            raise ValueError('Original input changed: ' + rel)
    actual = set()
    for folder, dirs, names in project.walk():
        dirs[:] = [n for n in dirs if n not in EXCLUDED]
        for name in names:
            # A Windows dependency junction may be reported in filenames.
            if name in EXCLUDED:
                continue
            p = folder/name
            if p.is_symlink():
                raise ValueError('Unexpected linked input')
            actual.add(p.relative_to(project).as_posix())
    if actual != set(expected):
        raise ValueError('Unexpected or missing build-project input files')

def deployment_environment(kind, api_prefix, public_base):
    route(api_prefix,False)
    route(public_base,True)
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(('VITE_','UNI_'))
           and k.upper() not in ('NODE_OPTIONS','NODE_ENV','DEBUG')}
    env.update({'NODE_ENV':'production','BROWSER':'none'})
    if kind == 'mobile':
        env.update({'UNI_PLATFORM':'h5','VITE_SERVER_BASEURL':api_prefix,'VITE_APP_PROXY':'true',
                    'VITE_APP_PROXY_PREFIX':api_prefix,'VITE_APP_PUBLIC_BASE':public_base,
                    'VITE_DELETE_CONSOLE':'true','VITE_SHOW_SOURCEMAP':'false'})
    else:
        env.update({'VITE_API_URL':api_prefix,'VITE_APP_BASE_PATH':public_base.rstrip('/')})
    return env

def restore_mobile_generated_manifest(project, expected, source_project, public_base, output):
    """UniManifest writes its generated router base into the independent copy."""
    rel='src/manifest.json'
    source=Path(source_project).resolve()/rel
    target=project/rel
    if sha(target)==expected[rel]:return False
    if sha(source)!=expected[rel]:raise ValueError('Pristine source manifest changed')
    original=json.loads(source.read_text(encoding='utf-8-sig'))
    generated=json.loads(target.read_text(encoding='utf-8-sig'))
    allowed=json.loads(json.dumps(original))
    allowed['h5']['router']['base']=public_base
    if generated!=allowed:raise ValueError('Unexpected compiler-generated manifest changes')
    for path,digest in expected.items():
        if path!=rel and sha(project/path)!=digest:
            raise ValueError('Unexpected compiler change to original input: '+path)
    (output/'compiler_generated_manifest.json').write_bytes(target.read_bytes())
    shutil.copyfile(source,target)
    verify_inputs(project,expected)
    return True

def build(kind, project, manifest_path, node, output, api_prefix, public_base, source_project=None,
          use_local_command=False,mobile_qr_url=None):
    project, manifest_path, node, output = (Path(x).resolve() for x in (project,manifest_path,node,output))
    if kind not in KINDS or not project.is_dir() or not node.is_file():
        raise ValueError('Missing original project or explicit Node executable')
    route(api_prefix,False);route(public_base,True)
    if (use_local_command or mobile_qr_url) and kind!='security_pc':
        raise ValueError('Portal deployment adapters apply only to original security PC')
    if use_local_command:
        if source_project is None:
            raise ValueError('Command deployment adapter requires a pristine original source root')
        verify_inputs(Path(source_project).resolve(),baseline_files(json.loads(manifest_path.read_text(encoding='utf-8-sig')),kind))
    if mobile_qr_url:mobile_entry_url(mobile_qr_url)
    if output.exists() or output.is_relative_to(project) or project.is_relative_to(output):
        raise ValueError('Fresh independent output required')
    if source_project is not None:
        pristine=Path(source_project).resolve()
        if output.is_relative_to(pristine) or pristine.is_relative_to(output):
            raise ValueError('Build output must not overlap the pristine source tree')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    expected = baseline_files(manifest,kind)
    verify_inputs(project,expected)
    if kind=='mobile':
        if source_project is None or Path(source_project).resolve()==project:
            raise ValueError('Mobile compiler requires a distinct pristine source project')
        verify_inputs(Path(source_project).resolve(),expected)
    cli = project / ('node_modules/@dcloudio/vite-plugin-uni/bin/uni.js' if kind=='mobile' else 'node_modules/vite/bin/vite.js')
    if not cli.is_file():
        raise ValueError('Existing original locked dependencies are required; no automatic installation')
    env = deployment_environment(kind,api_prefix,public_base)
    output.mkdir(parents=True)
    dist=output/'dist'
    command=[str(node),str(cli),'build','--mode','replica-deploy','--outDir',str(dist)]
    if kind!='mobile':command+=['--base',public_base]
    start=time.monotonic()
    restored=False
    command_adapter=None;qr_adapter=None
    try:
        with (local_command_override(project,source_project) if use_local_command else nullcontext()) as command_adapter:
            with (output/'build.log').open('wb') as log:
                process=subprocess.run(command,cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300,
                                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    finally:
        if kind=='mobile':
            restored=restore_mobile_generated_manifest(project,expected,source_project,public_base,output)
    verify_inputs(project,expected)
    success=process.returncode==0 and (dist/'index.html').is_file()
    if not success:
        raise RuntimeError('Original compiler failed; private build.log retained')
    if mobile_qr_url:qr_adapter=replace_output_mobile_qr(dist,mobile_qr_url)
    files=[{'path':p.relative_to(dist).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dist.rglob('*')) if p.is_file()]
    counts={k:0 for k in ('undefined/serv','undefined/jnpf',api_prefix)}
    for p in dist.rglob('*.js'):
        data=p.read_bytes()
        for text in counts:counts[text]+=data.count(text.encode())
    if counts['undefined/serv'] or counts['undefined/jnpf'] or not counts[api_prefix]:
        raise ValueError('Compiled API address verification failed')
    receipt={'recordedAt':datetime.now().astimezone().isoformat(timespec='seconds'),'kind':kind,
             'mode':'replica-deploy','command':command,'nodeSHA256':sha(node),'sourceManifestSHA256':sha(manifest_path),
             'sourceInputFilesVerified':len(expected),'sourceFilesUnchanged':True,'sourceLogicPatched':bool(command_adapter),
             'localCommandDeploymentAdapter':command_adapter,'mobileQRDeploymentAdapter':qr_adapter,
             'compilerGeneratedManifestRestored':restored,
             'deploymentOverrides':{k:v for k,v in env.items() if k.startswith(('VITE_','UNI_'))},
             'seconds':round(time.monotonic()-start,3),'exitCode':process.returncode,'output':str(dist),
             'fileCount':len(files),'bytes':sum(r['bytes'] for r in files),'files':files,'compiledPathOccurrences':counts,
             'originalSourceRoutesAndPagesPreserved':True,'backendConnected':False,'publicDeployed':False,
             'businessParityVerified':False}
    (output/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',choices=KINDS,required=True)
    for name in ('project','source-manifest','node','output'):ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--api-prefix',default='/tianjinrisk/api')
    ap.add_argument('--public-base')
    ap.add_argument('--source-project',type=Path)
    ap.add_argument('--use-local-command',action='store_true')
    ap.add_argument('--mobile-qr-url')
    a=ap.parse_args()
    r=build(a.kind,a.project,a.source_manifest,a.node,a.output,a.api_prefix,a.public_base or KINDS[a.kind],a.source_project,a.use_local_command,a.mobile_qr_url)
    print(json.dumps({k:r[k] for k in ('kind','fileCount','bytes','seconds','sourceInputFilesVerified','sourceFilesUnchanged','compiledPathOccurrences','backendConnected','publicDeployed')}))

if __name__=='__main__':main()
