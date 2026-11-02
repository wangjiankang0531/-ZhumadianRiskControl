from pathlib import Path
import sys,threading,time,unittest,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_source_memory_store as fixture
import test_source_memory_http as http_fixture
from readonly_source_memory_store import MemorySourceStore,MemoryStoreBusy,MemoryStoreClosed

class BundleWaitStore(unittest.TestCase):
    def store(self,reader=None,**kw):
        s=MemorySourceStore(fixture.Catalog(),reader or fixture.Reader(),**kw);self.addCleanup(s.close);return s
    def test_ready_reply_grants_once_and_keeps_exact_marker(self):
        s=self.store();plan=fixture.ready(s);marker,digest=s.grant(1,depth=1,wait_ms=200);token=marker.pop('cache_lease');self.assertEqual(marker,plan['marker']);self.assertEqual(digest,plan['markerSHA256']);self.assertEqual(s.audit()['activeLeases'],1);s.release(token);self.assertEqual(s.audit()['activeLeases'],0)
    def test_bounded_wait_wakes_on_completion_before_one_lease_exists(self):
        gate=threading.Event();started=threading.Event()
        class Slow(fixture.Reader):
            def __call__(self,*args):started.set();gate.wait(2);return super().__call__(*args)
        s=self.store(Slow());self.assertIsNone(s.grant(1,depth=1));self.assertTrue(started.wait(1));result=[];errors=[]
        def waiting():
            try:result.append(s.grant(1,depth=1,wait_ms=200))
            except Exception as e:errors.append(e)
        worker=threading.Thread(target=waiting);worker.start()
        try:
            deadline=time.monotonic()+1
            while s.audit()['activePlanWaiters']!=1 and time.monotonic()<deadline:time.sleep(.001)
            self.assertEqual(s.audit()['activeLeases'],0);gate.set();worker.join(1);self.assertFalse(worker.is_alive());self.assertFalse(errors);self.assertIsNotNone(result[0]);self.assertEqual(s.audit()['grantWaitCompleted'],1);self.assertEqual(s.audit()['activeLeases'],1);s.release(result[0][0]['cache_lease'])
        finally:gate.set();worker.join(2)
    def test_timeout_creates_no_partial_lease_and_wait_slots_are_released(self):
        gate=threading.Event()
        class Slow(fixture.Reader):
            def __call__(self,*args):gate.wait(2);return super().__call__(*args)
        s=self.store(Slow())
        try:
            self.assertIsNone(s.grant(1,depth=1,wait_ms=20));a=s.audit();self.assertEqual(a['activeLeases'],0);self.assertEqual(a['activePlanWaiters'],0);self.assertEqual(a['grantWaitTimeouts'],1)
        finally:gate.set()
    def test_invalid_wait_is_rejected_before_request_or_lease(self):
        s=self.store()
        for value in [True,-1,201,1.5,'200',None]:
            with self.assertRaises(ValueError):s.grant(1,depth=1,wait_ms=value)
        self.assertEqual(s.audit()['queuedJobs'],0);self.assertEqual(s.audit()['activeLeases'],0)
    def test_source_failure_propagates_and_allocates_no_lease(self):
        class Bad(fixture.Reader):
            def __call__(self,*args):raise ValueError('changed source')
        s=self.store(Bad())
        with self.assertRaisesRegex(ValueError,'changed source'):s.grant(1,depth=1,wait_ms=200)
        self.assertEqual(s.audit()['activeLeases'],0);self.assertEqual(s.audit()['activePlanWaiters'],0)
    def test_plan_and_bundle_share_existing_waiter_limit(self):
        gate=threading.Event()
        class Slow(fixture.Reader):
            def __call__(self,*args):gate.wait(2);return super().__call__(*args)
        s=self.store(Slow(),max_jobs=1);result=[]
        def wait():result.append(s.plan(1,depth=1,wait_ms=200))
        worker=threading.Thread(target=wait);worker.start()
        try:
            deadline=time.monotonic()+1
            while s.audit()['activePlanWaiters']!=1 and time.monotonic()<deadline:time.sleep(.001)
            self.assertEqual(s.audit()['activePlanWaiters'],1)
            with self.assertRaises(MemoryStoreBusy):s.grant(1,depth=1,wait_ms=200)
            self.assertEqual(s.audit()['activeLeases'],0)
        finally:gate.set();worker.join(2)
    def test_closed_store_stops_bundle_wait(self):
        s=self.store()
        with s.plan_ready:s.closed=True;s.plan_ready.notify_all()
        with self.assertRaises(MemoryStoreClosed):s.grant(1,depth=1,wait_ms=200)
        self.assertEqual(s.audit()['activeLeases'],0)
    def test_close_wakes_an_active_bundle_wait_before_builder_finishes(self):
        gate=threading.Event();errors=[]
        class Slow(fixture.Reader):
            def __call__(self,*args):gate.wait(2);return super().__call__(*args)
        s=self.store(Slow())
        def wait():
            try:s.grant(1,depth=1,wait_ms=200)
            except Exception as e:errors.append(e)
        worker=threading.Thread(target=wait);worker.start();closer=None
        try:
            deadline=time.monotonic()+1
            while s.audit()['activePlanWaiters']!=1 and time.monotonic()<deadline:time.sleep(.001)
            self.assertEqual(s.audit()['activePlanWaiters'],1);closer=threading.Thread(target=s.close);closer.start();worker.join(1);self.assertFalse(worker.is_alive());self.assertEqual(len(errors),1);self.assertIsInstance(errors[0],MemoryStoreClosed);self.assertEqual(s.audit()['activeLeases'],0);self.assertEqual(s.audit()['activePlanWaiters'],0)
        finally:
            gate.set();worker.join(2)
            if closer:closer.join(2)

