"""Verify source overlays against unchanged Spring Boot dependencies without running Spring.

The application main and class initializers are never invoked. Outputs can include
private class/resource names; keep the output folder outside source control.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

LOADER = 'org.springframework.boot.loader.PropertiesLauncher'
PROBE = 'xnby.audit.SourceClasspathProbe'
JAVA_INJECTION_KEYS = {'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH'}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def java_environment(source: dict[str, str], temp: Path) -> dict[str, str]:
    return {**{key: value for key, value in source.items()
               if not key.upper().startswith('LOADER_') and key.upper() not in JAVA_INJECTION_KEYS},
            'TEMP': str(temp), 'TMP': str(temp)}


def resource_name(value: str, *, is_class: bool = False) -> str:
    path = PurePosixPath(value)
    if not value or '\\' in value or '\t' in value or '\n' in value or '\r' in value:
        raise ValueError('Invalid resource name')
    if path.is_absolute() or ':' in value or any(part in ('', '.', '..') for part in value.split('/')):
        raise ValueError('Resource name must be a relative path without traversal')
    if is_class and not value.endswith('.class'):
        raise ValueError('Class resource must end in .class')
    return value


def snapshot(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def directory_entries(root: Path, *, classes: bool) -> list[tuple[str, str, str]]:
    rows = []
    for entry in sorted(root.rglob('*')):
        if entry.is_symlink():
            raise ValueError('Overlay symlinks are not supported')
        if not entry.is_file() or classes and entry.suffix != '.class':
            continue
        if not entry.resolve().is_relative_to(root):
            raise ValueError('Overlay file resolves outside its directory')
        name = resource_name(entry.relative_to(root).as_posix(), is_class=classes)
        rows.append(('C' if classes else 'R', name, sha256(entry)))
    return rows


def probe(args: argparse.Namespace) -> dict:
    runtime = args.runtime_jar.resolve(strict=True)
    java_home = args.java_home.resolve(strict=True)
    suffix = '.exe' if os.name == 'nt' else ''
    java, javac = (java_home / 'bin' / (name + suffix) for name in ('java', 'javac'))
    if not java.is_file() or not javac.is_file():
        raise ValueError('A complete JDK is required')
    if not args.runtime_sha256 or len(args.runtime_sha256) != 64 or any(c not in '0123456789abcdef' for c in args.runtime_sha256):
        raise ValueError('A lowercase runtime SHA-256 is required')
    if (args.overlay_classes is None) != (args.overlay_resources is None):
        raise ValueError('Specify both source classes and source resources, or neither')
    overlays = tuple(path.resolve(strict=True) for path in
                     (args.overlay_classes, args.overlay_resources) if path is not None)
    if any(not path.is_dir() for path in overlays):
        raise ValueError('Source overlays must be directories')
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError('Output must be a new directory')
    if any(output == path or output.is_relative_to(path) for path in overlays):
        raise ValueError('Output must not be inside a source overlay')
    source = Path(__file__).with_name('java') / 'SourceClasspathProbe.java'
    if not source.is_file():
        raise FileNotFoundError('Missing own Java probe source')
    before = snapshot(runtime)
    if sha256(runtime) != args.runtime_sha256:
        raise ValueError('Runtime SHA-256 mismatch; no Java process started')
    with zipfile.ZipFile(runtime) as archive:
        if LOADER.replace('.', '/') + '.class' not in archive.namelist():
            raise ValueError('Original runtime does not include PropertiesLauncher')
        if overlays:
            rows = directory_entries(overlays[0], classes=True) + directory_entries(overlays[1], classes=False)
        else:
            rows = [('C', resource_name(info.filename.removeprefix('BOOT-INF/classes/'), is_class=True),
                     hashlib.sha256(archive.read(info)).hexdigest())
                    for info in sorted(archive.infolist(), key=lambda info: info.filename)
                    if info.filename.startswith('BOOT-INF/classes/') and info.filename.endswith('.class')]
    if not rows or not any(row[0] == 'C' for row in rows):
        raise ValueError('No application classes to verify')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('Overlapping class and resource names are ambiguous')
    if before != snapshot(runtime):
        raise ValueError('Runtime changed during inspection')
    if any(row[1] == PROBE.replace('.', '/') + '.class' for row in rows):
        raise ValueError('Application must not shadow the own probe')
    for path in (output, *overlays):
        if ',' in path.as_uri():
            raise ValueError('Comma in loader path is not supported')
    output.mkdir(parents=True, exist_ok=False)
    compiled, temp = output / 'probe-classes', output / 'temp'
    compiled.mkdir()
    temp.mkdir()
    environment = java_environment(dict(os.environ), temp)
    spec, result = output / 'specification.tsv', output / 'result.tsv'
    spec.write_text(''.join('\t'.join(row) + '\n' for row in rows), encoding='utf-8')
    loader_config = output / 'empty-loader.properties'
    loader_config.write_text('', encoding='ascii')
    with (output / 'javac.log').open('wb') as log:
        compile_run = subprocess.run([str(javac), '--release', '8', '-encoding', 'UTF-8', '-d',
                                      str(compiled), str(source)], env=environment, cwd=output,
                                     stdout=log, stderr=subprocess.STDOUT, timeout=60)
    if compile_run.returncode:
        raise RuntimeError('Own probe compilation failed; inspect private javac.log')
    loader_paths = ','.join(path.as_uri().rstrip('/') + '/' for path in (compiled, *overlays))
    command = [str(java), '-Dfile.encoding=UTF-8', '-Djava.io.tmpdir=' + str(temp),
               '-Dloader.config.location=' + loader_config.as_uri(), '-Dloader.path=' + loader_paths,
               '-Dloader.main=' + PROBE, '-cp', str(runtime), LOADER, str(spec), str(result)]
    with (output / 'launcher.log').open('wb') as log:
        run = subprocess.run(command, env=environment, cwd=output, stdout=log,
                             stderr=subprocess.STDOUT, timeout=180)
    parsed = [line.split('\t') for line in result.read_text(encoding='utf-8').splitlines()] if result.exists() else []
    exact_results = len(parsed) == len(rows) and all(len(got) == 4 and got[:2] == list(expected[:2])
                                                   for got, expected in zip(parsed, rows))
    passed = sum(len(row) == 4 and row[2] == 'PASS' for row in parsed)
    runtime_stable = before == snapshot(runtime)
    report = {'recordedAt': datetime.now(timezone.utc).isoformat(), 'runtimeSHA256': args.runtime_sha256,
              'probeSourceSHA256': sha256(source), 'exitCode': run.returncode,
              'expectedEntries': len(rows), 'classes': sum(row[0] == 'C' for row in rows),
              'resources': sum(row[0] == 'R' for row in rows), 'passed': passed,
              'exactResultRows': exact_results, 'runtimeStable': runtime_stable,
              'success': run.returncode == 0 and exact_results and passed == len(rows) and runtime_stable,
              'applicationMainInvoked': False, 'classInitializationRequested': False,
              'runtimeJarCopied': False, 'businessParityVerified': False,
              'limitations': 'Checks selected bytes and reflection linkage only; excludes application startup and business behavior.'}
    (output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--runtime-jar', type=Path, required=True)
    parser.add_argument('--runtime-sha256', required=True)
    parser.add_argument('--overlay-classes', type=Path)
    parser.add_argument('--overlay-resources', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = probe(args)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, zipfile.BadZipFile) as error:
        print(json.dumps({'success': False, 'errorType': type(error).__name__,
                          'message': str(error) if isinstance(error, (ValueError, RuntimeError)) else 'See private output or verify input paths.'}))
        return 2
    print(json.dumps(report))
    return 0 if report['success'] else 4


if __name__ == '__main__':
    sys.exit(main())
