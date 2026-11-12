"""Finish only the two terminal owned IIS profiles; no ACL changes."""
from pathlib import Path
import ctypes,hashlib,importlib.util,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
D=R/'Document/Deployment/real_resource_https_iis_r2408_20261112'
C=A/'tools/experimental_source/client_resource_ingress_r2397'


def j(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf-8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def main():
    assert j(D/'corrected-real-iis.json')['passed']
    for n in [2405,2406]:
        result=j(D/('actual-iis-terminal-'+str(n)+'.json'))
        assert result['iisExitCode']==0 and result['metrics']['activeProcesses']==0 and result['facadeThreadJoined']
    old=[Path('D:/Temp/Administrator')/('xnby-native-resource-r'+str(n))for n in [2404,2405,2406]]
    assert all(not p.exists()for p in old)
    roots=[R/'work'/('real-resource-iis-r'+str(n))for n in [2405,2406]]
    needles=[str(p)for p in roots]
    ps="$ErrorActionPreference='Stop';$roots=ConvertFrom-Json '"+json.dumps(needles).replace("'","''")+"';$hits=@(Get-CimInstance Win32_Process|Where-Object{$_.Name-match '^(pythonw?|nginx|iisexpress|csc|vbc)\\.exe$' -and $_.CommandLine -and $($line=$_.CommandLine;$hit=$false;foreach($r in $roots){if($line.IndexOf($r,[StringComparison]::OrdinalIgnoreCase)-ge 0){$hit=$true}};$hit)});[pscustomobject]@{querySucceeded=$true;refs=$hits.Count}|ConvertTo-Json -Compress"
    p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate();assert p.returncode==0;value=json.loads(out.decode('utf-8-sig'));assert value['querySucceeded']and value['refs']==0
    entries=[]
    for root in roots:
        assert root.parent==R/'work'and root.name in ('real-resource-iis-r2405','real-resource-iis-r2406')and root.is_dir()
        for item in [root,*root.parents]:assert not item.is_symlink()and not(getattr(item.lstat(),'st_file_attributes',0)&1024)
        for item in root.rglob('*'):
            assert item.absolute().is_relative_to(root)and not item.is_symlink()and not(getattr(item.lstat(),'st_file_attributes',0)&1024)
            entries.append(item)
    file_count=sum(p.is_file()for p in entries);logical=sum(p.stat().st_size for p in entries if p.is_file())
    put(D/'remaining-own-cleanup-scope-r2409.json',{'roots':needles,'files':file_count,'logicalBytes':logical,
      'readonlyAttributePaths':[str(p)for p in entries if getattr(p.lstat(),'st_file_attributes',0)&1],
      'allOriginalRootsAndJobsAlreadyTerminal':True,'freshCimNoReferences':True})
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.SetFileAttributesW.argtypes=[ctypes.c_wchar_p,ctypes.c_ulong];api.SetFileAttributesW.restype=ctypes.c_int
    free=shutil.disk_usage(R).free;changed=[]
    for root in roots:
        items=[p for p in entries if p.is_relative_to(root)]
        for item in sorted(items,key=lambda p:len(p.parts),reverse=True):
            attributes=item.lstat().st_file_attributes
            if attributes&1:
                if not api.SetFileAttributesW(str(item),attributes&~1):raise ctypes.WinError(ctypes.get_last_error())
                changed.append(str(item))
            if item.is_dir():item.rmdir()
            else:item.unlink()
        if root.lstat().st_file_attributes&1:
            assert api.SetFileAttributesW(str(root),root.lstat().st_file_attributes&~1)
        root.rmdir()
    put(D/'own-TLS-IIS-QA-retirement-r2409.json',{'allFiveOwnedFixtureRootsNowAbsent':all(not p.exists()for p in old+roots),
       'remainingFilesRemoved':file_count,'remainingLogicalBytesRemoved':logical,
       'earlierPartialRemovedCountsNotReconstructedOrInvented':True,'onlyOwnReadOnlyAttributesCleared':changed,
       'ACLOrSystemSecuritySettingsNotChanged':True,'freeBeforeResume':free,'freeAfterResume':shutil.disk_usage(R).free,
       'exclusivePhysicalReleaseNotClaimed':True,'failureWasReadonlyGeneratedProfileDocumentsFolder':True,
       'allSourceSmallFailureSuccessAndActualTerminalsPreserved':True})
    correction='\n\nR2409收尾补充：首清理已移除三个TEMP测试根，随后在本轮IIS虚拟profile/Documents只读属性处拒绝；未修改DACL或用户目录。重新核原IIS/root/Jobs0和鲜CIM零引用后，仅清其余两个自有profile的ReadOnly文件属性再移除。首段未落盘的删除数量不重构、不编造，总结果只记剩余实际移除数与五根已不存在。专用测试私钥/ASP缓存已退役，系统证书存储保持。\n'
    for path in [D/'真实传输验证与代理修正说明.md',A/'deploy/handbook/资源管理真实HTTPS_IIS与GET带体修正_r2408_20261112.md',R/'XNBYEngine/docs/project/资源管理真实HTTPS_IIS与代理边界修正_r2408_20261112.md']:
        with path.open('a',encoding='utf-8')as f:f.write(correction)
    recipe=C/'verification-source/resume_iis_fixture_retirement_r2409.py';assert not recipe.exists();recipe.write_bytes(Path(__file__).read_bytes())
    assert sha(R/'Document/Deployment/public_home_same_window_r51_20261112/prepared-manifest.json')=='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
    spec=importlib.util.spec_from_file_location('r2409_explicit_commit',V/'commit_r18_local_review.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    proof=A/'deploy/verification/real_resource_https_iis_r2408_20261112'
    for name in ['remaining-own-cleanup-scope-r2409.json','own-TLS-IIS-QA-retirement-r2409.json']:
        assert not(proof/name).exists();(proof/name).write_bytes((D/name).read_bytes())
    files=[p.relative_to(A).as_posix()for p in proof.rglob('*')if p.is_file()]
    files +=[(C/'iis/XnbyReferenceProxy.cs').relative_to(A).as_posix(),(C/'iis-body-boundary-candidate.json').relative_to(A).as_posix(),
       'deploy/handbook/资源管理真实HTTPS_IIS与GET带体修正_r2408_20261112.md']
    names=['owned_resource_nginx_r2404.py','test_native_resource_ingress_r2404.py','owned_resource_nginx_r2405.py','test_real_iis_resource_ingress_r2405.py',
           'owned_resource_nginx_r2406.py','test_real_iis_resource_ingress_r2406.py','record_real_resource_ingress_r2408.py','resume_iis_fixture_retirement_r2409.py']
    files +=[(C/'verification-source'/name).relative_to(A).as_posix()for name in names]
    a=g.commit(A,'63d99c9fbf559356d295ed3debf0b43e5cac1e7f','review/workplace-r19-live-local-20261031',sorted(files),'r2409-app','Verify real resource TLS IIS nginx chain and reject GET HEAD bodies; retain exact cleanup failures',update_existing=True)
    e=g.commit(R/'XNBYEngine','ac382d9dea754f0331f56aaf629728633a9a2f74','review/workplace-r19-live-progress-local-20261031',['docs/project/资源管理真实HTTPS_IIS与代理边界修正_r2408_20261112.md'],'r2409-engine','Record real resource ingress validation with normal-login and full-application gaps',update_existing=True)
    put(D/'local-review-git-r2409.json',{'application':a,'engine':e,'publicPushed':False})
    print(json.dumps({'allFiveOwnedFixtureRootsRetired':True,'remainingFilesRemoved':file_count,'onlyOwnReadOnlyAttributesClearedCount':len(changed),'application':a,'engine':e,'newPublicUpdate':False},ensure_ascii=False))


if __name__=='__main__':main()
