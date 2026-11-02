from pathlib import Path
import ast,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
s=(T/'verify_project_header_full_program_r168_20261102.py').read_text(encoding='utf-8')
s=s.replace("S=W/'r33-project-header-candidate-r1'","S=W/'r34-pending-visibility-candidate-r1'").replace("OLD=W/'r32-avatar-candidate-r1/bundle'","OLD=W/'r33-project-header-candidate-r1/bundle'").replace("OUT=R/'work/r33gv-r1'","OUT=R/'work/r34gv-r1'")
s=s.replace("source=T/'original_public_test_update_r33_20261102.py'","source=T/'original_public_test_update_r34_20261102.py'")
old="p=(W/'avatar-full-r157'/('security_pc/build/dist'if n.split('/')[1]=='security_pc'else'emergency_pc/dist')/n.split('/',2)[2])if n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))else G/n;"
new="p=((W/'avatar-full-r157/security_pc/build/dist'if n.split('/')[1]=='security_pc'else W/'project-header-home-r167/dist')/n.split('/',2)[2])if n.startswith(('frontend/security_pc/','frontend/emergency_pc/'))else G/n;"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("T/'original_public_test_update_r32_20261102.py'","T/'original_public_test_update_r33_20261102.py'")
s=s.replace('xnby.r168.project-header-full-program-preflight.v1','xnby.r179.pending-visibility-full-program-preflight.v1').replace('full-R31-program-view-and-20-controls-exact-composition','full-R33-program-view-and-20-controls-exact-composition').replace('actualR31ProgramAndR32CandidatePinsRetained','actualR33ProgramAndR34CandidatePinsRetained')
p=V/'verify_pending_visibility_full_program_r179_20261102.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8');print(json.dumps({'prepared':True,'sourceMappingSecurityAndEmergencyOnly':True,'noActualPrivateSeedOrBusinessDataToBeRead':True}))
