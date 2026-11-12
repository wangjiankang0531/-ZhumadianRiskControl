from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent
D=R/'Document/Deployment/real_resource_https_iis_r2408_20261112'
C=A/'tools/experimental_source/client_resource_ingress_r2397'


def j(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):
    with p.open('x',encoding='utf-8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def copy(src,dst):
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
    with src.open('rb')as s,dst.open('xb')as d:shutil.copyfileobj(s,d)
    assert sha(src)==sha(dst)


def main():
    assert not D.exists();D.mkdir()
    for n,label in [(2404,'native-nginx'),(2405,'first-real-iis-failure'),(2406,'corrected-real-iis')]:
        src=Path('D:/Temp/Administrator')/('xnby-native-resource-r'+str(n))/'verification.json'
        value=j(src)
        assert value['passed']==(n!=2405)
        assert all(x['rootExitCode']==0 and x['actualJobBeforeClose']==0 for x in value['processes'])
        copy(src,D/(label+'.json'))
    for n in [2405,2406]:
        value=j(R/'work'/('real-resource-iis-r'+str(n))/'terminal.json')
        assert value['iisExitCode']==0 and value['metrics']['activeProcesses']==0 and value['facadeThreadJoined']
        assert value['QShutdown']['desktopInput']is False and value['QShutdown']['signalOrForceTerminationCalled']is False
        copy(R/'work'/('real-resource-iis-r'+str(n))/'terminal.json',D/('actual-iis-terminal-'+str(n)+'.json'))
    latest=j(D/'corrected-real-iis.json');assert latest['distinctChecks']==35
    assert 'actual-fixed-HTTPS-consumer-real-IIS-nginx-worker-monotonic-receipt'in j(Path('D:/Temp/Administrator/xnby-native-resource-r2406/verification.json'))['checks']
    copy(C/'iis-body-boundary-candidate.json',D/'IIS-source-change.json')
    put(D/'evidence-scope.json',{'actualProductWorkerManifestSHA256':'6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3',
      'actualProductIISSourceSHA256':'cdfae1908c16f6724ea5d6582fc78c9b0ea68ea7e8cbeac6b782f1811d0a38a5',
      'actualTypedConsumerSHA256':'4e93a65b51061978cb3f81f8a324c5f9e5d8f91893d024bf3330254c3356169d',
      'actualNginxSHA256':'c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44',
      'IISBridgeAdaptedOnlyTwoGatewayPortConstantsForFixture':True,
      'actualIISDirectTLSRequests':len(latest['actualIISCalls']),
      'actualFacadeFixedHTTPSRequests':j(D/'actual-iis-terminal-2406.json')['requestsThroughActualIIS'],
      'bridgeHistoricalRequestsThroughActualIISCounterActuallyCountsFacadeRequestsOnly':True,
      'actualCertificateCheckedByPinnedDERAndFacadeByFixtureTrustChainHostname':True,
      'systemTrustHostsURLACLFirewallUnchanged':True,'originalCurrentUserExplicitlySynthetic':True,
      'normalOriginalJavaLoginBrowserAnd252NotAccepted':True,'wholeApplicationControllerNotStartedOrInstalled':True,
      'R51TransportAndPublicNotUpdated':True})
    note='''R2408 资源管理候选真实HTTPS/IIS/Nginx传输通过；发现并修复代理GET/HEAD带体500

R2397资源管理route与原控制器配置候选已45项通过。本轮先实际启动固定SHA原Nginx和新6989d7a2…完整44源managed worker，在独立动态回环端口执行默认关/显式开两个正常周期，32不同检查标签通过；原OriginalPlatformAccess走明确合成CurrentUser HTTP。核新namespace原读/写scope、401/403/400/409、8KiB 413、POST-only、未知子路由404、单次grant重放拒绝、撤权拒绝、mandatory remaining-ms；原9字段GIS和DLG读路由保持。所有Nginx/worker及辅助root实际exit0、Job0，精确prefix/pid/出生身份后原-s quit，未强杀。

随后原R50 C#字节在真实IIS Express既有44300绑定与测试专用TLS门面→原Nginx18972→managed44执行。首次查到测试的GET带JSON体在HttpWebRequest.GetRequestStream发生500（此前仅Nginx直连为403），17标签处停止；这不是正常用户UI成功。保first-real-iis-failure及实际Windows500/响应大小，未把失败写成通过。实际IIS原Q退出0/Job0及Nginx/worker全部正常0。

独立候选仅在C#创建上游请求前增加GET/HEAD非空body明确400，原源SHA6cb8eb62…、新cdfae1908c16f6724ea5d6582fc78c9b0ea68ea7e8cbeac6b782f1811d0a38a5；移除新增三行与注释即可逐字恢复原源，其他鉴权/原业务/头/压缩/传输保持。没有修改已固定R51或现用Application/deploy源。

修后35不同标签完整通过：无体GET仍经原Nginx拒403，带体GET返回明确400固定短文本无堆栈、HEAD带体400，默认未开放404、原业务stub204、原DLG读200、新角色11字段/旧GIS9字段、8KiB/外部角色/撤权/重放等状态和剩余头跨真实IIS原样。实际未改D172固定HTTPS消费函数4e93a65b…以正式hostname/443/原路径调用，测试仅将连接地址与独立信任CA映到本轮专用TLS门面，仍做真实TLS证书/hostname核验，再过真实IIS TLS（上游逐DER pin）、Nginx和真实worker；返回有效单调deadline。不是正式公网证书/IIS或真实Java登录/浏览器/252验收。

IIS隐藏独立配置/应用池、临时ASP.NET缓存和测试证书文件均为本轮自有，未安装证书、不改hosts/URLACL/防火墙/系统IIS或用户桌面。两个实际IIS root0、内核Job0，原生独立控制台Q正常排空，峰223,928,320B低1GiB；不是把父退出当Job0。Bridge历史字段requestsThroughActualIIS仅统计TLS门面转发（失败轮0、修后1），实际直接IIS TLS请求另在driver actualIISCalls逐项记录；修后还加1条固定消费者走门面，不把历史counter零误解为未走IIS。

这是可并入未来完整资源管理发布的候选。仍须将新44包、原控制器支持、新IIS源同时纳入完整release/payload/controller/staticInitialLoadPerformance等声明，两个IIS路径一致；完成实际原应用生命周期与原账号/两机验收后才谈部署。不可只把C#或route文件稀疏复制进R50/R51，不能把这些独立测试当被拒_h七周期的替代执行或验收；本轮未运行_h/Java/MySQL/正式GIS。R51四文件47d94ded…保持未上传/未部署，具体批准未答。250已激活新启动；252正规D174十文件已预置，仍待其本机预览/安装/启动和公网正常账号体验。

已向三维D175回设计约束：可本地候选以原read查状态、原write显式控制同项目/同当前Windows用户/同固定安装的原GIS，慢资格阶段可取消，提交后正常收尾不强杀，禁止任意PID/path/argv。旧D172无子进程recover和ownedSubprocessesStarted=0不得直接沿用到会启动GIS的新代码；真实长活guard/句柄须自证。不是停止现用250/252、改公开授权或新部署的批准。

只同步本方源/证据到原本地Git分支，未公开推送；清本轮5个退役QA/ASP缓存/专用证书副本前核所有真实终态与鲜CIM零，保小型失败/清单/源和全部用户数据。完整UE G1—G10、EXE GIS/DLG多层多源空间牌、Web3D/真实两机/单系统南港B/S继续active，未宣称完成或公开检出一键构建。
'''
    with(D/'真实传输验证与代理修正说明.md').open('x',encoding='utf-8')as f:f.write(note)
    recipes=C/'verification-source'
    for name in ['owned_resource_nginx_r2404.py','test_native_resource_ingress_r2404.py','owned_resource_nginx_r2405.py','test_real_iis_resource_ingress_r2405.py',
                 'owned_resource_nginx_r2406.py','test_real_iis_resource_ingress_r2406.py','record_real_resource_ingress_r2408.py']:
        ast.parse((V/name).read_text('utf-8-sig'));copy(V/name,recipes/name)
    proof=A/'deploy/verification/real_resource_https_iis_r2408_20261112';proof.mkdir()
    for p in D.iterdir():
        if p.suffix=='.json':copy(p,proof/p.name)
    handbook=A/'deploy/handbook/资源管理真实HTTPS_IIS与GET带体修正_r2408_20261112.md';copy(D/'真实传输验证与代理修正说明.md',handbook)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    statepath=R/'Document/Coordination/驻马店3_当前协作状态.json';state=j(statepath)
    state.update(at=now,ownResourceNativeNginxActualTwoCycles32ChecksPassed=True,
      ownResourceActualIISGETBody500ReproducedAndCandidate400Fixed=True,ownResourceActualIIS_TLS_NginxWorker35ChecksPassed=True,
      ownResourceActualUnmodifiedFixedHTTPSConsumerPassed=True,ownResourceWholeApplicationAndOriginalLogin252StillPending=True,
      ownR51TransportNotChangedOrUploaded=True,publicStillR50=True,
      nextOwnWork='R51授权/桌面交接仍待答，不上传/绕过。原Nginx和真实IIS/TLS到managed资源worker及原消费器已过，GET/HEAD带体500新候选已明确400；下一完整release图/原应用生命周期和原账号252仍待，不稀疏复制进R51。')
    statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n','utf-8')
    put(R/'Document/Coordination/交接消息/驻马店3资源管理真实IIS_TLS原Nginx与原消费者通过及GET带体候选修正_r2408_20261112.json',
       {'fromChat':'驻马店3','to':'驻马店三维','stage':'R2408','atUTC':now,'actualOriginalNativeNginxTwoCycles32Checks':True,
        'actualTLSRealIISOriginalNginxManagedWorker35Checks':True,'actualUnmodifiedD172FixedHTTPSConsumerPassed':True,
        'CurrentUserExplicitlySyntheticNoJavaOrBrowserOr252Acceptance':True,'firstRealIISGETBody500Preserved':True,
        'candidateIISGETHEADNonemptyBody400OnlyAddedGuard':True,'candidateIISSourceSHA256':'cdfae1908c16f6724ea5d6582fc78c9b0ea68ea7e8cbeac6b782f1811d0a38a5',
        'actualAllIISNginxWorkersExitZeroJobsZeroNoForce':True,'noWindowsCertificateStoreHostsSecurityOrDesktopChanges':True,
        'candidateNotInstalledOrAddedToFrozenR51':True,'R51ScopeApprovalPendingPublicStillR50':True,
        'D175DesignResponseActuallyRecorded':'驻马店3核收D175更根启停设计与严格写权限候选约束_r2407_20261112.json',
        'completeReleaseAssemblyAndOriginalAppNormalUserBothClientsStillPending':True,'sharedFileNotRealtimeDelivery':True})
    paragraph='\n\n## 2026-11-12 R2408：资源管理真实TLS/IIS/Nginx链通过，候选修复GET/HEAD带体500\n\n'+note+'\n'
    for p in [R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/showcase_demo_completion.md']:
        with p.open('a',encoding='utf-8')as f:f.write(paragraph)
    engine=R/'XNBYEngine/docs/project/资源管理真实HTTPS_IIS与代理边界修正_r2408_20261112.md'
    with engine.open('x',encoding='utf-8')as f:f.write(note)
    roots=[Path('D:/Temp/Administrator')/('xnby-native-resource-r'+str(n))for n in [2404,2405,2406]]+[R/'work'/('real-resource-iis-r'+str(n))for n in [2405,2406]]
    needles=[str(p)for p in roots]+['test_native_resource_ingress_r2404.py','test_real_iis_resource_ingress_r2405.py','test_real_iis_resource_ingress_r2406.py']
    ps="$ErrorActionPreference='Stop';$needles=ConvertFrom-Json '"+json.dumps(needles).replace("'","''")+"';$hits=@(Get-CimInstance Win32_Process|Where-Object{$_.Name-match '^(pythonw?|nginx|iisexpress|csc|vbc)\\.exe$' -and $_.CommandLine -and $($line=$_.CommandLine;$hit=$false;foreach($n in $needles){if($line.IndexOf($n,[StringComparison]::OrdinalIgnoreCase)-ge 0){$hit=$true}};$hit)});[pscustomobject]@{querySucceeded=$true;refs=$hits.Count}|ConvertTo-Json -Compress"
    p=subprocess.Popen(['powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-Command',ps],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    out,err=p.communicate();assert p.returncode==0;obs=json.loads(out.decode('utf-8-sig'));assert obs['querySucceeded']and obs['refs']==0
    before=shutil.disk_usage(R).free;count=logical=0
    for root in roots:
        assert root.parent in (Path('D:/Temp/Administrator'),R/'work') and root.name in {'xnby-native-resource-r2404','xnby-native-resource-r2405','xnby-native-resource-r2406','real-resource-iis-r2405','real-resource-iis-r2406'}
        for p in [root,*root.parents]:assert not p.is_symlink()and not(getattr(p.lstat(),'st_file_attributes',0)&1024)
        entries=list(root.rglob('*'))
        for p in entries:
            assert p.absolute().is_relative_to(root)and not p.is_symlink()and not(getattr(p.lstat(),'st_file_attributes',0)&1024)
            if p.is_file():count+=1;logical+=p.stat().st_size
        for p in sorted(entries,key=lambda q:len(q.parts),reverse=True):
            if p.is_dir():p.rmdir()
            else:p.unlink()
        root.rmdir()
    put(D/'own-TLS-IIS-QA-retirement.json',{'roots':[str(p)for p in roots],'files':count,'logicalBytes':logical,'freeBefore':before,'freeAfter':shutil.disk_usage(R).free,
        'exclusivePhysicalFreeNotClaimed':True,'allActualNormalTerminalsAndFreshCimZero':True,'ownFixtureTLSPrivateKeysRetiredWithoutSystemStoreChange':True,
        'allUserDataGISSourceAndSmallFailedSuccessfulEvidencePreserved':True})
    assert sha(R/'Document/Deployment/public_home_same_window_r51_20261112/prepared-manifest.json')=='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
    spec=importlib.util.spec_from_file_location('r2408_own_git',V/'commit_r18_local_review.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    files=[p.relative_to(A).as_posix()for root in [proof]for p in root.rglob('*')if p.is_file()]
    files +=[(C/'iis/XnbyReferenceProxy.cs').relative_to(A).as_posix(),(C/'iis-body-boundary-candidate.json').relative_to(A).as_posix(),handbook.relative_to(A).as_posix()]
    files +=[(recipes/name).relative_to(A).as_posix()for name in ['owned_resource_nginx_r2404.py','test_native_resource_ingress_r2404.py','owned_resource_nginx_r2405.py','test_real_iis_resource_ingress_r2405.py','owned_resource_nginx_r2406.py','test_real_iis_resource_ingress_r2406.py','record_real_resource_ingress_r2408.py']]
    a=g.commit(A,'63d99c9fbf559356d295ed3debf0b43e5cac1e7f','review/workplace-r19-live-local-20261031',sorted(files),'r2408-app','Verify real TLS IIS nginx resource ingress and reject unsupported GET HEAD bodies safely',update_existing=True)
    e=g.commit(R/'XNBYEngine','ac382d9dea754f0331f56aaf629728633a9a2f74','review/workplace-r19-live-progress-local-20261031',[engine.relative_to(R/'XNBYEngine').as_posix()],'r2408-engine','Record actual resource ingress and fixed client consumer validation, normal-login gaps retained',update_existing=True)
    put(D/'local-review-git.json',{'application':a,'engine':e,'publicPushed':False})
    print(json.dumps({'recorded':True,'actualTLSIISAndNativeNginxPassed':True,'ownRetiredFiles':count,'logicalBytes':logical,'application':a,'engine':e,'newPublicUpdate':False},ensure_ascii=False))


if __name__=='__main__':main()
