"""Check static source/release pins separately from terminated historical preview processes."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';D=R/'Document/Deployment/confirmed_operations_20261029'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def git(root,*args):return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True).stdout.decode().strip()
def protected():
 rows={}
 for name in ['public_test_r13_20261029','public_test_r14_20261029','emergency_team_submit_20261029','emergency_resource_result_20261029','emergency_resource_integration_20261029','duty_submit_result_20261029','duty_result_integration_20261029','public_old_version_cleanup_20261029','public_test_r14_execution_20261029']:
  p=R/'Document/Deployment'/name/'source-files.json'
  if not p.is_file():continue
  for row in read(p)['files']:
   name=row['path']
   if Path(name).suffix not in ('.py','.mjs','.js','.json','.java','.cpp','.h'):continue
   assert name not in rows or rows[name]==row['SHA256'];assert sha(A/name)==row['SHA256'],name;rows[name]=row['SHA256']
 formal={}
 for root,pin in [(A,'f5704147137a076d4064e87c1e0d1e51178e26d7'),(E,'b89578afd4374ae30c6a5ca0c16e26183026efd1')]:
  assert git(root,'rev-parse','HEAD')==pin;index=Path(git(root,'rev-parse','--path-format=absolute','--git-path','index'));formal[root.name]={'HEAD':pin,'indexSHA256':sha(index)}
 assert formal['Application']['indexSHA256']=='5bc00d535ee2692fe12e3874f371aedd6694367a0f87125358fef45e574e5988'
 fixed=R/'Document/Deployment/public_test_r14_20261029/delivery-manifest.json';assert sha(fixed)=='d642393f1235fa07b9b89a31830ce0da5cf7c28ae783d4d24de62c5b354cbe75';delivery=list((R/'work').glob('*r14*/delivery/Zhumadian_Update_20261029_R14'));assert len(delivery)==1
 for name,row in read(fixed)['files'].items():p=delivery[0]/name;assert sha(p)==row['SHA256'] and p.stat().st_size==row['bytes']
 native=A/'native/main.cpp';raw=native.read_bytes()
 for token in [b'#include <hongtu/asset/Bc7Encoder.h>',b'#  include <bcrypt.h>',b'#include "zhumadian_native_bc7.inl"']:assert raw.count(token)==1
 return {'priorCodeFilesVerified':len(rows),'priorCodeSHA256':rows,'formalHEADAndIndex':formal,'heldNativeSourceSHA256':sha(native),'heldThreeBC7IncludesPreserved':True,'frozenPublicR14NineFilesUnchanged':True,'legacyCompositePreviewHealthNotClaimedPassed':True,'oldPreviewProcessRestorationNotPartOfThisStaticProof':True}
