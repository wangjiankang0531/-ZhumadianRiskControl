"""Compile the pinned service candidate and compare non-target method control flow to actual runtime bytes."""
from pathlib import Path
import datetime,hashlib,json,re,sys,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/emergency_exercise_atomic_20261029';W=R/'work/emergency_exercise_atomic_20261029';CLS='com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl';BASE='com/iemp/endanger/base/service/impl/BaseFileServiceImpl';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from verify_original_work_reservation_sql import run
from verify_event_disposal_local_state import current
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def dump(p,v):assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def methods(text):
 parts=re.split(r'(?m)(?=^  (?:public|protected|private).+;\s*$)',text.replace('\r\n','\n'));result={}
 for part in parts:
  lines=part.splitlines()
  if not lines or '(' not in lines[0]:continue
  signature=lines[0].strip();items=[];offsets={}
  for line in lines:
   case=re.match(r'^\s+(-?\d+|default):\s+(\d+)\s*$',line)
   if case and items and items[-1][0] in ['lookupswitch','tableswitch']:
    items[-1][2].append((case[1],case[2]));continue
   m=re.match(r'^\s+(\d+):\s+([a-z_][a-z0-9_]*)(.*)$',line)
   if m:offsets[m[1]]=len(items);items.append((m[2],m[3].strip(),[]))
  normalized=[]
  for op,args,cases in items:
   if op.startswith('if') or op in ['goto','goto_w']:args='@'+str(offsets[args])
   else:
    args=re.sub(r'#\d+','#',args);left,sep,right=args.partition('//');args=' '.join(left.split())+(' //'+right if sep else '')
   if cases:args=(args,tuple((label,'@'+str(offsets[target])) for label,target in cases))
   normalized.append(({'ldc_w':'ldc','goto_w':'goto'}.get(op,op),args))
  result[signature]=normalized
 return result

def main():
 assert not (D/'compiled-class-verification-v2.json').exists();classRoot=W/'compile-v2';assert not classRoot.exists();classRoot.mkdir();before=current();initial=read(D/'before-state-and-source-pins.json');assert before==initial['current'];deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');payload=read(Q/'payload-manifest.json');jar=Q/'payload/business/application.jar';assert sha(jar)==payload['files']['payload/business/application.jar']['sha256'];java=Path(deps['java']);assert sha(java)==deps['javaSHA256']
 for name,row in deps['inputPins'].items():assert sha(name)==row['SHA256']
 for name,pin in initial['sourcePins'].items():assert sha(name)==pin
 for name in ['original-classes','reference-classes','candidate-classes']:(classRoot/name).mkdir()
 classpins={}
 with zipfile.ZipFile(jar) as z:
  for name in [CLS,BASE]:
   rel=name+'.class';assert not (Q/'payload/business/run-template/classes'/rel).exists() and not (Path(before['activeLogRoot']).parent/'classes'/rel).exists();raw=z.read(rel);p=classRoot/'original-classes'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);classpins[name]=sha(p)
 sources=read(D/'candidate-source-prepared-v2.json')['sources'];pins={}
 for mode in ['reference','candidate']:
  p=Path(sources[mode]['path']);assert sha(p)==sources[mode]['SHA256'];pins[str(p)]=sha(p);run(classRoot,'compile-'+mode,[java.with_name('javac.exe'),'-J-Xmx192m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',classRoot/(mode+'-classes'),p],45)
 outputs={}
 for mode,classpath in [('original',str(classRoot/'original-classes')+';'+deps['classpath']),('reference',str(classRoot/'reference-classes')+';'+deps['classpath']),('candidate',str(classRoot/'candidate-classes')+';'+deps['classpath'])]:
  tag='bytecode-'+mode;run(classRoot,tag,[java.with_name('javap.exe'),'-J-Xmx128m','-J-Dfile.encoding=UTF-8','-p','-c','-s','-classpath',classpath,CLS.replace('/','.')],25);outputs[mode]=methods((classRoot/(tag+'.stdout.log')).read_text(encoding='utf-8-sig'))
 assert outputs['original']==outputs['reference'],'ORIGINAL_RUNTIME_AND_REFERENCE_INSTRUCTIONS_MISMATCH';changed=[' boolean save(', ' Boolean saveEmergencyExerciseList(', ' Boolean delete('];kept=[]
 for signature,instructions in outputs['original'].items():
  if any(name in signature for name in [' save(com.iemp.endanger.server.emergency.entity.EmergencyExerciseEntity)', ' saveEmergencyExerciseList(', ' delete(java.lang.String)']):continue
  assert outputs['candidate'].get(signature)==instructions,'NON_TARGET_METHOD_CONTROL_FLOW_CHANGED:'+signature;kept.append(signature)
 for path,pin in pins.items():assert sha(path)==pin
 assert current()==before;result={'at':datetime.datetime.now().astimezone().isoformat(),'actualOriginalClassPins':classpins,'compiledRoot':str(classRoot),'candidateClassSHA256':sha(classRoot/'candidate-classes'/(CLS+'.class')),'referenceCompileOnlyExplicitConstructorMatchesOriginalRuntime':True,'allOriginalMethodInstructionOperandsAndControlFlowMatchReference':True,'allNonTargetMethodsIncludingConstructorPreserved':kept,'candidateSourcePins':pins,'actualSQLNotYetExecuted':True,'runtimeInstalledOrPublicChanged':False,'currentJ58Unchanged':True,'fullCloneReady':False};dump(D/'compiled-class-verification-v2.json',result);print(json.dumps(result))
if __name__=='__main__':main()
