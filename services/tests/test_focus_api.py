"""Real HTTP/SQLite tests for park-side tracking and independent enterprise scopes."""
import concurrent.futures, copy, json, sqlite3, time, unittest, uuid
from services.tests import test_api as fixture
from services.api import Service
from services.focus import FocusStore
from services.auth import Principal

class FocusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixture.ApiTests.setUpClass()
    def setUp(self):
        self.p=fixture.ApiTests();self.p.setUp()
        for item in self.p.policy["principals"]:
            if item["subject"] in ("QA-A","QA-B","QA-ADMIN"):item["permissions"] += ["focus:read","focus:track"]
        self.p.policy["principals"] += [
            {"subject":"QA-READER","enabled":True,"permissions":["focus:read"],"enterprises":["A"]},
            {"subject":"QA-FEEDBACK","enabled":True,"permissions":["focus:read","focus:feedback"],"enterprises":["A"]}]
        self.p.write("policy.json",self.p.policy)
        self.p.config["businessDatabase"]="focus.sqlite";self.p.write("config.json",self.p.config)
        self.p.service=Service(self.p.root/"config.json");self.p.server.service=self.p.service
    def tearDown(self):self.p.tearDown()
    def call(self,path="",method="GET",payload=None,subject="QA-A",key=None,token=None,headers=None):
        h={}
        if payload is not None:h={"Content-Type":"application/json","Idempotency-Key":key or uuid.uuid4().hex}
        h.update(headers or {})
        auth=token if token is not None else self.p.token(subject,scope="spatial:read business:read focus:read focus:track focus:feedback")
        return self.p.request("/api/v1/focus_issues"+path,auth,method,h,None if payload is None else json.dumps(payload).encode())
    def payload(self,owner="A",source=None):
        return {"enterpriseId":owner,"sourceSystem":"TEST","sourceId":source or uuid.uuid4().hex,"title":"模拟重点问题","description":"合成验收，不用于监管","level":"major","flags":["major"],"dueDate":"2020-01-01"}
    def create(self,owner="A",subject="QA-A",payload=None,key=None):
        status,d,_=self.call(method="POST",payload=payload or self.payload(owner),subject=subject,key=key);self.assertEqual(status,200,d);return d["issue"]
    def action(self,issue,kind,extra,subject="QA-A",key=None):
        return self.call("/"+issue["id"]+"/"+kind,"POST",{"revision":issue["revision"],**extra},subject,key)
    def test_full_feedback_tracking_review_archive_reopen_and_history(self):
        issue=self.create();self.assertTrue(issue["overdue"])
        self.assertEqual(self.action(issue,"archive",{"note":"未复查不能归档"})[0],409)
        self.assertEqual(self.action(issue,"feedback",{"cause":"x"})[0],403)
        feedback={k:"模拟反馈" for k in ("cause","measures","plan","completion","improvement","materialVersion")}
        status,d,_=self.action(issue,"feedback",feedback,"QA-FEEDBACK");self.assertEqual(status,200,d);issue=d["issue"];self.assertEqual(issue["status"],"feedback")
        status,d,_=self.action(issue,"track",{"method":"phone","note":"模拟电话核实","status":"onsite"});self.assertEqual(status,200,d);issue=d["issue"]
        status,d,_=self.action(issue,"review",{"result":"inadequate","note":"模拟复查不通过"});self.assertEqual(status,200,d);issue=d["issue"];self.assertEqual(issue["status"],"supplement")
        self.assertEqual(self.action(issue,"archive",{"note":"不能归档"})[0],409)
        status,d,_=self.action(issue,"review",{"result":"rectified","note":"模拟复查认为已整改"});self.assertEqual(status,200,d);issue=d["issue"];self.assertFalse(issue["overdue"])
        status,d,_=self.action(issue,"archive",{"note":"模拟园区归档"});self.assertEqual(status,200,d);issue=d["issue"]
        self.assertEqual(self.action(issue,"track",{"method":"online","note":"x","status":"following"})[0],409)
        status,d,_=self.action(issue,"reopen",{"note":"发现新情况继续关注"});self.assertEqual(status,200,d);issue=d["issue"];self.assertIsNone(issue["latestReview"])
        status,d,_=self.call("/"+issue["id"]+"/events?offset=0&limit=2");self.assertEqual(status,200);self.assertEqual(d["total"],issue["revision"]);self.assertEqual([e["revision"] for e in d["items"]],[1,2]);self.assertEqual(d["items"][1]["actor"],"QA-FEEDBACK")
    def test_cross_enterprise_counts_filtering_and_claims_cannot_expand_scope(self):
        a=self.create();b=self.create("B","QA-B")
        status,d,_=self.call();self.assertEqual(d["total"],1);self.assertEqual(d["counts"]["overdue"],1)
        self.assertEqual(self.call("/"+b["id"])[0],404)
        self.assertEqual(self.call("?enterpriseId=B")[0],403)
        self.assertEqual(self.action(b,"track",{"note":"x","method":"phone","status":"following"})[0],404)
        status,d,_=self.call(token=self.p.token(enterprises=["B"],roles=["admin"],scope="focus:read focus:track"));self.assertEqual(d["total"],1);self.assertEqual(d["items"][0]["id"],a["id"])
        self.assertEqual(self.call(subject="QA-PUBLIC")[0],403)
    def test_read_only_and_feedback_roles_cannot_track_or_register(self):
        issue=self.create()
        for subject in ("QA-READER","QA-FEEDBACK"):
            self.assertEqual(self.call(subject=subject)[0],200)
            self.assertEqual(self.call(method="POST",payload=self.payload(),subject=subject)[0],403)
            self.assertEqual(self.action(issue,"review",{"result":"rectified","note":"x"},subject)[0],403)
    def test_idempotency_scope_payload_conflicts_and_source_uniqueness(self):
        key=uuid.uuid4().hex;payload=self.payload(source="same")
        issue=self.create(payload=payload,key=key)
        status,d,_=self.call(method="POST",payload=payload,key=key);self.assertEqual(status,200);self.assertTrue(d["replayed"]);self.assertEqual(d["issue"]["id"],issue["id"])
        self.assertEqual(self.call(method="POST",payload={**payload,"title":"changed"},key=key)[0],409)
        self.assertEqual(self.call(method="POST",payload=payload)[0],409)
        status,d,_=self.call("/"+issue["id"]+"/events");self.assertEqual(d["total"],1)
    def test_concurrent_revision_conflict_has_one_committed_event(self):
        issue=self.create()
        def post(_):return self.action(issue,"track",{"method":"phone","note":"同时修改","status":"following"})[0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(post,range(2)))
        self.assertEqual(sorted(results),[200,409]);self.assertEqual(self.call("/"+issue["id"]+"/events")[1]["total"],2)
    def test_rollback_on_journal_failure_and_failed_request_audit(self):
        with self.p.service.focus.transaction(write=True) as db:db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT,'test'); END")
        self.assertEqual(self.call(method="POST",payload=self.payload())[0],503)
        with self.p.service.focus.transaction() as db:
            self.assertEqual(db.execute("SELECT count(*) FROM issues").fetchone()[0],0);self.assertEqual(db.execute("SELECT count(*) FROM requests").fetchone()[0],0)
        with self.p.service.focus.transaction(write=True) as db:db.execute("DROP TRIGGER fail_event")
        self.p.service.audit_file=self.p.root
        self.assertEqual(self.call(method="POST",payload=self.payload())[0],503)
        with self.p.service.focus.transaction() as db:self.assertEqual(db.execute("SELECT count(*) FROM issues").fetchone()[0],0)
    def test_persistence_and_policy_revocation_on_next_request(self):
        issue=self.create();self.p.server.service=Service(self.p.root/"config.json")
        self.assertEqual(self.call("/"+issue["id"])[1]["issue"]["revision"],1)
        self.p.policy["principals"][0]["enterprises"]=[];self.p.write("policy.json",self.p.policy)
        self.assertEqual(self.call()[1]["total"],0);self.assertEqual(self.call("/"+issue["id"])[0],404)
    def test_validation_focus_reason_spatial_ownership_and_unknown_fields(self):
        for change in ({"flags":["invented"]},{"dueDate":"2026-02-30"},{"level":"unknown"},{"title":""},{"extra":True},{"level":"ordinary","flags":[],"dueDate":None}):
            self.assertEqual(self.call(method="POST",payload=self.payload()|change)[0],400,change)
        self.assertEqual(self.call(method="POST",payload=self.payload()|{"spatialId":"b"})[0],400)
        self.assertEqual(self.call(method="POST",payload=self.payload()|{"spatialId":"a"})[0],200)
        self.assertEqual(self.call("?status=invalid")[0],400)
        self.assertEqual(self.call("?flag=invalid")[0],400)
        self.assertEqual(self.call("?limit=201")[0],400)
        issue=self.create();self.assertEqual(self.action(issue,"review",{"revision":True,"note":"x","result":"rectified"})[0],400)
    def test_new_feedback_invalidates_review_and_write_requires_real_token_scope(self):
        issue=self.create();status,d,_=self.action(issue,"review",{"result":"rectified","note":"模拟复查"});self.assertEqual(status,200);issue=d["issue"]
        self.assertEqual(self.call(method="POST",payload=self.payload(),token=self.p.token())[0],403)
        fields={k:"新反馈" for k in ("cause","measures","plan","completion","improvement","materialVersion")}
        status,d,_=self.action(issue,"feedback",fields,"QA-FEEDBACK");self.assertEqual(status,200);self.assertIsNone(d["issue"]["latestReview"])
    def test_filtering_and_paginated_history(self):
        first=self.create(payload=self.payload()|{"title":"唯一搜索词","flags":["spillover"]});self.create()
        status,d,_=self.call("?search="+__import__('urllib.parse',fromlist=['quote']).quote('唯一搜索词'));self.assertEqual(status,200);self.assertEqual(d["total"],1)
        self.assertEqual(self.call("?flag=spillover")[1]["total"],1)
        self.assertEqual(self.call("?offset=1&limit=1")[1]["items"].__len__(),1)
    def test_seed_repeat_does_not_reset_user_edits(self):
        from services.focus_demo import seed
        store=self.p.service.focus;seed(store);status,d,_=self.call();self.assertEqual(d["total"],6)
        issue=d["items"][0];status,changed,_=self.action(issue,"track",{"method":"phone","note":"验收修改保留","status":"following"});self.assertEqual(status,200,changed)
        seed(FocusStore(self.p.root/"focus.sqlite"));self.assertEqual(self.call("/"+issue["id"])[1]["issue"]["revision"],changed["issue"]["revision"])

if __name__=="__main__":unittest.main()
