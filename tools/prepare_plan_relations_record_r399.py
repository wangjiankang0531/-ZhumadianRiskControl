from pathlib import Path
import ast,json
V=Path(__file__).resolve().parent
s=(V/'record_plan_relations_verified_r397.py').read_text(encoding='utf-8')
s=s.replace('r397','r399').replace('R397','R399')
s=s.replace('plan-six-relations-ui-r396','plan-six-relations-ui-r398').replace('verified-native-r396.json','verified-native-r398.json')
s=s.replace("full-controller-r163/r155'","full-controller-r163/r157'")
s=s.replace('r390ThreeControllersAndR396OneControllerNormalZero','r390ThreeControllersAndR398OneControllerNormalZero')
s=s.replace('r390ActualApplyAndRollbackSeparateFromR396UIIteration','r390ActualApplyAndRollbackSeparateFromR398UIIteration')
s=s.replace('R396是其后单控制器','R398是其后单控制器').replace('最终r155','最终r157')
anchor=" 'record_plan_relations_verified_r399.py']"
assert s.count(anchor)==1
s=s.replace(anchor," 'prepare_plan_relation_readonly_r396.py','prepare_plan_relation_ui_fixture_r396.py',\n 'verify_native_plan_six_relations_readonly_r396.mjs','plan_relation_ui_r396.py',\n 'prepare_plan_relation_download_r398.py','prepare_plan_relation_ui_fixture_r398.py',\n 'verify_native_plan_six_relations_disk_r398.mjs','plan_relation_ui_r398.py','prepare_plan_relations_record_r399.py',\n 'record_plan_relations_verified_r399.py']",1)
anchor=" 'ui-fixture-prepared-r394.json','readonly-retry-prepared-r396.json','verified-native-r398.json'"
assert s.count(anchor)==1;s=s.replace(anchor," 'ui-fixture-prepared-r394.json','readonly-retry-prepared-r396.json','download-retry-prepared-r398.json','verified-native-r398.json'",1)
anchor=" (R/'work/event_delivery_consistency_20261030/full-controller-r163/r153/plan-browser','failure.json')]:"
assert s.count(anchor)==1;s=s.replace(anchor," (R/'work/event_delivery_consistency_20261030/full-controller-r163/r153/plan-browser','failure.json'),\n (R/'work/event_delivery_consistency_20261030/full-controller-r163/r155/plan-browser','failure.json')]:",1)
s=s.replace('四个驱动问题保留：','五个驱动问题保留：').replace('只读误查textContent。','只读误查textContent、下载完成事件后未等最终文件落盘。')
s=s.replace('禁用输入值验证，产品候选','禁用输入值及最终文件名/字节等待验证，产品候选')
s=s.replace('两轮原G代码/配置/894元数据前像恢复','更新回滚轮与最终UI轮原G代码/配置/894元数据前像恢复')
s=s.replace("for n in names:shutil.copyfile", "assert len(names)==len(set(names)), 'DUPLICATE_SOURCE_SCOPE'\nfor n in names:shutil.copyfile")
# Earlier R397 template already listed the R396 tools: deduplicate only the explicit names literal.
t=ast.parse(s);node=next(n for n in t.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='names')
literal=ast.get_source_segment(s,node);names=list(dict.fromkeys(ast.literal_eval(node.value)))
s=s.replace(literal,'names='+repr(names),1)
s=s.replace("proof=J(D/'verified-native-r398.json');terminal=J(O/'terminal.json')", "proof=J(D/'lifecycle-r398/verified-native-r398.json');terminal=J(O/'terminal.json')",1)
s=s.replace(" shutil.copyfile(D/n,vf/n);files.append((vf/n).relative_to(A).as_posix())", " source=D/'lifecycle-r398'/n if n=='verified-native-r398.json'else D/n\n shutil.copyfile(source,vf/n);files.append((vf/n).relative_to(A).as_posix())\ndisk=J(C/'plan-browser/attachment-disk-evidence.json');assert disk['passed']and disk['all68BytesExactlyMatched']and disk['finalNameMatched']\ndump(vf/'attachment-disk-evidence.json',disk);files.append((vf/'attachment-disk-evidence.json').relative_to(A).as_posix())",1)
out=V/'record_plan_relations_verified_r399.py';assert not out.exists();ast.parse(s);out.write_text(s,encoding='utf-8')
print(json.dumps({'preparedOnly':True,'finalRecorder':out.name,'sourceFiles':len(names),'requiresActual29AndNormalRestoreAndCleanup':True}))
