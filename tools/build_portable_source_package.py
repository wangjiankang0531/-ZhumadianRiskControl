"""Build a new local source-runtime candidate without copying the original GIS.

The selected installed Data directory remains read-only and is bound explicitly.
This assembles a service candidate; native EXE owner bootstrap and full relocation
acceptance must be verified separately before calling it a standalone release.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from portable_source_runtime import SCHEMA, BINDING, PAYLOAD_DIRS, regular, payload_name
from services.data import validate_layers


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(1048576):
            digest.update(chunk)
    return digest.hexdigest()


def merge_layers(published, existing):
    validate_layers(published);validate_layers(existing)
    if published["scene"] != existing["scene"] or published["coordinates"] != existing["coordinates"]:
        raise ValueError("layer coordinate frames differ; never silently reproject user data")
    result = copy.deepcopy(published)
    layer_ids = {layer["id"]: layer for layer in result["layers"]}
    feature_ids = {feature["id"] for layer in result["layers"] for feature in layer["features"]}
    for layer in existing["layers"]:
        if layer["id"] in layer_ids:
            if layer != layer_ids[layer["id"]]:
                raise ValueError("conflicting user layer identity")
            continue
        if feature_ids.intersection(feature["id"] for feature in layer["features"]):
            raise ValueError("conflicting user feature identity")
        result["layers"].append(copy.deepcopy(layer));layer_ids[layer["id"]] = layer
        feature_ids.update(feature["id"] for feature in layer["features"])
    validate_layers(result)
    return result


def build(args):
    output = args.output.absolute()
    work = ROOT/"work"
    if output.exists() or not output.resolve().is_relative_to(work.resolve()) or output.resolve() == work.resolve():
        raise ValueError("candidate must be a new directory under project work/")
    for parent in output.parents:
        if parent.exists() and parent.is_relative_to(work):
            regular(parent, work, directory=True)
    resources = args.resources.resolve(strict=True)
    reader = args.reader.resolve(strict=True)
    python = args.python.resolve(strict=True)
    application = args.application.resolve(strict=True)
    editor = args.editor.resolve(strict=True)
    web = args.web.resolve(strict=True)
    data = args.data.resolve(strict=True)
    reader_files = json.loads(args.reader_manifest.read_text("utf8"))
    if {p.relative_to(reader).as_posix() for p in reader.rglob("*") if p.is_file()} != set(reader_files):
        raise ValueError("private reader file set changed")
    for name, sha in reader_files.items():
        if file_sha(regular(reader/name, reader)) != sha:
            raise ValueError("private reader identity changed")
    imported = json.loads(args.import_audit.read_text("utf8"))["localImportedFiles"]
    published = json.loads(args.layers.read_text("utf8"))
    original = json.loads(args.user_layers.read_text("utf8"))
    merged = merge_layers(published, original)
    output.mkdir(parents=True, exist_ok=False)
    for directory in PAYLOAD_DIRS:
        (output/directory).mkdir()
    copied = {}
    def put(source, destination, anchor):
        source = regular(Path(source), Path(anchor))
        destination = payload_name(destination)
        target = output/destination
        target.parent.mkdir(parents=True, exist_ok=True)
        before = source.stat()
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, 1048576)
        after = source.stat()
        if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns) or file_sha(source) != file_sha(target):
            raise ValueError("copied source changed: "+destination)
        copied[destination] = {"bytes":target.stat().st_size, "sha256":file_sha(target)}
    def tree(source, prefix):
        source = source.resolve(strict=True)
        regular(source, source, directory=True)
        for path in sorted(source.rglob("*")):
            if "__pycache__" in path.relative_to(source).parts or path.suffix in (".pyc", ".pyo"):
                continue
            regular(path, source, directory=path.is_dir())
            if path.is_file():
                put(path, prefix+"/"+path.relative_to(source).as_posix(), source)
    tree(python, "runtime/python")
    for name in reader_files:
        put(reader/name, "reader/"+name, reader)
    # The old development reader could resolve these from System32. Ship the
    # same tested editor CRT files beside the reader so its minimal DLL search
    # never depends on a separately installed Visual C++ runtime.
    private_crt = ("concrt140.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll",
                   "msvcp140_atomic_wait.dll", "msvcp140_codecvt_ids.dll", "vccorlib140.dll",
                   "vcruntime140.dll", "vcruntime140_1.dll", "vcruntime140_threads.dll")
    for name in private_crt:
        identity = file_sha(regular(editor/name, editor))
        if name in reader_files:
            if reader_files[name] != identity:
                raise ValueError("private CRT source identities conflict")
        else:
            put(editor/name, "reader/"+name, editor)
            reader_files[name] = identity
    if len(reader_files) > 32:
        raise ValueError("private reader exceeds unchanged runtime file bound")
    tree(editor, "editor")
    tree(web, "web")
    for name, sha in imported.items():
        name = name.replace("\\", "/")
        path = regular(application/name, application)
        if file_sha(path) != sha:
            raise ValueError("tested frozen module changed: "+name)
        put(path, "application/"+name, application)
    put(ROOT/"tools/portable_source_runtime.py", "application/tools/portable_source_runtime.py", ROOT)
    tree(application/"shared", "application/shared")
    for group in ("full", "context", "pages", "native_hierarchy"):
        tree(resources/"assets/showcase/runtime/zhumadian"/group, "resources/assets/showcase/runtime/zhumadian/"+group)
    tree(resources/"data/showcase", "resources/data/showcase")
    icons = (resources/"assets/landscape/icons.png").resolve(strict=True)
    put(icons, "resources/assets/landscape/icons.png", icons.parent)
    for source,name in ((args.layers,"layers.json"),(args.business,"business.json")):
        source = source.resolve(strict=True)
        put(source, "defaults/"+name, source.parent)
    if args.spatial:
        source = args.spatial.resolve(strict=True)
        put(source,"defaults/spatial.json",source.parent)
    raw = (json.dumps(merged,ensure_ascii=False,indent=2)+"\n").encode("utf8")
    target = output/"defaults/editor_layers.json"
    with target.open("xb") as stream:
        stream.write(raw)
    copied["defaults/editor_layers.json"] = {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
    for index,notice in enumerate(args.notice):
        notice = notice.resolve(strict=True)
        put(notice, "application/notices/"+str(index).zfill(2)+"_"+notice.name, notice.parent)
    manifest = {"schema":SCHEMA, "files":dict(sorted(copied.items())), "readerFiles":reader_files}
    (output/"source_runtime_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
    try:
        binding = os.path.relpath(data, output)
    except ValueError:
        binding = str(data)
    (output/"source_runtime_binding.json").write_text(json.dumps({"schema":BINDING,"dataRoot":binding},ensure_ascii=False,indent=2),encoding="utf8")
    return {"output":str(output),"files":len(copied),"bytes":sum(row["bytes"] for row in copied.values()),
            "manifestSHA256":file_sha(output/"source_runtime_manifest.json"),"originalGISCopied":False,
            "userOriginalOverwritten":False,"editorLayers":len(merged["layers"]),
            "editorFeatures":sum(len(layer["features"]) for layer in merged["layers"]),
            "editorAutoStartsServiceVerified":False,"phase":"relocatable_service_candidate"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "resources", "reader", "reader-manifest", "python", "application", "editor", "web", "data", "import-audit", "layers", "user-layers", "business"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--spatial", type=Path)
    parser.add_argument("--notice", type=Path, action="append", default=[])
    print(json.dumps(build(parser.parse_args()),ensure_ascii=False,indent=2),flush=True)


if __name__ == "__main__":
    main()
