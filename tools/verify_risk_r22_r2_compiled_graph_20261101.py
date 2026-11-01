from pathlib import Path
import hashlib,json,re,sys
R=Path('D:/Project/Zhumadian')
stage=R/'work/user_feedback_20261031/security-build-risk-r22-from-r21-r2'
root=stage/'build/dist'
result=json.loads((stage/'candidate-result.json').read_text(encoding='utf-8'))
files=result['fullFrontendFiles']
for name,row in files.items():
    raw=(root/name).read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
imports=0
for name in files:
    if not name.endswith('.js'):continue
    text=(root/name).read_text(encoding='utf-8')
    for rel in re.findall(r'(?:from\s*|import\s*|import\s*\(\s*)["\'](\.[^"\']+)["\']',text):
        dest=((root/name).parent/rel.split('?')[0].split('#')[0]).resolve()
        assert dest.is_relative_to(root.resolve()) and dest.is_file(),name+':'+rel
        imports+=1
html=(root/'index.html').read_text(encoding='utf-8')
for name in re.findall(r'(?:href|src)="(/zhumadian/[^"]+)"',html):
    assert (root/name.removeprefix('/zhumadian/')).is_file()
assert html.count('data-xnby-home-viewport=')==1
js={n:(root/n).read_text(encoding='utf-8')for n in files if n.endswith('.js')}
charts=[(n,s)for n,s in js.items()if '事件总数'in s and 'maxWidth:420'in s]
tasks=[(n,s)for n,s in js.items()if '巡检任务清单'in s]
stats=[(n,s)for n,s in js.items()if all(t in s for t in ['巡检统计','隐患数量统计','隐患整改统计','事件统计'])]
assert len(charts)==len(tasks)==len(stats)==1
assert all(t in tasks[0][1]for t in ['"min-width":"132"','"min-width":"168"','width:"100"'])
wrappers=[n for n,s in js.items()if 'name_ECharts_lang'in n and 'ResizeObserver'in s and 'disconnect'in s]
assert len(wrappers)==1
assert wrappers[0].split('/')[-1] in charts[0][1]
css='\n'.join((root/n).read_text(encoding='utf-8')for n in files if n.endswith('.css'))
assert 'container-type:inline-size'in css and 'minmax(min(100%,270px),1fr)'in css
risk=[(n,s)for n,s in js.items()if '新增后让既有页签机制重建列表'in s]
# Production minifiers remove comments; inspect the actual form's route and reload-hook call linkage.
risk=[(n,s)for n,s in js.items()if '"/hiddenInvestigate/riskAnalysisUnit"'in s and 'reloadPageTab'in s and '编辑成功！'in s]
assert len(risk)==1,'ACTUAL_COMPILED_RISK_FORM_AND_NATIVE_REFRESH_LINK_REQUIRED'
workflow=[(n,s)for n,s in js.items()if 'creatorUserId'in s and 'fetchUserInfo'in s and 'currentPage'in s and '我发起的'in s]
assert len(workflow)==1,'ACTUAL_R21_WORKFLOW_INITIATOR_INTERSECTION_COMPILED_REQUIRED'
baseline=json.loads((R/'work/user_feedback_20261031/workplace-security-build-r21-workflow/build-config.json').read_bytes())
config=json.loads((stage/'build-config.json').read_bytes());assert {k:v for k,v in baseline.items()if k not in ['project','output']}=={k:v for k,v in config.items()if k not in ['project','output']},'SAME_PRODUCTION_BUILD_CONFIG_REQUIRED'
assert result['workplaceAdapter']['riskUnitAddReturn']['sourceFilesRestored'] and result['workplaceAdapter']['sourceRestored']
report={'allFilesExactSHA256Verified':len(files),'localESMReferencesResolved':imports,
        'entryScriptsAndStylesPresent':True,'threeActualCompiledBusinessComponentsIdentified':True,
        'compiledTaskHeaderWidthsVerified':True,'compiledEventResponsiveMediaAndSharedResizeObserverLinked':True,
        'compiledStatisticsGridAndContainerUnitsPresent':True,
        'R18HomeStylesRetained':True,'compiledChunks':[charts[0][0],tasks[0][0],stats[0][0],wrappers[0]],
        'componentBrowserProof':'task-header-r20/browser-proof-r3/result.json',
        'fullAuthenticatedCompiledPortalBrowserExercised':False,'publicInstalled':False,'riskFormNativeRefreshCompiled':True,'riskFormChunk':risk[0][0],'R21InitiatorFilterCompiled':True,'workflowChunk':workflow[0][0],'sameProductionConfigAsPublicR21':True,'allAdapterSourceRestored':True}
(stage/'compiled-static-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))

