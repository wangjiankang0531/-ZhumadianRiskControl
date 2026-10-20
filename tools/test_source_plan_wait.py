"""Observe completion, timeout, failure and close of bounded metadata-only plans."""
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readonly_source_memory_store import MemorySourceStore, MemoryStoreBusy, MemoryStoreClosed
from source_memory_http import MemorySourceHTTP
from test_source_memory_store import Catalog, Reader, ROOT


class GatedReader(Reader):
    def __init__(self, *, fail=False):
        super().__init__()
        self.started, self.release = threading.Event(), threading.Event()
        self.fail = fail

    def __call__(self, *args):
        self.started.set()
        if not self.release.wait(2):
            raise TimeoutError('test reader gate expired')
        if self.fail:
            raise ValueError('original source SHA changed')
        return super().__call__(*args)


def await_waiter(store):
    deadline = time.monotonic() + 1
    while store.audit()['activePlanWaiters'] == 0:
        if time.monotonic() > deadline:
            raise AssertionError('plan did not enter bounded wait')
        time.sleep(.001)


class WaitPlans(unittest.TestCase):
    def store(self, **options):
        reader = GatedReader(fail=options.pop('fail', False))
        store = MemorySourceStore(Catalog(), reader, **options)
        self.addCleanup(store.close)
        self.addCleanup(reader.release.set)
        return store, reader

    def test_completion_wakes_one_request_and_cached_plan_does_not_rebuild(self):
        store, reader = self.store()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(store.plan, 1, depth=1, wait_ms=200)
            try:
                self.assertTrue(reader.started.wait(1))
                await_waiter(store)
                reader.release.set()
                plan = pending.result(1)
            finally:
                reader.release.set()
        self.assertIsNotNone(plan)
        self.assertEqual(plan, store.plan(1, depth=1, wait_ms=200))
        audit = store.audit()
        self.assertEqual((audit['builds'], audit['planWaitCompleted'], audit['planWaitTimeouts']), (1, 1, 0))
        self.assertEqual(audit['activeLeases'], 0)
        self.assertNotIn('cache_lease', plan['marker'])

    def test_default_is_nonblocking_and_timeout_keeps_metadata_unavailable(self):
        store, reader = self.store()
        self.assertIsNone(store.plan(1, depth=1))
        self.assertTrue(reader.started.wait(1))
        self.assertEqual(store.audit()['activePlanWaiters'], 0)
        self.assertIsNone(store.plan(1, depth=1, wait_ms=20))
        self.assertEqual(store.audit()['planWaitTimeouts'], 1)
        self.assertEqual(store.audit()['activeLeases'], 0)

    def test_invalid_waits_do_not_start_source_jobs(self):
        store, _ = self.store()
        for value in (-1, 201, True, 1.5, '200', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                store.plan(1, depth=1, wait_ms=value)
        self.assertEqual(store.audit()['queuedJobs'], 0)

    def test_waiter_slots_are_bounded_and_share_the_existing_job(self):
        store, reader = self.store(max_jobs=1)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(store.plan, 1, depth=1, wait_ms=200)
            try:
                self.assertTrue(reader.started.wait(1)); await_waiter(store)
                with self.assertRaises(MemoryStoreBusy):
                    store.plan(1, depth=1, wait_ms=200)
                self.assertEqual(store.audit()['queuedJobs'], 1)
                reader.release.set()
                self.assertIsNotNone(pending.result(1))
            finally:
                reader.release.set()
        self.assertEqual(store.audit()['peakPlanWaiters'], 1)
        self.assertEqual(store.audit()['builds'], 1)

    def test_failure_wakes_waiter_without_hiding_identity_error(self):
        store, reader = self.store(fail=True)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(store.plan, 1, depth=1, wait_ms=200)
            try:
                self.assertTrue(reader.started.wait(1)); await_waiter(store)
                reader.release.set()
                with self.assertRaisesRegex(ValueError, 'original source SHA changed'):
                    pending.result(1)
            finally:
                reader.release.set()
        self.assertEqual(store.audit()['failures'], 1)
        self.assertEqual(store.audit()['planWaitTimeouts'], 0)

    def test_close_releases_waiter_before_waiting_for_decoder_shutdown(self):
        store, reader = self.store()
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = pool.submit(store.plan, 1, depth=1, wait_ms=200)
            try:
                self.assertTrue(reader.started.wait(1)); await_waiter(store)
                closing = pool.submit(store.close)
                with self.assertRaises(MemoryStoreClosed):
                    pending.result(1)
                self.assertFalse(closing.done())  # still waiting for decoder, not the HTTP waiter
                reader.release.set(); closing.result(1)
            finally:
                reader.release.set()
        self.assertEqual(store.audit()['activePlanWaiters'], 0)
        self.assertEqual(store.audit()['queuedJobs'], 0)


class WaitHTTP(unittest.TestCase):
    def setUp(self):
        self.reader = GatedReader()
        self.store = MemorySourceStore(Catalog(), self.reader)
        class Base(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_error(404)
            def log_message(self, *args):
                pass
            def _readonly_plan(self, *args, **kwargs):
                raise AssertionError('RAM request reached filesystem producer')
        class Handler(MemorySourceHTTP, Base):
            memory_sources = self.store
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.root = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.reader.release.set()
        self.server.shutdown(); self.server.server_close(); self.thread.join(2)
        self.store.close()

    def request(self, path):
        try:
            response = urlopen(self.root+path, timeout=2)
        except HTTPError as error:
            response = error
        with response:
            return response.status, response.headers, response.read()

    def test_actual_root_route_waits_and_returns_exact_unleased_plan(self):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.request, '/api/lod-plan/1/1?wait_ms=200')
            try:
                self.assertTrue(self.reader.started.wait(1)); await_waiter(self.store)
                self.reader.release.set()
                status, headers, raw = future.result(1)
            finally:
                self.reader.release.set()
        self.assertEqual(status, 200)
        self.assertEqual(headers['X-XNBY-Source-Plan-Wait-Ms'], '200')
        self.assertEqual(json.loads(raw), self.store.plan(1, depth=1))
        self.assertEqual(self.store.audit()['activeLeases'], 0)

    def test_timeout_acknowledges_bound_and_legacy_request_still_returns_202(self):
        status, headers, _ = self.request('/api/lod-plan/1/1?wait_ms=20')
        self.assertEqual(status, 202)
        self.assertEqual(headers['X-XNBY-Source-Plan-Wait-Ms'], '20')
        status, headers, _ = self.request('/api/lod-plan/1/1')
        self.assertEqual(status, 202)
        self.assertIsNone(headers.get('X-XNBY-Source-Plan-Wait-Ms'))

    def test_family_route_preserves_marker_and_query_policy(self):
        self.reader.release.set()
        status, _, raw = self.request(f'/api/lod-family-plan/1/{ROOT}?wait_ms=200')
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)['marker']['complete_sibling_family'])
        for suffix in ('wait_ms=-1', 'wait_ms=201', 'wait_ms=1.5', 'wait_ms=',
                       'wait_ms=200&wait_ms=200', 'skip=1', 'wait_ms=001'):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.request('/api/lod-plan/1/1?'+suffix)[0], 400)
        self.assertEqual(self.request('/api/lod-plan/0/1?wait_ms=200')[0], 400)

    def test_closed_store_is_unavailable_not_a_fake_ready_plan(self):
        self.store.close()
        self.assertEqual(self.request('/api/lod-plan/1/1?wait_ms=200')[0], 409)


if __name__ == '__main__':
    unittest.main()
