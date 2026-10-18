"""Cross-process leases and bounded cleanup for disposable OSGB-derived bundles."""

from contextlib import contextmanager, ExitStack
from pathlib import Path
import json
import os
import re
import time
import uuid

BUNDLE = re.compile(r"(?:tile_(\d+)_depth_\d+|family_tile_(\d+)_[0-9a-f]{16})")
LIMIT = 1024 * 1048576


def linked(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def bundle_tile(name):
    match = BUNDLE.fullmatch(name)
    if not match:
        raise ValueError("invalid derived bundle name")
    tile = int(match.group(1) or match.group(2))
    if not 1 <= tile <= 2346:
        raise ValueError("invalid derived tile")
    return tile


class FileLock:
    def __init__(self, path, exclusive=False, timeout=100, *, read_only=False):
        if read_only and exclusive:
            raise ValueError("read-only cache locks cannot be exclusive")
        if not read_only:
            path.parent.mkdir(parents=True, exist_ok=True)
        if linked(path.parent) or linked(path):
            raise ValueError("cache lock path cannot be a link")
        self.file = path.open("rb" if read_only else "a+b")
        self.closed = False
        deadline = time.monotonic() + timeout
        if os.name == "nt":
            import ctypes
            import msvcrt
            from ctypes import wintypes

            class Overlapped(ctypes.Structure):
                _fields_ = [
                    ("Internal", ctypes.c_size_t),
                    ("InternalHigh", ctypes.c_size_t),
                    ("Offset", wintypes.DWORD),
                    ("OffsetHigh", wintypes.DWORD),
                    ("hEvent", wintypes.HANDLE),
                ]

            self.api = ctypes.WinDLL("kernel32", use_last_error=True)
            self.api.LockFileEx.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(Overlapped),
            ]
            self.api.UnlockFileEx.argtypes = [
                wintypes.HANDLE,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.DWORD,
                ctypes.POINTER(Overlapped),
            ]
            self.overlap = Overlapped()
            self.handle = msvcrt.get_osfhandle(self.file.fileno())

            def acquire():
                if self.api.LockFileEx(
                    self.handle,
                    1 | (2 if exclusive else 0),
                    0,
                    1,
                    0,
                    ctypes.byref(self.overlap),
                ):
                    return True
                error = ctypes.get_last_error()
                if error not in (32, 33):
                    raise ctypes.WinError(error)
                return False

        else:
            import fcntl

            def acquire():
                try:
                    fcntl.flock(
                        self.file,
                        (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB,
                    )
                    return True
                except BlockingIOError:
                    return False

        try:
            while not acquire():
                if time.monotonic() >= deadline:
                    raise TimeoutError("derived cache bundle is in use")
                time.sleep(min(0.025, max(0, deadline - time.monotonic())))
        except BaseException:
            self.file.close()
            self.closed = True
            raise

    def close(self):
        if self.closed:
            return
        self.closed = True
        if os.name == "nt":
            import ctypes

            self.api.UnlockFileEx(self.handle, 0, 1, 0, ctypes.byref(self.overlap))
        else:
            import fcntl

            fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def tile_lock(cache, tile, exclusive=False, timeout=100):
    if not 1 <= tile <= 2346:
        raise ValueError("invalid derived tile")
    return FileLock(cache / ".locks" / f"tile_{tile}.lock", exclusive, timeout)


@contextmanager
def bundle_lock(cache, name, exclusive=False, timeout=100):
    tile = bundle_tile(name)
    with ExitStack() as stack:
        stack.enter_context(tile_lock(cache, tile, timeout=timeout))
        stack.enter_context(
            FileLock(cache / ".locks" / (name + ".lock"), exclusive, timeout)
        )
        folder = cache / name
        if linked(folder) or folder.resolve().parent != cache.resolve():
            raise ValueError("derived bundle escapes cache")
        yield folder


@contextmanager
def readonly_bundle_lock(cache, name, timeout=0):
    """Reuse existing producer locks without creating directories or files."""
    tile = bundle_tile(name)
    with ExitStack() as stack:
        stack.enter_context(FileLock(cache / '.locks' / f'tile_{tile}.lock', timeout=timeout, read_only=True))
        stack.enter_context(FileLock(cache / '.locks' / (name+'.lock'), timeout=timeout, read_only=True))
        folder = cache / name
        if linked(cache) or linked(folder) or folder.resolve().parent != cache.resolve():
            raise ValueError('read-only bundle escapes cache')
        yield folder


def file_records(folder):
    # One lstat per entry; never walk Windows reparse points or symlinks.
    records = []
    pending = [Path(folder)]
    while pending:
        current = pending.pop()
        with os.scandir(current) as entries:
            for entry in entries:
                stat = entry.stat(follow_symlinks=False)
                if entry.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                    continue
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    records.append((Path(entry.path), stat))
    return records


def files_in(folder):
    return [path for path, _ in file_records(folder)]


def mark_dirty(cache):
    cache = Path(cache)
    with FileLock(cache / ".locks/maintenance.lock", True):
        request = cache / "maintenance.request"
        if linked(request):
            raise ValueError("maintenance request cannot be a link")
        request.write_text(uuid.uuid4().hex, encoding="ascii")


def maintenance_token(cache):
    with FileLock(cache / ".locks/maintenance.lock", True):
        request = cache / "maintenance.request"
        if linked(request):
            raise ValueError("maintenance request cannot be a link")
        return request.read_bytes() if request.exists() else None


def maintain(cache):
    """No growth means no capacity scan. A protected overage stays pending."""
    cache = Path(cache)
    if not (cache / "maintenance.request").exists():
        status = cache / "prune_status.json"
        try:
            report = json.loads(status.read_text(encoding="utf-8"))
            if (
                isinstance(report, dict)
                and all(
                    type(report.get(key)) is int and report[key] >= 0
                    for key in ("limit_bytes", "remaining_bytes", "over_limit_bytes")
                )
                and report["over_limit_bytes"]
                == max(0, report["remaining_bytes"] - report["limit_bytes"])
                and report["over_limit_bytes"] == 0
            ):
                return {"skipped": "cache unchanged"}
        except (OSError, ValueError):
            pass  # Missing or invalid accounting is repaired by an actual scan.
    return prune(cache)


def remove_bundle(cache, folder):
    # Explicit names only. Unknown files and links are retained, never followed.
    if linked(folder) or folder.resolve().parent != cache.resolve():
        raise ValueError("refusing cache path outside owned root")
    for path in folder.iterdir():
        if linked(path):
            continue
        if path.is_file() and path.name in {
            "complete.json",
            "complete.pending.json",
            "rejected.json",
            "failure.json",
        }:
            path.unlink()
        elif path.is_dir() and re.fullmatch(r"part_\d{3}", path.name):
            for item in path.iterdir():
                if (
                    item.is_file()
                    and not linked(item)
                    and (
                        item.name
                        in {
                            "geometry.gltf",
                            "geometry.bin",
                            "atlas.jpg",
                            "source_list.txt",
                            "source_triangles.tsv",
                            "frontier.obj",
                            "frontier.mtl",
                        }
                        or re.fullmatch(r"texture_\d+\.rgb", item.name)
                    )
                ):
                    item.unlink()
            if not any(path.iterdir()):
                path.rmdir()
    if not any(folder.iterdir()):
        folder.rmdir()


def prune(cache, protected=None, limit=LIMIT):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    if limit < 0:
        raise ValueError("negative cache limit")
    try:
        guard = FileLock(cache / ".locks/prune.lock", True, 0)
    except TimeoutError:
        return {"skipped": "another prune is active"}
    with guard:
        request_token = maintenance_token(cache)
        records = []
        for folder in cache.iterdir():
            if (
                not folder.is_dir()
                or linked(folder)
                or not BUNDLE.fullmatch(folder.name)
            ):
                continue
            try:
                tile = bundle_tile(folder.name)
                files = file_records(folder)
                records.append(
                    (
                        max((stat.st_mtime for _, stat in files), default=0),
                        folder,
                        sum(stat.st_size for _, stat in files),
                        tile,
                    )
                )
            except (OSError, ValueError):
                continue
        total = sum(row[2] for row in records)
        before = total
        removed = []
        busy = []
        for _, folder, size, tile in sorted(records):
            if total <= limit:
                break
            if protected is not None and folder.resolve() == Path(protected).resolve():
                busy.append(folder.name)
                continue
            try:
                # Exclusive tile lock atomically excludes conversion, marker-to-read
                # handoff, native decode and every active web batch/file response.
                with tile_lock(cache, tile, True, 0):
                    remove_bundle(cache, folder)
                    remaining = (
                        sum(stat.st_size for _, stat in file_records(folder))
                        if folder.exists()
                        else 0
                    )
                    total -= size - remaining
                    if size != remaining:
                        removed.append(folder.name)
            except (OSError, TimeoutError):
                busy.append(folder.name)
        report = {
            "limit_bytes": limit,
            "before_bytes": before,
            "remaining_bytes": total,
            "over_limit_bytes": max(0, total - limit),
            "removed": removed,
            "protected": busy,
        }
        pending = cache / "prune_status.pending.json"
        pending.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        pending.replace(cache / "prune_status.json")
        if total <= limit:
            with FileLock(cache / ".locks/maintenance.lock", True):
                request = cache / "maintenance.request"
                if (
                    not linked(request)
                    and request.exists()
                    and request.read_bytes() == request_token
                ):
                    request.unlink()
        return report
