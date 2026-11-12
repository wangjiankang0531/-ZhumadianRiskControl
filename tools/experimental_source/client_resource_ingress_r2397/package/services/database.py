"""SQLite business schema and transactions; external geometry assets stay as files."""
import sqlite3
from pathlib import Path
from contextlib import closing, contextmanager

SCHEMA_VERSION = 4
SCHEMA_SQLITE_V2 = '\n                CREATE TABLE IF NOT EXISTS issues (\n                    tenant TEXT NOT NULL, id TEXT NOT NULL, enterprise TEXT NOT NULL,\n                    source_system TEXT NOT NULL, source_id TEXT NOT NULL,\n                    revision INTEGER NOT NULL, updated TEXT NOT NULL, payload TEXT NOT NULL,\n                    PRIMARY KEY(tenant,id), UNIQUE(tenant,enterprise,source_system,source_id));\n                CREATE TABLE IF NOT EXISTS events (\n                    tenant TEXT NOT NULL, issue TEXT NOT NULL, revision INTEGER NOT NULL,\n                    at TEXT NOT NULL, actor TEXT NOT NULL, policy TEXT NOT NULL,\n                    kind TEXT NOT NULL, payload TEXT NOT NULL,\n                    PRIMARY KEY(tenant,issue,revision),\n                    FOREIGN KEY(tenant,issue) REFERENCES issues(tenant,id));\n                CREATE TABLE IF NOT EXISTS requests (\n                    tenant TEXT NOT NULL, actor TEXT NOT NULL, key TEXT NOT NULL,\n                    digest TEXT NOT NULL, enterprise TEXT NOT NULL, result TEXT NOT NULL,\n                    PRIMARY KEY(tenant,actor,key));\n                CREATE INDEX IF NOT EXISTS issue_enterprise ON issues(tenant,enterprise,updated);\n                \n            \nCREATE TABLE IF NOT EXISTS dlg_documents (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, revision INTEGER NOT NULL,\n    source_sha256 TEXT NOT NULL, updated TEXT NOT NULL, payload BLOB NOT NULL,\n    PRIMARY KEY(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_versions (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, revision INTEGER NOT NULL,\n    source_sha256 TEXT NOT NULL, updated TEXT NOT NULL, payload BLOB NOT NULL,\n    PRIMARY KEY(tenant,document_id,revision),\n    FOREIGN KEY(tenant,document_id) REFERENCES dlg_documents(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_layers (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, layer_id TEXT NOT NULL,\n    sort_index INTEGER NOT NULL, name TEXT NOT NULL, visible INTEGER NOT NULL,\n    locked INTEGER NOT NULL, payload TEXT NOT NULL,\n    PRIMARY KEY(tenant,document_id,layer_id),\n    FOREIGN KEY(tenant,document_id) REFERENCES dlg_documents(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_features (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, feature_id TEXT NOT NULL,\n    layer_id TEXT NOT NULL, sort_index INTEGER NOT NULL, geometry_type TEXT NOT NULL,\n    enterprise TEXT, payload TEXT NOT NULL,\n    PRIMARY KEY(tenant,document_id,feature_id),\n    FOREIGN KEY(tenant,document_id,layer_id) REFERENCES dlg_layers(tenant,document_id,layer_id));\nCREATE INDEX IF NOT EXISTS dlg_layer_order ON dlg_layers(tenant,document_id,sort_index);\nCREATE INDEX IF NOT EXISTS dlg_feature_layer ON dlg_features(tenant,document_id,layer_id,sort_index);\nCREATE INDEX IF NOT EXISTS dlg_feature_enterprise ON dlg_features(tenant,enterprise);\n'

SCHEMA_SQLITE_V3 = SCHEMA_SQLITE_V2 + """
CREATE TABLE IF NOT EXISTS issue_materials (
    tenant TEXT NOT NULL, issue TEXT NOT NULL, id TEXT NOT NULL,
    revision INTEGER NOT NULL, name TEXT NOT NULL, media_type TEXT NOT NULL,
    bytes INTEGER NOT NULL CHECK(bytes>0 AND bytes<=8388608),
    sha256 TEXT NOT NULL, created TEXT NOT NULL, actor TEXT NOT NULL,
    description TEXT NOT NULL, payload BLOB NOT NULL CHECK(length(payload)=bytes),
    PRIMARY KEY(tenant,issue,id), UNIQUE(tenant,issue,revision),
    FOREIGN KEY(tenant,issue,revision) REFERENCES events(tenant,issue,revision));
CREATE INDEX IF NOT EXISTS material_issue_revision ON issue_materials(tenant,issue,revision);
"""

