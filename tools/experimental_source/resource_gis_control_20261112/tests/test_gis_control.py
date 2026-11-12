from pathlib import Path
import copy,json,secrets,socket,threading,time,unittest,tempfile
from unittest.mock import patch
from resource_grants import ResourceAuthority,READ,WRITE,PROJECT_KEY
from grant_clock import ClockBoundGrant
from resource_service import ResourceManager
from resource_reports import OwnedReports
from registered_gis import RegisteredGIS,ConfigurationReadLease
from client_settings import workspace_document

class Clock:
 def __init__(self):self.now=1000
 def __call__(self):return self.now
class Settings:
 def configuration(self):return {'workspaceRoot':'D:/Project/Zhumadian','saved':True,'paths':{},'schema':'xnby.client-resources.configuration.v1'}
 def save_authorized(self,root,commit):commit(lambda:None)
 def audit(self,*a,**k):return{'result':{'schema':'xnby.offline-osgb.integrity.v1','passed':True,'cancelled':False,'issueCount':0}}
class Backend:
 def __init__(self):self.enter=threading.Event();self.allow=threading.Event();self.accepted=threading.Event();self.finish=threading.Event();self.calls=[];self.before_accept=lambda:None
 def status(self):return {'schema':'xnby.client-resources.gis-status.v1','phase':'stopped','owned':False}
 def execute(self,action,*,commit,cancel_event,progress):
  self.enter.set();self.allow.wait(5);self.before_accept();commit(lambda:True);self.accepted.set();self.calls.append(action);progress('starting'if action=='start'else'stopping');self.finish.wait(5)
  return {'phase':'ready'if action=='start'else'stopped','observationExpired':False,'alreadyRunning':False,'registeredOwnerOnly':True}
class Fixture:
 def __init__(self):
  self.tmp=tempfile.TemporaryDirectory();self.clock=Clock();self.scopes=[READ,WRITE];self.actor='a'*64
  def verifier(grant,expected):return ClockBoundGrant({**expected,'accepted':True,'scopes':list(self.scopes),'actorKey':self.actor,'projectKey':PROJECT_KEY,'expiresAt':-1},self.clock()+20)
  self.auth=ResourceAuthority(installation_identity='1'*64,source_identity='2'*64,index_identity='3'*64,verifier=verifier,clock=self.clock);self.backend=Backend();reports=OwnedReports(Path(self.tmp.name)/'reports',binding={k:self.auth.expected[k]for k in ['installationIdentity','sourceRuntimeIdentity','sourceIndexIdentity']});self.manager=ResourceManager(authority=self.auth,settings=Settings(),reports=reports,gis=self.backend);self.token=self.session()
 def session(self):return self.auth.establish(secrets.token_hex(32))['session']
 def close(self):self.backend.allow.set();self.backend.finish.set();self.manager.close();self.tmp.cleanup()
 def wait(self,identifier):
  deadline=time.monotonic()+5
  while time.monotonic()<deadline:
   with self.manager.lock:value=self.manager.controls[identifier]
   if value.state in ('completed','failed','cancelled'):return value
   time.sleep(.005)
  raise AssertionError('Original worker not terminal')

class AuthorityLifecycle(unittest.TestCase):
 def setUp(self):self.x=Fixture()
 def tearDown(self):self.x.close()
 def test_readonly_queries_status_but_cannot_start_or_stop(self):
  x=self.x;x.scopes=[READ];token=x.session();self.assertEqual(x.manager.gis_status(token)['phase'],'stopped')
  for action in ['start','stop']:
   with self.assertRaisesRegex(ValueError,'WRITE_FORBIDDEN'):x.manager.start_gis_operation(token,action)
  self.assertEqual(x.backend.calls,[])
 def test_actor_isolation_of_opaque_operation(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'start');x.actor='b'*64;other=x.session()
  with self.assertRaisesRegex(ValueError,'GIS_OPERATION_NOT_FOUND'):x.manager.gis_operation(other,value['id'])
 def test_expiry_while_qualifying_prevents_acceptance(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'start');self.assertTrue(x.backend.enter.wait(2));x.clock.now+=21;x.backend.allow.set();job=x.wait(value['id']);self.assertEqual(job.state,'cancelled');self.assertFalse(job.accepted);self.assertEqual(x.backend.calls,[])
 def test_expiry_during_last_accept_callback_checked_again(self):
  x=self.x;x.backend.before_accept=lambda:setattr(x.clock,'now',x.clock.now+21);value=x.manager.start_gis_operation(x.token,'stop');x.backend.allow.set();job=x.wait(value['id']);self.assertFalse(job.accepted);self.assertEqual(x.backend.calls,[])
 def test_account_revocation_before_acceptance_has_no_service_effect(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'stop');x.auth.revoke(x.token);x.backend.allow.set();self.assertEqual(x.wait(value['id']).state,'cancelled');self.assertEqual(x.backend.calls,[])
 def test_accepted_intent_finishes_after_lease_expiry(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'start');x.backend.allow.set();self.assertTrue(x.backend.accepted.wait(2));x.clock.now+=21;x.backend.finish.set();job=x.wait(value['id']);self.assertEqual(job.state,'completed');self.assertTrue(job.accepted);self.assertEqual(x.backend.calls,['start'])
 def test_session_close_waits_original_accepted_worker(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'stop');x.backend.allow.set();self.assertTrue(x.backend.accepted.wait(2));done=threading.Event();thread=threading.Thread(target=lambda:(x.manager.close_session(x.token),done.set()));thread.start();self.assertFalse(done.wait(.05));x.backend.finish.set();thread.join(3);self.assertTrue(done.is_set());self.assertFalse(x.manager.controls[value['id']].thread.is_alive())
 def test_root_save_audit_and_duplicate_intent_rejected_while_control_active(self):
  x=self.x;x.manager.start_gis_operation(x.token,'stop')
  for call in [lambda:x.manager.save(x.token,'E:/Zhumadian'),lambda:x.manager.start_audit(x.token),lambda:x.manager.start_gis_operation(x.token,'start')]:
   with self.assertRaisesRegex(ValueError,'OPERATION_BUSY'):call()
 def test_no_paths_commands_or_pid_actions_accepted(self):
  with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):self.x.manager.start_gis_operation(self.x.token,'kill-all')
 def test_terminal_only_after_actual_control_thread_join(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'start');x.backend.allow.set();self.assertTrue(x.backend.accepted.wait(2));self.assertEqual(x.manager.gis_operation(x.token,value['id'])['state'],'running');x.backend.finish.set();job=x.wait(value['id']);self.assertFalse(job.thread.is_alive());self.assertIsNone(x.manager.active_control)
 def test_no_secret_or_actor_key_in_public_operation(self):
  x=self.x;value=x.manager.start_gis_operation(x.token,'start');raw=json.dumps(value);self.assertNotIn(x.token,raw);self.assertNotIn('actorKey',raw);self.assertNotIn('ownerToken',raw);self.assertNotIn('stopSecret',raw)
 def test_status_cannot_be_returned_after_expiry_in_backend(self):
  x=self.x;x.backend.status=lambda:(setattr(x.clock,'now',x.clock.now+21)or{'schema':'xnby.client-resources.gis-status.v1','phase':'stopped','owned':False})
  with self.assertRaisesRegex(ValueError,'SESSION_REQUIRED'):x.manager.gis_status(x.token)

