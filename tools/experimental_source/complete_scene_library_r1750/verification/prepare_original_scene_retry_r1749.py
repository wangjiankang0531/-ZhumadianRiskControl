from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((R/'work/su1746/verified-result.json').read_bytes())
assert prior['actualTerminals'][0]['earlyExitBeforeRunAllocation']and prior['allActualJobsZeroBeforeClose']and not(R/'work/su1746/scene-file-write-intent.private.json').exists()
assert not(R/'work/scene-files-original-r1745/cloud-scenes').exists()
for old,new in [('original_configuration_lifecycle_r1746.mjs','original_configuration_lifecycle_r1749.mjs'),('run_original_configuration_lifecycle_r1746.py','run_original_configuration_lifecycle_r1749.py'),('launch_original_configuration_lifecycle_r1746.py','launch_original_configuration_lifecycle_r1749.py')]:
 s=(V/old).read_text('utf8').replace('r1746','r1749').replace('su1746','su1749').replace('r1745','r1748')
 for name in ['prepared-plan.private.json','resource-and-reconciliation.json']:
  s=s.replace(sha(R/'work/fine-browser-parent-r1745'/name),sha(R/'work/fine-browser-parent-r1748'/name))
 if new.endswith('.py'):ast.parse(s)
 p=V/new;assert not p.exists();p.write_text(s,encoding='utf8')
print('NEW_ORIGINAL_PARENT_RETRY_READY_PRIOR_DID_NOT_START_OR_POST')
