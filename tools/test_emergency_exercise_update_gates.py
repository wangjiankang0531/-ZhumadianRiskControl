"""Exercise actual generated preflight/readiness gates, including every retained initializer."""
from pathlib import Path
import argparse,ast,copy,json,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
import original_emergency_exercise_update_compat as b
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/emergency_exercise_local_20261029';W=R/'work/emergency_exercise_integration_20261029';Q=b.Q
def read(p):return json.loads(Path(p).read_bytes())
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def run(root):
 root=Path(root).absolute();assert not root.exists();root.mkdir();app=root/'Application';folder=app/'UserData/OriginalServer/runs/j1/b';folder.mkdir(parents=True);sample=W/'observer-context-r3/candidate/autoproxy/Application/UserData/OriginalServer/runs/j1/b';report=read(sample/'emergency-exercise-transaction-observation.json');(folder/'server-owner.properties').write_bytes((sample/'server-owner.properties').read_bytes());release={'emergencyExerciseAtomicCandidate':b.REVISION,'emergencyExerciseObservationCandidate':'existing-singletons-manager-v1'};payload={'files':{b.SERVICE:{'bytes':1,'sha256':b.CLASS_PIN},b.OBSERVER:{'bytes':1,'sha256':b.OBSERVER_PIN}}};row={'run':str(folder.parent),'children':{'business':report['PID']}};raw=b.adapt_updater((Q/'tools/original_public_test_update.py').read_bytes());u=b.module(raw);results=[]
 def check(name,patch=None,rpatch=None,ppatch=None,absent=False,oversize=False,accepted=False,legacy=False):
  value=copy.deepcopy(report);rr=copy.deepcopy(release);pp=copy.deepcopy(payload)
  if patch:patch(value)
  if rpatch:rpatch(rr)
  if ppatch:ppatch(pp)
  (app/'release-manifest.json').write_bytes(encode(rr));(app/'payload-manifest.json').write_bytes(encode(pp));file=folder/'emergency-exercise-transaction-observation.json'
  if file.exists():file.unlink()
  if not absent:file.write_bytes(encode(value)+(b' '*65537 if oversize else b''))
  failed=False;returned=None
  try:returned=u['emergency_exercise_observer_ready'](app,row)
  except (ValueError,FileNotFoundError):failed=True
  assert failed==(not accepted and not legacy),name
  if accepted:assert returned==report
  if legacy:assert returned is None
  results.append({'case':name,'passed':True})
 check('actual candidate Spring proxy accepted',accepted=True)
 for name,key,value in [('old PID','PID',report['PID']+1),('wrong run','run','j2'),('wrong schema','schema','bad'),('wrong owner','ownerIdSHA256','0'*64),('no manager','existingTransactionManagerCount',0),('two managers','existingTransactionManagerCount',2),('Boolean manager count','existingTransactionManagerCount',True),('business call claimed','businessMethodsInvoked',True),('SQL call claimed','SQLOrNetworkRequestsIssuedByObserver',True),('auth proof claimed by metadata','actualRollbackOrHTTPOrAuthenticationVerified',True),('non-singleton scope','existingSingletonMetadataOnly',False),('aggregate false','allEmergencyExerciseMethodsAndManagerMatched',False)]:check(name,lambda v,k=key,x=value:v.update({k:x}))
 check('duplicate service',lambda v:v['exercise']['save']['services'].append(copy.deepcopy(v['exercise']['save']['services'][0])))
 check('missing services',lambda v:v['exercise']['save'].update(services=[]))
 check('wrong service type',lambda v:v['exercise']['save'].update(serviceType='wrong'))
 check('wrong loaded class',lambda v:v['exercise']['save']['services'][0].update(targetClassSHA256='1'*64))
 check('unproxied service',lambda v:v['exercise']['save']['services'][0].update(isAopProxy=False))
 check('save advisor absent',lambda v:v['exercise']['save']['services'][0]['methods']['save'].update(matchingExceptionRollbackAdvisor=False))
 check('missing method details',lambda v:v['exercise']['save']['services'][0].update(methods={}))
 check('substituted class-payload pair',lambda v:v['exercise']['save']['services'][0].update(targetClassSHA256='2'*64),ppatch=lambda v:v['files'][b.SERVICE].update(sha256='2'*64))
 check('unknown release revision',rpatch=lambda v:v.update(emergencyExerciseAtomicCandidate='unknown'))
 check('missing observation revision',rpatch=lambda v:v.pop('emergencyExerciseObservationCandidate'))
 check('missing metadata file',absent=True);check('oversize metadata file',oversize=True);check('legacy without new flags',rpatch=lambda v:v.clear(),absent=True,legacy=True)
 for key,method in [('save','save'),('saveList','saveEmergencyExerciseList'),('delete','delete')]:
  for label,change in [
   ('no service',lambda g:g.update(services=[])),
   ('duplicate service',lambda g:g['services'].append(copy.deepcopy(g['services'][0]))),
   ('bad group',lambda g:g.update(allMethodsHaveMatchingTransactionAdvisor=False)),
   ('wrong class',lambda g:g['services'][0].update(targetClassSHA256='4'*64)),
   ('no proxy',lambda g:g['services'][0].update(isAopProxy=False)),
   ('missing method',lambda g:g['services'][0].update(methods={})),
   ('no checked rollback',lambda g,m=method:g['services'][0]['methods'][m].update(matchingExceptionRollbackAdvisor=False))]:check(key+':'+label,lambda v,k=key,f=change:f(v['exercise'][k]))
 check('missing one method group',lambda v:v['exercise'].pop('delete'))
 check('unmatched strategy aggregate',lambda v:v.update(nonNullUpdateStrategyMatched=False))
 for column in report['exerciseUpdateStrategies']:
  check(column+':ALWAYS rejected',lambda v,c=column:v['exerciseUpdateStrategies'][c].update(updateStrategy='ALWAYS'))
  check(column+':updateFill rejected',lambda v,c=column:v['exerciseUpdateStrategies'][c].update(withUpdateFill=True))
 check('missing strategy',lambda v:v['exerciseUpdateStrategies'].pop('created_at'))
 tree=ast.parse(raw);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='load_bundle');nodes=[]
 for n in fn.body:
  if not isinstance(n,ast.If):continue
  text=ast.unparse(n.test)
  if text in [repr(b.SERVICE)+" in plan['files']",repr(b.OBSERVER)+" in plan['files']","release.get('emergencyExerciseAtomicCandidate') is not None"]:nodes.append(n)
 assert len(nodes)==3;gate=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'exact-generated-preflight-gates.py','exec');bundle=root/'bundle';factory=app/b.FACTORIES;factory.parent.mkdir(parents=True);next_factory=bundle/'payload'/b.FACTORIES;next_factory.parent.mkdir(parents=True)
 base_registry=(Q/b.FACTORIES).read_bytes().replace((','+b.INITIALIZER).encode(),b'',1);assert b.digest(base_registry)==read(R/'work/emergency_exercise_update_20261029/update-manifest.json')['oldPayloadFiles'][b.FACTORIES]['sha256']
 for family,base in [('local',base_registry),('extra-retained',base_registry.replace(b'\n',b',xnby.replica.OtherRetainedInitializer\n',1))]:
  before=b.initializers(base);new=b.adapt_factories(base);assert b.initializers(new)==before+[b.INITIALIZER];factory.write_bytes(base)
  def preflight(name,registry=new,patch=None,accepted=False):
   rr=copy.deepcopy(release);pp=copy.deepcopy(payload);plan={'files':{b.SERVICE:{'bytes':1,'SHA256':b.CLASS_PIN},b.OBSERVER:{'bytes':1,'SHA256':b.OBSERVER_PIN},b.FACTORIES:{}}};next_factory.write_bytes(registry)
   if patch:patch(rr,pp,plan)
   ns={**u,'app':app,'bundle':bundle,'release':rr,'payload':pp,'plan':plan};failed=False
   try:exec(gate,ns)
   except (ValueError,FileNotFoundError):failed=True
   assert failed!=accepted,family+':'+name;results.append({'case':family+':'+name,'passed':True})
  preflight('all existing initializers plus new accepted',accepted=True)
  for name in before:preflight('drop retained '+name,registry=new.replace((name+',').encode(),b'',1) if (name+',').encode() in new else new.replace((','+name).encode(),b'',1))
  preflight('missing new initializer',registry=base)
  preflight('duplicate new initializer',registry=new.replace(b.INITIALIZER.encode(),(b.INITIALIZER+','+b.INITIALIZER).encode(),1))
  preflight('new classes without explicit revision',patch=lambda rr,pp,p:rr.clear())
  preflight('substituted observer class',patch=lambda rr,pp,p:(p['files'][b.OBSERVER].update(SHA256='3'*64),pp['files'][b.OBSERVER].update(sha256='3'*64)))
  preflight('missing class declaration',patch=lambda rr,pp,p:pp['files'].pop(b.SERVICE))
  preflight('factory not in update',patch=lambda rr,pp,p:p['files'].pop(b.FACTORIES))
 factory.write_bytes((Q/b.FACTORIES).read_bytes());repair_plan={'files':{b.OBSERVER:{'bytes':1,'SHA256':b.OBSERVER_PIN}}};exec(gate,{**u,'app':app,'bundle':bundle,'release':release,'payload':payload,'plan':repair_plan});results.append({'case':'actual already-six registry retained without registry replacement and retained service class','passed':True})
 for name,data in [('duplicate declaration',b'org.springframework.context.ApplicationContextInitializer=a.B\norg.springframework.context.ApplicationContextInitializer=c.D\n'),('oversize registry',b' '*4097),('unknown key',b'other=a.B\n')]:
  try:b.initializers(data)
  except ValueError:results.append({'case':name,'passed':True})
  else:raise AssertionError(name)
 for original in [(Q/'tools/original_public_test_update.py').read_bytes()+b' ',(R/'work/public_test_update_20261029_r14/from-r8/bundle/payload/tools/original_public_test_update.py').read_bytes()]:
  try:b.adapt_updater(original)
  except ValueError:results.append({'case':'unknown or public updater preimage rejected','passed':True})
  else:raise AssertionError('unrecognized updater accepted')
 result={'checks':len(results),'cases':results,'updaterSHA256':b.digest(raw),'sourceSHA256':b.digest(Path(b.__file__).read_bytes()),'originalAndCandidateActualSpringReportUsed':True,'actualGeneratedPreflightASTExecuted':True,'allFiveExistingAndAdditionalUnknownInitializersRequiredBeforeDowntime':True,'noActualRuntimeOrSQLOrRemoteOperations':True,'fullCloneReady':False};(root/'result.json').write_bytes(encode(result));return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);result=run(p.parse_args().root);print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
