from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T));P=R/'Application/work/tianjin_native_20261023/emergency_pc';F=R/'work/user_feedback_20261031/emergency-workflow-source-r8/source'
import original_business_result_compat as business
import original_duty_result_compat as duty
import original_confirmed_operation_compat as confirm
sha=lambda raw:hashlib.sha256(raw).hexdigest();rows=[]
def add(rel,updated):
 before=(P/rel).read_bytes();current=(F/rel).read_bytes();rows.append({'path':rel,'originalSHA256':sha(before),'expectedRetainedSHA256':sha(updated),'currentSHA256':sha(current),'status':'retained'if current==updated else'original-guard-missing'if current==before else'changed-needs-exact-composition'})
rel=business.relative('emergency_pc');add(rel,business.transform('emergency_pc',(P/rel).read_bytes())[0])
for kind in duty.PINS:
 rel=duty.relative(kind);add(rel,duty.transform(kind,(P/rel).read_bytes())[0])
catalog=confirm.catalog()['kindResults']['emergency_pc'];rel=catalog['hook']['path'];add(rel,confirm.transform_hook((P/rel).read_bytes()))
for rel,record in catalog['files'].items():add(rel,confirm.transform_caller((P/rel).read_bytes(),record))
out=R/'work/event_delivery_consistency_20261030/full-controller-r129/retained-front-adapter-audit.json';out.write_text(json.dumps({'files':rows,'scope':'published R21 confirmed emergency builder compatibility chain','productModified':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
