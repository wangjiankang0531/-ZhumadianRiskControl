
CREATE TABLE IF NOT EXISTS wf_cases(
 id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('hazard','event','work','inspection','investigation')),
 title TEXT NOT NULL, enterprise TEXT NOT NULL, location TEXT NOT NULL,
 state TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 reporter TEXT NOT NULL, assignee TEXT NOT NULL, reviewer TEXT NOT NULL,
 due_date TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 details TEXT NOT NULL CHECK(json_valid(details)), parent_id TEXT REFERENCES wf_cases(id));
CREATE INDEX IF NOT EXISTS wf_case_query ON wf_cases(kind,state,updated_at,id);
CREATE INDEX IF NOT EXISTS wf_case_assignee ON wf_cases(assignee,state,due_date);
CREATE TABLE IF NOT EXISTS wf_actions(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, previous TEXT NOT NULL, state TEXT NOT NULL,
 note TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL CHECK(json_valid(data)),
 PRIMARY KEY(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_requests(
 actor TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 PRIMARY KEY(actor,request_id));
CREATE TABLE IF NOT EXISTS wf_tasks(
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES wf_cases(id),
 revision INTEGER NOT NULL, assignee TEXT NOT NULL, action TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','done')), created_at TEXT NOT NULL, finished_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS wf_pending_task ON wf_tasks(case_id) WHERE status='pending';
CREATE INDEX IF NOT EXISTS wf_user_tasks ON wf_tasks(assignee,status,created_at);
CREATE TABLE IF NOT EXISTS wf_points(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), position INTEGER NOT NULL CHECK(position>=0),
 name TEXT NOT NULL, standard TEXT NOT NULL, result TEXT NOT NULL CHECK(result IN ('pending','normal','abnormal')),
 note TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
 issue_id TEXT REFERENCES wf_cases(id), PRIMARY KEY(case_id,position));
CREATE TABLE IF NOT EXISTS wf_hazard_corrections(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 department TEXT NOT NULL, actual_date TEXT NOT NULL, reason TEXT NOT NULL,
 description TEXT NOT NULL, cost TEXT NOT NULL, preventive_measures TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(case_id,revision), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_reviews(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 result TEXT NOT NULL CHECK(result IN ('pass','return')), description TEXT NOT NULL,
 actor TEXT NOT NULL, at TEXT NOT NULL,
 PRIMARY KEY(case_id,revision), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_work_checks(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 kind TEXT NOT NULL, content TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
 PRIMARY KEY(case_id,revision,kind), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_resources(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, warehouse TEXT NOT NULL,
 unit TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>=0),
 reserved INTEGER NOT NULL CHECK(reserved>=0 AND reserved<=quantity), revision INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS wf_reservations(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), resource_id TEXT NOT NULL REFERENCES wf_resources(id),
 quantity INTEGER NOT NULL CHECK(quantity>0), state TEXT NOT NULL CHECK(state IN ('reserved','returned')),
 actor TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY(case_id,resource_id));
CREATE TABLE IF NOT EXISTS wf_resource_requests(
 actor TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
 resource_id TEXT NOT NULL REFERENCES wf_resources(id), PRIMARY KEY(actor,request_id));
CREATE TABLE IF NOT EXISTS wf_stock_events(
 resource_id TEXT NOT NULL REFERENCES wf_resources(id), revision INTEGER NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, quantity_delta INTEGER NOT NULL,
 reserved_delta INTEGER NOT NULL, case_id TEXT REFERENCES wf_cases(id), at TEXT NOT NULL,
 PRIMARY KEY(resource_id,revision));

CREATE TABLE IF NOT EXISTS wf_materials(
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 name TEXT NOT NULL, media_type TEXT NOT NULL, bytes INTEGER NOT NULL CHECK(bytes>0 AND bytes<=2097152),
 sha256 TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL, description TEXT NOT NULL,
 payload BLOB NOT NULL CHECK(length(payload)=bytes),
 FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE INDEX IF NOT EXISTS wf_case_materials ON wf_materials(case_id,revision);

PRAGMA user_version=2;
