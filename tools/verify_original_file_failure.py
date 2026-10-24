"""Observe unchanged original file-service error handling against an owned failing HTTP fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile


def verify(workspace, output):
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('FRESH_OUTPUT_REQUIRED')
    flat = workspace / 'original-shared-runtime-r1_20261024/flat'
    meta = json.loads((flat / 'receipt.json').read_bytes())
    jar = flat / 'application.jar'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if meta['applicationJarSHA256'] != 'c4637e950664ff2ee26746b80366ca12e8c1f36f69288d35e126871f9afe30ae' or sha(jar) != meta['applicationJarSHA256']:
        raise ValueError('ORIGINAL_FLAT_JAR_PIN_MISMATCH')
    for row in meta['dependencies']:
        path = flat / row['relativePath']
        if not path.is_file() or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('ORIGINAL_DEPENDENCY_PIN_MISMATCH')
    class_names = ('com/iemp/endanger/minio/MinioConfig.class', 'com/iemp/endanger/minio/MinioUtil.class', 'com/iemp/endanger/server/file/service/impl/SysFileServiceImpl.class')
    rows = {r['file']: r for r in meta['applicationEntries']}
    with zipfile.ZipFile(jar) as archive:
        pins = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in class_names}
    if any(pins[name] != rows[name]['sha256'] for name in class_names):
        raise ValueError('ORIGINAL_FILE_CLASS_PIN_MISMATCH')
    dbmeta = json.loads((workspace / 'own-mysql-r13/fixture_compile.json').read_bytes())
    boundary = Path(dbmeta['boundaryJar'])
    if sha(boundary) != dbmeta['boundaryJarSHA256'] or sha(boundary) != '3f5b36ef4a48714a0424b7470d7a1aecf7bd1beb385a4843fd08adc02bd16bb9':
        raise ValueError('EXISTING_PROCESS_BOUNDARY_PIN_MISMATCH')
    java = Path(json.loads((workspace / 'own-pboot-r32/preparation.json').read_bytes())['javaHome'])
    here = Path(__file__).resolve().parent
    source = here / 'java/OriginalFileFailureFixture.java'
    if not source.is_file():
        raise ValueError('EXPLICIT_OWN_FIXTURE_SOURCE_REQUIRED')
    env = {k: v for k, v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS', 'CLASSPATH') and not k.upper().startswith(('LOADER_', 'MINIO_'))}
    output.mkdir(parents=True); classes = output / 'classes'; classes.mkdir(); allowed = output / 'allowed'; allowed.mkdir()
    config = output / 'own-logback.xml'
    config.write_text('<configuration><root level="OFF"/></configuration>', encoding='ascii')

    def run(command, name):
        result = subprocess.run(list(map(str, command)), cwd=output, env=env, capture_output=True, timeout=30,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / (name + '.private.log')).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('ORIGINAL_FILE_' + name.upper() + '_FAILED')
        return result.stdout

    run([java / 'bin/javac.exe', '-proc:none', '-encoding', 'UTF-8', '-cp', os.pathsep.join(map(str, (boundary, jar))), '-d', classes, source], 'compile')
    raw = run([java / 'bin/java.exe', '-Xmx128m', '-Dlogback.configurationFile=' + str(config), '-Djava.io.tmpdir=' + str(allowed),
               '-cp', os.pathsep.join(map(str, (classes, boundary, jar))), 'xnby.replica.OriginalFileFailureFixture', allowed, jar], 'fixture')
    prefix = b'ORIGINAL_FILE_FAILURE_OBSERVATION '
    result = json.loads(next(line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)))
    if result['passedChecks'] != 19 or result['ownedFailureHTTPRequests'] < 4 or result['objectPUTRequests'] != 0:
        raise RuntimeError('ORIGINAL_FILE_OBSERVATION_INCOMPLETE')
    result.update(originalFileClassSHA256=pins, originalFlatJarSHA256=sha(jar), originalDependencyCount=len(meta['dependencies']),
                  unchangedProcessBoundaryJarSHA256=sha(boundary), fixtureSourceSHA256=sha(source),
                  fixtureProcessExited0=True, fullCloneReady=False)
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(verify(a.workspace, a.output)))


if __name__ == '__main__':
    main()
