"""Freeze only the inventoried R23 source; never create remote Git objects."""
from pathlib import Path
import hashlib,json,datetime

R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_r23_20261101'
A=R/'Application';E=R/'XNBYEngine';F=R/'work/user_feedback_20261031/public-git-r23-fixed-r1'
read=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
draft=read(D/'public-source-closure-draft-r118.json')
assert not draft['credentialPatternFindings']and not draft['unknownIdentifierLiteralFindings']
assert not F.exists()and not(D/'public-git-sync-manifest.json').exists(),'FROZEN_SCOPE_ALREADY_EXISTS'
selection={(draft['bases'][0]['repo'],r['path']):(Path(r['source']),r['sha256'],r['oldPublicBlobSHA1'])for r in draft['files']}
extra=[(0,'deploy/handbook/unified-emergency-r23-source-sync-20261101.md',A),
       (1,'docs/project/r23-unified-emergency-public-progress-20261101.md',E)]
for index,rel,root in extra:
    p=root/rel;selection[(draft['bases'][index]['repo'],rel)]=(p,sha(p.read_bytes()),None)
rows=[]
for(repo,rel),(source,digest,oldblob)in sorted(selection.items()):
    base=next(x for x in draft['bases']if x['repo']==repo)
    raw=source.read_bytes();assert sha(raw)==digest,'SOURCE_DRIFT:'+rel
    assert source.suffix in{'.py','.java','.mjs','.ps1','.in','.md','.json','.vue','.ts'}
    raw.decode('utf-8');target=F/('application'if repo==draft['bases'][0]['repo']else'engine')/rel
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    rows.append({'repo':repo,'branch':base['branch'],'path':rel,'source':str(source),'snapshot':str(target),
                 'bytes':len(raw),'sha256':digest,'gitBlobSHA1':blob(raw),'oldPublicBlobSHA1':oldblob})
manifest={'schema':'xnby.r23.public-git-sync.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'files':rows,'fileCount':len(rows),'bytes':sum(r['bytes']for r in rows),'bases':draft['bases'],
 'actualControlSourceAliases':draft['aliases'],
 'deliveryManifestSHA256':'27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41',
 'fixedSnapshot':True,'existingBranchesOnly':True,'oneCurrentPublicParentPerCommit':True,
 'sendPrivateAncestors':False,'mainOrOtherBranchesChanged':False,'publicObjectsCreated':False,
 'publicDeployed':False,'approvalGranted':False,'sourceRepositoryStandaloneCleanBuildClaimed':False,
 'requiresOriginalProgramArchivesAndVerifiedPrivateInputs':True,'fullCloneReady':False}
out=D/'public-git-sync-manifest.json';out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'manifestSHA256':sha(out.read_bytes()),'files':len(rows),'bytes':manifest['bytes'],
 'applicationFiles':sum(x['repo']==draft['bases'][0]['repo']for x in rows),'engineFiles':sum(x['repo']==draft['bases'][1]['repo']for x in rows),
 'publicObjectsCreated':False}))
