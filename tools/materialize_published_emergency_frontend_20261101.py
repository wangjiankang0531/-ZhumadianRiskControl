"""Recover exact 204-file public emergency frontend; no older candidate substitution."""
from pathlib import Path
import hashlib,json,shutil,urllib.request
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application');W=R/'work';D=W/'user_feedback_20261031/published-emergency-frontend-r1';BASE=W/'user_feedback_20261031/r22-risk-candidate-r3/r21-base-payload-manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def materialize():
 assert sha(BASE)=='2ef7ada7b156166009f7b7d9483d34e1ec36237446a07c80813f32903e28f720';files={k.removeprefix('frontend/emergency_pc/'):v for k,v in json.loads(BASE.read_bytes())['files'].items()if k.startswith('frontend/emergency_pc/')};assert len(files)==204
 if D.exists():
  receipt=json.loads((D/'source-proof.json').read_bytes());assert receipt['manifestSHA256']==sha(BASE)
  for n,pin in files.items():assert sha(D/'frontend'/n)==pin['sha256']and(D/'frontend'/n).stat().st_size==pin['bytes']
  return D/'frontend'
 roots=[Q,*[W/('public_test_update_20261029_'+r)/sub/'bundle/payload'for r,sub in [('r16','from-r15'),('r15','from-r14'),('r14','from-r8')]]];prepared={};sources={}
 for n,pin in files.items():
  assert '..'not in Path(n).parts and not Path(n).is_absolute()
  for source in roots:
   p=source/'frontend/emergency_pc'/n
   if p.is_file()and not p.lstat().st_file_attributes&0x400 and sha(p)==pin['sha256']:prepared[n]=p.read_bytes();sources[n]=str(p);break
  else:
   assert n in ['assets/css/index-COsv9OER.css','assets/css/index-DYzDggvx.css'];url='https://www.joinlinksmart.com/zhumadian/emergency/'+n
   with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url,timeout=15)as response:assert response.status==200 and response.url==url;prepared[n]=response.read(262145);sources[n]=url
  assert len(prepared[n])==pin['bytes']and hashlib.sha256(prepared[n]).hexdigest()==pin['sha256']
 D.mkdir();target=D/'frontend';target.mkdir()
 for n,raw in prepared.items():p=target/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 (D/'source-proof.json').write_text(json.dumps({'manifestSHA256':sha(BASE),'publishedFiles':204,'oldR10Files206NotUsed':True,'files':files,'sources':sources,'sourceFilesModified':False},indent=2),encoding='utf-8');return target
if __name__=='__main__':print('EXACT_PUBLISHED_EMERGENCY_FRONTEND',materialize())
