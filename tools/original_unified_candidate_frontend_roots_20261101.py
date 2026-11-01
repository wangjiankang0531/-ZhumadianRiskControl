"""Read only the actual staged combined frontend bytes and the pinned published gateway."""
from pathlib import Path
import json,hashlib,importlib.util
R=Path('D:/Project/Zhumadian');S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
def roots():
 rows=json.loads((S/'candidate-stage.json').read_bytes())['allMaterializedPayloadFiles'];found={}
 for kind,count in [('security_pc',836),('emergency_pc',204)]:
  prefix='frontend/'+kind+'/';selected={n:v for n,v in rows.items()if n.startswith(prefix)};assert len(selected)==count
  for n,pin in selected.items():
   p=S/'payload'/n;assert p.resolve()==p.absolute()and not p.lstat().st_file_attributes&0x400 and p.stat().st_size==pin['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256']
  found[kind]=S/'payload/frontend'/kind
 return found
def prepare(*args,**kwargs):
 p=S/'public-control/tools/prepare_original_frontend_gateway.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='006b17531f83d548d161b332531ff4c75e395816780744e033a52d56b5541cc8';spec=importlib.util.spec_from_file_location('exact_published_gateway_r21',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.prepare(*args,**kwargs)
