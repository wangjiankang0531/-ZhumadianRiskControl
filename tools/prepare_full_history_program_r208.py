from pathlib import Path
import ast
V=Path(__file__).parent;s=(V/'verify_personal_workflow_full_program_r197_20261103.py').read_text(encoding='utf-8')
s=s.replace("S=W/'r35-personal-workflow-candidate-r1'","S=W/'r36-native-history-candidate-r1'").replace("OLD=W/'r34-pending-visibility-candidate-r1/bundle'","OLD=W/'r35-personal-workflow-candidate-r1/bundle'").replace('r35gv-r1','r36gv-r1').replace('original_public_test_update_r35_20261103.py','original_public_test_update_r36_20261103.py').replace('original_public_test_update_r34_20261102.py','original_public_test_update_r35_20261103.py').replace('workflow-pending-visibility-r178/dist','personal-workflow-routes-r195/dist')
old="else G/n;assert sha(p)==pin;controllers[n]="
new="else W/'r35-personal-workflow-candidate-r1/contract-Application'/n;assert sha(p)==pin;controllers[n]="
assert s.count(old)==1;s=s.replace(old,new)
old="name=next(n for n in plan['files']if n.startswith('frontend/emergency_pc/')and n not in oldq['files']);"
new="name=next(n for n in m.R36_HISTORY_CONTRACT['files']if n not in oldq['files']);"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('xnby.r197.personal-workflow-full-program-preflight.v1','xnby.r208.native-history-full-program-preflight.v1').replace('full-R34-program-view-and-20-controls-exact-composition','full-R35-program-view-and-20-old-21-new-controls-exact-composition').replace('actualR34ProgramAndR35CandidatePinsRetained','actualR35ProgramAndR36CandidatePinsRetained').replace('fullR34ProgramViewBuilt','fullR35ProgramViewBuilt').replace("'oldAndNewControlFiles':20","'oldControlFiles':20,'newControlFiles':21")
ast.parse(s);p=V/'verify_native_history_full_program_r208_20261103.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('R36_FULL_OLD_PROGRAM_VIEW_FROM_EXACT_R35_FRONTENDS_AND_IMMUTABLE_OLD_CONTROLS_PREPARED')
