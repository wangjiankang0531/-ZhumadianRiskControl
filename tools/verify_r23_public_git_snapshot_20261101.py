"""Independently verify frozen bytes, syntax, source aliases and fixed transport."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys,zipfile

R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/public_test_unified_r23_20261101'
F=R/'work/user_feedback_20261031/public-git-r23-fixed-r1';T=R/'Application/tools'
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_bytes())
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
p=D/'public-git-sync-manifest.json';assert len(sys.argv)==2 and sha(p.read_bytes())==sys.argv[1]
m=read(p);seen=set();python_count=json_count=node_count=ps_count=0
patterns=[r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}',
          r'\bsk-[A-Za-z0-9_-]{24,}',r'\bAKIA[A-Z0-9]{16}\b',r'[\"\']eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+']
for row in m['files']:
    f=Path(row['snapshot']);assert f.is_relative_to(F)and f.is_file()and not f.is_symlink()
    assert not set(Path(row['path']).parts).intersection({'Assets','Reference','UserData','private','.git','node_modules'})
    raw=f.read_bytes();text=raw.decode('utf-8');assert len(raw)==row['bytes']and sha(raw)==row['sha256']and blob(raw)==row['gitBlobSHA1']
    assert all(not re.search(pattern,text)for pattern in patterns),'CREDENTIAL_SHAPE:'+row['path']
    for found in re.findall(r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',text):
        assert found.lower().startswith(('a531','00000000','11111111','22222222'))or found.upper()=='96240625-934F-490B-8AA6-0BC775B18468','UNKNOWN_IDENTIFIER:'+row['path']
    if f.suffix=='.py':ast.parse(text);compile(text,str(f),'exec');python_count+=1
    if f.suffix=='.json':json.loads(raw);json_count+=1
    if f.suffix=='.mjs':subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(f)],check=True,capture_output=True);node_count+=1
    if f.suffix=='.ps1':
        # Parser only: this never invokes the script or any of its statements.
        code='$tokens=$null;$errors=$null;[void][System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$tokens,[ref]$errors);if($errors.Count){exit 1}'
        cmd='& { '+code+' } '+"'"+str(f).replace("'","''")+"'"
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',cmd],check=True,capture_output=True);ps_count+=1
    seen.add(f)
assert seen=={p for p in F.rglob('*')if p.is_file()}and len(seen)==m['fileCount']
assert sum(row['bytes']for row in m['files'])==m['bytes']
assert m['existingBranchesOnly']and m['oneCurrentPublicParentPerCommit']and not m['sendPrivateAncestors']and not m['mainOrOtherBranchesChanged']
assert not m['publicObjectsCreated']and not m['publicDeployed']and not m['approvalGranted']and not m['sourceRepositoryStandaloneCleanBuildClaimed']
expected={'serve_original_server_release.py':'8b6006fac79e096939bfb7b2cffc333c1bcd39dc01f9d43070c68dee4f402660',
 'original_server_windows_job.py':'e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22',
 'original_public_test_update.py':'d500b5b591971532a74dd632d2cff7139474bd61986c01bc75b184017c143d41',
 'original_platform_async_release_support.py':'541699cbbb7792f6f1b71813eed32f7441c6bf696539aed6deaa20d963eeb078',
 'original_server_release_parameters.py':'8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9',
 'prepare_original_frontend_gateway.py':'006b17531f83d548d161b332531ff4c75e395816780744e033a52d56b5541cc8'}
for name,digest in expected.items():assert sha((F/'application/tools'/name).read_bytes())==digest
assert sha((D/'delivery-manifest.json').read_bytes())==m['deliveryManifestSHA256']
with zipfile.ZipFile(next((D/'delivery').glob('*.zip')))as z:
    assert z.testzip()is None
    for name in list(expected)[:4]:assert sha(z.read('payload/tools/'+name))==expected[name]
assert sha((D/'delivery/r23_update_runtime.py').read_bytes())==expected['original_public_test_update.py']
old=R/'Document/Deployment/public_test_risk_r22_20261101'
assert sha((old/'public-git-sync-manifest.json').read_bytes())=='df81999b5ff6c40aa476e89c457e633dbf29bf1f52436a05d102274e86e7f275'
assert sha((old/'delivery-manifest.json').read_bytes())=='9482746b9a8a7d7ccbe7a6279ca813bb3fda05ed83bf188f8da042f4dba7f5f5'
result={'manifestSHA256':sys.argv[1],'files':len(seen),'bytes':m['bytes'],'pythonParsedAndCompiled':python_count,
 'jsonParsed':json_count,'nodeSyntaxChecked':node_count,'powershellParserChecked':ps_count,'credentialShapeAndUnknownIdentifierFindings':0,
 'allFrozenBytesAndBlobHashesVerified':True,'actualSixControlSourceAliasesVerified':True,
 'actualFourZipControlPayloadsAndTransportUpdaterMatchPublicSource':True,'oldR22FrozenScopeAndR23TransportUnchanged':True,
 'publicWritesPerformed':False,'publicDeployed':False,'fullCloneReady':False,'standaloneCleanBuildClaimed':False}
(D/'public-git-independent-verification-r118.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
