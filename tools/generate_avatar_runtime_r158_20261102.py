from pathlib import Path
import ast
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
s=(T/'verify_avatar_controller_r157_20261102.py').read_text(encoding='utf-8');assert s.count("base=R/'work/event_delivery_consistency_20261030/full-controller-r157'")==1;s=s.replace("base=R/'work/event_delivery_consistency_20261030/full-controller-r157'","base=R/'work/event_delivery_consistency_20261030/full-controller-r158'")
s=s.replace("'verify_avatar_runtime_r157_20261102.mjs'","'verify_avatar_runtime_r158_20261102.mjs'")
a="                    (run/'stop-requested.txt').write_text('OWN_NORMAL_STOP\\n',encoding='ascii')"
b="""                    if process.poll()is None:
                        try:
                            stopped=m.normal_stop(app,prepared['releaseSHA256'],candidate)
                            dump(root/'actual-updater-normal-stop.json',{'passed':True,'actualNewUpdaterNormalStopExecuted':True,'normalAllSixZero':all(v==0 for v in stopped['exitCodesBeforeJobClose'].values()),'forcedTerminationUsed':False})
                        except BaseException as error:
                            failure=type(error).__name__
                            dump(root/'actual-updater-normal-stop.json',{'passed':False,'actualNewUpdaterNormalStopExecuted':True,'failureType':type(error).__name__,'forcedTerminationUsed':False})
                            (run/'stop-requested.txt').write_text('OWN_NORMAL_STOP_AFTER_UPDATER_OBSERVATION_FAILURE\\n',encoding='ascii')"""
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("'schema':'xnby.r157.full-compiled-avatar-controller-check.v1'","'schema':'xnby.r158.new-updater-avatar-controller-check.v1','actualNewUpdaterNormalStopPassed':read(root/'actual-updater-normal-stop.json')['passed'],'updaterSHA256':prepared['updaterSHA256']")
ast.parse(s);p=V/'verify_avatar_controller_r158_20261102.py';assert not p.exists();p.write_text(s,encoding='utf-8')
s=(T/'verify_avatar_runtime_r157_20261102.mjs').read_text(encoding='utf-8');s=s.replace('full-controller-r157','full-controller-r158').replace('xnby.r157.actual-full-compiled-avatar-browser.v1','xnby.r158.actual-full-compiled-avatar-browser.v1');p=V/'verify_avatar_runtime_r158_20261102.mjs';assert not p.exists();p.write_text(s,encoding='utf-8')
s=(T/'run_avatar_controller_r157_20261102.py').read_text(encoding='utf-8');s=s.replace('full-controller-r157','full-controller-r158').replace('verify_avatar_controller_r157_20261102.py','verify_avatar_controller_r158_20261102.py');p=V/'run_avatar_controller_r158_20261102.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
print('OWN_NEW_UPDATER_RUNTIME_DRIVER_AND_ACTUAL_NORMAL_STOP_PREPARED')
