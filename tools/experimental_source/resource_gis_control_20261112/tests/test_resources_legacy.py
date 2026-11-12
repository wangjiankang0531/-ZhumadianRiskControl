from pathlib import Path
import copy,hashlib,http.client,json,secrets,threading,time,unittest
from resource_grants import ResourceAuthority,READ,WRITE,ORIGIN,Principal,require,PROJECT_KEY
from grant_clock import ClockBoundGrant
from resource_service import ResourceManager,TERMINAL
from resource_reports import OwnedReports,checked_report
from resource_http import ResourceHTTPServer,PREFIX,SESSION
from resource_settings import ResourceSettings
BINDING={'installationIdentity':'1'*64,'sourceRuntimeIdentity':'2'*64,'sourceIndexIdentity':'3'*64}
R=Path('D:/Project/Zhumadian');W=R/'work/resource_gis_control_20261112/legacy';PACKAGE=R/'Application/Packages/ClientGISIntegrityCandidate_20261107'
def wait_for(test,operation,*,seconds=4):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=operation()
        if value:return value
        time.sleep(.005)
    test.fail('Expected lifecycle condition not reached')
class Clock:
    def __init__(self):self.now=1000
    def __call__(self):return self.now
class Verifier:
    def __init__(self,clock=time.monotonic):self.clock=clock;self.used=set();self.owner=('a'*64,PROJECT_KEY);self.scopes=[READ,WRITE];self.transform=lambda x:x
    def __call__(self,grant,expected):
        if grant in self.used:raise ValueError('RESOURCE_GRANT_REPLAY')
        self.used.add(grant);value={**expected,'accepted':True,'actorKey':self.owner[0],'projectKey':self.owner[1],'scopes':list(self.scopes),'expiresAt':-9000000000}
        return self.transform(ClockBoundGrant(value,self.clock()+20))
def authority(verifier,clock=time.monotonic):return ResourceAuthority(installation_identity='1'*64,source_identity='2'*64,index_identity='3'*64,verifier=verifier,clock=clock)
def report(*,passed=True,cancelled=False):return{'schema':'xnby.offline-osgb.integrity.v1','passed':passed,'cancelled':cancelled,'issueCount':0,'progress':{'verifiedFiles':3,'completedFiles':3,'readBytes':12}}
class SettingsFixture:
    def __init__(self):self.root='D:/Project/Zhumadian';self.saved=False;self.enter=threading.Event();self.allow_finish=threading.Event();self.cancel_seen=threading.Event();self.commit_gate=None;self.writes=0
    def configuration(self):return{'schema':'xnby.client-resources.configuration.v1','workspaceRoot':self.root,'saved':self.saved,'paths':{'gis':'Assets/3DGIS/驻马店园区','renderData':'Assets/Runtime','icons':'Assets/Icons/PointSymbols','downloads':'UserData/Cache/Downloads','dlgDrafts':'UserData/Drafts/DLG','sceneDrafts':'UserData/Drafts/Scenes'}}
    def save_authorized(self,root,commit):
        if self.commit_gate:self.commit_gate()
        def write():self.root=root;self.saved=True;self.writes+=1
        commit(write)
    def audit(self,root,*,progress,cancel_event):
        self.enter.set();progress({'phase':'reading_osgb','verifiedFiles':1,'readBytes':4})
        while not self.allow_finish.wait(.005):
            if cancel_event.is_set():self.cancel_seen.set();break
        if cancel_event.is_set():
            self.cancel_seen.set();self.allow_finish.wait(3);return{'result':report(passed=False,cancelled=True)}
        return{'result':report()}
class Fixture:
    def __init__(self,*,clock=time.monotonic,settings=None):
        self.verify=Verifier(clock);self.auth=authority(self.verify,clock);self.settings=settings or SettingsFixture();self.folder=W/'test-profiles'/secrets.token_hex(8);self.store=OwnedReports(self.folder,binding=BINDING);self.manager=ResourceManager(authority=self.auth,settings=self.settings,reports=self.store);self.token=self.auth.establish(secrets.token_hex(32))['session']
    def close(self):self.settings.allow_finish.set();self.manager.close()
