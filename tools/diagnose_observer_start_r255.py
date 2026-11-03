from pathlib import Path
import json,re
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r163';A=R/'_g/Application';J=lambda p:json.loads(p.read_bytes())
pid=J(C/'r123/controller-started.json')['pid'];hits=[]
for p in(A/'UserData/OriginalServer/runs').glob('j*/receipt.json'):
 if J(p).get('controllerPID')==pid:hits.append(p.parent)
assert len(hits)==1;root=hits[0];rows=[]
for p in root.rglob('*'):
 if not p.is_file()or not any(w in p.name.lower()for w in ['log','error','failure']):continue
 if p.stat().st_size>8*1024*1024:continue
 text=p.read_text(encoding='utf-8',errors='replace');markers=sorted(set(re.findall(r'OWN_MAPPER_[A-Z_]+',text)))
 exceptions=[]
 for line in text.splitlines():
  if 'Caused by:' in line:
   m=re.search(r'Caused by:\s+([A-Za-z0-9_.$]+)',line)
   if m:exceptions.append(m.group(1))
 frames=re.findall(r'at (xnby\.own\.OwnMapperRegistrationObservationR255[^\r\n]*)',text)
 known=['Could not find or load main class','ClassNotFoundException','NoClassDefFoundError','UnsupportedClassVersionError','Unrecognized option','Could not reserve enough space','OutOfMemoryError','insufficient memory','Unrecognized VM option','AccessControlException','ExceptionInInitializerError','Error occurred during initialization of VM','Picked up JAVA_TOOL_OPTIONS','JVMJ9VM','Invalid maximum heap size','os::commit_memory','Native memory allocation','Paging file','paging file']
 matched=[x for x in known if x.lower()in text.lower()]
 codes=sorted(set(re.findall(r'(?:Exception|Error):\s+([A-Z][A-Z0-9_]{3,})\s*$',text,re.M)))
 generic=sorted(set(re.findall(r'\b(?:java|org|com|xnby)\.[\w.$]*(?:Exception|Error)\b',text)))
 if markers or exceptions or matched or generic:rows.append({'file':p.relative_to(root).as_posix(),'ownMarkerCodes':markers,'exceptionClasses':exceptions,'ownObserverFrames':frames,'knownFailurePhrasesMatched':matched,'qualifiedExceptionClassNames':generic,'uppercaseExceptionCodes':codes})
out={'ownAttempt':'r123','runtimeDirectory':root.name,'diagnostics':rows,'rawLogOrCredentialOrSQLTextReturned':False}
(R/'Document/Deployment/original_mapper_registration_r255_20261103/startup-failure-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
