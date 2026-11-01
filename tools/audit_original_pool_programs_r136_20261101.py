from pathlib import Path
import hashlib,io,json,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101';out=R/'work/event_delivery_consistency_20261030/full-controller-r136/pool-static';assert not out.exists();out.mkdir(parents=True)
names=[]
with zipfile.ZipFile(A/'payload/business/lib/dynamic-datasource-creator-4.2.0.jar')as z:
    names=[n[:-6].replace('/','.')for n in z.namelist()if n.endswith('.class')and any(s in n for s in ['HikariCpConfig','HikariDataSourceCreator','DefaultDataSourceCreator'])]
results={}
for name in names:
    p=out/(name.rsplit('.',1)[-1]+'.txt');r=subprocess.run([str(A/'runtime/jdk17/bin/javap.exe'),'-J-Xmx128m','-p','-c','-classpath',str(A/'payload/business/lib/dynamic-datasource-creator-4.2.0.jar'),name],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0;p.write_bytes(r.stdout);results[name]={'bytecodeFile':str(p),'sha256':hashlib.sha256(r.stdout).hexdigest()}
with zipfile.ZipFile(A/'payload/platform/original-platform.jar')as z:platform=[n for n in z.namelist()if n.startswith('BOOT-INF/lib/')and any(s in n.lower()for s in ['hikari','druid','datasource'])]
result={'businessInspectedClasses':results,'platformNestedPoolLibraryNames':platform,'runtimeOrPrivateConfigurationOrDatabasesChanged':False};(D/'pool-program-class-inspection.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
