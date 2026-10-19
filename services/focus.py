"""Tenant-scoped, lightweight park-side issue tracking; never enterprise approval."""
import hashlib, json, re, sqlite3, uuid
from datetime import date, datetime, timezone
from pathlib import Path
from .common import ApiError, fields, text, integer, strings
from .database import SQLiteDatabase
from .focus_materials import MaterialsMixin

STATES = {"pending", "feedback", "supplement", "onsite", "following", "inspection", "archived"}
FLAGS = {"major", "spillover", "repeated", "high-risk", "special-inspection", "supervision"}
RESULTS = {"rectified", "inadequate", "continue", "special-inspection", "emergency"}

def content(value, maximum):
    if not isinstance(value,str) or not value.strip() or len(value.encode("utf-8"))>maximum or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",value):
        raise ValueError("invalid content")
    return value

def stamp():
    return datetime.now(timezone.utc).isoformat()

def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))

def date_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("invalid date")
    date.fromisoformat(value)
    return value

class FocusStore(MaterialsMixin,SQLiteDatabase):



    def access(self, principal, enterprise):
        principal.require("focus:read")
        if not principal.enterprise(enterprise):
            raise ApiError(404, "NOT_FOUND")

    def row(self, db, principal, issue_id):
        row = db.execute("SELECT * FROM issues WHERE tenant=? AND id=?", (principal.tenant, issue_id)).fetchone()
        if row is None:
            raise ApiError(404, "NOT_FOUND")
        self.access(principal, row["enterprise"])
        return row, json.loads(row["payload"])

    def public(self, issue):
        result = dict(issue)
        result["overdue"] = bool(issue.get("dueDate") and issue["dueDate"] < date.today().isoformat() and (issue.get("latestReview") or {}).get("result") != "rectified")
        return result

    def listing(self, principal, query):
        principal.require("focus:read")
        enterprise = query.get("enterpriseId")
        if enterprise and not principal.enterprise(enterprise):
            raise ApiError(403, "FORBIDDEN")
        if query.get("status") and query["status"] not in STATES:
            raise ApiError(400, "INVALID_QUERY")
        if query.get("flag") and query["flag"] not in FLAGS | {"overdue"}:
            raise ApiError(400, "INVALID_QUERY")
        with self.transaction() as db:
            # Ownership is filtered in SQL before decoding or counting records.
            where = "tenant=?"; args = [principal.tenant]
            if enterprise:
                where += " AND enterprise=?"; args.append(enterprise)
            elif not principal.all_enterprises:
                if not principal.enterprises:
                    return {"items": [], "total": 0, "offset": query.get("offset", 0), "limit": query.get("limit", 50), "counts": {"total": 0, "overdue": 0, "archived": 0, "onsite": 0}}
                where += " AND enterprise IN (" + ",".join("?" for _ in principal.enterprises) + ")"; args.extend(sorted(principal.enterprises))
            rows = db.execute("SELECT payload FROM issues WHERE " + where + " ORDER BY updated DESC,id", args)
            items = []
            for row in rows:
                issue = self.public(json.loads(row[0]))
                if query.get("status") and issue["status"] != query["status"]: continue
                if query.get("flag") == "overdue" and not issue["overdue"]: continue
                if query.get("flag") in FLAGS and query["flag"] not in issue["flags"]: continue
                search = query.get("search", "").casefold()
                if search and search not in " ".join(str(issue.get(k,"")) for k in ("title","description","enterpriseId","sourceSystem","sourceId")).casefold(): continue
                items.append(issue)
            offset, limit = query.get("offset", 0), query.get("limit", 50)
            return {"items": items[offset:offset+limit], "total": len(items), "offset": offset, "limit": limit,
                    "counts": {"total": len(items), "overdue": sum(i["overdue"] for i in items), "archived": sum(i["status"]=="archived" for i in items), "onsite": sum(i["status"]=="onsite" for i in items)}}

    def detail(self, principal, issue_id, query, events=False):
        with self.transaction() as db:
            row, issue = self.row(db, principal, issue_id)
            if not events: return {"issue": self.public(issue)}
            offset, limit = query.get("offset", 0), query.get("limit", 50)
            rows = db.execute("SELECT * FROM events WHERE tenant=? AND issue=? ORDER BY revision LIMIT ? OFFSET ?", (principal.tenant,issue_id,limit,offset))
            return {"items": [{"revision":r["revision"],"at":r["at"],"actor":r["actor"],"policyVersion":r["policy"],"kind":r["kind"],"data":json.loads(r["payload"])} for r in rows], "total": row["revision"], "revision": row["revision"], "offset":offset,"limit":limit}

    def validate_create(self, payload):
        required = ["enterpriseId","sourceSystem","sourceId","title","description","level","flags","dueDate"]
        fields(payload, required + ["spatialId"], required)
        for k in ("enterpriseId","sourceSystem","sourceId"): text(payload[k],256,True)
        text(payload["title"],256); content(payload["description"],4000)
        if payload["level"] not in ("major","ordinary","unclassified"): raise ValueError("invalid level")
        flags = strings(payload["flags"],6)
        if not flags <= FLAGS: raise ValueError("invalid focus flags")
        if payload["dueDate"] is not None: date_value(payload["dueDate"])
        # Ordinary issues only enter the park list with a focus reason or expired deadline.
        if not flags and payload["level"] != "major" and not (payload["dueDate"] and payload["dueDate"] < date.today().isoformat()):
            raise ValueError("focus reason required")
        if "spatialId" in payload: text(payload["spatialId"],256,True)

    def mutate(self, principal, issue_id, action, payload, request_key, spatial_check=lambda *_: None):
        if not re.fullmatch(r"[a-f0-9]{32}", request_key or ""):
            raise ApiError(400, "IDEMPOTENCY_KEY_REQUIRED")
        principal.require("focus:read")
        principal.require("focus:feedback" if action=="feedback" else "focus:track")
        digest = hashlib.sha256(encode([issue_id,action,payload]).encode()).hexdigest()
        with self.transaction(write=True) as db:
            if action == "create":
                self.validate_create(payload)
                self.access(principal,payload["enterpriseId"])
                issue = None
            else:
                _, issue = self.row(db,principal,issue_id)
            previous = db.execute("SELECT * FROM requests WHERE tenant=? AND actor=? AND key=?",(principal.tenant,principal.subject,request_key)).fetchone()
            if previous:
                self.access(principal,previous["enterprise"])
                if previous["digest"] != digest: raise ApiError(409,"IDEMPOTENCY_CONFLICT")
                return {**json.loads(previous["result"]), "replayed":True}
            at=stamp()
            if action == "create":
                if payload.get("spatialId"): spatial_check(principal,payload["enterpriseId"],payload["spatialId"])
                issue_id=uuid.uuid4().hex
                issue={**payload,"id":issue_id,"status":"pending","revision":1,"createdAt":at,"updatedAt":at,"latestFeedback":None,"latestReview":None}
                if issue["level"]=="major" and "major" not in issue["flags"]: issue["flags"]=[*issue["flags"],"major"]
                try:
                    db.execute("INSERT INTO issues VALUES (?,?,?,?,?,?,?,?)",(principal.tenant,issue_id,issue["enterpriseId"],issue["sourceSystem"],issue["sourceId"],1,at,encode(issue)))
                except sqlite3.IntegrityError: raise ApiError(409,"SOURCE_ALREADY_REGISTERED") from None
            else:
                integer(payload.get("revision"),1,2**31-1)
                if payload["revision"] != issue["revision"]: raise ApiError(409,"REVISION_CONFLICT")
                if issue["revision"]>=10000: raise ApiError(409,"ISSUE_HISTORY_LIMIT")
                if issue["status"]=="archived" and action!="reopen": raise ApiError(409,"ISSUE_ARCHIVED")
                if action=="feedback":
                    required=["cause","measures","plan","completion","improvement","materialVersion"]
                    fields(payload,["revision",*required],["revision",*required])
                    for k in required:content(payload[k],2000)
                    issue["latestFeedback"]={k:payload[k] for k in required}|{"at":at,"actor":principal.subject}
                    issue["latestReview"]=None;issue["status"]="feedback"
                elif action=="track":
                    fields(payload,["revision","method","note","status"],["revision","method","note","status"])
                    if payload["method"] not in ("phone","online","onsite","communication","supplement"): raise ValueError("invalid method")
                    if payload["status"] not in STATES-{"archived","feedback"}: raise ValueError("invalid state")
                    content(payload["note"],4000);issue["status"]=payload["status"]
                    # Follow-up requiring more evidence invalidates the previous positive review.
                    if issue["status"] in ("pending","supplement","onsite","inspection"):issue["latestReview"]=None
                elif action=="review":
                    fields(payload,["revision","result","note"],["revision","result","note"])
                    if payload["result"] not in RESULTS:raise ValueError("invalid result")
                    content(payload["note"],4000)
                    issue["latestReview"]={"result":payload["result"],"note":payload["note"],"at":at,"actor":principal.subject}
                    issue["status"]={"inadequate":"supplement","special-inspection":"inspection"}.get(payload["result"],"following")
                elif action in ("archive","reopen"):
                    fields(payload,["revision","note"],["revision","note"]);content(payload["note"],4000)
                    if action=="archive":
                        if (issue["latestReview"] or {}).get("result")!="rectified":raise ApiError(409,"REVIEW_REQUIRED")
                        issue["status"]="archived"
                    else:
                        if issue["status"]!="archived":raise ApiError(409,"NOT_ARCHIVED")
                        issue["status"]="following";issue["latestReview"]=None
                else: raise ApiError(404,"NOT_FOUND")
                issue["revision"]+=1;issue["updatedAt"]=at
                db.execute("UPDATE issues SET revision=?,updated=?,payload=? WHERE tenant=? AND id=?",(issue["revision"],at,encode(issue),principal.tenant,issue_id))
            # This journal is the authoritative successful-write audit, in the SAME commit as data and idempotency.
            db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?)",(principal.tenant,issue_id,issue["revision"],at,principal.subject,principal.policy_version,action,encode(payload)))
            result={"issue":self.public(issue),"replayed":False}
            db.execute("INSERT INTO requests VALUES(?,?,?,?,?,?)",(principal.tenant,principal.subject,request_key,digest,issue["enterpriseId"],encode(result)))
            return result
