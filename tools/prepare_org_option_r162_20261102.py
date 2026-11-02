from pathlib import Path
import json,hashlib
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r159'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(C/'r3/controller-terminal.json')['exitCode']==0 and J(C/'r3-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert not(C/'r4').exists()and not(C/'prepared-r4').exists()
lib=R/'Application/work/tianjin_native_20261023/security_pc/node_modules/element-plus/es/components'
assert 'extends: ElOption'in(lib/'tree-select/src/tree-select-option.mjs').read_text(encoding='utf-8')
assert 'role: "option"'in(lib/'select/src/option.mjs').read_text(encoding='utf-8')
p=V/'verify_org_native_diagnostic_r159_20261102.mjs';s=p.read_text(encoding='utf-8');before=sha(p)
s=s.replace('.el-tree-select__popper .el-tree-node__label','.el-tree-select__popper [role=option]')
s=s.replace("const options=await evaluate(","await fs.writeFile(O+'/own-select-control-structure.json',JSON.stringify(await evaluate('(()=>{const f=Array.from(document.querySelectorAll(\".el-form-item\")).find(e=>e.querySelector(\".el-form-item__label\")?.textContent.trim().startsWith(\"责任部门\"));return{field:f?.outerHTML.slice(0,7000),poppers:Array.from(document.querySelectorAll(\".el-tree-select__popper\")).map(e=>e.outerHTML.slice(0,10000))}})()'),null,2));\n const options=await evaluate(",1)
s=s.replace("{headers:{Authorization:normalToken,'User-Agent':agent}})","{headers:{Authorization:normalToken,'User-Agent':agent},signal:AbortSignal.timeout(10000)})")
p.write_text(s,encoding='utf-8')
run=V/'run_org_controller_r159_20261102.py';t=run.read_text(encoding='utf-8');t=t.replace("attempt in['r1','r2','r3']","attempt in['r1','r2','r3','r4']");run.write_text(t,encoding='utf-8')
P=C/'prepared-r4';P.mkdir()
for name in ['controller-fixture-ready.json','own-serial-definition.json']:(P/name).write_bytes((C/'prepared-r1'/name).read_bytes())
assert sha(R/'_g/Application/release-manifest.json')==J(P/'controller-fixture-ready.json')['releaseSHA256']
(P/'diagnostic-source-pins.json').write_text(json.dumps({'beforeObserverSHA256':before,'browserSHA256':sha(p),'hostSHA256':sha(V/'verify_org_controller_r159_20261102.py'),'runnerSHA256':sha(run),'originalTreeSelectOptionSHA256':sha(lib/'tree-select/src/tree-select-option.mjs'),'originalElOptionSHA256':sha(lib/'select/src/option.mjs'),'actualRenderedOptionSelector':'.el-tree-select__popper [role=option]','noProductConfigurationOrBusinessRowsChange':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'attempt':'r4','priorActualProcessesTerminal':True,'actualElOptionRenderingDerivedFromOriginalLibrary':True,'ownControlMarkupCapturedBeforeAssertions':True,'noProductChange':True}))
