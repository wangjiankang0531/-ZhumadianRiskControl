"""Freeze a reviewed text-only public scope; never contacts or writes GitHub."""
from pathlib import Path
import ast,datetime,hashlib,importlib.util,json,subprocess
import xml.etree.ElementTree as ET
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_source_r48_repair_r1060_20261105'
APP_COMMITS=['6923737c105aa1d5bc06a1e6297ae7692132d948','0189ea18a0387ce3dc58f096487bebee3d8ca5a5','55fb2d1dab0ebcd3c3f40819feaec8d8da43d6ef','0f3755af7af5e01ec24964e4f314ce0fd0805c37','e107759a01ead07676b583ddbd0f7cac83b67923']
ENG_COMMITS=['c7806c3962028b04c94bfe07f7dd7418d1c3095b','b07c00627350b4a87f77b9389378670302112c6d','550c5123441770d6c44b16f7bd10b25bbbe298f0','6457748a61ea2eb77d9664122addc1abbe073cd6','eab0ca72c3f31d784d6e87a9bb5327e351a8c41f']

def git(root,args,stdin=None):
    p=subprocess.run(['git','-C',str(root),*args],input=stdin,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert p.returncode==0,p.stderr.decode('utf-8',errors='replace')[:200]
    return p.stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump(p,data):
    assert not p.exists(),str(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def main():
    assert not D.exists()
    app=R/'Application';engine=R/'XNBYEngine'
    assert git(app,['rev-parse','refs/heads/review/workplace-r19-live-local-20261031']).decode().strip()==APP_COMMITS[-1]
    assert git(engine,['rev-parse','refs/heads/review/workplace-r19-live-progress-local-20261031']).decode().strip()==ENG_COMMITS[-1]
    assert read(R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3/publication-stage-r1058.json')['allOwnedProcessesAndJobsTerminal']
    peer=read(V/'d80-receiver-inspection-r1060.json')
    peer_source=R/'Document/Coordination/交接消息/驻马店三维D80真实登录与便携协同候选_给驻马店3_20261105.json'
    assert sha(peer_source)==peer['handoffSHA256']and len(peer['sourceDeltaGitBlobsMatched'])==5
    note='''2026-11-05 R1060：本轮公开同步准备只选择本方R1040至R1058清理技能、上传/预检/失败和R48第三稿源码及小型证据，另加本轮范围构建器、D80接收证明和两份说明。排除AGENTS与3份共享总历史、资产/Reference/SDK或Jar/class等二进制、截图、原日志、原始业务/账号会话/口令值和运行库UUID；不发私有祖先，不改main/其它分支，不新建分支。GitHub当前两个公开头已只读核同46454047和0d1e6662，新范围仍待具体批准，不创建GitHub内容/提交/ref。
R48旧包失败待恢复，第三稿9文件25690504B/清单8f0d27eb已固定且尚未上传。后台实际原apply错误复现、recover、修正apply和rollback已闭合，5控制器六组件正常0/两Job实零/719代码等独立还原；初次测试器KeyError和收尾目录复制错误保留，非全南港/IIS TLS验收。公网最后13:53匿名两入口502，旧Recover结果未收到，不能推定原R45已恢复，不用第三稿恢复旧失败、不删服务器恢复材料。
D80两个归档/候选manifest和5源码Git Blob独立核同，接收审阅不运行真实EXE/登录/安装；发送方原页面、真实C++流程仍是合成身份/本地HTTP，可信原账号、公网TLS/252两机仍待。D79完整源归档仍为其增量前置，不混入B/S本次公开载荷或第三稿。当前工作只后台文档/Git；完整UE效果效率引擎、EXE GIS/DLG点线面图层/多源标牌、Web3D和单系统南港B/S继续active/fullCloneReady=false，公开干净检出一键完整构建仍未声称。
'''
    handbook=app/'deploy/handbook/r48_repair_public_source_scope_20261105_r1060.md'
    engine_note=engine/'docs/R48修正公开范围与D80接收_20261105_r1060.md'
    assert not handbook.exists()and not engine_note.exists()
    handbook.write_text('# R48修正与公开源码范围\n\n'+note,encoding='utf-8',newline='\n')
    engine_note.write_text('# R48修正与三维交接进展\n\n'+note,encoding='utf-8',newline='\n')
    marker='BS_R48_REPAIR_PUBLIC_SCOPE_R1060_20261105'
    for relative in ['Document/Engine/project/htengine_goal_state.md','Document/Engine/project/当前工作断点.md','Document/Engine/showcase_demo_completion.md']:
        path=R/relative;assert marker not in path.read_text('utf-8-sig')
        with path.open('a',encoding='utf-8',newline='\n')as f:f.write('\n\n<!-- '+marker+' -->\n'+note+'<!-- '+marker+'_END -->\n')
    source=app/'tools/verification/event_result_r1060'/Path(__file__).name
    assert not source.exists();source.parent.mkdir(parents=True);source.write_bytes(Path(__file__).read_bytes())
    proof=app/'deploy/verification/event_result_r1060/d80-receiver-inspection-r1060.json';dump(proof,peer)
    ack={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维','recordedAt':datetime.datetime.now().astimezone().isoformat(),
        **peer,'publicR48FailedAndRecoveryResultStillPending':True,'R48R3UnchangedAndUninstalled':True}
    dump(R/'Document/Coordination/交接消息/驻马店3已读D80登录便携候选_20261105_r1060.json',ack)
    spec=importlib.util.spec_from_file_location('private_review_r1060',V/'commit_r18_local_review.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    a=h.commit(app,APP_COMMITS[-1],'review/workplace-r19-live-local-20261031',[str(p.relative_to(app)).replace('\\','/')for p in [handbook,source,proof]],'app-r1060',message_override='Prepare repaired R48 public text scope and receive D80 without deployment',update_existing=True)
    e=h.commit(engine,ENG_COMMITS[-1],'review/workplace-r19-live-progress-local-20261031',['docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md',str(engine_note.relative_to(engine)).replace('\\','/')],'engine-r1060',message_override='Record public source scope and bounded D80 receiver review',update_existing=True)
    specs=[{'kind':'application','root':app,'repository':'wangjiankang0531/-ZhumadianRiskControl','branch':'review/workplace-r19-verified-partial-20261031','publicParent':'4645404702428e83ffc7bd5f34c57273108cd94e','localCommit':a['commit'],'commits':APP_COMMITS+[a['commit']]},
        {'kind':'engine','root':engine,'repository':'wangjiankang0531/-XNBYEngine','branch':'review/workplace-r19-verified-progress-20261031','publicParent':'0d1e6662cef927d124c2f468ef352dc6e4ced528','localCommit':e['commit'],'commits':ENG_COMMITS+[e['commit']]}]
    excluded={'AGENTS.md','docs/project/htengine_goal_state.md','docs/project/当前工作断点.md','docs/showcase_demo_completion.md'}
    rows=[];blobs=[];targets=[];counts={};flags=[]
    def audit_json(value,path):
        if isinstance(value,dict):
            for key,item in value.items():
                if key.lower()in {'password','seedrootpassword','access_token','refresh_token','authorization','cookie','databaseuuid','userid','user_id'}and isinstance(item,str)and item:flags.append({'path':path,'key':key})
                audit_json(item,path)
        elif isinstance(value,list):
            for item in value:audit_json(item,path)
    for s in specs:
        paths=set()
        for commit in s['commits']:paths.update(git(s['root'],['diff-tree','--no-commit-id','--name-only','-r','-z',commit]).decode('utf-8').split('\0'))
        paths=sorted(paths-{''}-excluded)
        for rel in paths:
            assert not rel.startswith(('Assets/','Reference/','native/','UserData/','private/'))
            assert rel.startswith(('tools/verification/','deploy/','docs/'))or rel=='.agents/skills/zhumadian-history-cleanup/SKILL.md'
            suffix=Path(rel).suffix.lower();assert suffix in {'.py','.json','.md','.cmd','.config'}
            raw=git(s['root'],['show',s['localCommit']+':'+rel]);text=raw.decode('utf-8-sig');assert '\0'not in text
            counts[suffix]=counts.get(suffix,0)+1
            if suffix=='.py':ast.parse(text,filename=rel)
            if suffix=='.json':audit_json(json.loads(text),rel)
            if suffix=='.config':ET.fromstring(text)
            if suffix=='.cmd':assert text.startswith('@echo off')and'-I -B'in text and'pause'in text
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            assert git(s['root'],['hash-object','--stdin'],raw).decode().strip()==blob
            rows.append({'repository':s['repository'],'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gitBlobSHA1':blob})
            blobs.append((s['kind'],rel,raw))
        targets.append({k:s[k]for k in ['kind','repository','branch','publicParent','localCommit']}|{'files':len(paths)})
    audit={'files':len(rows),'bytes':sum(row['bytes']for row in rows),'syntaxKinds':counts,'flags':flags,'publicObjectsCreated':False}
    (V/'public-source-preflight-r1060.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert not flags,'SENSITIVE_FIELD_REVIEW_REQUIRED_NO_UPLOAD'
    D.mkdir()
    for kind,rel,raw in blobs:
        path=D/'snapshot'/kind/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
    manifest={'schema':'xnby.fixed.public-source-scope.v1','revision':'r1060-repaired-r48-real-apply-and-cleanup-source',
        'targets':targets,'files':rows,'totalFiles':len(rows),'totalBytes':sum(row['bytes']for row in rows),
        'fromExistingPublicParentsOnly':True,'privateCommitAncestorsNotSent':True,'noNewBranchesOrMainChanges':True,
        'oldR48FailedAndRecoveryResultPending':True,'repairedR48R3NotUploadedOrDeployed':True,
        'actualOwnedApplyAndRecoveryWithLocalHTTPBindingAccepted':True,'realIISPublicTLSOrNormalPublicUIAccepted':False,
        'fullOriginalNangangAcceptanceStillPending':True,'publicCleanCheckoutOneCommandBuildClaimed':False,
        'assetsReferenceBinariesCredentialsRawLogsRuntimeUUIDOrActualBusinessRowsIncluded':False}
    dump(D/'public-git-sync-r1060-manifest.json',manifest)
    summary={**audit,'manifestSHA256':sha(D/'public-git-sync-r1060-manifest.json'),'targets':targets,'applicationLocal':a,'engineLocal':e}
    dump(D/'prepared-source-scope-r1060.json',summary)
    explanation='# 固定公开源码范围\n\n本批只向原两个公开review分支追加固定文本；各以清单publicParent为唯一父提交，不发送私有祖先，不改main或其他分支。逐Blob、完整树、唯一父和ref回读。\n\n覆盖清理SKILL、R48上传/预检/失败、严格控制桥、真实升级恢复回滚/失败续接/临时清理源码与小型证明、第三稿运输文本和D78至D80接收说明。包含代码、内部路径、本地构建标识与合成验证/PID，不含实际账号口令令牌/业务行/运行库UUID/数据库资产Reference或SDK二进制/截图原日志/held三维源及3共享总历史。\n\n如实记录旧R48失败且恢复结果待验、第三稿未上传、IIS TLS/正常公网UI/真实南港模板和EXE252仍待；不声称公开干净检出一键构建。本批尚未创建GitHub对象/提交或更新ref，需要新的固定公开范围批准。\n'
    (D/'固定公开源码范围说明.md').write_text(explanation,encoding='utf-8',newline='\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
