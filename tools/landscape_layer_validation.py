"""Validate the unchanged DLG bytes that will be consumed by the Web renderer.

Business geometry snapshots have a broader contract. This check applies only to
local editor publication, before selecting or replacing a renderable snapshot.
"""
import math
import re
from services.data import BUSINESS


def _number(value, low, high):
    return type(value) in (int, float) and low <= value <= high and math.isfinite(value)


def _string(value, maximum, required=False):
    return (isinstance(value, str) and (bool(value) or not required)
            and len(value.encode("utf-8")) <= maximum
            and not re.search(r"[\x00-\x20\x7f]", value))


def _color(value):
    return isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None


def _ring(points):
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def on(a, b, c):
        return (abs(cross(a,b,c)) < .0001
                and min(a[0],b[0])-.0001 <= c[0] <= max(a[0],b[0])+.0001
                and min(a[1],b[1])-.0001 <= c[1] <= max(a[1],b[1])+.0001)
    area=0
    for i,a in enumerate(points):
        b=points[(i+1)%len(points)]
        if math.hypot(a[0]-b[0],a[1]-b[1]) < .001:
            raise ValueError("region has repeated vertices")
        area += a[0]*b[1]-b[0]*a[1]
        for j in range(i+1,len(points)):
            if j==i+1 or (i==0 and j==len(points)-1):
                continue
            c,d=points[j],points[(j+1)%len(points)]
            if ((cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0)
                    or on(a,b,c) or on(a,b,d) or on(c,d,a) or on(c,d,b)):
                raise ValueError("region boundary intersects itself")
    if abs(area)<.001:
        raise ValueError("region has zero area")


def _label(label):
    if (not isinstance(label,dict) or type(label.get("visible")) is not bool
            or not isinstance(label.get("text"),str) or len(label["text"].encode("utf-8"))>768
            or not _color(label.get("color")) or not _number(label.get("fontPx"),8,48)
            or not _number(label.get("opacity"),0,1)
            or not isinstance(label.get("offset"),list) or len(label["offset"])!=2
            or any(not _number(n,-1000,1000) for n in label["offset"])
            or label.get("placement","screen") not in ("screen","billboard")
            or not _number(label.get("heightM",60),0,500)):
        raise ValueError("invalid rendering label")


def _business(binding):
    if (not isinstance(binding,dict)
            or set(binding)-{"objectType","businessId","sourceSystem","enterpriseId"}
            or not isinstance(binding.get("objectType"),str) or binding["objectType"] not in BUSINESS):
        raise ValueError("invalid rendering business binding")
    for key,maximum,required in (("businessId",256,True),("sourceSystem",128,True),("enterpriseId",256,False)):
        if key not in binding and not required:
            continue
        if not _string(binding.get(key),maximum,required):
            raise ValueError("invalid rendering business reference")


def validate_editor_layers(document):
    """Return the same object, never normalize geometry, style, IDs or raw bytes."""
    if not isinstance(document,dict) or document.get("schema")!="hongtu.landscape.layers.v1" or document.get("scene")!="zhumadian":
        raise ValueError("invalid rendering DLG schema")
    coordinates=document.get("coordinates")
    if (not isinstance(coordinates,dict) or coordinates.get("srs")!="EPSG:32650"
            or coordinates.get("unit")!="metre" or coordinates.get("axes")!="east,north,up"
            or coordinates.get("origin")!=[225319.5,3648440.1,30.9]):
        raise ValueError("rendering DLG coordinate frame differs")
    layers=document.get("layers")
    if not isinstance(layers,list) or len(layers)>1000:
        raise ValueError("invalid rendering layer count")
    layer_ids=set();feature_ids=set();total=0
    for layer in layers:
        if (not isinstance(layer,dict) or not isinstance(layer.get("id"),str) or not layer["id"]
                or layer["id"] in layer_ids or not isinstance(layer.get("name"),str)
                or type(layer.get("visible")) is not bool or type(layer.get("locked")) is not bool
                or not isinstance(layer.get("features"),list)):
            raise ValueError("invalid rendering layer")
        layer_ids.add(layer["id"])
        for feature in layer["features"]:
            total+=1
            if (not isinstance(feature,dict) or total>10000
                    or not isinstance(feature.get("id"),str) or not feature["id"]
                    or feature["id"] in feature_ids or not isinstance(feature.get("name"),str)
                    or feature.get("type") not in ("point","line","region")):
                raise ValueError("invalid rendering feature")
            feature_ids.add(feature["id"])
            kind=feature["type"];points=feature.get("positions")
            minimum={"point":1,"line":2,"region":3}[kind]
            if (not isinstance(points,list) or not minimum<=len(points)<=1000
                    or (kind=="point" and len(points)!=1)
                    or any(not isinstance(p,list) or len(p)!=3
                           or any(not _number(n,-100000,100000) for n in p) for p in points)):
                raise ValueError("invalid rendering geometry")
            if kind=="region":
                _ring(points)
            style=feature.get("style")
            if (not isinstance(style,dict) or not _color(style.get("color")) or not _color(style.get("fillColor"))
                    or style.get("pattern") not in ("solid","dash","dot")
                    or style.get("icon") not in ("pin","circle","square","star","warning","custom")):
                raise ValueError("invalid rendering style")
            for key,low,high in (("opacity",0,1),("fillOpacity",0,1),("widthPx",.5,32),("sizePx",8,128)):
                if not _number(style.get(key),low,high):
                    raise ValueError("rendering style outside supported range")
            if style["icon"]=="custom":
                data=style.get("iconData")
                if not isinstance(data,str) or not data.startswith("data:image/png;base64,") or len(data)>6*1048576:
                    raise ValueError("invalid embedded rendering icon")
            if "label" in feature:
                _label(feature["label"])
            if "business" in feature:
                _business(feature["business"])
    return document