class BundleWaitHTTP(unittest.TestCase):
    def handler(self):
        f=http_fixture.HTTP('test_plan_bundle_header_and_exact_leased_payload');f.setUp();self.addCleanup(f.tearDown);return f
    def test_wait_header_and_lease_payload_preserve_default_no_query_contract(self):
        h=self.handler();status,headers,raw=h.request('/bundle?wait_ms=200');self.assertEqual(status,200);self.assertEqual(headers['X-XNBY-Source-Bundle-Wait-Ms'],'200');token=json.loads(raw)['cache_lease'];h.store.release(token);status,headers,raw=h.request('/bundle');self.assertEqual(status,200);self.assertNotIn('X-XNBY-Source-Bundle-Wait-Ms',headers);h.store.release(json.loads(raw)['cache_lease'])
    def test_malformed_bundle_query_cannot_allocate_lease(self):
        h=self.handler()
        for suffix in ['wait_ms=201','wait_ms=-1','wait_ms=0200','wait_ms=','wait_ms=200&wait_ms=200','wait_ms=200&x=1','lease=abc']:
            self.assertEqual(h.request('/bundle?'+suffix)[0],400);self.assertEqual(h.store.audit()['activeLeases'],0)

class PurePreviewBundleWait(unittest.TestCase):
    def source(self):
        import test_preview_osgb_data_lod as preview
        f=preview.DataPreviewTests('test_plan_grant_three_payloads_matching_lease_and_release');f.setUp();self.addCleanup(f.doCleanups);return f
    def test_actual_preview_bundle_wait_keeps_exact_marker_and_lease_release(self):
        f=self.source();plan=f.ready();h=f.request('/api/lod/1/1?wait_ms=200');self.assertEqual(h.result[0],200);self.assertEqual(h.headers['X-XNBY-Source-Bundle-Wait-Ms'],'200');marker=json.loads(h.result[1]);token=marker.pop('cache_lease');self.assertEqual(marker,plan['marker']);self.assertEqual(h.source_marker_sha256,plan['markerSHA256']);self.assertEqual(f.request('/api/lod-lease/'+token+'/release','POST').result[0],204);self.assertEqual(f.lod.memory.audit()['activeLeases'],0)
    def test_preview_health_exposes_bounded_grant_counters_and_no_native_or_asset_writes(self):
        f=self.source();f.ready();h=f.request('/api/lod/1/1?wait_ms=200');f.lod.memory.release(json.loads(h.result[1])['cache_lease']);health=f.lod.health();self.assertFalse(health['nativeReaderEnabled']);self.assertFalse(health['pythonOriginalSources']['assetWritesEnabled']);self.assertEqual(health['pythonOriginalSources']['grantWaitRequests'],1)

class IndexedBundleWaitHTTP(unittest.TestCase):
    def test_indexed_route_delegates_bounded_wait_and_preserves_source_identity(self):
        import test_indexed_family_source as old
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        from urllib.request import urlopen
        fixture_case=old.IndexedServiceTests('test_bounded_wait_indexed_http_preserves_request_identity');self.addCleanup(fixture_case.doCleanups);_,catalogs,provider=fixture_case.setup_provider();store=old.IndexedFamilyStore(catalogs,old.Reader(),provider);self.addCleanup(store.close)
        class Base(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):self.send_error(404)
        class Handler(old.IndexedFamilyHTTP,Base):memory_sources=store
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();self.addCleanup(lambda:(server.shutdown(),server.server_close(),thread.join(2)));root=f'http://127.0.0.1:{server.server_port}'
        route=root+f'/api/lod-index-family-plan/1/{old.A}?view=0,0,0,0,1,0,90,1,100,6&wait_ms=200'
        with urlopen(route) as r:plan=json.load(r)
        with urlopen(root+'/api/lod-index-family/1/'+plan['indexedRequest']+'?wait_ms=200') as r:
            self.assertEqual(r.status,200);self.assertEqual(r.headers['X-XNBY-Source-Bundle-Wait-Ms'],'200');self.assertEqual(r.headers['X-XNBY-Source-Marker-SHA256'],plan['markerSHA256']);marker=json.load(r)
        token=marker.pop('cache_lease');self.assertEqual(marker,plan['marker']);store.release(token);self.assertEqual(store.audit()['activeLeases'],0)

if __name__=='__main__':unittest.main()
