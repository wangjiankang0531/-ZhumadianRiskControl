from pathlib import Path
import ast,json
T=Path('D:/Project/Zhumadian/Application/tools')
def save(n,s):
 p=T/n;assert not p.exists(),n
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8')
def swap(s,a,b):
 assert s.count(a)==1,(a[:90],s.count(a));return s.replace(a,b)
browser=(T/'verify_native_plan_exercise_r226_20261103.mjs').read_text(encoding='utf-8')
start=browser.index('const value=label=>');end=browser.index('async function ownAPI(',start)
fields='''let activeFormTitle=null,optionalJoinConsoleErrors=0;
const fieldOwner=()=>activeFormTitle?`Array.from(document.querySelectorAll('.el-dialog')).find(d=>d.getClientRects().length&&d.querySelector('.el-dialog__title')?.textContent.trim()===${JSON.stringify(activeFormTitle)})`:'document';
const value=label=>evaluate(`(()=>{const root=${fieldOwner()};const a=Array.from(root?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});return a?.querySelector('input,textarea')?.value??null})()`);
async function fill(label,text){if(!await evaluate(`(()=>{const root=${fieldOwner()};const a=Array.from(root?.querySelectorAll('.el-form-item')||[]).find(e=>e.getClientRects().length&&e.querySelector('.el-form-item__label')?.textContent.trim()===${JSON.stringify(label)});const e=a?.querySelector('input,textarea');if(!e||e.disabled||e.readOnly)return false;e.value=${JSON.stringify(text)};e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return e.value===${JSON.stringify(text)}})()`))throw Error('EXACT_ACTIVE_FORM_FIELD_'+label);}
'''
browser=browser[:start]+fields+browser[end:]
anchor=" }else if(v.method==='Runtime.exceptionThrown')"
assert browser.count(anchor)==1
browser=browser.replace(anchor," }else if(v.method==='Runtime.consoleAPICalled'){const text=(v.params.args||[]).map(a=>String(a.description||a.value||'')).join(' ');if(/TypeError/.test(text)&&/join|undefined/.test(text))optionalJoinConsoleErrors++;\n }else if(v.method==='Runtime.exceptionThrown')")
browser=swap(browser,"stage='optional-participants-baseline-reproduction';", "activeFormTitle='新增演练记录';stage='optional-participants-baseline-reproduction';")
browser=swap(browser,"const beforeEmpty=exerciseCount();", "if(await value('演练地点')!==exerciseName+'_EMPTY')throw Error('ACTIVE_EXERCISE_LOCATION_REQUIRED_BEFORE_SUBMIT');\n const beforeEmpty=exerciseCount();")
browser=swap(browser,"await until(()=>exceptions.some(x=>/join|undefined/.test(x.description||'')));", "await until(()=>optionalJoinConsoleErrors>0||exceptions.some(x=>/join|undefined/.test(x.description||'')));")
browser=swap(browser,"uncaughtUndefinedJoinException:true", "actualUndefinedJoinErrorObservedViaRuntimeOrConsole:true,activeChildDialogLocationFilled:true")
browser=swap(browser,"if(!row)throw Error('EXERCISE_LIST_VIEW_BUTTON');", "if(!row)throw Error('EXERCISE_LIST_VIEW_BUTTON');activeFormTitle='演练记录详情';")
save('verify_native_plan_exercise_r227_20261103.mjs',browser)
host=(T/'verify_full_controller_plan_exercise_r226_20261103.py').read_text(encoding='utf-8').replace('r226','r227').replace('r113','r115').replace('r114','r116')
save('verify_full_controller_plan_exercise_r227_20261103.py',host)
save('plan_mapper_patch_r227.py',(T/'plan_mapper_patch_r226.py').read_text(encoding='utf-8').replace('r226','r227').replace('r113','r115').replace('r114','r116'))
for mode,old_attempt,new_attempt in [('baseline','r113','r115'),('candidate','r114','r116')]:
 for base in ['prepare_personal_workflow_frontend','restore_personal_workflow_frontend','prepare_production_history_runtime','restore_production_history_runtime']:
  old=base+'_r226_'+mode+'.py';new=base+'_r227_'+mode+'.py'
  save(new,(T/old).read_text(encoding='utf-8').replace('r226','r227').replace(old_attempt,new_attempt))
 s=(T/('run_plan_exercise_r226_'+mode+'_20261103.py')).read_text(encoding='utf-8').replace('r226','r227').replace(old_attempt,new_attempt)
 save('run_plan_exercise_r227_'+mode+'_20261103.py',s)
print(json.dumps({'prepared':True,'baselineAttempt':'r115','candidateAttempt':'r116','testFieldScopedToExactActiveChildDialog':True,'consoleAndRuntimeErrorChannelsObserved':True,'productSourceChangedByThisHarnessRevision':False,'notYetRun':True}))
