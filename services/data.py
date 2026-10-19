"""Validated file-snapshot adapter. Authorization precedes filtering, counts and paging."""

import hashlib, json, math, re, time
from datetime import datetime
from pathlib import Path
from .common import ApiError, fields, read_json, text, integer, strings, relative

TYPES = read_json(Path(__file__).parents[1] / "shared/spatial_types.json", 65536)
CATEGORIES = TYPES["categories"]
TOPICS = TYPES["topics"]
BUSINESS = {key for key, item in CATEGORIES.items() if item["businessReference"]}


def utc(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z", value
    ):
        raise ValueError("invalid UTC")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def ordered_json(value):
    import rfc8785
    # Retain v1 field order, but use ECMAScript-compatible scalar serialization.
    if isinstance(value, dict):
        return (
            b"{"
            + b",".join(
                rfc8785.dumps(key) + b":" + ordered_json(item)
                for key, item in value.items()
            )
            + b"}"
        )
    if isinstance(value, list):
        return b"[" + b",".join(ordered_json(item) for item in value) + b"]"
    return rfc8785.dumps(value)


def binding(value):
    fields(
        value,
        ["objectType", "businessId", "sourceSystem", "enterpriseId"],
        ["objectType", "businessId", "sourceSystem"],
    )
    if value["objectType"] not in BUSINESS:
        raise ValueError("unknown business class")
    text(value["businessId"], 256, True)
    text(value["sourceSystem"], 128, True)
    if "enterpriseId" in value and value["enterpriseId"] != "":
        text(value["enterpriseId"], 256, True)
    return value


def key(value):
    return (value["sourceSystem"], value["objectType"], value["businessId"])


def fingerprint(document):
    objects = []
    for layer in document["layers"]:
        for feature in layer["features"]:
            b = feature.get("business")
            objects.append(
                {
                    "id": feature["id"],
                    "type": feature["type"],
                    "positions": feature["positions"],
                    "business": (
                        None
                        if b is None
                        else {
                            "objectType": b["objectType"],
                            "businessId": b["businessId"],
                            "sourceSystem": b["sourceSystem"],
                            "enterpriseId": b.get("enterpriseId") or None,
                        }
                    ),
                }
            )
    objects.sort(key=lambda item: item["id"].encode("utf-16-be"))
    c = document["coordinates"]
    payload = {
        "schema": "xnby.spatial.fingerprint.v1",
        "scene": document["scene"],
        "coordinates": {k: c[k] for k in ("srs", "unit", "axes", "origin")},
        "objects": objects,
    }
    return hashlib.sha256(ordered_json(payload)).hexdigest()


def validate_layers(d):
    if d.get("schema") != "hongtu.landscape.layers.v1" or d.get("scene") != "zhumadian":
        raise ValueError("invalid layer schema")
    c = d["coordinates"]
    if (
        c.get("srs") != "EPSG:32650"
        or c.get("unit") != "metre"
        or c.get("axes") != "east,north,up"
    ):
        raise ValueError("invalid coordinates")

    def position(p):
        if (
            not isinstance(p, list)
            or len(p) != 3
            or any(
                type(n) not in (int, float) or not math.isfinite(n) or abs(n) > 1e9
                for n in p
            )
        ):
            raise ValueError("invalid position")

    position(c["origin"])
    if not isinstance(d["layers"], list) or len(d["layers"]) > 1000:
        raise ValueError("invalid layers")
    ids = set()
    layer_ids = set()
    total = 0
    for layer in d["layers"]:
        text(layer["id"])
        text(layer["name"])
        if layer["id"] in layer_ids:
            raise ValueError("duplicate layer")
        layer_ids.add(layer["id"])
        if not isinstance(layer["features"], list):
            raise ValueError("invalid features")
        for f in layer["features"]:
            total += 1
            text(f["id"])
            text(f["name"])
            if total > 10000 or f["id"] in ids:
                raise ValueError("duplicate or excessive objects")
            ids.add(f["id"])
            minimum = {"point": 1, "line": 2, "region": 3}.get(f["type"])
            if (
                minimum is None
                or not isinstance(f["positions"], list)
                or not minimum <= len(f["positions"]) <= 1000
                or f["type"] == "point"
                and len(f["positions"]) != 1
            ):
                raise ValueError("invalid geometry")
            for p in f["positions"]:
                position(p)
            if "business" in f:
                binding(f["business"])
    return ids


