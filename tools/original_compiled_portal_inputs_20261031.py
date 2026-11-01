"""Restore only the fixed R10 emergency frontend and construct owned-test portal menu data."""
from pathlib import Path
import re,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';P=R/'Application/work/tianjin_native_20261023/emergency_pc'
def frontend_wire_key():
 text=(P/'src/utils/common.ts').read_text(encoding='utf-8');m=re.search(r'''if\s*\(!cipherKey\)\s*cipherKey\s*=\s*(['"])([^'"\\]+)\1;''',text)
 if not m or len(m[2].encode()) not in [16,24,32]:raise RuntimeError('PUBLIC_COMPILED_CLIENT_WIRE_KEY_CONTRACT_REQUIRED')
 return m[2]
def materialize(root):
 root=Path(root);assert root.parent==R/'work/event_delivery_consistency_20261030' and re.fullmatch('full-business-main-r[1-9][0-9]*',root.name);bundle=R/'work/emergency_plan_report_20261030/local-update-emergency-modules-r10';assert hashlib.sha256((bundle/'update-manifest.json').read_bytes()).hexdigest()=='155c96bd54ab4fda8ef94d102f9c1bab769b342f809edd2c2365ef54fb9e9f7a';meta=json.loads((bundle/'payload/payload-manifest.json').read_text(encoding='utf-8'));files={n:v for n,v in meta['files'].items() if n.startswith('frontend/emergency_pc/')};assert len(files)==206;destination=root/'compiled-frontend';assert not destination.exists();destination.mkdir();rows={}
 for n,v in files.items():
  relative=Path(n).relative_to('frontend/emergency_pc');assert '..' not in relative.parts;source=bundle/'payload'/n
  if not source.exists():source=Path('D:/Zqa20261025/Application')/n
  assert not source.lstat().st_file_attributes&0x400;raw=source.read_bytes();assert len(raw)==v['bytes'] and hashlib.sha256(raw).hexdigest()==v['sha256'];target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);rows[str(relative)]={'SHA256':v['sha256'],'bytes':v['bytes'],'fromFixedDelta':source.is_relative_to(bundle)}
 (root/'compiled-frontend-materialization.json').write_text(json.dumps({'files':rows,'fileCount':206,'allBytesMatchedFixedR10':True,'frontendModifiedOrRebuilt':False,'formalFrontendReadOnly':True},indent=2),encoding='utf-8');return destination
