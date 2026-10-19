"""Consistent SQLite backup + lossless portable archive + MySQL INSERT script.

Never overwrites an existing export, restore database or SQL file. No credentials.
"""
import argparse, base64, hashlib, json, sqlite3, tempfile, uuid
from contextlib import closing
from pathlib import Path
from .database import SQLiteDatabase, SCHEMA_VERSION, SCHEMA_SQLITE, SCHEMA_SQLITE_V2, SCHEMA_SQLITE_V3
from .common import loads

LEGACY_TABLES=("issues","events","requests","dlg_documents","dlg_versions","dlg_layers","dlg_features")
LEGACY_TABLES_V3=("issues","events","requests","issue_materials","dlg_documents","dlg_versions","dlg_layers","dlg_features")
GAS_TABLES=("gas_alerts","gas_history","gas_requests","gas_outbox","gas_materials","gas_delivery_attempts")
TABLES=LEGACY_TABLES_V3+GAS_TABLES
MAX_ROW=24*1048576
MAX_ARCHIVE=1024*1048576

def encoded(value):
    return {"$binary":base64.b64encode(value).decode("ascii")} if isinstance(value,bytes) else value

def decoded(value):
    if isinstance(value,dict):
        if set(value)!={"$binary"}:raise ValueError("invalid binary field")
        return base64.b64decode(value["$binary"],validate=True)
    if value is not None and type(value) not in (str,int,float):raise ValueError("invalid field type")
    return value

def canonical(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(",",":")).encode("utf-8")

def columns(db,table):return [row[1] for row in db.execute(f"PRAGMA table_info({table})")]

def validate_database(db):
    if db.execute("PRAGMA user_version").fetchone()[0]!=SCHEMA_VERSION:raise ValueError("schema version mismatch")
    if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or db.execute("PRAGMA foreign_key_check").fetchall():raise ValueError("database integrity failure")
    for tenant,issue_id,revision,owner,system,source,payload in db.execute("SELECT tenant,id,revision,enterprise,source_system,source_id,payload FROM issues"):
        issue=json.loads(payload)
        if (issue["id"],issue["revision"],issue["enterpriseId"],issue["sourceSystem"],issue["sourceId"])!=(issue_id,revision,owner,system,source):raise ValueError("issue snapshot mismatch")
        n,low,high=db.execute("SELECT count(*),min(revision),max(revision) FROM events WHERE tenant=? AND issue=?",(tenant,issue_id)).fetchone()
        if (n,low,high)!=(revision,1,revision):raise ValueError("incomplete issue history")
    from .focus_materials import validate_stored_material,material_metadata
    db.row_factory=sqlite3.Row
    for material in db.execute('SELECT * FROM issue_materials'):
        validate_stored_material(material)
        event=db.execute('SELECT kind,payload FROM events WHERE tenant=? AND issue=? AND revision=?',(material['tenant'],material['issue'],material['revision'])).fetchone()
        if event is None or event['kind']!='material' or json.loads(event['payload']).get('material')!=material_metadata(material):raise ValueError('material journal differs')
    for table in ("dlg_documents","dlg_versions"):
        for raw,digest in db.execute(f"SELECT payload,source_sha256 FROM {table}"):
            if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("DLG checksum mismatch")
            from .data import validate_layers
            validate_layers(loads(raw))
    # Check materialized current layer/feature rows against the lossless document.
    for tenant,document,raw in db.execute("SELECT tenant,document_id,payload FROM dlg_documents"):
        source=loads(raw)
        actual_layers=list(db.execute("SELECT layer_id,sort_index,payload FROM dlg_layers WHERE tenant=? AND document_id=? ORDER BY sort_index",(tenant,document)))
        if len(actual_layers)!=len(source["layers"]):raise ValueError("DLG layer index mismatch")
        count=0
        for order,(layer,indexed) in enumerate(zip(source["layers"],actual_layers)):
            if indexed[0]!=layer["id"] or indexed[1]!=order or json.loads(indexed[2])!={k:v for k,v in layer.items() if k!="features"}:raise ValueError("DLG layer mismatch")
            features=list(db.execute("SELECT feature_id,sort_index,payload FROM dlg_features WHERE tenant=? AND document_id=? AND layer_id=? ORDER BY sort_index",(tenant,document,layer["id"])))
            if len(features)!=len(layer["features"]):raise ValueError("DLG feature count mismatch")
            for number,(feature,row) in enumerate(zip(layer["features"],features)):
                if row[0]!=feature["id"] or row[1]!=number or json.loads(row[2])!=feature:raise ValueError("DLG feature mismatch")
            count+=len(features)
        if db.execute("SELECT count(*) FROM dlg_features WHERE tenant=? AND document_id=?",(tenant,document)).fetchone()[0]!=count:raise ValueError("orphan DLG features")

    from .gas_integrity import validate_gas
    validate_gas(db)

