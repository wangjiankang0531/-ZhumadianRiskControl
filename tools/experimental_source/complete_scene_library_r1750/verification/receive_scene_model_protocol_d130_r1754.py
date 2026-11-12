"""Independently receive exact D130 sources while preserving the qualified receiver and all previews."""
from pathlib import Path,PurePosixPath
import ast,hashlib,json,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';W=R/'work/d130-source-receiver-r1754';D=R/'Document/Deployment/d130_source_receiver_r1754_20261107'
h=json.loads((R/'Document/Coordination/交接消息/驻马店三维D130模型持久化CAS与原鉴权传输_给驻马店3_20261107.json').read_bytes());zpath=Path(h['sourceZIP']);raw=zpath.read_bytes()
assert len(raw)==1363541 and hashlib.sha256(raw).hexdigest()=='b8d6cafe6ec15fdb4a364804fa949e86e82c546eac80f63763f7674969442fb3'and h['sourceCommit']=='642ac71599ee75301e1e21618481906cd7c27940'
assert not W.exists()and not D.exists();bodies={};records={}
with zipfile.ZipFile(zpath)as z:
 names=[n for n in z.namelist()if not n.endswith('/')];assert len(names)==len(set(names))==316
 for n in names:
  p=PurePosixPath(n);assert not p.is_absolute()and '..'not in p.parts and p.as_posix()==n and not any(c in n for c in [chr(10),chr(13),chr(92),':'])and p.suffix.lower()not in ['.exe','.dll','.class','.jar','.png','.zip']
  b=z.read(n);b.decode('utf8');assert len(b)<4*1048576;bodies[n]=b
 wire=('\n'.join(h['sourceCommit']+':'+n for n in names)+'\n').encode('utf8');p=subprocess.run(['git','-C',str(A),'cat-file','--batch'],input=wire,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0;offset=0
 for n in names:
  end=p.stdout.index(b'\n',offset);header=p.stdout[offset:end].decode('ascii').split();assert len(header)==3 and header[1]=='blob';length=int(header[2]);offset=end+1;body=p.stdout[offset:offset+length];assert body==bodies[n]and p.stdout[offset+length:offset+length+1]==b'\n';offset+=length+1;records[n]={'bytes':length,'sha256':hashlib.sha256(body).hexdigest(),'blob':header[0]}
 assert offset==len(p.stdout)
 prefix='tools/experimental_source/scene_model_sync_20261107/';pins=json.loads(bodies[prefix+'source-pins.json'])['files']
 for n,digest in pins.items():assert hashlib.sha256(bodies[prefix+n]).hexdigest()==digest
 selected={n:b for n,b in bodies.items()if n.startswith(prefix+'candidate/scene_model_sync/')or n.startswith(prefix+'candidate/web/')and PurePosixPath(n).name in ['cloud_layer_client.js','scene_models_sync.js','scene_models.test.mjs','scene_models_transport.test.mjs','scene_models_cases.json']}
 assert len([n for n in selected if '/scene_model_sync/'in n])==4
 for n,b in selected.items():
  if n.endswith('.py'):ast.parse(b)
 W.mkdir()
 for n,b in selected.items():
  p=W/n.removeprefix(prefix+'candidate/');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
D.mkdir();proof={'schema':'xnby.D130.receiver.v1','passed':True,'sourceCommit':h['sourceCommit'],'sourceArchiveSHA256':hashlib.sha256(raw).hexdigest(),'archiveFilesMatchedGit':316,'candidatePinsVerified':len(pins),'selectedReviewFiles':sorted(selected),'installedOrMerged':False,'senderRuntimeTestsNotClaimedAsReceiverTests':True,'namedCompleteSceneLibraryAndLiveStateKeptDistinct':True,'ownIdentityPrivateAssetFetcherAndNewSceneFileClientMustBeKeptDuringFutureMerge':True,'publicUpdated':False,'publicPushed':False,'sourceClosure':records}
(D/'received-d130.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in proof.items()if k!='sourceClosure'}))
