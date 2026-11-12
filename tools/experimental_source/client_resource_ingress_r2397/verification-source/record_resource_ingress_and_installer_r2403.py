from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,subprocess

R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
D=R/'Document/Deployment/resource_ingress_and_client252_installer_r2403_20261112'
C=A/'tools/experimental_source/client_resource_ingress_r2397'


def j(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,value):
    with p.open('x',encoding='utf-8')as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
def copy(src,dst):
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb')as s,dst.open('xb')as d:shutil.copyfileobj(s,d)
    assert sha(src)==sha(dst)


def main():
    assert not D.exists();D.mkdir()
    verify=Path('D:/Temp/Administrator/xnby-resource-ingress-r2399/verification.json')
    assert j(verify)['passed']and j(verify)['count']==45
    copied=j(R/'Document/Deployment/client252_visible_installer_r2402_20261112/verification.json');assert copied['passed']and copied['copiedFiles']==10
    copy(verify,D/'resource-route-config-45-checks.json')
    copy(Path('D:/Temp/Administrator/xnby-resource-ingress-r2398/fixture-failure.json'),D/'first-nginx-fixture-failure.json')
    copy(V/'client-installer-receipt-r2400/verification.json',D/'D174-independent-receipt.json')
    copy(R/'Document/Deployment/client252_visible_installer_r2402_20261112/verification.json',D/'client252-ten-files-staged.json')
    copy(R/'Document/Deployment/client252_visible_installer_r2402_20261112/fixed-scope.json',D/'client252-ten-file-scope.json')
    put(D/'client252-first-stage-path-failure.json',{'actualFailure':'The optional metadata guard used Data/metadata.xml; actual metadata.xml is its parent sibling.',
      'failedBeforeAnyLocalReceiptOrRemoteDirectoryOrFileCreation':True,'actualNormalContextGISRootListingConfirmedParent':True,
      'unprivilegedUNCQueryDeniedNotAbsenceProof':True,'sameTenFileTransportBytesNotChanged':True})
    assert sha(R/'Document/Deployment/public_home_same_window_r51_20261112/prepared-manifest.json')=='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
    note='''R2403 资源管理公网接线缺口修正候选；252正规安装器十文件已预置

上一阶段actual managed44后台→D172管理9+953 HTTP/保存/取消/撤权/报告一次重启已通过，但当时未经过公网网关。本轮只读核实际R50/R51源，发现独立后台通过不等于原站可达：原route_candidate仅列图层/工程/模型/GIS，未列v2/client-resources/grants和consume；原spatial发布支持还严格41源并拒绝新clientResources私有配置，worker配置也不传新项。这些是实际装配缺口，未以源码存在冒称已接通。

新独立candidate tools/experimental_source/client_resource_ingress_r2397：44源完整包中仅route generator改变，增加默认关闭的严格bool client_resources，启用时只加两条精确8KiB POST路由，保无重试/无缓存/无错误重写；关闭时16种原flags生成字节与旧包逐字同。新package manifest 6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3。独立原spatial支持候选先核新44完整pin，再允许严格1至16个manager清单，拒绝重复/未知字段/非SHA身份/项目未声明源；真实启动传给worker并将可信启用标志传路由生成器，增加匿名401/结构拒绝403健康探测。原worker句柄、归属、正常停止/恢复函数AST保持，仅preflight/start配置组装/configure_gateway/verify_gateway四处有意更新；没有覆盖原helper或任何现用安装。

45项源/配置/默认路由/拒绝边界、实际控制器内置路由inspector子进程生成及原Nginx -t通过。首Nginx检查配置语法已ok但自有薄fixture未建temp父目录，保exit1；补原gateway generator本来就创建的temp后同产品候选过。没有启动Nginx监听器/原应用/数据库，没有真实IIS/HTTPS/原用户全链；完整release图声明、真实7组件生命周期及正式发布仍待，不能稀疏替换到R51。R51固定四文件SHA保持47d94ded…，仍待具体批准，没有新公网上传。

三维D174正规可视安装器已独立核收：17源Git762693df14d726cf6dc0881ea7ff8eb453064a4c、ZIP ec16b0e9…和工作字节全同；两机20运输文件SHA闭合，内D171四文件与此前已核源相同；原WSH只读快捷方式目标/参数，确为各机PSF pythonw -I -B普通产品GUI，无cmd/PowerShell、未执行快捷方式。未冒称重跑发送方23测试或原生UI。

根据用户明确的252共享路径和访问修复要求，已将252固定10文件37966B复制到\\\\192.168.250.252\\Fofme\\XNBY\\Zhumadian\\Application\\ClientInstaller，完整回读SHA同。该机实际入口为F:/XNBY/Zhumadian/Application/ClientInstaller/驻马店客户机安装.lnk，只能在252本机正常运行。原953程序manifest、Config/client-workspace.json、园区metadata.xml前后SHA保持，没有运行GUI/远程进程、没有改252注册表/GIS。首准备误将metadata位置写为Data/metadata.xml，在任何复制前退出；正常只读核真实parent后仅改保护路径，原10文件字节保持。未将受限上下文UNC拒绝当目录不存在；正常上下文确核新目标不存在才新建。

252仍须在本机检查安装方案（固定首装只接受Run不存在，未知旧值或目标内容拒绝），显式安装/立即准备，随后正常原账号公网进入完整地景/标牌/图层验收；不通过250 UNC冒充252运行。当前桌面交接未答，不操作桌面；250已合格新Run保持。D171管理注册仍null，独立18768管理不插入此次紧急入口修复。

全部新源/验收只本地原分支，未公开推送；只清自有两个Nginx语法fixture，保源码、小型失败/清单/报告及全部用户数据。完整UE G1—G10效果效率、EXE GIS/DLG点线面/多层/多源空间牌、Web3D及单系统南港B/S仍active，未宣称完成或公开检出一键构建。
'''
    with(D/'实际修正与252准备说明.md').open('x',encoding='utf-8')as f:f.write(note)
    recipes=C/'verification-source';recipes.mkdir()
    names=['prepare_resource_ingress_candidate_r2397.py','test_resource_ingress_candidate_r2398.py','test_resource_ingress_candidate_r2399.py',
           'receive_client_installer_r2400.py','stage_client252_visible_installer_r2401.py','stage_client252_visible_installer_r2402.py','record_resource_ingress_and_installer_r2403.py']
    for name in names:ast.parse((V/name).read_text('utf-8-sig'));copy(V/name,recipes/name)
    proof=A/'deploy/verification/resource_ingress_and_client252_installer_r2403_20261112';proof.mkdir()
    for p in D.iterdir():
        if p.suffix=='.json':copy(p,proof/p.name)
    handbook=A/'deploy/handbook/资源管理网关候选与252可视安装准备_r2403_20261112.md';copy(D/'实际修正与252准备说明.md',handbook)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    path=R/'Document/Coordination/驻马店3_当前协作状态.json';state=j(path)
    state.update(at=now,ownResourceIngressActualMissingRoutesAndDroppedConfigurationFound=True,
        ownResourceIngressNew44CandidateSHA256=j(C/'prepared.json')['packageManifestSHA256'],
        ownResourceIngress45ChecksAndActualNginxSyntaxPassed=True,ownResourceIngressFullProfileAndIISLifecycleStillPending=True,
        ownD17417AndTwoTenFileMapsIndependentlyReceived=True,own252VisibleInstallerTenFilesActuallyStaged=True,
        own252InstallerCanonical='F:/XNBY/Zhumadian/Application/ClientInstaller',own252InstallerExecuted=False,
        own252RegistryAndGISNotChanged=True,ownR51ExactApprovalPending=True,publicStillR50=True,
        nextOwnWork='R51批准/桌面交接待答不越过。252正规GUI十文件已预置，等本机正常预览安装/准备GIS和原公网验收。资源管理44新route/原控制器严格配置候选45检查和Nginx语法过，实际Nginx/IIS/TLS全链及完整release装配仍待，不能并入R51。')
    path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
    put(R/'Document/Coordination/交接消息/驻马店3核收D174十文件预置252及资源管理网关装配缺口候选_r2403_20261112.json',
       {'fromChat':'驻马店3','to':'驻马店三维','stage':'R2403','atUTC':now,'D17417GitZipWorkingAndBothTenFilesIndependentlyMatched':True,
        '252TenFiles37966BytesActuallyCopiedAndSHAReadback':True,'252CanonicalInstaller':'F:/XNBY/Zhumadian/Application/ClientInstaller',
        '252ShortcutGUIProcessRegistryNotExecuted':True,'252GISConfigProgrammeMetadataSHAUnchanged':True,
        'onlyActualMetadataGuardPathCorrectedBeforeCopy':True,'250ExistingD171Kept':True,
        'originalPublicResourceRoutesAndPrivateConfigAssemblyWereMissing':True,
        'independentNew44WorkerPackageManifestSHA256':j(C/'prepared.json')['packageManifestSHA256'],
        'newCandidateDefaultOffOldRoutes16CombinationsByteIdentical':True,'candidate45ChecksAndRealNginxSyntaxPassed':True,
        'NginxListenerOriginalIISAndFullApplicationNotYetRun':True,'managementClientPackageD172AndD170NotChanged':True,
        'newCandidateNotInstalledOrAddedToFrozenR51':True,'R51FixedScopeApprovalPendingPublicStillR50':True,
        'desktopHandoffPendingNoInput':True,'fullNormalLogin250252NotAccepted':True,'sharedFileNotRealtimeDelivery':True})
    paragraph='\n\n## 2026-11-12 R2403：管理路由/原控制器配置装配候选修正，252正规安装十文件已放置\n\n'+note+'\n'
    for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/showcase_demo_completion.md']:
        with p.open('a',encoding='utf-8')as f:f.write(paragraph)
    engine=R/'XNBYEngine/docs/project/资源管理网关装配与252可视安装准备_r2403_20261112.md'
    with engine.open('x',encoding='utf-8')as f:f.write(note)
    # Small syntax fixtures only; all actual -t and inspector handles returned.
    roots=[Path('D:/Temp/Administrator/xnby-resource-ingress-r2398'),Path('D:/Temp/Administrator/xnby-resource-ingress-r2399')]
    needles=[str(p)for p in roots]+['test_resource_ingress_candidate_r2398.py','test_resource_ingress_candidate_r2399.py']
    ps="$ErrorActionPreference='Stop';$needles=ConvertFrom-Json '"+json.dumps(needles).replace("'","''")+"';$hits=@(Get-CimInstance Win32_Process|Where-Object{$_.Name-match '^(pythonw?|nginx)\\.exe$' -and $_.CommandLine -and $($line=$_.CommandLine;$hit=$false;foreach($n in $needles){if($line.IndexOf($n,[StringComparison]::OrdinalIgnoreCase)-ge 0){$hit=$true}};$hit)});[pscustomobject]@{querySucceeded=$true;refs=$hits.Count}|ConvertTo-Json -Compress"
    p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate();assert p.returncode==0;obs=json.loads(out.decode('utf-8-sig'));assert obs['querySucceeded']and obs['refs']==0
    free=shutil.disk_usage(roots[0].parent).free;files=logical=0
    for root in roots:
        assert root.parent==Path('D:/Temp/Administrator')
        for q in [root,*root.parents]:assert not q.is_symlink()and not(getattr(q.lstat(),'st_file_attributes',0)&1024)
        entries=list(root.rglob('*'))
        for q in entries:
            assert q.absolute().is_relative_to(root)and not q.is_symlink()and not(getattr(q.lstat(),'st_file_attributes',0)&1024)
            if q.is_file():files+=1;logical+=q.stat().st_size
        for q in sorted(entries,key=lambda x:len(x.parts),reverse=True):
            if q.is_dir():q.rmdir()
            else:q.unlink()
        root.rmdir()
    put(D/'own-syntax-fixtures-retired.json',{'roots':[str(p)for p in roots],'files':files,'logicalBytes':logical,'freeBefore':free,'freeAfter':shutil.disk_usage(roots[0].parent).free,
       'exclusivePhysicalFreeNotClaimed':True,'actualHandlesTerminalAndFreshCimNoRefs':True,'allSourceAndFailureAndVerificationPreserved':True})
    spec=importlib.util.spec_from_file_location('r2403_own_git',V/'commit_r18_local_review.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    files=[p.relative_to(A).as_posix()for root in [C,proof]for p in root.rglob('*')if p.is_file()]+[handbook.relative_to(A).as_posix()]
    a=g.commit(A,'267b88eae2e1e73c80fba1ad6801a07d8eb60130','review/workplace-r19-live-local-20261031',sorted(files),'r2403-app','Add opt-in resource routes and strict original controller assembly; stage normal 252 installer',update_existing=True)
    e=g.commit(R/'XNBYEngine','532e3aa1ba67f56fc543edb8f96f222a1e14ed35','review/workplace-r19-live-progress-local-20261031',[engine.relative_to(R/'XNBYEngine').as_posix()],'r2403-engine','Record resource ingress candidate and actual 252 installer staging',update_existing=True)
    put(D/'local-review-git.json',{'application':a,'engine':e,'publicPushed':False})
    print(json.dumps({'recorded':True,'newProductCandidate44SourcesAndSupport':True,'actual252TenFileStagingPassed':True,'application':a,'engine':e,'newPublicUpdate':False},ensure_ascii=False))


if __name__=='__main__':main()
