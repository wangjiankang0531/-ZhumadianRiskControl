"""Reproduce original missing-token failure with empty request doubles; never log in or invoke business methods."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess,zipfile
from reference_flat_runtime import verify

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args()
 W=args.workspace.resolve(strict=True);A=W.parents[1];root=args.output.resolve();assert A.name=='Application' and root.is_relative_to(W) and not root.exists()
 flat=W/'original-shared-runtime-r1_20261024/flat';verify(flat)
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 assert sha(flat/'application.jar')=='c4637e950664ff2ee26746b80366ca12e8c1f36f69288d35e126871f9afe30ae'
 with zipfile.ZipFile(flat/'application.jar') as z:
  assert hashlib.sha256(z.read('com/iemp/endanger/server/emergencyResponse/controller/EventDisposalRecordController.class')).hexdigest()=='28d7258b66d27bb236b33347acc40393161daf51d5cd00bbab228a852d8591e0'
 meta=json.loads((W/'own-pboot-r32/preparation.json').read_bytes());jdk=pathlib.Path(meta['javaHome'])
 assert sha(jdk/'bin/java.exe')=='6db7759259dc79800c5c6014f0ec68961a1fe69c36bb9b2a15a42c3b0c413f6a'
 assert sha(jdk/'bin/javac.exe')=='50b7d8d069b58e10cd8cc6a36d647d8049144d0a0508da8a0a892b76610cc68b'
 root.mkdir();classes=root/'classes';classes.mkdir();(root/'tmp').mkdir()
 source=pathlib.Path(__file__).parent/'java/OriginalMissingAuthenticationProbe.java'
 env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};env.update(TMP=str(root/'tmp'),TEMP=str(root/'tmp'))
 def run(command,name):
  r=subprocess.run(list(map(str,command)),cwd=root,env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);(root/(name+'.private.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,name;return r.stdout
 run([jdk/'bin/javac.exe','-proc:none','-encoding','UTF-8','-cp',flat/'application.jar','-d',classes,source],'compile')
 stdout=run([jdk/'bin/java.exe','-Xmx128m','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',str(classes)+os.pathsep+str(flat/'application.jar'),'xnby.replica.OriginalMissingAuthenticationProbe'],'probe')
 assert b'originalInterceptorMissingAuthNullPointerReproduced=true' in stdout and b'controllerMethodInvoked=false' in stdout and b'realTokenReadOrCreated=false' in stdout
 result={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'originalInterceptorMissingAuthNullPointerReproduced':True,'onlyEmptyRequestHeadersUsed':['X-TOKEN','Authorization'],'originalControllerMethodInvoked':False,'databaseConnected':False,'realTokenReadOrCreated':False,'authenticationChangedOrBypassed':False,'originalLibraryOrApplicationChanged':False,'sourceSHA256':sha(source),'compiledClassSHA256':sha(classes/'xnby/replica/OriginalMissingAuthenticationProbe.class'),'publicDeployed':False,'fullCloneReady':False}
 (root/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
