"""Receive D97 sources by actual Git blobs; do not execute sender tests or demos."""
from pathlib import Path,PurePosixPath
import hashlib,json,re,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
message=R/'Document/Coordination/交接消息/驻马店三维D97浏览器草稿恢复界面_给驻马店3_20261106.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
x=json.loads(message.read_bytes());assert x['publicDeploymentRequested']is False and x['doNotDeploySyntheticFixtures']is True
s=x['source'];commit=s['applicationCommit'];assert commit=='1b7c1eb1cdeb4b764bf86036bf7ba76ed088c93f'and re.fullmatch('[0-9a-f]{40}',commit)
arc=s['sourceArchive'];p=Path(arc['path']);assert p.is_relative_to(R/'Document/Deployment')and p.stat().st_size==arc['bytes']and sha(p)==arc['sha256']
checks=[]
with zipfile.ZipFile(p)as z:
 entries=z.infolist();assert len(entries)==8 and set(z.namelist())==set(s['files'])and sum(e.file_size for e in entries)<16*1024**2
 for e in entries:
  n=PurePosixPath(e.filename);assert not n.is_absolute()and '..'not in n.parts and '\\'not in e.filename and ':'not in e.filename and not e.flag_bits&1 and not e.is_dir()
  raw=z.read(e);b=subprocess.run(['git','-C',str(A),'cat-file','blob',commit+':'+e.filename],capture_output=True,check=True).stdout;assert raw==b
  blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob==s['files'][e.filename]
  checks.append({'path':e.filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gitBlob':blob})
 assert z.testzip()is None
proof={'passed':True,'messageSHA256':sha(message),'senderCommit':commit,'actualSourceBlobsMatched':checks,'actualGitBlobsMatched':len(checks),'senderRuntimeOrBrowserChecksIndependentlyReplayed':False,'sourceOnlyReceiverReview':True,'peerPreviewOrDataTouched':False,'noSyntheticLoginOrFixtureDeployed':True,'publicDeploymentRequested':False,'realNormalHostLoginAndTLS252StillPending':True,'sharedFileNotRealtimeCommunication':True}
out=V/'receiver-d97-source-check-r1209.json';assert not out.exists();out.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'actualGitBlobsMatched':len(checks),'publicOrPeerRuntimeChanged':False}))
