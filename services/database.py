"""SQLite business schema and transactions; external geometry assets stay as files."""
import sqlite3
from pathlib import Path
from contextlib import closing, contextmanager

SCHEMA_VERSION = 3
SCHEMA_SQLITE_V2 = '\n                CREATE TABLE IF NOT EXISTS issues (\n                    tenant TEXT NOT NULL, id TEXT NOT NULL, enterprise TEXT NOT NULL,\n                    source_system TEXT NOT NULL, source_id TEXT NOT NULL,\n                    revision INTEGER NOT NULL, updated TEXT NOT NULL, payload TEXT NOT NULL,\n                    PRIMARY KEY(tenant,id), UNIQUE(tenant,enterprise,source_system,source_id));\n                CREATE TABLE IF NOT EXISTS events (\n                    tenant TEXT NOT NULL, issue TEXT NOT NULL, revision INTEGER NOT NULL,\n                    at TEXT NOT NULL, actor TEXT NOT NULL, policy TEXT NOT NULL,\n                    kind TEXT NOT NULL, payload TEXT NOT NULL,\n                    PRIMARY KEY(tenant,issue,revision),\n                    FOREIGN KEY(tenant,issue) REFERENCES issues(tenant,id));\n                CREATE TABLE IF NOT EXISTS requests (\n                    tenant TEXT NOT NULL, actor TEXT NOT NULL, key TEXT NOT NULL,\n                    digest TEXT NOT NULL, enterprise TEXT NOT NULL, result TEXT NOT NULL,\n                    PRIMARY KEY(tenant,actor,key));\n                CREATE INDEX IF NOT EXISTS issue_enterprise ON issues(tenant,enterprise,updated);\n                \n            \nCREATE TABLE IF NOT EXISTS dlg_documents (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, revision INTEGER NOT NULL,\n    source_sha256 TEXT NOT NULL, updated TEXT NOT NULL, payload BLOB NOT NULL,\n    PRIMARY KEY(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_versions (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, revision INTEGER NOT NULL,\n    source_sha256 TEXT NOT NULL, updated TEXT NOT NULL, payload BLOB NOT NULL,\n    PRIMARY KEY(tenant,document_id,revision),\n    FOREIGN KEY(tenant,document_id) REFERENCES dlg_documents(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_layers (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, layer_id TEXT NOT NULL,\n    sort_index INTEGER NOT NULL, name TEXT NOT NULL, visible INTEGER NOT NULL,\n    locked INTEGER NOT NULL, payload TEXT NOT NULL,\n    PRIMARY KEY(tenant,document_id,layer_id),\n    FOREIGN KEY(tenant,document_id) REFERENCES dlg_documents(tenant,document_id));\nCREATE TABLE IF NOT EXISTS dlg_features (\n    tenant TEXT NOT NULL, document_id TEXT NOT NULL, feature_id TEXT NOT NULL,\n    layer_id TEXT NOT NULL, sort_index INTEGER NOT NULL, geometry_type TEXT NOT NULL,\n    enterprise TEXT, payload TEXT NOT NULL,\n    PRIMARY KEY(tenant,document_id,feature_id),\n    FOREIGN KEY(tenant,document_id,layer_id) REFERENCES dlg_layers(tenant,document_id,layer_id));\nCREATE INDEX IF NOT EXISTS dlg_layer_order ON dlg_layers(tenant,document_id,sort_index);\nCREATE INDEX IF NOT EXISTS dlg_feature_layer ON dlg_features(tenant,document_id,layer_id,sort_index);\nCREATE INDEX IF NOT EXISTS dlg_feature_enterprise ON dlg_features(tenant,enterprise);\n'

SCHEMA_SQLITE = SCHEMA_SQLITE_V2 + """
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

class SQLiteDatabase:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            version=db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0,1,2,SCHEMA_VERSION):raise ValueError("unsupported database version")
            # Additive v1/v2 -> v3: original issues, events and DLG remain; new evidence is separate.
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
