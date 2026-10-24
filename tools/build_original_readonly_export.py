"""Build the own bounded JDBC export GUI without starting it or connecting to a DB.

Dependencies are read from an explicitly SHA-pinned existing original platform jar.
Configuration and generated artifacts remain private, outside source control.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile

JAVA_SOURCES = ('ReadOnlyDatabaseExport.java', 'ReadOnlyExportPreflight.java', 'ReadOnlyExportSelfTest.java')
DEPENDENCIES = ('mysql-connector-j-8.0.33.jar', 'snakeyaml-2.2.jar')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-home', required=True, type=Path)
    parser.add_argument('--platform-jar', required=True, type=Path)
    parser.add_argument('--platform-sha256', required=True)
    parser.add_argument('--source-config', required=True, type=Path)
    parser.add_argument('--source-config-sha256', required=True)
    parser.add_argument('--source-host', required=True)
    parser.add_argument('--remote-config', required=True)
    parser.add_argument('--remote-export-root', required=True)
    parser.add_argument('--existing-runtime-image', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if os.name != 'nt':
        raise ValueError('This recipe packages a Windows GUI')
    jdk, platform, config = (path.resolve(strict=True) for path in (args.java_home, args.platform_jar, args.source_config))
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError('Output must be new; inspect interrupted builds before retrying')
    if output.is_relative_to(Path(__file__).resolve().parent):
        raise ValueError('Generated runtime and private configuration must stay outside the tools source tree')
    for value in (args.remote_config, args.remote_export_root):
        if not value or any(char.isspace() or char in '\"\r\n' for char in value):
            raise ValueError('Remote launcher paths must have no whitespace or quotes')
    if config.stat().st_size > 65536 or sha(config) != args.source_config_sha256.lower():
        raise ValueError('Source configuration SHA or size mismatch')
    before = platform.stat()
    if sha(platform) != args.platform_sha256.lower():
        raise ValueError('Original platform SHA mismatch')
    if shutil.disk_usage(output.parent).free < 1024**3:
        raise ValueError('Keep at least 1 GiB free for bounded packaging')
    own_sources = Path(__file__).with_name('java') / 'xnby/export'
    sources = [own_sources / name for name in JAVA_SOURCES]
    if not all(path.is_file() for path in sources):
        raise FileNotFoundError('Missing own Java sources')
    runtime = args.existing_runtime_image.resolve(strict=True) if args.existing_runtime_image else None
    if runtime and not (runtime / 'bin/java.exe').is_file():
        raise ValueError('Explicit runtime image is incomplete')
    output.mkdir(parents=True, exist_ok=False)
    input_root, classes, temp = (output / name for name in ('input', 'classes', 'temp'))
    for path in (input_root, classes, temp):
        path.mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if not key.upper().startswith('LOADER_') and key.upper() not in
                   ('JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH')}
    environment['TEMP'] = environment['TMP'] = str(temp)
    dependency_receipts = []
    with zipfile.ZipFile(platform) as archive:
        for name in DEPENDENCIES:
            info = archive.getinfo('BOOT-INF/lib/' + name)
            if info.file_size > 4 * 1024**2:
                raise ValueError('Unexpected dependency size')
            target = input_root / name
            target.write_bytes(archive.read(info))
            dependency_receipts.append({'name': name, 'sha256': sha(target), 'bytes': target.stat().st_size})
    after = platform.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Platform changed during dependency read')

    def run(label, command, timeout=180):
        with (output / (label + '.log')).open('wb') as stream:
            result = subprocess.run(list(map(str, command)), cwd=output, env=environment,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            raise RuntimeError(label + ' failed; inspect the private build log')

    cp = os.pathsep.join(str(input_root / name) for name in DEPENDENCIES)
    run('javac', [jdk / 'bin/javac.exe', '--release', '17', '-encoding', 'UTF-8', '-cp', cp, '-d', classes, *sources])
    run('self_tests', [jdk / 'bin/java.exe', '-Xmx256m', '-Djava.awt.headless=true', '-Dfile.encoding=UTF-8',
                       '-cp', str(classes) + os.pathsep + cp, 'xnby.export.ReadOnlyExportSelfTest'])
    expected = 'SELF_TESTS_PASSED=34 realDatabaseConnections=0 sourceWrites=0'
    if expected not in (output / 'self_tests.log').read_text(encoding='utf-8'):
        raise RuntimeError('Own fixture coverage was not verified')
    run('config_preflight', [jdk / 'bin/java.exe', '-Xmx128m', '-Djava.awt.headless=true', '-Dfile.encoding=UTF-8',
                            '-cp', str(classes) + os.pathsep + cp, 'xnby.export.ReadOnlyExportPreflight', config, args.source_host])
    if 'sourceConfigSHA256=' + args.source_config_sha256.lower() not in (output / 'config_preflight.log').read_text(encoding='utf-8'):
        raise RuntimeError('Original configuration preflight was not verified')
    run('jar', [jdk / 'bin/jar.exe', '--create', '--file', input_root / 'ReadOnlyExport.jar', '-C', classes, '.'])
    if runtime is None:
        runtime = output / 'runtime-staging'
        run('jlink', [jdk / 'bin/jlink.exe', '--module-path', jdk / 'jmods', '--add-modules',
                      'java.desktop,java.sql,java.naming,java.management,java.security.jgss,jdk.crypto.ec,jdk.charsets,jdk.unsupported',
                      '--strip-debug', '--no-header-files', '--no-man-pages', '--compress=2', '--output', runtime])
    arguments = ' '.join((args.remote_config, args.source_host, args.remote_export_root, args.source_config_sha256.lower()))
    run('jpackage', [jdk / 'bin/jpackage.exe', '--type', 'app-image', '--input', input_root,
                     '--dest', output / 'image', '--name', 'TianjinReadOnlyExport', '--main-jar', 'ReadOnlyExport.jar',
                     '--main-class', 'xnby.export.ReadOnlyDatabaseExport', '--runtime-image', runtime,
                     '--java-options', '-Xmx256m', '--java-options', '-Dfile.encoding=UTF-8', '--arguments', arguments])
    image = output / 'image/TianjinReadOnlyExport'
    packaged_cp = os.pathsep.join(str(image / 'app' / name) for name in ('ReadOnlyExport.jar', *DEPENDENCIES))
    run('packaged_self_tests', [image / 'runtime/bin/java.exe', '-Xmx256m', '-Djava.awt.headless=true',
                               '-Dfile.encoding=UTF-8', '-cp', packaged_cp, 'xnby.export.ReadOnlyExportSelfTest'])
    if expected not in (output / 'packaged_self_tests.log').read_text(encoding='utf-8'):
        raise RuntimeError('Packaged runtime fixtures failed')
    files = [{'path': path.relative_to(image).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)}
             for path in sorted(image.rglob('*')) if path.is_file()]
    receipt = {'recordedAt': datetime.now(timezone.utc).isoformat(), 'platformSHA256': args.platform_sha256.lower(),
               'sourceConfigSHA256': args.source_config_sha256.lower(), 'dependencies': dependency_receipts,
               'ownSources': [{'name': path.name, 'sha256': sha(path)} for path in sources], 'files': files,
               'ownTests': 34, 'packagedRuntimeTests': 34, 'imageBytes': sum(row['bytes'] for row in files),
               'guiStarted': False, 'realDatabaseConnections': 0, 'originalDatabaseExportPerformed': False,
               'exportRestoreVerified': False, 'fullCloneReady': False}
    (output / 'build_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'imageRoot': str(image), 'imageBytes': receipt['imageBytes'], 'tests': 34,
                      'realDatabaseConnections': 0, 'guiStarted': False}))


if __name__ == '__main__':
    main()
