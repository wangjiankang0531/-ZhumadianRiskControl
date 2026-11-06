"""Patch only two original service methods; never modify the Reference archive/Jar."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
S=A/'source-review/hazard-source-attachment-transaction-r1210';D=R/'Document/Deployment/hazard_attachment_transaction_r1210_20261106'
origin=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.java'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not S.exists()and not D.exists()
ui=json.loads((R/'work/hazard-attachment-probe-r1207/ui-mainflow/result.json').read_bytes());assert ui['passed']and ui['failedEditPreservedMainRow']and ui['attachmentAtomicityPreserved']is False and ui['writeCounts']=={'upload':1,'create':1,'failedEdit':1}
source=origin.read_text('utf8');text=source
def one(a,b):
 global text
 assert text.count(a)==1,a
 text=text.replace(a,b)
one('import org.springframework.stereotype.Service;','import org.springframework.stereotype.Service;\nimport org.springframework.transaction.annotation.Transactional;')
one('    @Override\n    public boolean save(HazardSourceVo vo){\n        getBaseMapper().insert(vo.getHazardSource());','''    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean save(HazardSourceVo vo){
        if (getBaseMapper().insert(vo.getHazardSource()) != 1) return false;''')
one('''    @Override
    public boolean updateById(HazardSourceVo vo){
        baseFileService.deleteFile(vo.getHazardSource().getId());
        if(CommonUtil.isExist(vo.getBaseFileList())){
            baseFileService.insertFile(vo.getBaseFileList(),vo.getHazardSource().getId());
        }
        return getBaseMapper().updateById(vo.getHazardSource())!=0;
    }''','''    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(HazardSourceVo vo){
        // Acquire/update the live business row before touching its attachments.
        // A missing or concurrently deleted row returns false with no link writes.
        if (getBaseMapper().updateById(vo.getHazardSource()) != 1) return false;
        baseFileService.deleteFile(vo.getHazardSource().getId());
        if(CommonUtil.isExist(vo.getBaseFileList())){
            baseFileService.insertFile(vo.getBaseFileList(),vo.getHazardSource().getId());
        }
        return true;
    }''')
assert text.count('@Transactional(rollbackFor = Exception.class)')==2
S.mkdir();D.mkdir();target=S/'src/com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.java';target.parent.mkdir(parents=True);target.write_text(text,encoding='utf8')
classes=V/'hazard_transaction_r1210/classes';classes.mkdir(parents=True)
cmd=[str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx256m','--release','17','-encoding','UTF-8','-proc:none','-cp',str(G/'payload/business/application.jar')+';'+str(G/'payload/business/lib/*'),'-d',str(classes),str(target)]
p=subprocess.run(cmd,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
if p.returncode!=0:
 (D/'compile-failure.private.log').write_bytes(p.stdout+p.stderr)
 raise AssertionError('CANDIDATE_COMPILE_FAILED_INSPECT_RETAINED_LOG')
outputs=list(classes.rglob('*.class'));assert len(outputs)==1 and outputs[0].relative_to(classes).as_posix()=='com/iemp/endanger/server/hazardSource/service/impl/HazardSourceServiceImpl.class'
javap=subprocess.run([str(G/'runtime/jdk17/bin/javap.exe'),'-J-Dfile.encoding=UTF-8','-J-Dsun.stdout.encoding=UTF-8','-v','-p',str(outputs[0])],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW).stdout.decode('utf8')
assert javap.count('org.springframework.transaction.annotation.Transactional(')==2 and javap.count('rollbackFor=[class Ljava/lang/Exception;]')==2
proof={'schema':'xnby.hazard-source-attachment-transaction-candidate.v1','originalSourceSHA256':sha(origin),'candidateSourceSHA256':sha(target),'candidateClassSHA256':sha(outputs[0]),'candidateClassBytes':outputs[0].stat().st_size,'compiledWithOriginalBusinessArchiveAndDependencies':True,'javaClassMajor':61,'methodsChanged':['save(HazardSourceVo)','updateById(HazardSourceVo)'],'otherServiceSourceUnchanged':True,'rollbackForExceptionOnBothMethods':True,'updateFalsePrecedesEveryAttachmentMutation':True,'databaseSchemaChanged':False,'ReferenceOrOriginalJarChanged':False,'actualOriginalServiceLifecycleAccepted':False,'notificationAfterCommitOrAllNangangAccepted':False,'publicInstalled':False}
(D/'candidate-source-compile.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
