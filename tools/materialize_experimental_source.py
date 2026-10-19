"""Materialize SHA-pinned experimental sources without touching the working tree.

This prepares source only. It does not build/run executables, start servers,
convert scene assets, install runtimes, or select a default release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OVERLAYS = ROOT / "tools/experimental_source"
NAMES = ("native_readonly_depth", "osgb_readonly_roi", "native_readonly_crop", "osgb_readonly_stdio")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_name(value):
    if (not isinstance(value, str) or not value.isascii() or "\\" in value or ":" in value
            or not (value.startswith("native/") or value.startswith("tools/osgb_stream_reader/"))
            or any(p in ("", ".", "..") for p in value.split("/")) or PurePosixPath(value).is_absolute()):
        raise ValueError("invalid source-only overlay path")
    return value


def materialize(name, output, base_ref="HEAD"):
    if name not in NAMES or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,127}", base_ref):
        raise ValueError("invalid overlay or base revision")
    output = Path(output)
    output = (ROOT / output).absolute() if not output.is_absolute() else output.absolute()
    work = ROOT / "work"
    if not output.resolve().is_relative_to(work.resolve()) or output.resolve() == work.resolve():
        raise ValueError("output must be a new directory beneath project work/")
    for ancestor in [work, *reversed(output.parents)]:
        if ancestor.exists() and ancestor.is_relative_to(work):
            info = ancestor.lstat()
            if ancestor.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("linked output parents are forbidden")
    if output.exists():
        raise FileExistsError("never overwrite an existing source candidate")
    manifest = json.loads((OVERLAYS / (name + ".json")).read_text("utf-8"))
    if (manifest.get("schema") != "zhumadian.experimental_source_overlay.v1" or manifest.get("name") != name
            or manifest.get("patch") != name + ".patch" or manifest.get("dataFilesIncluded") is not False):
        raise ValueError("invalid experimental source manifest")
    base, target = manifest["baseFiles"], manifest["targetFiles"]
    if not base or not target or max(len(base), len(target)) > 64:
        raise ValueError("invalid source file count")
    for path, identity in [*base.items(), *target.items()]:
        source_name(path)
        if not re.fullmatch(r"[0-9a-f]{64}", identity):
            raise ValueError("invalid source SHA256")
    patch = (OVERLAYS / manifest["patch"]).read_bytes()
    if len(patch) > 1048576 or digest(patch) != manifest["patchSHA256"]:
        raise ValueError("source overlay patch changed")
    for header in re.findall(rb"(?m)^(?:---|\+\+\+) ([^\r\n]+)", patch):
        if header == b"/dev/null":
            continue
        path = header.decode("ascii")
        if path[:2] not in ("a/", "b/") or source_name(path[2:]) not in set(base) | set(target):
            raise ValueError("patch path outside declared source set")
    normalized, crlf = manifest["normalizeBaseLF"], manifest["restoreTargetCRLF"]
    if not set(normalized) <= set(base) or not set(crlf) <= set(target):
        raise ValueError("invalid line-ending recipe")
    # Keep the private scratch tree for diagnosis; never recursively delete project paths.
    scratch = Path(tempfile.mkdtemp(prefix="zhumadian_source_overlay_"))
    for path, identity in base.items():
        raw = subprocess.check_output(["git", "cat-file", "blob", base_ref + ":" + path], cwd=ROOT)
        if len(raw) > 8 * 1048576 or digest(raw) != identity:
            raise ValueError("base committed source identity differs: " + path)
        if path in normalized:
            raw = raw.replace(b"\r\n", b"\n")
            if b"\r" in raw:
                raise ValueError("unsupported mixed source newline recipe")
        destination = scratch / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    patch_file = scratch / "overlay.patch"
    patch_file.write_bytes(patch)
    environment = {**os.environ, "GIT_CEILING_DIRECTORIES": str(scratch.parent),
                   "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    for check in (True, False):
        command = ["git", "apply", *(["--check"] if check else []), str(patch_file)]
        subprocess.run(command, cwd=scratch, env=environment, check=True, capture_output=True)
    patch_file.unlink()  # This exact source-only scratch file was created above, never a computed tree deletion.
    actual = {p.relative_to(scratch).as_posix() for p in scratch.rglob("*") if p.is_file()}
    if actual != set(target):
        raise ValueError("unexpected materialized source file set")
    values = {}
    for path, identity in target.items():
        raw = (scratch / path).read_bytes()
        if path in crlf:
            if b"\r" in raw:
                raise ValueError("target newline recipe already applied")
            raw = raw.replace(b"\n", b"\r\n")
        if digest(raw) != identity:
            raise ValueError("materialized source differs from tested candidate: " + path)
        values[path] = raw
    output.mkdir(parents=True, exist_ok=False)
    for path, raw in values.items():
        destination = output / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(raw)
    return {"overlay": name, "sourceFiles": len(values), "sourceOnly": True, "baseRef": base_ref,
            "output": str(output), "scratchPreserved": str(scratch), "targetSHA256": target}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", choices=NAMES, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-ref", default="HEAD")
    options = parser.parse_args()
    print(json.dumps(materialize(options.overlay, options.output, options.base_ref), indent=2))


if __name__ == "__main__":
    main()