def validate_records(d):
    fields(
        d,
        ["schema", "scene", "exportedAt", "ttlHours", "records"],
        ["schema", "scene", "exportedAt", "ttlHours", "records"],
    )
    if d["schema"] != "xnby.business.records.v1" or d["scene"] != "zhumadian":
        raise ValueError("invalid records schema")
    utc(d["exportedAt"])
    integer(d["ttlHours"], 1, 8760)
    if not isinstance(d["records"], list) or len(d["records"]) > 10000:
        raise ValueError("too many records")
    records = {}
    for r in d["records"]:
        fields(
            r,
            [
                "sourceSystem",
                "objectType",
                "businessId",
                "enterpriseId",
                "name",
                "updatedAt",
                "attributes",
            ],
            [
                "sourceSystem",
                "objectType",
                "businessId",
                "name",
                "updatedAt",
                "attributes",
            ],
        )
        binding(
            {
                k: r[k]
                for k in ("sourceSystem", "objectType", "businessId", "enterpriseId")
                if k in r
            }
        )
        text(r["name"])
        utc(r["updatedAt"])
        if not isinstance(r["attributes"], list) or len(r["attributes"]) > 32:
            raise ValueError("invalid attributes")
        names = set()
        for a in r["attributes"]:
            fields(a, ["label", "value"], ["label", "value"])
            text(a["label"], 96)
            if a["label"] in names:
                raise ValueError("duplicate attribute")
            names.add(a["label"])
            v = a["value"]
            if isinstance(v, str):
                if len(v.encode("utf-8")) > 4096 or re.search(
                    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", v
                ):
                    raise ValueError("invalid attribute text")
            elif (
                v is not None
                and type(v) not in (bool, int, float)
                or type(v) in (int, float)
                and not math.isfinite(v)
            ):
                raise ValueError("invalid attribute value")
        if key(r) in records:
            raise ValueError("duplicate business key")
        records[key(r)] = r
    return records


def validate_spatial(d, layer_hash, ids):
    fields(
        d,
        ["schema", "scene", "layerFingerprint", "exportedAt", "objects"],
        ["schema", "scene", "layerFingerprint", "exportedAt", "objects"],
    )
    if (
        d["schema"] != "xnby.spatial.catalog.v1"
        or d["scene"] != "zhumadian"
        or d["layerFingerprint"] != layer_hash
    ):
        raise ValueError("catalog fingerprint mismatch")
    utc(d["exportedAt"])
    if not isinstance(d["objects"], list) or len(d["objects"]) > 10000:
        raise ValueError("invalid catalog count")
    result = {}
    for item in d["objects"]:
        fields(item, ["spatialId", "category", "themes"], ["spatialId", "category"])
        text(item["spatialId"])
        if (
            item["category"] not in CATEGORIES
            or item["spatialId"] in result
            or item["spatialId"] not in ids
        ):
            raise ValueError("invalid catalog object")
        themes = item.get("themes", CATEGORIES[item["category"]]["defaultTopics"])
        checked = strings(themes, 5)
        if not checked or not checked <= TOPICS.keys():
            raise ValueError("invalid themes")
        result[item["spatialId"]] = {
            "category": item["category"],
            "themes": list(themes),
        }
    return result


def presentation(feature, private):
    style = {
        "color": "#43D6E7",
        "fillColor": "#34D399",
        "opacity": 1,
        "fillOpacity": 0.25,
        "widthPx": 3,
        "sizePx": 26,
        "pattern": "solid",
        "icon": "pin",
    }
    source = feature.get("style", {})
    if not isinstance(source, dict):
        raise ValueError("invalid presentation")
    for name in ("color", "fillColor"):
        if name in source:
            if not isinstance(source[name], str) or not re.fullmatch(
                r"#[0-9a-fA-F]{6}", source[name]
            ):
                raise ValueError("invalid color")
            style[name] = source[name]
    for name, low, high in [
        ("opacity", 0, 1),
        ("fillOpacity", 0, 1),
        ("widthPx", 0.5, 32),
        ("sizePx", 8, 128),
    ]:
        if name in source:
            v = source[name]
            if (
                type(v) not in (int, float)
                or not math.isfinite(v)
                or not low <= v <= high
            ):
                raise ValueError("invalid style number")
            style[name] = v
    if "pattern" in source:
        if source["pattern"] not in ("solid", "dash", "dot"):
            raise ValueError("invalid pattern")
        style["pattern"] = source["pattern"]
    if "icon" in source:
        if source["icon"] not in (
            "pin",
            "circle",
            "square",
            "star",
            "warning",
            "custom",
        ):
            raise ValueError("invalid icon")
        style["icon"] = source["icon"]
    if style["icon"] == "custom":
        if private:
            data = source.get("iconData")
            if (
                not isinstance(data, str)
                or not data.startswith("data:image/png;base64,")
                or len(data) > 6 * 1048576
            ):
                raise ValueError("invalid icon data")
            style["iconData"] = data
        else:
            style["icon"] = "pin"
    label = {
        "text": feature["name"],
        "visible": True,
        "fontPx": 14,
        "color": "#FFFFFF",
        "opacity": 1,
        "offset": [12, -24],
    }
    original = feature.get("label")
    required = {"text", "visible", "fontPx", "color", "opacity", "offset"}
    if private and isinstance(original, dict) and required <= original.keys():
        if (
            not isinstance(original["text"], str)
            or len(original["text"].encode("utf-8")) > 768
            or type(original["visible"]) is not bool
            or not isinstance(original["color"], str)
            or not re.fullmatch(r"#[0-9a-fA-F]{6}", original["color"])
        ):
            raise ValueError("invalid label")
        for name, low, high in [("fontPx", 8, 48), ("opacity", 0, 1)]:
            v = original[name]
            if (
                type(v) not in (int, float)
                or not math.isfinite(v)
                or not low <= v <= high
            ):
                raise ValueError("invalid label number")
        offset = original["offset"]
        if (
            not isinstance(offset, list)
            or len(offset) != 2
            or any(
                type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 1000
                for v in offset
            )
        ):
            raise ValueError("invalid label offset")
        label = {name: original[name] for name in required}
    return style, label


