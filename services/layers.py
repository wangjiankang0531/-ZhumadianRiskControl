"""Lossless DLG snapshots + queryable layers/features in the business database."""
import hashlib, json
from .common import ApiError, loads, text, integer
from .database import SQLiteDatabase
from .data import validate_layers
from .focus import encode, stamp

class LayerRepository(SQLiteDatabase):
    def get(self,tenant,document_id="default"):
        with self.transaction() as db:
            row=db.execute("SELECT * FROM dlg_documents WHERE tenant=? AND document_id=?",(tenant,document_id)).fetchone()
            if row is None:raise ApiError(404,"LAYER_DOCUMENT_NOT_FOUND")
            raw=bytes(row["payload"])
            if hashlib.sha256(raw).hexdigest()!=row["source_sha256"]:raise ApiError(503,"LAYER_STORAGE_INVALID")
            return {"revision":row["revision"],"sha256":row["source_sha256"],"updatedAt":row["updated"],"raw":raw,"document":loads(raw)}

    def import_bytes(self,tenant,document_id,raw,expected_revision):
        text(tenant,128,True);text(document_id,128,True);integer(expected_revision,0,2**31-2)
        if not isinstance(raw,bytes) or len(raw)>16*1048576:raise ValueError("invalid DLG byte size")
        doc=loads(raw);validate_layers(doc)
        digest=hashlib.sha256(raw).hexdigest();at=stamp()
        with self.transaction(write=True) as db:
            current=db.execute("SELECT revision,source_sha256 FROM dlg_documents WHERE tenant=? AND document_id=?",(tenant,document_id)).fetchone()
            revision=current["revision"] if current else 0
            if expected_revision!=revision:raise ApiError(409,"LAYER_REVISION_CONFLICT")
            if current and current["source_sha256"]==digest:return {"revision":revision,"sha256":digest,"changed":False}
            revision+=1
            if current:
                db.execute("UPDATE dlg_documents SET revision=?,source_sha256=?,updated=?,payload=? WHERE tenant=? AND document_id=?",(revision,digest,at,raw,tenant,document_id))
                db.execute("DELETE FROM dlg_features WHERE tenant=? AND document_id=?",(tenant,document_id))
                db.execute("DELETE FROM dlg_layers WHERE tenant=? AND document_id=?",(tenant,document_id))
            else:db.execute("INSERT INTO dlg_documents VALUES(?,?,?,?,?,?)",(tenant,document_id,revision,digest,at,raw))
            db.execute("INSERT INTO dlg_versions VALUES(?,?,?,?,?,?)",(tenant,document_id,revision,digest,at,raw))
            for order,layer in enumerate(doc["layers"]):
                visible,locked=layer.get("visible",True),layer.get("locked",False)
                if type(visible) is not bool or type(locked) is not bool:raise ValueError("invalid layer flags")
                meta={k:v for k,v in layer.items() if k!="features"}
                db.execute("INSERT INTO dlg_layers VALUES(?,?,?,?,?,?,?,?)",(tenant,document_id,layer["id"],order,layer["name"],int(visible),int(locked),encode(meta)))
                for draw_order,feature in enumerate(layer["features"]):
                    owner=feature.get("business",{}).get("enterpriseId") or None
                    db.execute("INSERT INTO dlg_features VALUES(?,?,?,?,?,?,?,?)",(tenant,document_id,feature["id"],layer["id"],draw_order,feature["type"],owner,encode(feature)))
            return {"revision":revision,"sha256":digest,"changed":True,"layerCount":len(doc["layers"]),"featureCount":sum(len(l["features"]) for l in doc["layers"])}
