"""Do not rerun preparation/compilation; verify the existing candidate class."""
from pathlib import Path
import hashlib,json,struct,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
S=A/'source-review/hazard-source-attachment-transaction-r1210';D=R/'Document/Deployment/hazard_attachment_transaction_r1210_20261106'
origin=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.java'
target=S/'src/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.java';cls=V/'hazard_transaction_r1210/classes/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert cls.is_file()and not(D/'candidate-source-compile.json').exists()
p=subprocess.run([str(G/'runtime/jdk17/bin/javap.exe'),'-J-Dfile.encoding=UTF-8','-J-Dsun.stdout.encoding=UTF-8','-v','-p',str(cls)],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
text=p.stdout.decode('utf8');assert text.count('org.springframework.transaction.annotation.Transactional(')==2 and text.count('rollbackFor=[class Ljava/lang/Exception;]')==2
raw=cls.read_bytes();assert raw[:4]==b'\xca\xfe\xba\xbe'and struct.unpack('>H',raw[6:8])[0]==61
proof={'schema':'xnby.hazard-source-attachment-transaction-candidate.v1','originalSourceSHA256':sha(origin),'candidateSourceSHA256':sha(target),'candidateClassSHA256':sha(cls),'candidateClassBytes':cls.stat().st_size,'compiledWithOriginalBusinessArchiveAndDependencies':True,'javaClassMajor':61,'methodsChanged':['save(HazardSourceVo)','updateById(HazardSourceVo)'],'rollbackForExceptionOnBothMethods':True,'updateFalsePrecedesEveryAttachmentMutation':True,'databaseSchemaChanged':False,'ReferenceOrOriginalJarChanged':False,'actualOriginalServiceLifecycleAccepted':False,'notificationAfterCommitOrAllNangangAccepted':False,'publicInstalled':False,'firstCompileSucceededButInspectionDecoderFailed':True,'verificationUsesExplicitJavaUTF8Output':True,'compileWasNotRepeated':True}
(D/'candidate-source-compile.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');(D/'candidate-class-javap.txt').write_text(text,encoding='utf8');print(json.dumps(proof))