def export_database(database,output):
    database,output=Path(database).resolve(),Path(output).resolve()
    if not database.is_file() or output.exists():raise ValueError("source missing or output already exists")
    staging=output.with_name(output.name+".partial-"+uuid.uuid4().hex)
    staging.mkdir(parents=True)
    manifest={"schema":"xnby.business.database.transfer.v1","databaseVersion":SCHEMA_VERSION,"schemaDefinitionSHA256":hashlib.sha256(SCHEMA_SQLITE.encode()).hexdigest(),"tables":{}}
    with tempfile.TemporaryDirectory() as temporary:
        snapshot=Path(temporary)/"snapshot.sqlite"
        with closing(sqlite3.connect(database.as_uri()+"?mode=ro",uri=True)) as src,closing(sqlite3.connect(snapshot)) as dst:src.backup(dst)
        with closing(sqlite3.connect(snapshot)) as db:
            validate_database(db)
            for table in TABLES:
                names=columns(db,table);digest=hashlib.sha256();count=0;size=0
                with (staging/(table+".jsonl")).open("wb") as stream:
                    for row in db.execute("SELECT * FROM "+table+" ORDER BY "+",".join('"'+name+'"' for name in names[:2])):
                        line=canonical([encoded(v) for v in row])+b"\n"
                        if len(line)>MAX_ROW:raise ValueError("transfer row too large")
                        stream.write(line);digest.update(line);count+=1;size+=len(line)
                        if size>MAX_ARCHIVE:raise ValueError("transfer file too large")
                manifest["tables"][table]={"columns":names,"rows":count,"bytes":size,"sha256":digest.hexdigest()}
    (staging/"manifest.json").write_bytes(canonical(manifest))
    staging.rename(output)
    return manifest

def read_archive(directory):
    directory=Path(directory).resolve()
    raw=(directory/"manifest.json").read_bytes()
    if len(raw)>1048576:raise ValueError("manifest too large")
    manifest=loads(raw)
    layouts={2:(LEGACY_TABLES,SCHEMA_SQLITE_V2),3:(LEGACY_TABLES_V3,SCHEMA_SQLITE_V3),SCHEMA_VERSION:(TABLES,SCHEMA_SQLITE)}
    version=manifest.get('databaseVersion')
    if manifest.get("schema")!="xnby.business.database.transfer.v1" or version not in layouts:raise ValueError("unsupported archive")
    expected_tables,definition=layouts[version]
    if set(manifest.get('tables',{}))!=set(expected_tables):raise ValueError('archive tables differ')
    if manifest.get("schemaDefinitionSHA256")!=hashlib.sha256(definition.encode()).hexdigest():raise ValueError("schema definition mismatch")
    # Validate all bytes before any target database write.
    for table in expected_tables:
        path=directory/(table+".jsonl");m=manifest["tables"][table]
        if path.is_symlink() or path.stat().st_size!=m["bytes"] or not 0<=m["bytes"]<=MAX_ARCHIVE:raise ValueError("archive size mismatch")
        digest=hashlib.sha256()
        with path.open("rb") as stream:
            while block:=stream.read(1048576):digest.update(block)
        if digest.hexdigest()!=m["sha256"]:raise ValueError("archive checksum mismatch")
    return directory,manifest

