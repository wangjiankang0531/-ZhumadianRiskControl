"""Relocatable, loopback-only owner-controlled original-source runtime.

The package contains code, private Python/plugins and derived base resources.
An explicit local binding selects the already installed original Data directory.
No converter, source write, public bind or automatic process restart is enabled.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.server
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import socket
import stat
import sys
import threading
from urllib.parse import urlsplit

SCHEMA = "zhumadian.source.runtime.package.v1"
BINDING = "zhumadian.source.runtime.binding.v1"
PAYLOAD_DIRS = frozenset(("runtime", "reader", "editor", "application", "resources", "web", "defaults"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path, root, *, directory=False):
    path, root = Path(path), Path(root)
    if not path.is_relative_to(root):
        raise ValueError("path escapes fixed runtime root")
    parts = path.relative_to(root).parts
    for entry in (root, *(root.joinpath(*parts[:i]) for i in range(1, len(parts)+1))):
        fact = entry.lstat()
        if stat.S_ISLNK(fact.st_mode) or getattr(fact, "st_file_attributes", 0) & 0x400:
            raise ValueError("linked runtime path is not allowed")
    if not (stat.S_ISDIR(fact.st_mode) if directory else stat.S_ISREG(fact.st_mode)):
        raise ValueError("unexpected runtime path kind")
    return path


def payload_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or re.search(r"[\x00-\x1f\x7f]", name) or PurePosixPath(name).is_absolute() or name.split("/")[0] not in PAYLOAD_DIRS
            or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError("invalid package payload path")
    return name


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate runtime configuration key")
        result[key] = value
    return result


def json_file(path, limit=8*1048576):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit+1)
    if len(raw) > limit:
        raise ValueError("runtime metadata exceeds bound")
    return json.loads(raw, object_pairs_hook=object_pairs), raw


def load_package(root):
    root = Path(root).resolve(strict=True)
    regular(root, root, directory=True)
    manifest, raw = json_file(regular(root/"source_runtime_manifest.json", root))
    if set(manifest) != {"schema", "files", "readerFiles"} or manifest["schema"] != SCHEMA:
        raise ValueError("unsupported source runtime manifest")
    files = manifest["files"]
    if not isinstance(files, dict) or not 1 <= len(files) <= 12000:
        raise ValueError("unbounded source runtime file list")
    for name, identity in files.items():
        payload_name(name)
        if (not isinstance(identity, dict) or set(identity) != {"bytes", "sha256"}
                or type(identity["bytes"]) is not int or not 0 <= identity["bytes"] <= 512*1048576
                or not isinstance(identity["sha256"], str) or not re.fullmatch("[0-9a-f]{64}", identity["sha256"])):
            raise ValueError("invalid package payload identity")
    def verify_payload(item):
        name,identity=item
        path=regular(root/name,root)
        if path.stat().st_size!=identity["bytes"]:
            raise ValueError("package payload identity differs: "+name)
        value=hashlib.sha256()
        with path.open("rb") as stream:
            while block:=stream.read(1048576):
                value.update(block)
        if value.hexdigest()!=identity["sha256"]:
            raise ValueError("package payload identity differs: "+name)
    # All declared files and all ancestors are checked on every launch. Four
    # independent read streams cap buffers at 4 MiB without a trust cache.
    with ThreadPoolExecutor(max_workers=4,thread_name_prefix="package_verify") as pool:
        for _ in pool.map(verify_payload,files.items()):
            pass
    actual = set()
    for directory in PAYLOAD_DIRS:
        folder = regular(root/directory, root, directory=True)
        for path in folder.rglob("*"):
            regular(path, root, directory=path.is_dir())
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
    if actual != set(files):
        raise ValueError("unexpected or missing package payload files")
    reader_files = manifest["readerFiles"]
    if not isinstance(reader_files, dict) or not 1 <= len(reader_files) <= 32:
        raise ValueError("invalid private reader manifest")
    if {"reader/"+name for name in reader_files} != {name for name in files if name.startswith("reader/")}:
        raise ValueError("private reader file set differs")
    for name, identity in reader_files.items():
        if files["reader/"+name]["sha256"] != identity:
            raise ValueError("private reader identity differs")
    binding, _ = json_file(regular(root/"source_runtime_binding.json", root), 16384)
    if (set(binding) != {"schema", "dataRoot"} or binding["schema"] != BINDING
            or not isinstance(binding["dataRoot"], str) or not binding["dataRoot"] or "\0" in binding["dataRoot"]):
        raise ValueError("invalid explicit local Data binding")
    data = Path(binding["dataRoot"])
    data = (root/data if not data.is_absolute() else data).resolve(strict=True)
    if not data.is_dir() or data.name != "Data" or data == root or root.is_relative_to(data):
        raise ValueError("binding must select a separate local Data directory")
    regular(data, data, directory=True)
    return {"root": root, "data": data, "manifest": manifest, "identity": digest(raw)}


def preflight(package):
    from PIL import Image
    import PIL
    import io
    from readonly_source_memory_store import PinnedCatalogs, ordinary
    root, data = package["root"], package["data"]
    catalogs = PinnedCatalogs(root/"resources")
    catalog = catalogs(141)
    source = next(row for row in catalog["nodes"] if row["name"] == catalog["root"])
    path = ordinary(data/"Tile_141"/source["name"], data)
    if path.stat().st_size != source["bytes"] or digest(path.read_bytes()) != source["sha256"]:
        raise ValueError("Data binding differs from source catalog")
    rgba = bytes([10, 20, 30, 255])*6
    stream = io.BytesIO()
    Image.frombytes("RGBA", (3, 2), rgba).save(stream, format="PNG")
    with Image.open(io.BytesIO(stream.getvalue())) as decoded:
        if decoded.mode != "RGBA" or decoded.tobytes() != rgba:
            raise ValueError("private PNG codec verification failed")
    prefix = Path(sys.prefix).resolve()
    if not prefix.is_relative_to(root/"runtime") or not Path(PIL.__file__).resolve().is_relative_to(prefix):
        raise ValueError("source runtime must use its packaged Python and Pillow")
    return {"packageIdentity": package["identity"], "python": sys.version,
            "privatePython": True, "pillow": PIL.__version__, "pngRoundtrip": True,
            "sampleOriginalSHA256": source["sha256"], "converterEnabled": False}


def initialize_user_layers(root):
    from services.data import validate_layers
    root = Path(root)
    user = root/"UserData"
    if not user.exists():
        user.mkdir()
    regular(user, root, directory=True)
    target = user/"layers.json"
    from portable_layer_workspace import publication_marker, read_editor_publication
    if publication_marker(root) is not None:
        read_editor_publication(root, target)
        return target
    if target.exists():
        document, _ = json_file(regular(target, root), 16*1048576)
        validate_layers(document)
        return target
    source = regular(root/"defaults/editor_layers.json", root)
    document, raw = json_file(source, 16*1048576)
    validate_layers(document)
    with target.open("xb") as stream:
        stream.write(raw)
    provenance = {"schema":"zhumadian.user_layers.origin.v1", "source":"defaults/editor_layers.json",
                  "sourceSHA256":digest(raw), "policy":"copy once; never overwrite existing user layers"}
    with (user/"layers.origin.json").open("x", encoding="utf8") as stream:
        json.dump(provenance, stream, indent=2)
    return target


class ReadOnlySourceGuard:
    def __init__(self, package):
        root = package["root"]
        self.protected = tuple([package["data"], *(root/name for name in PAYLOAD_DIRS),
                                root/"source_runtime_manifest.json", root/"source_runtime_binding.json",
                                root/"UserData/layers.json", root/"UserData/layers.origin.json", root/"UserData/PublishedLayers"])
        self.layer_database = root/"UserData/BusinessData/layers.sqlite"
        self.executable = root/"reader/zmd_osgb_stream_reader.exe"
        self.violations = []
    def _protected(self, value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        path = Path(os.fsdecode(value)).resolve()
        return any(path == root or path.is_relative_to(root) for root in self.protected)
    def deny(self, event):
        self.violations.append(event)
        raise PermissionError("packaged original-source runtime is read-only")
    def __call__(self, event, args):
        if event == "sqlite3.connect" and args and str(args[0]) != ":memory:" and Path(os.fsdecode(args[0])).resolve() != self.layer_database:
            self.deny(event)
        if event == "subprocess.Popen" and (args[0] is None or Path(args[0]).resolve() != self.executable):
            self.deny(event)
        if event in ("os.system", "os.spawn", "os.posix_spawn"):
            self.deny(event)
        if event == "open" and len(args) >= 3:
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")
                       or isinstance(flags, int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing and self._protected(args[0]):
                self.deny(event)
        if event in ("os.remove", "os.rmdir", "os.mkdir", "os.rename", "os.replace", "os.utime", "os.chmod"):
            for path in args[:2 if event in ("os.rename", "os.replace") else 1]:
                if self._protected(path):
                    self.deny(event)


def ready_path(root, name):
    if not re.fullmatch(r"[0-9a-f]{32}", name):
        raise ValueError("invalid owner launch identity")
    user = root/"UserData"
    if not user.exists():
        user.mkdir()
    regular(user, root, directory=True)
    folder = user/"Run"
    if not folder.exists():
        folder.mkdir()
    regular(folder, root, directory=True)
    path = folder/(name+".json")
    if path.exists():
        raise FileExistsError("owner launch identity already used; never overwrite another run")
    return path


def publish_owner_ready(path, result):
    """Windows atomic no-overwrite publication: readers never see partial JSON."""
    path = Path(path)
    if os.path.lexists(path):
        raise FileExistsError("owner ready identity already exists")
    pending = path.with_name(path.stem+".ready.pending.json")
    with pending.open("x", encoding="utf8") as stream:
        json.dump(result, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    # Windows rename refuses an existing destination. Interrupted pending state
    # is retained and an owner launch identity is never automatically reused.
    pending.rename(path)


def serve(package, *, port, owner):
    if type(port) is not int or not 0 <= port <= 65535 or port and port < 1024:
        raise ValueError("invalid loopback runtime port")
    root = package["root"]
    state = ready_path(root, owner)
    report = preflight(package)
    user_layers = initialize_user_layers(root)
    from portable_layer_workspace import initialize_layer_repository, read_editor_publication, publish_layer_bytes
    from services.common import ApiError
    import io
    from services.database import SCHEMA_VERSION
    layer_repository = initialize_layer_repository(root)
    from tools import landscape_web_server as landscape
    from readonly_source_memory_store import PinnedCatalogs, MemorySourceStore
    from osgb_cropped_pages import build_bundle, builder_identity
    from osgb_stdio_worker import PinnedPersistentCropReader
    from source_memory_http import MemorySourceHTTP
    guard = ReadOnlySourceGuard(package)
    sys.addaudithook(guard)
    landscape.POOL.submit = lambda *a, **k: guard.deny("legacy producer submit")
    reader = PinnedPersistentCropReader(root/"reader/zmd_osgb_stream_reader.exe", package["data"], package["manifest"]["readerFiles"])
    level_directory = root/"resources/data/showcase/level_index"
    if (level_directory/"index_manifest.json").is_file():
        from indexed_family_source import LevelIndexProvider, IndexedFamilyStore, IndexedFamilyHTTP
        catalogs = PinnedCatalogs(root/"resources")
        provider = LevelIndexProvider(level_directory, catalogs)
        store = IndexedFamilyStore(catalogs, reader, provider)
        MemorySourceHTTP = IndexedFamilyHTTP
    else:
        store = MemorySourceStore(PinnedCatalogs(root/"resources"), reader, builder=build_bundle, builder_identity=builder_identity())
    class Handler(MemorySourceHTTP, landscape.Handler):
        read_only_lod = True
        allow_local_layer_database = True
        prepared_textures = None
        memory_sources = store
        def _database_layers(self):
            try:
                raw = read_editor_publication(root, self.layers)
                stored = publish_layer_bytes(self.layer_repository, raw)
                data = stored["raw"]
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-XNBY-Layer-Storage", "sqlite")
                self.send_header("X-XNBY-Layer-Revision", str(stored["revision"]))
                self.end_headers()
                return io.BytesIO(data)
            except ApiError as error:
                self.send_error(error.status, error.code)
            except (ValueError, OSError, KeyError, TypeError):
                self.send_error(422, "LAYER_SOURCE_INVALID")
            except Exception:
                self.send_error(503, "LAYER_DATABASE_UNAVAILABLE")
            return None
        def setup(self):
            super().setup()
            if self.connection.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY) != 1:
                raise RuntimeError("private source transport lost TCP_NODELAY")
        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/api/runtime/status":
                if urlsplit(self.path).query:
                    return self.send_error(400)
                return self._memory_json({"schema":"zhumadian.source.runtime.status.v1", "identity":package["identity"],
                    "pid":os.getpid(), "port":self.server.server_port, "readOnly":True, "conversionEnabled":False,
                    "sourceAccess":"read_only", "layerStorage":"sqlite", "layerSchemaVersion":SCHEMA_VERSION,
                    "store":store.audit(), "worker":reader.worker.audit(), "protectedWrites":len(guard.violations)})
            return super().do_GET()
        def do_POST(self):
            if urlsplit(self.path).path == "/api/runtime/shutdown":
                if (urlsplit(self.path).query or self.headers.get("Transfer-Encoding")
                        or self.headers.get("Content-Length", "0") != "0"
                        or not re.fullmatch(r"[0-9a-f]{32}", self.headers.get("X-Local-Owner", ""))
                        or not secrets.compare_digest(self.headers.get("X-Local-Owner", ""), owner)):
                    return self.send_error(403)
                self.send_response(204);self.send_header("Content-Length", "0");self.end_headers()
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            return super().do_POST()
        def translate_path(self, path):
            route = urlsplit(path).path
            static = {"index.html", "viewer.js", "source-gain-worker.js", "THREE-LICENSE.txt",
                      "portal.html", "portal.js", "portal.css", "gas.html", "gas.css", "gas-workbench.js",
                      "reference-demo.html", "reference-demo.js", "reference-demo.css"}
            if route == "/" or route.lstrip("/") in static:
                return str(root/"web"/(route.lstrip("/") or "index.html"))
            return super().translate_path(path)
    Handler.layer_repository = layer_repository
    Handler.root = root/"resources"
    Handler.layers = user_layers
    Handler.business = root/"defaults/business.json"
    Handler.spatial = root/"defaults/spatial.json"
    server = None
    result = {"schema":"zhumadian.source.runtime.ready.v1", "identity":package["identity"],
              "pid":os.getpid(), "launchId":owner, "readOnly":True, "conversionEnabled":False}
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
        result.update(state="ready", port=server.server_port, preflight=report)
        publish_owner_ready(state, result)
        print(json.dumps({"ready":True, "pid":os.getpid(), "port":server.server_port}), flush=True)
        server.serve_forever()
    finally:
        if server is not None:
            server.server_close()
        store.close()
        result.update(state="stopped", store=store.audit(), worker=reader.worker.audit(), protectedWrites=len(guard.violations))
        if state.is_file():
            pending = state.with_suffix(".pending.json")
            with pending.open("x", encoding="utf8") as stream:
                json.dump(result, stream, indent=2)
            pending.replace(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--owner-token")
    args = parser.parse_args()
    package = load_package(args.package)
    if args.check:
        print(json.dumps(preflight(package)), flush=True)
        return
    if args.owner_token is None:
        parser.error("--owner-token is required for an owned runtime")
    serve(package, port=args.port, owner=args.owner_token)


if __name__ == "__main__":
    # -I ignores caller PYTHONPATH and the current directory. Add only this
    # SHA-verified package application and its tools, never a developer path.
    application = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(application), str(application/"tools")]
    main()
