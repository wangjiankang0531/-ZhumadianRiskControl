"""Fresh attempt after pre-allocation missing-source refusal; identical product/flight."""
from pathlib import Path
import ast,copy,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
OLD=V/'hazard_transaction_r1212';H=V/'hazard_transaction_r1214';OD=R/'Document/Deployment/hazard_attachment_transaction_r1212_20261106';D=R/'Document/Deployment/hazard_attachment_transaction_r1214_20261106'
def j(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return{'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def enc(v):return(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
assert not H.exists()and not D.exists()and not(R/'work/ht1214').exists()and not(R/'work/hazard-transaction-probe-r1214').exists()
assert j(OD/'parent-terminal-r1213.json')['actualJobDescendantsZero']and j(OD/'parent-terminal-r1213.json')['exitCode']==1
assert 'PINNED_CODE_SOURCE_REQUIRED'in(OD/'parent-r1213.private.log').read_text('utf8')
assert not(R/'work/ht1212').exists()and {p.name for p in(R/'work/hazard-transaction-probe-r1212').iterdir()}=={'own-normal-manager-test.marker'}
plan=copy.deepcopy(j(OD/'full-source-and-restore-plan.private.json'));oldSHA=sha(OD/'full-source-and-restore-plan.private.json')
for n,row in plan['mutations'].items():
 assert pin(G/n)==row['before'],'NO_CODE_CHANGE_IN_PREALLOCATION_REFUSAL'
 if row['after']is not None:row['source']=plan['sources'][n]['source']
assert pin(G/'private/server-configuration.json')==plan['configBefore']and sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
q="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe' OR Name='node.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
p=subprocess.run(['powershell.exe','-NoProfile','-Command',q],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0 and p.stdout.decode('utf-8-sig').strip()=='0'
D.mkdir();H.mkdir();(D/'flight.private.json').write_bytes((OD/'flight.private.json').read_bytes());(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan));newSHA=sha(D/'full-source-and-restore-plan.private.json')
for src in OLD.iterdir():
 if not src.is_file()or src.name.startswith('source-pins'):continue
 name=src.name.replace('r1212','r1214').replace('R1212','R1214')
 if src.suffix=='.png':(H/name).write_bytes(src.read_bytes());continue
 t=src.read_text('utf8').replace('r1212','r1214').replace('R1212','R1214').replace('ht1212','ht1214').replace(oldSHA,newSHA)
 if src.suffix=='.py':ast.parse(t)
 (H/name).write_text(t,encoding='utf8')
t=(V/'launch_hazard_transaction_r1213.py').read_text('utf8').replace('r1212','r1214').replace('R1212','R1214').replace('ht1212','ht1214').replace('r1213','r1215').replace('R1213','R1215');ast.parse(t);(V/'launch_hazard_transaction_r1215.py').write_text(t,encoding='utf8')
pins={str(p):sha(p)for p in H.iterdir()if p.is_file()}
for p in [V/'original_public_test_update_r45_bootstrap_r847.py',A/'tools/owned_candidate_code_transaction_r543.py',A/'tools/owned_run_pointer_r717.py',A/'tools/bounded_build_job_r671.py',V/'launch_hazard_transaction_r1215.py',D/'flight.private.json']:pins[str(p)]=sha(p)
(H/'source-pins-r1214.json').write_bytes(enc({'files':pins,'sameExactProductClassAndFrontend':True,'sameExistingOwnRecord':True,'previousAttemptRefusedBeforeCodeOrServicesOrBrowser':True,'onlyExplicitMutationSourcePathsFixed':True}))
(D/'previous-preallocation-refusal.json').write_bytes(enc({'missingPinnedCodeSourceRefused':True,'actualJobZero':True,'noCodeConfigurationOrDataChanged':True,'noServicesOrBrowserStarted':True,'sameFlightNotRecreated':True}))
print(json.dumps({'preparedOnly':True,'sameProductAndExistingFlight':True,'previousCodeAndServicesChanged':False,'explicitMutationSourcesFixed':True}))