class Tests(unittest.TestCase):
    def test_read_scope_cannot_save(self):
        x=Fixture()
        try:
            x.verify.scopes=[READ];token=x.auth.establish(secrets.token_hex(32))['session'];self.assertFalse(x.manager.configuration(token)['canConfigure'])
            with self.assertRaisesRegex(ValueError,'RESOURCE_WRITE_FORBIDDEN'):x.manager.save(token,'E:/Zhumadian')
            self.assertEqual(x.settings.writes,0)
        finally:x.close()
    def test_expiry_during_qualification_cannot_commit(self):
        clock=Clock();x=Fixture(clock=clock)
        try:
            x.settings.commit_gate=lambda:setattr(clock,'now',clock.now+21)
            with self.assertRaisesRegex(ValueError,'RESOURCE_SESSION_REQUIRED'):x.manager.save(x.token,'E:/Zhumadian')
            self.assertEqual(x.settings.writes,0);self.assertFalse(x.settings.saved)
        finally:x.close()
    def test_no_wall_clock_permission_fallback_and_no_plain_receipt(self):
        clock=Clock();v=Verifier(clock);a=authority(v,clock);t=a.establish(secrets.token_hex(32))['session'];self.assertTrue(a.active(t));clock.now+=21;self.assertFalse(a.active(t));a.close()
        v=Verifier();v.transform=dict;a=authority(v)
        with self.assertRaisesRegex(ValueError,'RESOURCE_GRANT_REJECTED'):a.establish(secrets.token_hex(32))
        a.close()
    def test_unknown_duplicate_and_gis_scopes_rejected(self):
        for scopes in [[READ,READ],['gis.read'],[READ,'admin'],[WRITE],[]]:
            v=Verifier();v.scopes=scopes;a=authority(v)
            with self.assertRaisesRegex(ValueError,'RESOURCE_SCOPE_REJECTED'):a.establish(secrets.token_hex(32))
            a.close()
    def test_grant_replay_and_renew_owner_change_revoke(self):
        v=Verifier();a=authority(v);grant=secrets.token_hex(32);t=a.establish(grant)['session']
        with self.assertRaisesRegex(ValueError,'RESOURCE_GRANT_REPLAY'):a.establish(grant)
        v.owner=('c'*64,PROJECT_KEY)
        with self.assertRaisesRegex(ValueError,'RESOURCE_SESSION_BINDING_CHANGED'):a.renew(t,secrets.token_hex(32))
        self.assertFalse(a.active(t));a.close()
    def test_report_actor_and_project_isolation_and_persistence(self):
        store=OwnedReports(W/'report-fixtures'/secrets.token_hex(8),binding=BINDING);owner=('a'*64,'b'*64);identifier=store.persist(owner,report());self.assertTrue(store.read(owner,identifier)['passed']);self.assertEqual(len(OwnedReports(store.folder,binding=BINDING).summaries(owner)),1)
        for other in [('c'*64,'b'*64),('a'*64,'d'*64)]:
            self.assertEqual(store.summaries(other),[])
            with self.assertRaises(FileNotFoundError):store.read(other,identifier)
        for bad in ['../x','D:/secret','a'*31,'a'*32+'.json']:
            with self.assertRaisesRegex(ValueError,'RESOURCE_IDENTIFIER_INVALID'):store.read(owner,bad)
    def test_report_size_and_contradictory_terminal_rejected(self):
        with self.assertRaisesRegex(ValueError,'RESOURCE_REPORT_INVALID'):checked_report(report(passed=True,cancelled=True))
        value=report();value['large']='x'*262144
        with self.assertRaisesRegex(ValueError,'RESOURCE_REPORT_TOO_LARGE'):checked_report(value)
    def test_cancel_does_not_fabricate_worker_terminal(self):
        x=Fixture()
        try:
            job=x.manager.start_audit(x.token);self.assertTrue(x.settings.enter.wait(1));value=x.manager.cancel_audit(x.token,job['id']);self.assertEqual(value['state'],'cancelling');self.assertTrue(x.settings.cancel_seen.wait(1));self.assertEqual(x.manager.audit(x.token,job['id'])['state'],'cancelling');x.settings.allow_finish.set();done=wait_for(self,lambda:(v if(v:=x.manager.audit(x.token,job['id']))['state']in TERMINAL else None));self.assertEqual(done['state'],'cancelled');self.assertFalse(x.manager.jobs[job['id']].thread.is_alive());self.assertTrue(x.manager.report(x.token,done['reportId'])['cancelled'])
        finally:x.close()
    def test_expired_session_cancels_without_followup_request(self):
        clock=Clock();x=Fixture(clock=clock)
        try:
            job=x.manager.start_audit(x.token);self.assertTrue(x.settings.enter.wait(1));clock.now+=21;self.assertTrue(x.settings.cancel_seen.wait(1));x.settings.allow_finish.set();wait_for(self,lambda:x.manager.jobs[job['id']].state in TERMINAL);self.assertEqual(x.manager.jobs[job['id']].state,'cancelled')
        finally:x.close()
    def test_busy_blocks_root_save_and_second_audit(self):
        x=Fixture()
        try:
            x.manager.start_audit(x.token)
            with self.assertRaisesRegex(ValueError,'RESOURCE_OPERATION_BUSY'):x.manager.save(x.token,'E:/Zhumadian')
            with self.assertRaisesRegex(ValueError,'RESOURCE_OPERATION_BUSY'):x.manager.start_audit(x.token)
        finally:x.close()
    def test_other_actor_cannot_poll_or_cancel_audit(self):
        x=Fixture()
        try:
            job=x.manager.start_audit(x.token);x.verify.owner=('c'*64,PROJECT_KEY);other=x.auth.establish(secrets.token_hex(32))['session']
            for op in [x.manager.audit,x.manager.cancel_audit]:
                with self.assertRaisesRegex(ValueError,'RESOURCE_AUDIT_NOT_FOUND'):op(other,job['id'])
            self.assertFalse(x.manager.jobs[job['id']].cancel.is_set())
        finally:x.close()
    def test_close_waits_for_owned_worker_and_private_report(self):
        x=Fixture();job=x.manager.start_audit(x.token);self.assertTrue(x.settings.enter.wait(1));finished=threading.Event();thread=threading.Thread(target=lambda:(x.manager.close_session(x.token),finished.set()));thread.start();self.assertTrue(x.settings.cancel_seen.wait(1));self.assertFalse(finished.is_set());x.settings.allow_finish.set();thread.join(2);self.assertTrue(finished.is_set());self.assertEqual(x.manager.jobs[job['id']].state,'cancelled');self.assertFalse(x.manager.jobs[job['id']].thread.is_alive());x.close();self.assertFalse(x.manager.watcher.is_alive())
    def test_real_package_qualification_cannot_bypass_commit_fence(self):
        settings=ResourceSettings(PACKAGE,profile_folder=W/'real-settings-fence'/secrets.token_hex(8));before=hashlib.sha256((PACKAGE/'client-gis-install.json').read_bytes()).hexdigest();seen=[]
        def revoked(operation):seen.append(True);raise ValueError('RESOURCE_SESSION_REQUIRED')
        with self.assertRaisesRegex(ValueError,'RESOURCE_SESSION_REQUIRED'):settings.save_authorized('D:/Project/Zhumadian',revoked)
        self.assertEqual(seen,[True]);self.assertFalse(settings.file.exists());self.assertEqual(list(settings.folder.glob('candidate-*.json')),[]);self.assertEqual(hashlib.sha256((PACKAGE/'client-gis-install.json').read_bytes()).hexdigest(),before)
    def test_project_namespace_is_fixed_not_arbitrary_verified_hash(self):
        v=Verifier();v.owner=('a'*64,'f'*64);a=authority(v)
        with self.assertRaisesRegex(ValueError,'RESOURCE_PROJECT_REJECTED'):a.establish(secrets.token_hex(32))
        a.close()
    def test_historical_report_keeps_immutable_source_install_binding(self):
        folder=W/'historic-fixtures'/secrets.token_hex(8);owner=('a'*64,PROJECT_KEY);old=OwnedReports(folder,binding=BINDING);identifier=old.persist(owner,report());original=old.read(owner,identifier);self.assertTrue(original['reportMatchesCurrentInstallation']);changed={**BINDING,'installationIdentity':'4'*64};current=OwnedReports(folder,binding=changed);historical=current.read(owner,identifier);self.assertFalse(historical['reportMatchesCurrentInstallation']);self.assertEqual(historical['clientResourceBinding'],BINDING);self.assertTrue(historical['passed']);binding=old.binding;binding['installationIdentity']='f'*64;self.assertEqual(old.binding,BINDING)
    def test_store_binding_must_match_actual_authority_descriptor(self):
        v=Verifier();a=authority(v);store=OwnedReports(W/'bad-store'/secrets.token_hex(8),binding={**BINDING,'sourceRuntimeIdentity':'9'*64})
        with self.assertRaisesRegex(ValueError,'RESOURCE_REPORT_STORE_BINDING_MISMATCH'):ResourceManager(authority=a,settings=SettingsFixture(),reports=store)
        a.close()

    def test_configuration_access_without_original_gis(self):
        from client_settings import workspace_document
        from client_control import atomic_json,private_directory
        folder=W/'missing-gis-config'/secrets.token_hex(8);settings=ResourceSettings(PACKAGE,profile_folder=folder);folder.mkdir(parents=True);private_directory(folder);missing=W/'not-installed'/secrets.token_hex(8)/'Zhumadian';atomic_json(settings.file,workspace_document(missing.as_posix()),replace=False);self.assertFalse(missing.exists());v=Verifier();a=authority(v);store=OwnedReports(folder/'web-reports',binding=BINDING);manager=ResourceManager(authority=a,settings=settings,reports=store)
        try:
            token=a.establish(secrets.token_hex(32))['session'];config=manager.configuration(token);self.assertTrue(config['saved']);self.assertEqual(config['workspaceRoot'],missing.as_posix());self.assertFalse(missing.exists());self.assertEqual(manager.list_reports(token)['reports'],[])
        finally:manager.close()
    def tls_fixture(self,*,headers=None,raw=None,times=None):
        import resource_grants as module
        from unittest.mock import patch
        expected=authority(Verifier()).expected;record={};value={**expected,'accepted':True,'scopes':[READ],'actorKey':'a'*64,'projectKey':PROJECT_KEY,'expiresAt':-99999};payload=json.dumps(value).encode()if raw is None else raw
        class Reply:
            status=200
            def getheader(self,key,default=''):return'application/json'
            def getheaders(self):return[('X-XNBY-Local-GIS-Remaining-Ms','20000')]if headers is None else headers
            def read(self,count):return payload[:count]
        class Connection:
            def request(self,method,path,body,headers):record.update(method=method,path=path,body=json.loads(body),headers=headers)
            def getresponse(self):return Reply()
            def close(self):record['closed']=True
        def connection(host,port,**kwargs):record.update(host=host,port=port,context=kwargs.get('context'));return Connection()
        with patch.object(module.http.client,'HTTPSConnection',side_effect=connection),patch.object(module.time,'monotonic',side_effect=times or[100.,100.5]):receipt=module.consume_original_resource_grant('f'*64,expected)
        return receipt,record
    def test_fixed_tls_consumer_endpoint_and_elapsed_duration(self):
        receipt,record=self.tls_fixture();self.assertEqual(receipt.monotonic_deadline,120.);self.assertEqual(receipt['expiresAt'],-99999);self.assertEqual(record['host'],'www.joinlinksmart.com');self.assertEqual(record['port'],443);self.assertEqual(record['path'],'/zhumadian/api/spatial-sync/v2/client-resources/grants/consume');self.assertEqual(set(record['body']),{'grant','expected'});self.assertEqual(set(record['headers']),{'Content-Type','Accept'});self.assertTrue(record['closed']);self.assertTrue(record['context'].check_hostname)
    def test_fixed_tls_consumer_rejects_missing_duplicate_or_elapsed_header(self):
        for headers,times in [([],[100.,100.5]),([('X-XNBY-Local-GIS-Remaining-Ms','10'),('X-XNBY-Local-GIS-Remaining-Ms','10')],[100.,100.5]),([('X-XNBY-Local-GIS-Remaining-Ms','1')],[100.,100.5])]:
            with self.subTest(headers=headers):
                with self.assertRaises(ValueError):self.tls_fixture(headers=headers,times=times)
    def test_fixed_tls_consumer_rejects_oversize_and_duplicate_json(self):
        for raw in [b'x'*16385,b'{"accepted":true,"accepted":false}']:
            with self.subTest(size=len(raw)):
                with self.assertRaises(ValueError):self.tls_fixture(raw=raw)

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.fx=Fixture();self.server=ResourceHTTPServer(self.fx.manager,port=0,qa=True);self.thread=threading.Thread(target=lambda:self.server.serve_forever(poll_interval=.025));self.thread.start();self.port=self.server.server_port
    def tearDown(self):
        self.server.shutdown();self.fx.close();self.server.server_close();self.thread.join(2);self.assertFalse(self.thread.is_alive())
    def call(self,method,route,*,token=None,body=None,headers=None):
        h={'Origin':ORIGIN,**(headers or{})}
        if token is not None:h[SESSION]=token
        if body is not None:h['Content-Type']='application/json';body=json.dumps(body).encode('utf-8')
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=4)
        try:
            c.request(method,PREFIX+route,body=body,headers=h);r=c.getresponse();raw=r.read();return r.status,dict(r.getheaders()),json.loads(raw)if raw else None
        finally:c.close()
    def test_discovery_and_session_do_not_expose_windows_owner_or_root(self):
        status,headers,value=self.call('GET','discovery');self.assertEqual(status,200);self.assertEqual(headers['Access-Control-Allow-Origin'],ORIGIN);self.assertNotIn('workspaceRoot',value);self.assertNotIn('ownerToken',value);status,headers,value=self.call('POST','sessions',body={'grant':secrets.token_hex(32)});self.assertEqual(status,201);self.assertGreater(int(headers['X-XNBY-Local-GIS-Remaining-Ms']),0);self.assertEqual(len(value['session']),64)
    def test_configuration_requires_session_and_preserves_role(self):
        self.assertEqual(self.call('GET','configuration')[0],401);self.assertTrue(self.call('GET','configuration',token=self.fx.token)[2]['canConfigure']);self.fx.verify.scopes=[READ];t=self.fx.auth.establish(secrets.token_hex(32))['session'];self.assertEqual(self.call('POST','configuration',token=t,body={'workspaceRoot':'E:/Zhumadian'})[0],403);self.assertEqual(self.fx.settings.writes,0)
    def test_wrong_origin_host_private_and_encoded_paths_rejected(self):
        self.assertEqual(self.call('GET','configuration',token=self.fx.token,headers={'Origin':'https://evil.invalid'})[0],403);self.assertEqual(self.call('GET','configuration',token=self.fx.token,headers={'Host':'localhost:'+str(self.port)})[0],403)
        for key in ['Authorization','Cookie','X-Provider-Owner']:
            self.assertEqual(self.call('GET','configuration',token=self.fx.token,headers={key:'private'})[0],400)
        for route in ['configuration?path=D:/','reports/%2e%2e','../configuration']:
            self.assertEqual(self.call('GET',route,token=self.fx.token)[0],404)
    def test_post_schema_and_report_path_are_fixed(self):
        self.assertEqual(self.call('POST','configuration',token=self.fx.token,body={'workspaceRoot':'E:/Zhumadian','canConfigure':True})[0],400);self.assertEqual(self.call('POST','audits',token=self.fx.token,body={'path':'D:/secret'})[0],400);self.assertEqual(self.call('GET','reports/'+('a'*32),token=self.fx.token)[0],404);self.assertEqual(self.fx.settings.writes,0)
    def test_actual_http_audit_progress_cancel_report_and_account_isolation(self):
        status,_,job=self.call('POST','audits',token=self.fx.token,body={});self.assertEqual(status,202);self.assertTrue(self.fx.settings.enter.wait(1));self.assertEqual(self.call('POST','audits/'+job['id']+'/cancel',token=self.fx.token,body={})[2]['state'],'cancelling');self.fx.settings.allow_finish.set();done=wait_for(self,lambda:(v if(v:=self.call('GET','audits/'+job['id'],token=self.fx.token)[2])['state']in TERMINAL else None));self.assertEqual(done['state'],'cancelled');self.assertTrue(self.call('GET','reports/'+done['reportId'],token=self.fx.token)[2]['cancelled']);self.fx.verify.owner=('d'*64,PROJECT_KEY);other=self.fx.auth.establish(secrets.token_hex(32))['session'];self.assertEqual(self.call('GET','reports',token=other)[2]['reports'],[]);self.assertEqual(self.call('GET','reports/'+done['reportId'],token=other)[0],404)
if __name__=='__main__':unittest.main(verbosity=2)
