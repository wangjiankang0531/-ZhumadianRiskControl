from pathlib import Path
import json,hashlib
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r159'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert J(C/'r2/controller-terminal.json')['exitCode']==0 and J(C/'r2-outer-terminal.json')['actualDescendantsZeroBeforeClose']
assert J(R/'_g/own-fixture.json')['ownedSyntheticFixtureOnly']and not(R/'_g/user-manual-protected.json').exists()
assert not(C/'r3').exists()and not(C/'prepared-r3').exists()
component=R/'Application/work/tianjin_native_20261023/security_pc/node_modules/element-plus/es/components/tree-select/src/select.mjs'
text=component.read_text(encoding='utf-8');assert 'useNamespace("tree-select")'in text and 'ns.e("popper")'in text
p=V/'verify_org_native_diagnostic_r159_20261102.mjs';s=p.read_text(encoding='utf-8');before=sha(p)
assert '.el-select__popper .el-tree-node__label'in s
s=s.replace('.el-select__popper .el-tree-node__label','.el-tree-select__popper .el-tree-node__label')
s=s.replace('total:Number.isFinite(b.data?.total)?b.data.total:null,','total:b.data?.total!==null&&b.data?.total!==undefined&&Number.isFinite(Number(b.data.total))?Number(b.data.total):null,totalWireType:typeof b.data?.total,')
s=s.replace("check(baseline.httpStatus===200&&baseline.code===0&&baseline.rows>0&&baseline.mixedOwnDepartments,","check(baseline.httpStatus===200&&baseline.code===0&&baseline.rows>0&&Number.isInteger(baseline.total)&&baseline.total>0&&baseline.mixedOwnDepartments,")
p.write_text(s,encoding='utf-8')
run=V/'run_org_controller_r159_20261102.py';t=run.read_text(encoding='utf-8');assert "attempt in['r1','r2']"in t;t=t.replace("attempt in['r1','r2']","attempt in['r1','r2','r3']");run.write_text(t,encoding='utf-8')
P=C/'prepared-r3';P.mkdir()
for name in ['controller-fixture-ready.json','own-serial-definition.json']:(P/name).write_bytes((C/'prepared-r1'/name).read_bytes())
assert sha(R/'_g/Application/release-manifest.json')==J(P/'controller-fixture-ready.json')['releaseSHA256']
(P/'diagnostic-source-pins.json').write_text(json.dumps({'beforeObserverSHA256':before,'browserSHA256':sha(p),'hostSHA256':sha(V/'verify_org_controller_r159_20261102.py'),'runnerSHA256':sha(run),'actualOriginalTreeSelectSourceSHA256':sha(component),'actualOriginalComponentVersion':'2.9.7','correctTreeSelectPopperSelector':'.el-tree-select__popper','noProductConfigurationOrBusinessRowsChange':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'attempt':'r3','priorAttemptsTerminalAndEvidenceKept':True,'selectorDerivedFromActualInstalledComponent':True,'nativeTotalStringAndNumberHandled':True,'noProductChange':True}))
