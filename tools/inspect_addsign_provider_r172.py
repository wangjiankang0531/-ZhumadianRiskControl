from pathlib import Path
import zipfile,io,subprocess,hashlib,json,re
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent
with zipfile.ZipFile(R/'_g/Application/payload/platform/original-platform.jar')as z:
    jar=z.read('BOOT-INF/lib/jnpf-workflow-engine-biz-3.6.0-RELEASE.jar')
with zipfile.ZipFile(io.BytesIO(jar))as z:raw=z.read('jnpf/engine/service/impl/FlowTaskNewServiceImpl.class')
p=V/'r172-private-sdk-inspection';p.mkdir(exist_ok=False);c=p/'FlowTaskNewServiceImpl.class';c.write_bytes(raw)
r=subprocess.run([str(R/'_g/Application/runtime/jdk17/bin/javap.exe'),'-p','-c',str(c)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0
s=r.stdout.decode('utf-8',errors='replace');(p/'original-javap.private.txt').write_text(s,encoding='utf-8')
methods=re.split(r'(?=^  (?:public|private|protected) )',s,flags=re.M)
selected=[b for b in methods if re.search(r'^  .*freeApprover\(',b,re.M|re.I)]
assert len(selected)==1
block=selected[0];(p/'free-approver.private.txt').write_text(block,encoding='utf-8')
calls=[line.strip() for line in block.splitlines() if any(k in line for k in ['handleOpinion','HandleOpinion','OperatorRecord','HandleStatus','approve','Approval','Approval','freeApproverType','FreeApproverType'])]
proof={'classSHA256':hashlib.sha256(raw).hexdigest(),'originalNestedWorkflowJarSHA256':hashlib.sha256(jar).hexdigest(),'freeApproverMethodFound':True,'methodLines':len(block.splitlines()),'selectedCallReferences':calls,'scope':'original-fixed-platform-jar-read-only','originalSDKBytesPublished':False}
(p/'method-summary.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