def rows(directory,table,names):
    with (directory/(table+".jsonl")).open("rb") as stream:
        while line:=stream.readline(MAX_ROW+1):
            if len(line)>MAX_ROW or not line.endswith(b"\n"):raise ValueError("invalid archive row")
            values=loads(line)
            if not isinstance(values,list) or len(values)!=len(names):raise ValueError("invalid archive columns")
            yield [decoded(v) for v in values]

def restore_database(directory,database):
    directory,manifest=read_archive(directory);database=Path(database).resolve()
    if database.exists():raise ValueError("refusing to overwrite database")
    database.parent.mkdir(parents=True,exist_ok=True)
    stage=database.with_name(database.name+".partial-"+uuid.uuid4().hex)
    store=SQLiteDatabase(stage)
    with store.transaction(write=True) as db:
        for table in TABLES:
            if table not in manifest["tables"]:continue
            names=columns(db,table);meta=manifest["tables"][table]
            if names!=meta["columns"]:raise ValueError("schema columns mismatch")
            count=0
            for row in rows(directory,table,names):
                db.execute("INSERT INTO "+table+" VALUES("+",".join("?" for _ in names)+")",row);count+=1
            if count!=meta["rows"]:raise ValueError("archive row count mismatch")
        validate_database(db)
    with closing(store.connect()) as db:db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    stage.rename(database)
    return manifest

def upgrade_copy(database,output):
    database,output=Path(database).resolve(),Path(output).resolve()
    if not database.is_file() or output.exists():raise ValueError('source missing or output already exists')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=output.with_name(output.name+'.partial-'+uuid.uuid4().hex)
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(stage)) as target:
        if source.execute('PRAGMA user_version').fetchone()[0] not in (1,2,3,SCHEMA_VERSION):raise ValueError('unsupported source version')
        source.backup(target)
    store=SQLiteDatabase(stage)
    with closing(store.connect()) as db:
        validate_database(db);db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    stage.rename(output)
    return {'databaseVersion':SCHEMA_VERSION,'tables':{}}

def mysql_script(directory,output):
    directory,manifest=read_archive(directory);output=Path(output).resolve()
    # A SQLite restore validates row semantics, byte identity and schema before generating SQL.
    with tempfile.TemporaryDirectory() as temporary:
        restored=Path(temporary)/"validate.sqlite";restore_database(directory,restored)
        with closing(sqlite3.connect(restored)) as db:
            with output.open("x",encoding="utf-8",newline="\n") as stream:
                stream.write("-- Apply the matching MySQL schema first to an EMPTY staging database.\nSET NAMES utf8mb4;\nSTART TRANSACTION;\n")
                for table in TABLES:
                    names=columns(db,table)
                    for row in db.execute("SELECT * FROM "+table):
                        values=[]
                        for value in row:
                            if value is None:values.append("NULL")
                            elif type(value) in (int,float):values.append(str(value))
                            elif isinstance(value,bytes):values.append("0x"+value.hex())
                            else:values.append("CONVERT(0x"+value.encode('utf-8').hex()+" USING utf8mb4)")
                        stream.write("INSERT INTO `"+table+"` ("+",".join("`"+n+"`" for n in names)+") VALUES ("+",".join(values)+");\n")
                stream.write("COMMIT;\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    e=sub.add_parser("export");e.add_argument("--database",required=True);e.add_argument("--output",required=True)
    r=sub.add_parser("restore");r.add_argument("--archive",required=True);r.add_argument("--database",required=True)
    u=sub.add_parser("upgrade-copy");u.add_argument("--database",required=True);u.add_argument("--output",required=True)
    m=sub.add_parser("mysql-script");m.add_argument("--archive",required=True);m.add_argument("--output",required=True)
    a=p.parse_args()
    if a.command=="export":result=export_database(a.database,a.output)
    elif a.command=="restore":result=restore_database(a.archive,a.database)
    elif a.command=="upgrade-copy":result=upgrade_copy(a.database,a.output)
    else:result=mysql_script(a.archive,a.output)
    print(json.dumps({"schemaVersion":SCHEMA_VERSION,"sourceArchiveVersion":result["databaseVersion"],"rows":{k:v["rows"] for k,v in result["tables"].items()}},ensure_ascii=False))
if __name__=="__main__":main()
