from pathlib import Path
import ast,hashlib,json,shutil

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
old=json.loads((D/'transaction-sources-r340.json').read_bytes())
assert not(D/'transaction-sources-r342.json').exists()
free=shutil.disk_usage(R).free;maximum=1024**3
assert free>maximum+2*1024**3
rows=[]
for row in old['sources']:
    src=V/row['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==row['sha256']
    text=src.read_text(encoding='utf-8')
    anchor='peak=(sum(map(len,baseline.values()))+sum(map(len,bodies.values())))*14'
    assert text.count(anchor)==1
    text=text.replace(anchor,'peak=(2*sum(map(len,baseline.values()))+sum(map(len,bodies.values())))*16+8*1024**2',1)
    ast.parse(text);dst=V/src.name.replace('_r340.py','_r342.py');assert not dst.exists();dst.write_text(text,encoding='utf-8')
    rows.append({'variant':row['variant'],'source':dst.name,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
proof={'prepared':True,'sources':rows,'freeBefore':free,'conservativeTwoVariantMaximumAdditionalBytes':maximum,
 'perVariantDynamicLimitBytes':512*1024**2,'sixteenFileScenariosBudgetIncludesPreimageAndWorkingCopies':True,
 'previousUnexecutedR340DriversSupersededForCorrectAllocationEstimate':True,
 'noAssetsDependenciesDatabaseOrRealConfigurationCopied':True,'servicesWillNotStart':True}
(D/'transaction-sources-r342.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items()if k!='sources'}))