SCHEMA_GAS = """
CREATE TABLE IF NOT EXISTS gas_alerts (
 tenant TEXT NOT NULL,id TEXT NOT NULL,source_system TEXT NOT NULL,source_id TEXT NOT NULL,
 spatial_id TEXT NOT NULL,source_revision INTEGER NOT NULL,revision INTEGER NOT NULL,
 updated TEXT NOT NULL,payload TEXT NOT NULL,
 PRIMARY KEY(tenant,id),UNIQUE(tenant,source_system,source_id));
CREATE INDEX IF NOT EXISTS gas_point_updated ON gas_alerts(tenant,spatial_id,updated);
CREATE TABLE IF NOT EXISTS gas_history (
 tenant TEXT NOT NULL,event_id TEXT NOT NULL,revision INTEGER NOT NULL,
 at TEXT NOT NULL,actor TEXT NOT NULL,policy TEXT NOT NULL,kind TEXT NOT NULL,
 payload TEXT NOT NULL,state_sha256 TEXT NOT NULL,
 PRIMARY KEY(tenant,event_id,revision),FOREIGN KEY(tenant,event_id) REFERENCES gas_alerts(tenant,id));
CREATE TABLE IF NOT EXISTS gas_requests (
 tenant TEXT NOT NULL,actor TEXT NOT NULL,key TEXT NOT NULL,event_id TEXT NOT NULL,
 digest TEXT NOT NULL,result TEXT NOT NULL,
 PRIMARY KEY(tenant,actor,key),FOREIGN KEY(tenant,event_id) REFERENCES gas_alerts(tenant,id));
CREATE TABLE IF NOT EXISTS gas_outbox (
 tenant TEXT NOT NULL,id TEXT NOT NULL,event_id TEXT NOT NULL,revision INTEGER NOT NULL,
 target_system TEXT NOT NULL,delivery_state TEXT NOT NULL,attempts INTEGER NOT NULL,
 lease_sha256 TEXT,lease_until TEXT,next_attempt_at TEXT NOT NULL,last_error TEXT,
 package_sha256 TEXT NOT NULL,payload TEXT NOT NULL,
 PRIMARY KEY(tenant,id),FOREIGN KEY(tenant,event_id,revision) REFERENCES gas_history(tenant,event_id,revision));
CREATE INDEX IF NOT EXISTS gas_outbox_due ON gas_outbox(tenant,delivery_state,next_attempt_at);
CREATE TABLE IF NOT EXISTS gas_materials (
 tenant TEXT NOT NULL,event_id TEXT NOT NULL,id TEXT NOT NULL,revision INTEGER NOT NULL,
 scope TEXT NOT NULL,enterprise TEXT,name TEXT NOT NULL,media_type TEXT NOT NULL,
 bytes INTEGER NOT NULL CHECK(bytes>0 AND bytes<=8388608),sha256 TEXT NOT NULL,
 created TEXT NOT NULL,actor TEXT NOT NULL,description TEXT NOT NULL,payload BLOB NOT NULL CHECK(length(payload)=bytes),
 PRIMARY KEY(tenant,event_id,id),UNIQUE(tenant,event_id,revision),
 CHECK((scope='public' AND enterprise IS NULL) OR (scope='enterprise' AND enterprise IS NOT NULL)),
 FOREIGN KEY(tenant,event_id,revision) REFERENCES gas_history(tenant,event_id,revision));
CREATE INDEX IF NOT EXISTS gas_material_scope ON gas_materials(tenant,event_id,scope,enterprise);
CREATE TABLE IF NOT EXISTS gas_delivery_attempts (
 tenant TEXT NOT NULL,request_id TEXT NOT NULL,attempt INTEGER NOT NULL,
 claimed_at TEXT NOT NULL,lease_sha256 TEXT NOT NULL,lease_until TEXT NOT NULL,
 finished_at TEXT,outcome TEXT NOT NULL,error_code TEXT,
 PRIMARY KEY(tenant,request_id,attempt),FOREIGN KEY(tenant,request_id) REFERENCES gas_outbox(tenant,id));
"""
SCHEMA_SQLITE = SCHEMA_SQLITE_V3 + SCHEMA_GAS

class SQLiteDatabase:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            version=db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0,1,2,3,SCHEMA_VERSION):raise ValueError("unsupported database version")
            # Additive v1/v2/v3 -> v4; legacy issues, DLG and evidence remain, gas is independent.
            db.executescript("BEGIN IMMEDIATE;"+SCHEMA_SQLITE+f"PRAGMA user_version={SCHEMA_VERSION};COMMIT;")

    def connect(self):
        db=sqlite3.connect(self.path,timeout=5,isolation_level=None)
        db.row_factory=sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        return db

    @contextmanager
    def transaction(self,write=False):
        db=self.connect()
        try:
            db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:db.close()
