from pathlib import Path
import hashlib,json,re,sys
R=Path('D:/Project/Zhumadian')
stage=R/'work/user_feedback_20261031/workplace-security-build-r1'
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
assert all(t in tasks[0][1]for t in ['"min-width":"112"','"min-width":"168"','width:"80"'])
wrappers=[n for n,s in js.items()if 'name_ECharts_lang'in n and 'ResizeObserver'in s and 'disconnect'in s]
assert len(wrappers)==1
assert wrappers[0].split('/')[-1] in charts[0][1]
css='\n'.join((root/n).read_text(encoding='utf-8')for n in files if n.endswith('.css'))
assert 'container-type:inline-size'in css and 'minmax(min(100%,270px),1fr)'in css
report={'allFilesExactSHA256Verified':len(files),'localESMReferencesResolved':imports,
        'entryScriptsAndStylesPresent':True,'threeActualCompiledBusinessComponentsIdentified':True,
        'compiledTaskHeaderWidthsVerified':True,'compiledEventResponsiveMediaAndSharedResizeObserverLinked':True,
        'compiledStatisticsGridAndContainerUnitsPresent':True,
        'R18HomeStylesRetained':True,'compiledChunks':[charts[0][0],tasks[0][0],stats[0][0],wrappers[0]],
        'componentBrowserProof':'workplace-chart-r1/browser-proof-r3/result.json',
        'fullAuthenticatedCompiledPortalBrowserExercised':False,'publicInstalled':False}
(stage/'compiled-static-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
