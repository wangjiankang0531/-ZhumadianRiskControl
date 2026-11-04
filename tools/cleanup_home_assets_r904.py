"""Remove only verified owned static-fixture copies and exited browser caches."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil,subprocess,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application'
S=V/'performance-assets-r893';D=R/'Document/Deployment/home_transfer_candidate_r903_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
assert not(D/'cleanup-r904.json').exists()
assert J(R/'work/ha902/gateway-result.json')['passed']
plan=J(V/'feedback_r889/full-source-and-restore-plan.private.json')
script=ast.parse((V/'run_home_asset_gateway_r896.py').read_bytes())
base=ast.literal_eval(next(n.value for n in script.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='base'for t in n.targets)))
targets=[];checked=0
def add(root):
    assert root.is_dir() and root.resolve()==root.absolute()
    assert root.resolve().is_relative_to(R/'work')or root.resolve().is_relative_to(S)
    for p in [root,*root.rglob('*')]:assert not(p.lstat().st_file_attributes&0x400),'NO_REPARSE_REQUIRED'
    targets.append(root)
for name,built_name in [('gateway-r896','lossless-candidate-r895.json'),('ha897','lossless-candidate-r895.json'),('ha898','lossless-candidate-r895.json'),('ha899','lossless-candidate-r895.json'),('ha900','lossless-candidate-r900.json'),('ha901','lossless-candidate-r900.json'),('ha902','lossless-candidate-r900.json')]:
    w=S/name if name.startswith('gateway')else R/'work'/name
    built=J(S/built_name);expected={}
    for n in ['assets/css/index-ClWHaJx5.css','assets/css/index-DoM5WgUA.css','assets/png/background-BHYqFd8n.png','assets/png/header-Cp7ANu3F.png','assets/png/title_line-B0Cs5B57.png','assets/ttf/YouSheBiaoTiHei-fahbdFno.ttf']:
        expected[n]=plan['sources']['frontend/security_pc/'+n]['sha256']
    expected.update({n:p['sha256']for n,p in built['files'].items()if n!='index.html'})
    extra=next(n for n in built['files']if n.endswith('.css'))
    for variant in ['baseline','candidate']:
        link='' if variant=='baseline'else'<link rel="stylesheet" href="/zhumadian/'+extra+'">'
        expected[variant+'.html']=hashlib.sha256(base.replace('EXTRA',link).encode('utf8')).hexdigest()
    www=w/'www';actual={p.relative_to(www/'zhumadian').as_posix():sha(p)for p in www.rglob('*')if p.is_file()}
    assert actual==expected, 'EXACT_OWN_STATIC_COPY_REQUIRED:'+name
    add(www);checked+=len(actual)
    control=w/'control-app';known={'tools/original_project_branding.py':plan['sources']['tools/original_project_branding.py']['sha256'],'deploy/branding/zhumadian-emergency.svg':plan['sources']['deploy/branding/zhumadian-emergency.svg']['sha256']}
    assert {p.relative_to(control).as_posix():sha(p)for p in control.rglob('*')if p.is_file()}==known
    add(control);checked+=2
    if name in ['ha899','ha900','ha901','ha902']:
        proof=J(w/'gateway-result.json');assert all(t['actualJobDescendantsZero']and not t['forceTerminationUsed']for t in proof['terminals'].values())
        browser=w/'browser-r896';term=J(browser/'browser-terminal.json')
        assert term['normalCloseRequested']and term['exitCode']==0 and not term['forceTerminationUsed']
        add(browser/'chrome-profile')
        if name!='ha902':
            rows=J(browser/'result.json')['rows']
            for p in browser.glob('*.png'):
                row=next(r for r in rows if p.name==r['variant']+'-'+str(r['width'])+'.png');assert sha(p)==row['screenshotSHA256']
                # Individual saved test frames are verified then removed below.
                targets.append(p)
old=J(S/'lossless-candidate-r895.json');p=S/'candidate-r895'
assert {f.relative_to(p).as_posix():sha(f)for f in p.rglob('*')if f.is_file()}=={n:p['sha256']for n,p in old['files'].items()};add(p)
p=S/'candidate';files=[x for x in p.rglob('*')if x.is_file()];assert len(files)==1 and sha(files[0])==old['image']['outputSHA256'];add(p)
assert len(targets)==len(set(targets))and all(not a.is_relative_to(b)for a in targets for b in targets if a!=b)
needles=json.dumps([str(p).replace('\\','/').lower()for p in targets])
query="$ErrorActionPreference='Stop';$n=ConvertFrom-Json '"+needles.replace("'","''")+"';$count=0;Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('python.exe','pythonw.exe','nginx.exe','chrome.exe','node.exe')} | ForEach-Object {$line=([string]$_.CommandLine -replace '\\\\','/').ToLowerInvariant();foreach($s in $n){if($line.Contains($s)){$count++;break}}};$count"
result=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode==0 and result.stdout.decode('utf-8-sig').strip()=='0'
pins=[{'path':str(p),'files':sum(f.is_file()for f in p.rglob('*')) if p.is_dir()else 1,'logicalBytes':sum(f.stat().st_size for f in p.rglob('*')if f.is_file())if p.is_dir()else p.stat().st_size}for p in targets]
space=shutil.disk_usage(R).free
for p in targets:
    assert p.resolve().is_relative_to(R/'work')or p.resolve().is_relative_to(S)
    if p.is_dir():shutil.rmtree(p)
    else:p.unlink()
assert all(not p.exists()for p in targets)
proof={'passed':True,'sourceCopiesSHA256Checked':checked,'removed':pins,'observedFreeSpaceDeltaNotExclusiveAttribution':shutil.disk_usage(R).free-space,'originalsFinalCandidateDependenciesLogsFinalRenderProofAndDataRetained':True,'noProcessKilled':True,'freshSelectedProcessReferences':0,'publicChanged':False}
(D/'cleanup-r904.json').write_bytes(enc(proof))
files=[]
for rel,raw in {'tools/cleanup_home_assets_r904.py':Path(__file__).read_bytes(),'deploy/verification/home_asset_cleanup_r904_20261104.json':enc(proof)}.items():
    q=A/rel;assert not q.exists();q.write_bytes(raw);files.append(rel)
spec=importlib.util.spec_from_file_location('local_r904',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
a=h.commit(A,'80444b19fc2e6bc7484fbbacdc076e58cbb9e998','review/workplace-r19-live-local-20261031',files,'app-r904',message_override='chore: retire verified static fixture copies and exited test browser caches',update_existing=True)
(D/'local-review-git-r904.json').write_bytes(enc({'application':a,'publicPushed':False}))
print(json.dumps({'passed':True,'cleanupTargets':len(targets),'logicalBytes':sum(p['logicalBytes']for p in pins),'application':a}))
