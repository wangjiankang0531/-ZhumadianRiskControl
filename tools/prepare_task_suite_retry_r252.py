from pathlib import Path
import ast,json,subprocess,sys
V=Path(__file__).parent;T=Path('D:/Project/Zhumadian/Application/tools')
s=(V/'prepare_task_attachment_candidate_r250.py').read_text(encoding='utf-8').replace('r250','r252').replace('r121','r122')
anchor="save('verify_full_controller_task_attachment_r252_20261103.py',host)"
assert s.count(anchor)==1
s=s.replace(anchor,"""java=(T/'OwnPersonalWorkflowMenuVisibilityR218.java').read_text(encoding='utf-8').replace('OwnPersonalWorkflowMenuVisibilityR218','OwnPersonalWorkflowMenuVisibilityR252').replace('r108','r122')
save('OwnPersonalWorkflowMenuVisibilityR252.java',java)
host=host.replace('OwnPersonalWorkflowMenuVisibilityR218','OwnPersonalWorkflowMenuVisibilityR252')
"""+anchor)
p=V/'prepare_task_attachment_candidate_r252.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(V/'prepare_task_fixture_r250.py').read_text(encoding='utf-8').replace('r250','r252').replace('r121','r122')
p2=V/'prepare_task_fixture_r252.py';assert not p2.exists();ast.parse(s);p2.write_text(s,encoding='utf-8')
r=subprocess.run([sys.executable,str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')[-700:];print(r.stdout.decode())
