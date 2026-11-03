from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=J(R/'work/plan-six-relations-ui-r394/terminal.json');assert t['allOwnedControllerHandlesTerminal']and t['originalGCodeAndPointersRestored']
f=J(R/'work/event_delivery_consistency_20261030/full-controller-r163/r153/plan-browser/failure.json')
assert f['message']=='OWN_READONLY_MEMBER_VALUE_副指挥长'and len(f['cases'])==11
assert len(f['resourceDeletionSteps'])==12
b=(V/'verify_native_plan_six_relations_dialog_r394.mjs').read_text(encoding='utf-8')
old=' for(const kind of memberKinds)if(!await evaluate(`(${memberRoot(kind.title)})?.textContent.includes(${JSON.stringify(ownMemberValue(kind,0,kind.fields[0],true))})===true`))throw Error(\'OWN_READONLY_MEMBER_VALUE_\'+kind.title);'
new=r'''
 stage='readonly-all-six-relation-values';
 for(const kind of memberKinds){
  for(const field of kind.fields){const expected=ownMemberValue(kind,0,field,true);
   if(!await evaluate(`(()=>{const g=${memberRoot(kind.title)},rows=g?.querySelectorAll('.item-form');if(rows?.length!==1)return false;const f=Array.from(rows[0].querySelectorAll('.el-form-item')).find(e=>e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(field)}),input=f?.querySelector('input,textarea');return!!input&&input.disabled&&input.value===${JSON.stringify(expected)}})()`))throw Error('OWN_READONLY_DISABLED_INPUT_VALUE_'+kind.title+'_'+field);
  }
 }
'''
assert b.count(old)==1;b=b.replace(old,new,1)
bf=V/'verify_native_plan_six_relations_readonly_r396.mjs';assert not bf.exists();bf.write_text(b,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
s=(V/'plan_relation_ui_r394.py').read_text(encoding='utf-8')
s=s.replace('plan-six-relations-ui-r394','plan-six-relations-ui-r396').replace('lifecycle-r394','lifecycle-r396')
s=s.replace("full-controller-r163/r153'","full-controller-r163/r155'")
s=s.replace('verify_native_plan_six_relations_dialog_r394.mjs',bf.name).replace('bbc40e5a9c5f75d041b2da4850837cf5fc5250ddcc6b2a85ce6b73f74560ebe6',sha(bf))
s=s.replace('verified-native-r394.json','verified-native-r396.json')
out=V/'plan_relation_ui_r396.py';assert not out.exists();ast.parse(s);out.write_text(s,encoding='utf-8')
prep=(V/'prepare_plan_relation_ui_fixture_r394.py').read_text(encoding='utf-8').split('# Keep diagnostics',1)[0]
prep=prep.replace('plan-six-relations-ui-r394','plan-six-relations-ui-r396')
prep+="\n(D/'lifecycle-r396').mkdir()\nprint(json.dumps({'prepared':True,'codeOnly':True,'databaseCopiedOrServicesStarted':False}))\n"
pf=V/'prepare_plan_relation_ui_fixture_r396.py';assert not pf.exists();ast.parse(prep);pf.write_text(prep,encoding='utf-8')
proof={'preparedOnly':True,'r394ActualAllSixEditedReadbackPassed':True,'r394ThreeResourcesTwelveCancelConfirmStepsPassed':True,
 'r394ReadonlyTextAssertionNotAcceptedAsMissingDataProof':True,'readonlyNowChecksActualDisabledInputValueForEveryMemberField':True,
 'browserSHA256':sha(bf),'driverSHA256':sha(out),'fixturePreparerSHA256':sha(pf),'productCandidateChanged':False,'native29Pending':True}
(D/'readonly-retry-prepared-r396.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