class FileStore:
    def __init__(self, config, base):
        fields(
            config, ["layers", "business", "spatial", "publicSpatialIds", "layerDocument"], ["layers"]
        )
        self.paths = {
            name: relative(base, config[name])
            for name in ("layers", "business", "spatial")
            if config.get(name)
        }
        self.public = strings(config.get("publicSpatialIds", []), 10000)
        self.layer_document=config.get("layerDocument")
        if self.layer_document is not None:text(self.layer_document,128,True)
        self.layer_repository=None
        self.layer_tenant=None

    def snapshot(self):
        try:
            documents = {}
            paths=self.paths
            layer_version=None
            if self.layer_document is not None:
                if self.layer_repository is None:raise ValueError("layer database not configured")
                stored=self.layer_repository.get(self.layer_tenant,self.layer_document)
                documents["layers"]=stored["document"];layer_version=stored["revision"]
                paths={k:v for k,v in paths.items() if k!="layers"}
            limits = {
                "layers": 16 * 1024 * 1024,
                "business": 8 * 1024 * 1024,
                "spatial": 4 * 1024 * 1024,
            }
            # Detect writes during acquisition. Operators publish each complete file by atomic replace.
            before = {
                name: (p.stat().st_mtime_ns, p.stat().st_size)
                for name, p in paths.items()
            }
            for name, p in paths.items():
                documents[name] = read_json(p, limits[name])
            after = {
                name: (p.stat().st_mtime_ns, p.stat().st_size)
                for name, p in paths.items()
            }
            if layer_version is not None and self.layer_repository.get(self.layer_tenant,self.layer_document)["revision"]!=layer_version:raise ValueError("layer publication changed")
            if before != after:
                raise ValueError("dataset changed during read")
            ids = validate_layers(documents["layers"])
            layer_hash = fingerprint(documents["layers"])
            records = (
                validate_records(documents["business"])
                if "business" in documents
                else {}
            )
            catalog = (
                validate_spatial(documents["spatial"], layer_hash, ids)
                if "spatial" in documents
                else {}
            )
            objects = []
            for layer in documents["layers"]["layers"]:
                for f in layer["features"]:
                    b = f.get("business")
                    r = records.get(key(b)) if b else None
                    if (
                        r
                        and b.get("enterpriseId")
                        and r.get("enterpriseId")
                        and b["enterpriseId"] != r["enterpriseId"]
                    ):
                        raise ValueError("enterprise mismatch")
                    # If a record exists, its ownership is authoritative, including missing ownership.
                    owner = (
                        r.get("enterpriseId")
                        if r is not None
                        else b.get("enterpriseId") if b else None
                    )
                    category = catalog.get(f["id"], {}).get(
                        "category", b["objectType"] if b else "unregistered"
                    )
                    themes = catalog.get(f["id"], {}).get(
                        "themes", CATEGORIES.get(category, {}).get("defaultTopics", [])
                    )
                    objects.append((f, owner, category, themes, layer))
            return {
                "objects": objects,
                "records": records,
                "business": documents.get("business"),
                "coordinates": documents["layers"]["coordinates"],
                "fingerprint": layer_hash,
                "version": hashlib.sha256(
                    json.dumps(
                        documents,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode("utf-8")
                ).hexdigest(),
            }
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            raise ApiError(503, "DATA_SOURCE_UNAVAILABLE") from None

    def spatial(self, principal, query, *, snapshot=None):
        principal.require("spatial:read")
        snapshot = self.snapshot() if snapshot is None else snapshot
        items = []
        grouped = {}
        for f, owner, category, themes, layer in snapshot["objects"]:
            private = principal.enterprise(owner)
            allowed = private or (principal.public_spatial and f["id"] in self.public)
            group = grouped.setdefault(
                layer["id"],
                {"source": layer, "allAllowed": True, "private": False, "features": {}},
            )
            group["allAllowed"] = group["allAllowed"] and bool(allowed)
            group["private"] = group["private"] or bool(private)
            if allowed:
                group["features"][f["id"]] = len(group["features"])
        metadata = {}
        for layer_id, group in grouped.items():
            if not group["features"]:
                continue
            layer = group["source"]
            visible = layer.get("visible", True)
            if type(visible) is not bool:
                raise ApiError(503, "DATA_SOURCE_UNAVAILABLE")
            ordinal = len(metadata)
            name = (
                layer["name"]
                if group["allAllowed"] and group["private"]
                else ("授权图层" if group["private"] else "公共图层")
                + " "
                + str(ordinal + 1)
            )
            metadata[layer_id] = {
                "id": "API-LAYER-"
                + hashlib.sha256(layer_id.encode("utf-8")).hexdigest()[:24],
                "name": name,
                "order": ordinal,
                "visible": visible,
            }
        for f, owner, category, themes, layer in snapshot["objects"]:
            private = principal.enterprise(owner)
            if not private and not (
                principal.public_spatial and f["id"] in self.public
            ):
                continue
            if query.get("enterpriseId") and (
                not private or owner != query["enterpriseId"]
            ):
                continue
            if query.get("category") and category != query["category"]:
                continue
            if query.get("topic") and query["topic"] not in themes:
                continue
            item = {
                "id": f["id"],
                "name": f["name"],
                "type": f["type"],
                "positions": f["positions"],
                "category": category,
                "themes": themes,
                "access": "enterprise" if private else "public_basic",
                "layer": metadata[layer["id"]],
                "drawOrder": grouped[layer["id"]]["features"][f["id"]],
            }
            try:
                item["style"], item["label"] = presentation(f, private)
            except (ValueError, TypeError):
                raise ApiError(503, "DATA_SOURCE_UNAVAILABLE") from None
            if private:
                item["enterpriseId"] = owner
                if f.get("business") and "business:read" in principal.permissions:
                    item["business"] = dict(f["business"], enterpriseId=owner)
            if (
                query.get("search")
                and query["search"].casefold()
                not in (item["name"] + " " + item["id"]).casefold()
            ):
                continue
            items.append(item)
        return page(items, query) | {
            "coordinates": snapshot["coordinates"],
            "layerFingerprint": snapshot["fingerprint"],
            "datasetVersion": snapshot["version"],
            "source": "file_snapshot",
        }

    def business(self, principal, query, record_key=None, *, snapshot=None):
        principal.require("business:read")
        if "business" not in self.paths:
            raise ApiError(503, "BUSINESS_SOURCE_NOT_CONFIGURED")
        snapshot = self.snapshot() if snapshot is None else snapshot
        document = snapshot["business"]
        items = []
        now = time.time()
        for k, r in snapshot["records"].items():
            if not principal.enterprise(r.get("enterpriseId")):
                continue
            if record_key is not None and k != record_key:
                continue
            if (
                query.get("enterpriseId")
                and r.get("enterpriseId") != query["enterpriseId"]
            ):
                continue
            if query.get("objectType") and r["objectType"] != query["objectType"]:
                continue
            if query.get("sourceSystem") and r["sourceSystem"] != query["sourceSystem"]:
                continue
            if (
                query.get("search")
                and query["search"].casefold()
                not in (r["name"] + " " + r["businessId"]).casefold()
            ):
                continue
            export = utc(document["exportedAt"])
            update = utc(r["updatedAt"])
            state = (
                "future"
                if max(export, update) > now + 300
                else (
                    "stale"
                    if max(now - export, now - update) > document["ttlHours"] * 3600
                    else "ready"
                )
            )
            items.append(dict(r, state=state))
        if record_key is not None:
            if not items:
                raise ApiError(404, "NOT_FOUND")
            result = {"item": items[0]}
        else:
            result = page(items, query)
        return result | {
            "source": "file_snapshot",
            "datasetVersion": snapshot["version"],
            "exportedAt": document["exportedAt"],
            "ttlHours": document["ttlHours"],
        }


def page(items, query):
    items.sort(
        key=lambda r: (
            r.get("sourceSystem", ""),
            r.get("objectType", ""),
            r.get("businessId", r.get("id", "")),
        )
    )
    offset = query.get("offset", 0)
    limit = query.get("limit", 50)
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "offset": offset,
        "limit": limit,
    }
