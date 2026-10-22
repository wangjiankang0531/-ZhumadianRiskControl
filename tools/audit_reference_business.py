"""Inventory business reference interfaces without executing code or reading secrets."""
import argparse,hashlib,json,re
from pathlib import Path
def audit(root):
 root=Path(root);pom=next(root.rglob('cloud-endanger/pom.xml'));server=pom.parent;mobile=next(root.rglob('whwly-mobile/src/pages.json')).parent
 java=list((server/'src/main/java').rglob('*.java'));services=list((mobile/'service').rglob('*.ts'))
 report={'schema':'xnby.reference.business.audit.v1','javaFiles':len(java),'mobilePageRoutes':json.loads((mobile/'pages.json').read_text(encoding='utf-8'))['pages'],'controllers':[],'mobileServices':[],'sourceInputs':{}}
 for path in java:
  raw=path.read_bytes();text=raw.decode('utf-8-sig');name=path.relative_to(root).as_posix()
  if '@RestController' in text:
   report['controllers'].append({'file':name,'routes':re.findall(r'@(Get|Post|Put|Delete|Request)Mapping\s*\(\s*"([^"\n]+)"',text),'hasIgnoreAuth':'@IgnoreAuth' in text})
   report['sourceInputs'][name]=hashlib.sha256(raw).hexdigest()
 for path in services:
  if 'interface' in path.parts or path.name!='index.ts':continue
  raw=path.read_bytes();text=raw.decode('utf-8-sig');name=path.relative_to(root).as_posix();routes=re.findall(r'http\.(get|post|put|delete)(?:<[^\n]+?>)?\(\s*[\x27\x22`]([^\x27\x22`\n]+)',text)
  report['mobileServices'].append({'file':name,'routes':routes});report['sourceInputs'][name]=hashlib.sha256(raw).hexdigest()
 report['controllerCount']=len(report['controllers']);report['mobileEndpointReferences']=sum(len(s['routes']) for s in report['mobileServices'])
 report['reuseDecision']='Port explicit business invariants to the existing authenticated backend; do not deploy private endpoints, credentials, IgnoreAuth or unavailable workflow/organization infrastructure.'
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=audit(a.root);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ('javaFiles','controllerCount','mobileEndpointReferences')}))
