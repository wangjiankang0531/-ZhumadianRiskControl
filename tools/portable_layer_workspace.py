"""Local editor file -> existing versioned SQLite DLG publication.

The mutable workspace is separate from immutable code/GIS. Existing unknown or
older databases are refused rather than upgraded by a portable viewer startup.
No schema, tenant ownership or feature payload transformations are introduced.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
from portable_source_runtime import regular, json_file, digest
from services.database import SCHEMA_VERSION, SCHEMA_SQLITE
from services.layers import LayerRepository
from services.common import ApiError, loads
from landscape_layer_validation import validate_editor_layers
import os, re


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


def publication_marker(root):
    root = Path(root)
    folder = root/"UserData/PublishedLayers"
    if not os.path.lexists(folder):
        return None
    regular(folder, root, directory=True)
    marker = folder/"current.json"
    return regular(marker, root) if os.path.lexists(marker) else None


def read_editor_publication(root, default_file):
    """Read once, validate those exact bytes, and never return an arbitrary path."""
    root = Path(root)
    marker = publication_marker(root)
    identity = None
    if marker is not None:
        record, _ = json_file(marker, 4096)
        if (not isinstance(record, dict) or set(record)!={"schema","sha256","bytes"}
                or record["schema"]!="zhumadian.layers.publication.v1"
                or not isinstance(record["sha256"],str) or not re.fullmatch(r"[0-9a-f]{64}",record["sha256"])
                or type(record["bytes"]) is not int or not 0 < record["bytes"] <= 16*1048576):
            raise ValueError("invalid editor publication identity")
        identity = record
        source = regular(root/"UserData/PublishedLayers"/(record["sha256"]+".json"), root)
    else:
        source = regular(Path(default_file), root)
    before = source.stat()
    with source.open("rb") as stream:
        raw = stream.read(16*1048576+1)
    after = source.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ApiError(409,"LAYER_SOURCE_CHANGED")
    if len(raw)>16*1048576:
        raise ApiError(413,"LAYER_SOURCE_TOO_LARGE")
    if identity is not None and (len(raw)!=identity["bytes"] or digest(raw)!=identity["sha256"]):
        raise ValueError("editor publication payload identity differs")
    validate_editor_layers(loads(raw))
    return raw


def publish_layer_bytes(repository, raw):
    """CAS publication of the already validated immutable bytes, no file reread."""
    validate_editor_layers(loads(raw))
    try:
        current = repository.get("zhumadian","default")
    except ApiError as error:
        if error.code!="LAYER_DOCUMENT_NOT_FOUND":
            raise
        current = {"revision":0,"sha256":None}
    if current["sha256"]!=digest(raw):
        repository.import_bytes("zhumadian","default",raw,current["revision"])
    return repository.get("zhumadian","default")
