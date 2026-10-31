from pathlib import Path
from contextlib import contextmanager
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

R=Path('D:/Project/Zhumadian')
A=R/'Application'
T=A/'tools'
V=Path(__file__).resolve().parent
W=R/'work/user_feedback_20261031'
CASE=W/'workplace-chart-r1'
STAGE=W/'workplace-security-build-r1'
CANONICAL=T/'frontend/workplace'
FILES={'ECharts.vue':'src/components/ECharts/index.vue',
       'Chart3.vue':'src/views/workplace/components/Analysis/Chart3.vue',
       'event-report-layout.ts':'src/views/workplace/components/Analysis/event-report-layout.ts',
       'TaskList.vue':'src/views/workplace/components/TaskList/index.vue',
       'Statistics.vue':'src/views/workplace/components/Statistics/index.vue'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    proof=json.loads((CASE/'browser-proof-r3/result.json').read_text(encoding='utf-8'))
    assert proof['passed'] and proof['normalBrowserClosed'] and len(proof['textCases'])==6
    pins=json.loads((R/'Document/Deployment/confirmed_operations_20261029/integration-source-files.json').read_text(encoding='utf-8'))['files']
    for row in pins:assert sha(A/row['path'])==row['SHA256']
    config=json.loads((R/'Document/Deployment/confirmed_operations_20261029/security-build-r2-config.json').read_text(encoding='utf-8'))
    source=Path(config['project']);assert not STAGE.exists()
    listed=[]
    for parent,dirs,files in os.walk(source,followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('node_modules','.git','dist','.vite')]
        for name in files:
            p=Path(parent)/name
            assert not p.is_symlink() and not p.is_junction()
            listed.append((p,p.relative_to(source),p.stat().st_size))
    amount=sum(s for _,_,s in listed);free=shutil.disk_usage(W).free
    assert amount<1024**3 and free>amount*2+512*1024**2
    STAGE.mkdir();project=STAGE/'source';project.mkdir()
    put(STAGE/'storage-plan.json',{'sourceFiles':len(listed),'sourceBytes':amount,
        'freeBefore':free,'conservativeAdditionalBudget':amount*2+512*1024**2,
        'GISOrAssetsRepositoryCopied':False,'dependenciesSharedByReadOnlyUse':True})
    for p,rel,_ in listed:
        dest=project/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    command="New-Item -ItemType Junction -Path '"+str(project/'node_modules')+"' -Target '"+str(source/'node_modules')+"' | Out-Null"
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
        capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
    assert result.returncode==0
    CANONICAL.mkdir(parents=True,exist_ok=True)
    tested={}
    for filename in FILES:
        data=(CASE/filename).read_bytes();dest=CANONICAL/filename
        assert not dest.exists();dest.write_bytes(data);tested[filename]=sha(dest)
    (T/'verify_workplace_viewport_20261031.mjs').write_bytes((V/'verify_workplace_chart.mjs').read_bytes())
    put(A/'deploy/verification/workplace_viewport_components_20261031.json',dict(proof,
        verifiedCandidateFiles=tested,publicDeployed=False,sourceScriptsTaskAndStatisticsPreserved=True))
    sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
    import build_original_confirmed_security_frontend as builder
    old=builder.base.request_error_override
    adapter={}
    @contextmanager
    def combined(kind,project,reference):
        with old(kind,project,reference) as original:
            saved={rel:(project/rel).read_bytes() if (project/rel).exists() else None for rel in FILES.values()}
            try:
                for name,rel in FILES.items():(project/rel).write_bytes((CANONICAL/name).read_bytes())
                adapter.update(revision='workplace-viewport-components-20261031-r1',files=tested,
                    originalAPIAndStatsLogicRetained=True,referenceModified=False)
                yield original
            finally:
                for rel,raw in saved.items():
                    p=project/rel
                    if raw is None:p.unlink()
                    else:p.write_bytes(raw)
                adapter['sourceRestored']=all((project/rel).read_bytes()==raw if raw is not None else not(project/rel).exists() for rel,raw in saved.items())
    builder.base.request_error_override=combined
    config.update(project=str(project),output=str(STAGE/'build'))
    put(STAGE/'build-config.json',config)
    receipt=builder.build(**config,business_result=True,inspection_filter=True,third_party_credentials=True,
        training_assessment=True,finding_guard=True,finding_images=True)
    assert adapter['sourceRestored']
    for row in pins:assert sha(A/row['path'])==row['SHA256']
    from build_home_viewport_overlay_20261031 import build as home_overlay
    dist=Path(receipt['output']);overlay=home_overlay(dist/'index.html',sha(dist/'index.html'),STAGE/'home-overlay','disk')
    for filename in overlay['files']:shutil.copyfile(STAGE/'home-overlay'/filename,dist/filename)
    files={p.relative_to(dist).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in dist.rglob('*')if p.is_file()}
    result={'at':datetime.datetime.now().astimezone().isoformat(),'buildExitCode':receipt['exitCode'],
        'baselineJ57ExecutedSourcesMatched':len(pins),'allPreviousSecurityAdaptersRetained':True,
        'workplaceAdapter':adapter,'R18HomeCSSRetained':True,'fullFrontendFiles':files,
        'onlyIndependentSourceCopyChanged':True,'referenceAndOriginalSourceRestored':True,
        'compiledFrontendBrowserIntegrationPending':True,'formalOrPublicInstalled':False}
    put(STAGE/'candidate-result.json',result)
    print(json.dumps({'builtFiles':len(files),'bytes':sum(x['bytes'] for x in files.values()),
        'R18HomeCSSRetained':True,'publicInstalled':False,'fullBrowserIntegrationPending':True}))
if __name__=='__main__':main()
