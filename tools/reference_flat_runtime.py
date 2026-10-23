"""Package original BOOT-INF/classes as a standard JAR, reusing exact dependency files.

No Java class is executed and no dependency or business database is downloaded.
The output is a private runtime artifact, not source suitable for Git publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from urllib.parse import quote
import zipfile

APP_PREFIX = "BOOT-INF/classes/"
LIB_PREFIX = "BOOT-INF/lib/"
MAX_APPLICATION_BYTES = 128 * 1024 * 1024


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_values(data: bytes) -> dict[str, str]:
    unfolded: list[bytes] = []
    for line in data.replace(b"\r\n", b"\n").split(b"\n"):
        if line.startswith(b" "):
            if not unfolded:
                raise ValueError("MANIFEST_CONTINUATION_WITHOUT_HEADER")
            unfolded[-1] += line[1:]
        elif not line:
            if unfolded:
                break
        else:
            unfolded.append(line)
    return dict(line.decode("utf-8").split(": ", 1) for line in unfolded)


def manifest_bytes(values: dict[str, str]) -> bytes:
    output: list[bytes] = []
    for key, value in values.items():
        if any(c in key + value for c in "\r\n\x00"):
            raise ValueError("MANIFEST_CONTROL_CHARACTER")
        raw = (key + ": " + value).encode("utf-8")
        # URI values are ASCII; limit each physical line including CRLF to 72 bytes.
        output.append(raw[:70]); raw = raw[70:]
        while raw:
            output.append(b" " + raw[:69]); raw = raw[69:]
    return b"\r\n".join(output) + b"\r\n\r\n"


def safe_member(name: str) -> None:
    parts = PurePosixPath(name)
    if not name or name.startswith("/") or "\\" in name or ":" in name or ".." in parts.parts:
        raise ValueError("UNSAFE_ARCHIVE_MEMBER")


def package_directories(names: list[str]) -> list[str]:
    """Explicit directory entries are required by classpath package/resource scanners."""
    directories = {"META-INF/"}
    for name in names:
        parent = PurePosixPath(name).parent
        while str(parent) != ".":
            directories.add(parent.as_posix() + "/")
            parent = parent.parent
    return sorted(directories)


def inspect_source(source: zipfile.ZipFile) -> tuple[list[zipfile.ZipInfo], list[zipfile.ZipInfo], str]:
    entries = source.infolist()
    names = [e.filename for e in entries]
    if len(names) != len(set(names)):
        raise ValueError("DUPLICATE_SOURCE_MEMBER")
    applications = [e for e in entries if e.filename.startswith(APP_PREFIX) and not e.is_dir()]
    libraries = [e for e in entries if e.filename.startswith(LIB_PREFIX) and not e.is_dir()]
    if not applications or not libraries or len(applications) > 100000:
        raise ValueError("UNEXPECTED_SOURCE_LAYOUT")
    if sum(e.file_size for e in applications) > MAX_APPLICATION_BYTES:
        raise ValueError("APPLICATION_SIZE_LIMIT")
    for entry in applications:
        name = entry.filename[len(APP_PREFIX):]; safe_member(name)
        if name.casefold() == "meta-inf/manifest.mf":
            raise ValueError("APPLICATION_MANIFEST_COLLISION")
    library_names: set[str] = set()
    for entry in libraries:
        name = entry.filename[len(LIB_PREFIX):]; safe_member(name)
        if "/" in name or not name.endswith(".jar") or name.casefold() in library_names:
            raise ValueError("UNEXPECTED_DEPENDENCY_MEMBER")
        library_names.add(name.casefold())
    main = manifest_values(source.read("META-INF/MANIFEST.MF")).get("Start-Class")
    if not main or main.replace(".", "/") + ".class" not in {e.filename[len(APP_PREFIX):] for e in applications}:
        raise ValueError("SOURCE_START_CLASS_MISSING")
    return applications, libraries, main


def build(source_jar: Path, dependency_dir: Path, output_dir: Path, expected_source_sha256: str) -> dict:
    source_jar = source_jar.resolve(strict=True)
    dependency_dir = dependency_dir.resolve(strict=True)
    output_dir = output_dir.absolute()
    if output_dir.exists():
        raise FileExistsError("OUTPUT_DIRECTORY_EXISTS")
    if file_sha256(source_jar) != expected_source_sha256:
        raise ValueError("SOURCE_ARCHIVE_HASH_DIFFERS")
    with zipfile.ZipFile(source_jar) as source:
        applications, libraries, main = inspect_source(source)
        app_records: list[dict] = []; dependency_records: list[dict] = []
        for entry in libraries:
            name = entry.filename[len(LIB_PREFIX):]
            local = dependency_dir / name
            if not local.is_file() or local.resolve().parent != dependency_dir:
                raise ValueError("DEPENDENCY_NOT_IN_EXPECTED_DIRECTORY")
            original_digest = bytes_sha256(source.read(entry))
            if file_sha256(local) != original_digest:
                raise ValueError("DEPENDENCY_BYTES_DIFFER")
            relative = os.path.relpath(local, output_dir).replace(os.sep, "/")
            dependency_records.append({"file": name, "relativePath": relative, "manifestURI": quote(relative, safe="/._-"),
                "sourceEntry": entry.filename, "bytes": local.stat().st_size, "sha256": original_digest})
        manifest = manifest_bytes({"Manifest-Version": "1.0", "Main-Class": main,
            "Class-Path": " ".join(r["manifestURI"] for r in dependency_records),
            "Created-By": "XNBY original-source flat runtime packager",
            "Source-Archive-SHA256": expected_source_sha256})
        output_dir.mkdir(parents=False)
        try:
            target = output_dir / "application.jar"
            with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED) as flat:
                def add(name: str, data: bytes) -> None:
                    info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                    if name.endswith("/"):
                        info.compress_type = zipfile.ZIP_STORED; info.external_attr = (0o40755 << 16) | 0x10
                    flat.writestr(info, data)
                add("META-INF/MANIFEST.MF", manifest)
                directories = package_directories([entry.filename[len(APP_PREFIX):] for entry in applications])
                for name in directories:
                    add(name, b"")
                for entry in applications:
                    name = entry.filename[len(APP_PREFIX):]; data = source.read(entry)
                    add(name, data)
                    app_records.append({"file": name, "sourceEntry": entry.filename, "bytes": len(data), "sha256": bytes_sha256(data)})
            receipt = {"sourceArchive": str(source_jar), "sourceArchiveSHA256": expected_source_sha256,
                "applicationJar": target.name, "applicationJarSHA256": file_sha256(target), "applicationJarBytes": target.stat().st_size,
                "mainClass": main, "applicationEntries": app_records, "applicationEntryCount": len(app_records),
                "compiledClassCount": sum(r["file"].endswith(".class") for r in app_records),
                "resourceCount": sum(not r["file"].endswith(".class") for r in app_records),
                "explicitPackageAndResourceDirectories": directories,
                "dependencies": dependency_records, "dependencyCount": len(dependency_records),
                "originalEntryOrderPreserved": True, "dependencyFilesCopied": 0, "businessClassBytesChanged": False,
                "originalConfigurationBytesChanged": False, "originalApplicationExecuted": False,
                "sourceCredentialsInventoriedOrPrinted": False, "privateRuntimeArtifact": True,
                "databaseOrBusinessParityVerified": False, "publicOrGitUpload": False}
            (output_dir / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            verify(output_dir)
            return receipt
        except Exception:
            # Retain a partial output for diagnosis, refuse overwrite/retry into this directory.
            raise


def verify(output_dir: Path) -> dict:
    output_dir = output_dir.resolve(strict=True)
    r = json.loads((output_dir / "receipt.json").read_text(encoding="utf-8"))
    source_path = Path(r["sourceArchive"])
    if file_sha256(source_path) != r["sourceArchiveSHA256"] or file_sha256(output_dir / r["applicationJar"]) != r["applicationJarSHA256"]:
        raise ValueError("RUNTIME_OR_SOURCE_HASH_DIFFERS")
    with zipfile.ZipFile(source_path) as source, zipfile.ZipFile(output_dir / r["applicationJar"]) as flat:
        apps, libs, main = inspect_source(source)
        if main != r["mainClass"] or len(apps) != r["applicationEntryCount"] or len(libs) != r["dependencyCount"]:
            raise ValueError("RUNTIME_LAYOUT_DIFFERS")
        directories = package_directories([e.filename[len(APP_PREFIX):] for e in apps])
        expected_names = ["META-INF/MANIFEST.MF", *directories, *[e.filename[len(APP_PREFIX):] for e in apps]]
        if flat.namelist() != expected_names:
            raise ValueError("RUNTIME_MEMBERS_DIFFER")
        if any(not flat.getinfo(name).is_dir() for name in directories):
            raise ValueError("CLASSPATH_PACKAGE_DIRECTORIES_MISSING")
        for entry in apps:
            if source.read(entry) != flat.read(entry.filename[len(APP_PREFIX):]):
                raise ValueError("APPLICATION_BYTES_DIFFER")
        for entry, dep in zip(libs, r["dependencies"]):
            actual = (output_dir / dep["relativePath"]).resolve(strict=True)
            if dep["sourceEntry"] != entry.filename or file_sha256(actual) != bytes_sha256(source.read(entry)):
                raise ValueError("DEPENDENCY_BYTES_DIFFER")
        manifest = manifest_values(flat.read("META-INF/MANIFEST.MF"))
        if manifest.get("Main-Class") != main or manifest.get("Class-Path") != " ".join(dep["manifestURI"] for dep in r["dependencies"]):
            raise ValueError("RUNTIME_MANIFEST_DIFFERS")
    return {"applicationEntryCount": len(apps), "dependencyCount": len(libs), "allOriginalApplicationAndDependencyBytesEqual": True,
        "originalApplicationExecuted": False, "databaseOrBusinessParityVerified": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("build"); create.add_argument("--source", type=Path, required=True)
    create.add_argument("--dependencies", type=Path, required=True); create.add_argument("--output", type=Path, required=True)
    create.add_argument("--source-sha256", required=True)
    check = sub.add_parser("verify"); check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source, args.dependencies, args.output, args.source_sha256) if args.command == "build" else verify(args.output)
    print(json.dumps({k: result[k] for k in ("compiledClassCount", "resourceCount", "dependencyCount", "applicationJarBytes")}
        if args.command == "build" else result, ensure_ascii=False))


if __name__ == "__main__":
    main()