class RootFileGuards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'Zhumadian';self.root.mkdir();self.install=self.root/'programme';self.install.mkdir();(self.install/'client-gis-install.json').write_text('{}');self.cfg=self.root/'config.json';self.cfg.write_text(json.dumps(workspace_document(self.root.as_posix())));self.state=self.root/'UserData/ClientGIS';self.state.mkdir(parents=True);self.socket=socket.socket();self.socket.bind(('127.0.0.1',0));self.port=self.socket.getsockname()[1];self.socket.close()
  import hashlib
  self.gis=RegisteredGIS(self.install,self.cfg,expected_manifest=hashlib.sha256(b'{}').hexdigest(),qa=True,port=self.port,base_override=self.root,history_file=self.root/'history.json')
 def tearDown(self):self.tmp.cleanup()
 def test_configuration_read_lease_blocks_atomic_swap(self):
  other=self.cfg.with_name('other.json');other.write_text('{}');lease=ConfigurationReadLease(self.cfg)
  try:
   with self.assertRaises(OSError):other.replace(self.cfg)
  finally:lease.close()
  other.replace(self.cfg)
 def test_open_bootstrap_stdout_prevents_root_change(self):
  log=self.state/('bootstrap-'+'a'*16+'.log')
  with log.open('wb') as stream:
   with patch.object(self.gis,'status',return_value={'phase':'stopped','owned':False}):
    with self.assertRaisesRegex(ValueError,'PENDING_BOOTSTRAP'):self.gis.begin_root_change()
  with patch.object(self.gis,'status',return_value={'phase':'stopped','owned':False}):
   guard=self.gis.begin_root_change();guard.close()
 def test_live_owned_service_blocks_root_change(self):
  with patch.object(self.gis,'status',return_value={'phase':'ready','owned':True}):
   with self.assertRaisesRegex(ValueError,'STOP_GIS_BEFORE'):self.gis.begin_root_change()
 def test_change_after_guard_invalidates_commit(self):
  with patch.object(self.gis,'status',return_value={'phase':'stopped','owned':False}):
   guard=self.gis.begin_root_change();self.cfg.write_text(json.dumps({**workspace_document(self.root.as_posix()),'extra':1}))
   try:
    with self.assertRaisesRegex(ValueError,'CONFIGURATION_CHANGED'):guard.commit(lambda:self.fail('must not write'))
   finally:guard.close()
 def test_guard_commits_only_while_still_stopped(self):
  with patch.object(self.gis,'status',return_value={'phase':'stopped','owned':False}):guard=self.gis.begin_root_change()
  try:
   with patch.object(self.gis,'status',return_value={'phase':'starting','owned':False}):
    with self.assertRaisesRegex(ValueError,'STOP_GIS_BEFORE'):guard.commit(lambda:self.fail('must not write'))
  finally:guard.close()
 def test_unknown_bootstrap_files_not_read_or_executed(self):
  (self.state/'not-a-bootstrap.log').write_text('private ignored');handles=self.gis.bootstrap_read_leases();self.assertEqual(handles,[])
 def test_occupied_unowned_port_is_not_stopped(self):
  listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();self.gis.port=listener.getsockname()[1]
  try:
   with patch('registered_gis.active_record',return_value=None),patch('registered_gis.request',return_value=(200,b'{}')):
    with self.assertRaisesRegex(ValueError,'UNOWNED_INSTANCE'):self.gis._owner({'state':self.state})
  finally:listener.close()
 def test_qa_overrides_cannot_enter_production(self):
  with self.assertRaisesRegex(ValueError,'QA'):RegisteredGIS(self.install,self.cfg,expected_manifest='a'*64,port=self.port,base_override=self.root)

if __name__=='__main__':unittest.main(verbosity=2)
