"""Local editor file -> existing versioned SQLite DLG publication.

The mutable workspace is separate from immutable code/GIS. Existing unknown or
older databases are refused rather than upgraded by a portable viewer startup.
No schema, tenant ownership or feature payload transformations are introduced.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
from portable_source_runtime import regular
from services.database import SCHEMA_VERSION, SCHEMA_SQLITE
from services.layers import LayerRepository


def schema_rows(db):
    return list(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))


def initialize_layer_repository(root):
    root = Path(root)
    user = regular(root/"UserData", root, directory=True)
    folder = user/"BusinessData"
    if not folder.exists():
        folder.mkdir()
    regular(folder, root, directory=True)
    target = folder/"layers.sqlite"

    def check_paths():
        regular(folder, root, directory=True)
        for name in ("layers.sqlite", "layers.sqlite-wal", "layers.sqlite-shm", "layers.sqlite-journal"):
            path = folder/name
            if path.exists() or path.is_symlink():
                regular(path, root)

    check_paths()
    if target.exists():
        with closing(sqlite3.connect(target.as_uri()+"?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                raise ValueError("portable layer database requires an explicit copy migration")
            with closing(sqlite3.connect(":memory:")) as expected:
                expected.executescript(SCHEMA_SQLITE)
                if schema_rows(db) != schema_rows(expected):
                    raise ValueError("portable layer database schema differs; no automatic repair")
            if db.execute("PRAGMA quick_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("portable layer database is invalid; retain for diagnosis")

    class WorkspaceRepository(LayerRepository):
        def connect(self):
            check_paths()
            return super().connect()

    return WorkspaceRepository(target)
