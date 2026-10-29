"""Test the bound one-baseline selector and limited collector against owned synthetic metadata."""
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
import argparse,hashlib,importlib.util,io,json,shutil,sys,tempfile,zipfile
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';ROOT=R/'work/public_test_update_20261029_r16';DELIVERY=ROOT/'delivery/Zhumadian_Update_20261029_R16';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from build_original_public_r16_update import BASE,UPDATER,FACTORIES,UPIN,FPIN,sha,read,encode,need
def load(p):s=importlib.util.spec_from_file_location('own_r16_bound_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def rejected(fn,text):
 try:fn()
 except ValueError as error:need(text in str(error),'EXPECTED_REJECTION:'+text)
 else:raise AssertionError('REJECTION_REQUIRED:'+text)
def run():
 target=ROOT/'unit-qa';need(not target.exists() and not (ROOT/'transport-collector-verification.json').exists(),'FRESH_R16_UNIT_ROOT');target.mkdir();cases=[];m=load(DELIVERY/'deploy_public_test_r16.py');oldRaw=(ROOT/'from-r15/baseline/release-manifest.json').read_bytes();newRaw=(ROOT/'from-r15/bundle/payload/release-manifest.json').read_bytes();newpin=m.NEW_RELEASE_SHA256
 with tempfile.TemporaryDirectory(prefix='selector-',dir=target) as tmp:
  app=Path(tmp)/'Application';app.mkdir();release=app/'release-manifest.json';release.write_bytes(oldRaw)
  for args in [[],['--check-only']]:need(m.select_variant(app,args)==m.VARIANTS[BASE],'ONLY_EXACT_R15_SELECTED');cases.append('exact-R15-'+str(args))
  for name,raw in [('unknown',b'OWN_UNKNOWN'),('already-R16',newRaw),('old-R8',(R/'work/public_test_update_20261029_r8/bundle/payload/release-manifest.json').read_bytes()),('old-R12',(R/'work/public_test_update_20261029_r12/from-r8/bundle/payload/release-manifest.json').read_bytes()),('failed-R13',(R/'work/public_test_update_20261029_r13/from-r8/bundle/payload/release-manifest.json').read_bytes())]:
   release.write_bytes(raw);before={str(p) for p in app.rglob('*')};rejected(lambda:m.select_variant(app,[]),'UNKNOWN_OR_ALREADY_UPDATED');need(release.read_bytes()==raw and {str(p) for p in app.rglob('*')}==before,'NO_FILES_CHANGED_ON_UNKNOWN_BASE');cases.append(name+'-refused-before-write')
  release.write_bytes(oldRaw)
  for args in [['--start'],['--apply','other'],['--check-only','--rollback-latest']]:rejected(lambda args=args:m.select_variant(app,args),'EXACT_UPDATE_MODE');cases.append('invalid-mode-'+str(args))
  def receipt(name,value):p=app/'UserData/OriginalPublicUpdates'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encode(value))
  own={'newReleaseSHA256':newpin,'updateId':'20261029-R16-from-R15'};other={'newReleaseSHA256':BASE,'updateId':'20261029-R15-from-R8'}
  for mode,name,opposite in [('--recover-pending','pending.json','latest.json'),('--rollback-latest','latest.json','pending.json')]:
   receipt(name,own);receipt(opposite,other);need(m.select_variant(app,[mode])==m.VARIANTS[BASE],'OWN_EXACT_RECOVERY');cases.append(mode+'-own-record')
   for label,value in [('old-R15',other),('wrong-release',{**own,'newReleaseSHA256':'f'*64}),('wrong-update-id',{**own,'updateId':'other'})]:receipt(name,value);rejected(lambda mode=mode:m.select_variant(app,[mode]),'ONLY_THIS_R16');cases.append(mode+'-'+label+'-refused')
  receipt('pending.json',own);(app/'UserData/OriginalPublicUpdates/pending.json').write_bytes(b'x'*(2*1024**2+1));rejected(lambda:m.select_variant(app,['--recover-pending']),'OWN_R16_PENDING');cases.append('oversized-pending-refused')
  blank=load(T/'public_r16_transport.py');rejected(lambda:blank.select_variant(app,[]),'BOUND_R16_PINS');cases.append('unbound-selector-refused')
 reports=['transaction-bean-observation.json','work-services-transaction-observation.json','own-finding-observer-ready.json','training-transaction-observation.json','work-safety-batch-observation.json','emergency-team-transaction-observation.json']
 def collector_case(label,releaseRaw,after,want=None,badCode=False,oversizeReport=False):
  with tempfile.TemporaryDirectory(prefix='collector-',dir=target) as tmp:
   root=Path(tmp);app=root/'Application';delivery=root/'Delivery';app.mkdir();delivery.mkdir();(delivery/'web.config').write_bytes((DELIVERY/'web.config').read_bytes());c=load(DELIVERY/'collect_original_public_r16_state.py');c.APP=app;c.DELIVERY=delivery;(app/'release-manifest.json').write_bytes(releaseRaw);payload=ROOT/('from-r15/bundle/payload' if hashlib.sha256(releaseRaw).hexdigest()==newpin else 'from-r15/baseline');(app/'payload-manifest.json').write_bytes((payload/'payload-manifest.json').read_bytes())
   for name,body in [(UPDATER,(payload/UPDATER).read_bytes()),(FACTORIES,(payload/FACTORIES).read_bytes())]:p=app/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'OWN_BAD_UPDATER' if badCode and name==UPDATER else body)
   run=app/'UserData/OriginalServer/runs/j1';(run/'b').mkdir(parents=True);children={name:pid for name,pid in zip(['store','mysql','redis','platform','business','gateway'],range(12,18))};state={'controllerPID':11,'run':str(run),'gatewayPort':18892,'startedAt':'OWN_TIME','persistent':True,'ready':True,'children':children,'databaseUUID':'OWN_SYNTHETIC_UUID'};(app/'UserData/OriginalServer/current-run.json').write_bytes(encode(state))
   caseReports=reports+(['event-disposal-transaction-observation.json','emergency-exercise-transaction-observation.json'] if after else [])
   for name in caseReports:(run/'b'/name).write_bytes(b'x'*65537 if oversizeReport and name==reports[0] else encode({'schema':'OWN_SYNTHETIC_REPORT','PID':16}))
   latest=app/'UserData/OriginalPublicUpdates/latest.json';latest.parent.mkdir();latest.write_bytes(encode({'updateId':'OWN_ID','newReleaseSHA256':newpin,'ready':True,'secret':'OWN_NEVER_EXPORT_CANARY'}));private=app/'private';private.mkdir();(private/'OWN_CANARY').write_bytes(b'OWN_NEVER_EXPORT_CANARY');allowed={app/'release-manifest.json',app/'payload-manifest.json',app/'UserData/OriginalServer/current-run.json',latest,*[run/'b'/n for n in caseReports]};reader=c.read_json;accessed=[]
   def limited(path,*args):need(Path(path) in allowed,'UNEXPECTED_METADATA_READ');accessed.append(str(Path(path).relative_to(app)));return reader(path,*args)
   response=io.BytesIO(b'OWN_SYNTHETIC_HTML');response.status=200
   with patch.object(c,'read_json',limited),patch.object(c,'image',lambda pid:{'pid':pid,'live':True,'image':'OWN_SYNTHETIC_IMAGE'}),patch.object(c.urllib.request,'urlopen',return_value=response),patch.object(sys,'argv',[str(DELIVERY/'collect_original_public_r16_state.py'),*(['--after'] if after else [])]),redirect_stdout(io.StringIO()):
    if want:rejected(c.main,want)
    else:c.main()
   archives=list(delivery.glob('*.zip'))
   if want:need(not archives,'REJECTED_COLLECTOR_MUST_NOT_EMIT_ARCHIVE')
   else:
    need(len(archives)==1,'ONE_LIMITED_METADATA_ARCHIVE')
    with zipfile.ZipFile(archives[0]) as z:
     need(set(z.namelist())=={'release-manifest.json','payload-manifest.json','state.json'} and len(z.namelist())==3,'ONLY_THREE_METADATA_MEMBERS');raw=z.read('state.json');result=json.loads(raw);need(b'OWN_NEVER_EXPORT_CANARY' not in raw and set(result['runtimeReports'])==set(caseReports) and len(result['processes'])==7 and result['businessDataCredentialsOrSessionsRead'] is False and result['originalLogsRead'] is False and result['servicesChanged'] is False,'LIMITED_NO_CREDENTIAL_OR_BUSINESS_COLLECTION');need(len(accessed)==4+len(caseReports),'EXACT_TEN_DECLARED_METADATA_READS')
   cases.append(label)
 collector_case('collector-exact-R15-before',oldRaw,False);collector_case('collector-exact-R16-after',newRaw,True);collector_case('collector-R15-after-refused',oldRaw,True,'EXACT_R15_BEFORE_OR_R16_AFTER');collector_case('collector-R16-before-refused',newRaw,False,'EXACT_R15_BEFORE_OR_R16_AFTER');collector_case('collector-bad-code-refused',oldRaw,False,'EXACT_DECLARED_SERVER_CODE',badCode=True);collector_case('collector-oversized-report-refused',oldRaw,False,'METADATA_BOUND',oversizeReport=True)
 for name in ['deploy_public_test_r16.py','collect_original_public_r16_state.py']:compile((DELIVERY/name).read_bytes(),name,'exec')
 target.rmdir();result={'sourceSHA256':sha(Path(__file__)),'boundTransportSHA256':sha(DELIVERY/'deploy_public_test_r16.py'),'boundCollectorSHA256':sha(DELIVERY/'collect_original_public_r16_state.py'),'passed':len(cases),'cases':cases,'syntheticOwnedMetadataOnly':True,'actualNetworkDatabaseAccountSessionOrServerUsed':False,'normalPreflightAndDeploymentNotExecuted':True};(ROOT/'transport-collector-verification.json').write_bytes(encode(result));print(json.dumps(result));return result
if __name__=='__main__':run()
