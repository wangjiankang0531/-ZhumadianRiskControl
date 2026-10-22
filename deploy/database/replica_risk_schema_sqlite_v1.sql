
CREATE TABLE IF NOT EXISTS rp_risk_units(
 project TEXT NOT NULL, id TEXT NOT NULL, department_id TEXT NOT NULL, person_id TEXT NOT NULL,
 department TEXT NOT NULL, person TEXT NOT NULL, analysis_object TEXT NOT NULL, analysis_unit TEXT NOT NULL,
 risk_level TEXT NOT NULL, coordinate TEXT NOT NULL, longitude REAL NOT NULL, latitude REAL NOT NULL,
 coordinate_system TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 deleted INTEGER NOT NULL CHECK(deleted IN (0,1)),created_at TEXT NOT NULL,created_by TEXT NOT NULL,updated_at TEXT NOT NULL,
 PRIMARY KEY(project,id));
CREATE INDEX IF NOT EXISTS rp_risk_unit_scope ON rp_risk_units(project,deleted,department_id,created_at DESC,id);
CREATE INDEX IF NOT EXISTS rp_risk_unit_level ON rp_risk_units(project,deleted,risk_level,created_at DESC,id);
CREATE TABLE IF NOT EXISTS rp_risk_events(
 project TEXT NOT NULL, unit_id TEXT NOT NULL, revision INTEGER NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('create','update','delete')),
 actor TEXT NOT NULL,policy_version TEXT NOT NULL,at TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),sha256 TEXT NOT NULL,
 PRIMARY KEY(project,unit_id,revision),FOREIGN KEY(project,unit_id) REFERENCES rp_risk_units(project,id));
CREATE TABLE IF NOT EXISTS rp_risk_requests(
 project TEXT NOT NULL, actor TEXT NOT NULL,request_id TEXT NOT NULL,digest TEXT NOT NULL,
 unit_id TEXT NOT NULL,revision INTEGER NOT NULL,result TEXT NOT NULL CHECK(json_valid(result)),
 PRIMARY KEY(project,actor,request_id),FOREIGN KEY(project,unit_id,revision) REFERENCES rp_risk_events(project,unit_id,revision));
CREATE TABLE IF NOT EXISTS rp_risk_outbox(
 project TEXT NOT NULL,unit_id TEXT NOT NULL,revision INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','delivered','failed')),
 event TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),sha256 TEXT NOT NULL,created_at TEXT NOT NULL,
 PRIMARY KEY(project,unit_id,revision),FOREIGN KEY(project,unit_id,revision) REFERENCES rp_risk_events(project,unit_id,revision));
CREATE INDEX IF NOT EXISTS rp_risk_outbox_pending ON rp_risk_outbox(project,state,created_at,unit_id,revision);

PRAGMA user_version=1;
