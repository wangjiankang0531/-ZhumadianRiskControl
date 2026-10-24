"""Audit pinned platform storage topology and exercise unchanged local storage across JVMs."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile
import uuid

SOURCE_PIN = '294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8'
YAML_PIN = '1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b'
GUARD_PIN = '799d1289e3122b0e73ef4b6a3c9639bc5c59d820c7670800c673a1b7acd5a508'


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(workspace, candidate, output, connection):
    workspace, candidate, output = map(lambda p: Path(p).resolve(), (workspace, candidate, output))
    app = workspace.parents[1]
    require(app.name == 'Application' and (app / 'tools/reference_flat_runtime.py').is_file(), 'KNOWN_WORKSPACE_REQUIRED')
    require(not output.exists() and output.is_relative_to(workspace), 'FRESH_OWN_OUTPUT_REQUIRED')
    require(candidate.is_relative_to(workspace) and candidate.is_file() and candidate.stat().st_size <= 256 * 1024, 'BOUNDED_OWN_CANDIDATE_REQUIRED')
    meta = json.loads((workspace / 'own-pboot-r32/preparation.json').read_bytes())
    archive = Path(meta['sourceArchive'])
    # Windows drive mappings may differ between elevation contexts; use the already mapped share identity.
    if not archive.is_file():
        archive = Path('//192.168.0.107/Fofme/TJZY/home/tjng/ap/opm-service-admin-3.6.0.jar')
    require(meta['sourceJarSHA256'] == SOURCE_PIN and sha(archive) == SOURCE_PIN, 'ORIGINAL_ARCHIVE_PIN_MISMATCH')
    java, java8 = Path(meta['javaHome']), Path(meta['platformJavaHome'])
    yaml, guard = Path(meta['yamlJar']), Path(meta['guardJar'])
    require(sha(yaml) == YAML_PIN and sha(guard) == GUARD_PIN, 'YAML_OR_PLATFORM_JAVA8_GUARD_PIN_MISMATCH')
    for name, pin in meta['platformRuntimePins'].items():
        require(sha(java8 / name) == pin, 'EXISTING_JAVA8_RUNTIME_PIN_MISMATCH')
    deps = []
    for row in meta['compileDependencies']:
        require(sha(row['file']) == row['sha256'], 'COMPILE_DEPENDENCY_PIN_MISMATCH')
        deps.append(Path(row['file']))
    before = sha(candidate)
    connection = Path(connection).resolve()
    require(connection.is_relative_to(workspace) and connection.is_file() and connection.stat().st_size <= 4096, 'EXPLICIT_BOUNDED_OWN_CONNECTION_REQUIRED')
    connection_pin = sha(connection)
    output.mkdir()
    for folder in ('classes', 'deps', 'synthetic'):
        (output / folder).mkdir()
    owner = str(uuid.uuid4())
    (output / 'synthetic/owner.json').write_text(json.dumps({'schema': 'xnby.synthetic.platform-storage.v1', 'ownerId': owner}), encoding='ascii')
    selected = ['jnpf-file-core-starter-3.6.0-RELEASE.jar', 'hutool-all-5.8.22.jar', 'slf4j-api-1.7.36.jar', 'thumbnailator-0.4.17.jar', 'spring-webmvc-5.3.31.jar']
    original_deps, original_classes = [], {}
    with zipfile.ZipFile(archive) as zipped:
        for name in selected:
            entry = zipped.getinfo('BOOT-INF/lib/' + name)
            require(0 < entry.file_size < 4 * 1024**2, 'BOUNDED_ORIGINAL_DEPENDENCY_REQUIRED')
            raw = zipped.read(entry)
            path = output / 'deps' / name
            path.write_bytes(raw)
            deps.append(path)
            original_deps.append({'entry': entry.filename, 'bytes': len(raw), 'sha256': sha(path)})
    with zipfile.ZipFile(output / 'deps' / selected[0]) as original:
        for name in ('FileStorageService', 'FileInfo', 'UploadPretreatment', 'platform/LocalPlusFileStorage'):
            original_classes[name] = hashlib.sha256(original.read('cn/xuyanwu/spring/file/storage/' + name + '.class')).hexdigest()
    here = Path(__file__).resolve().parent
    sources = [here / 'java' / name for name in ('OriginalBusinessConfigInventory.java', 'OriginalPlatformStorageInventory.java', 'OriginalPlatformLocalStorageFixture.java', 'PlatformStorageInventoryFixture.java', 'OriginalPlatformStorageOverlay.java', 'PlatformStorageOverlayFixture.java', 'PlatformStorageBindingFixture.java')]
    env = {k: v for k, v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS', 'CLASSPATH')}
    env['TMP'] = env['TEMP'] = str(output / 'synthetic')
    cp = os.pathsep.join(map(str, [output / 'classes', guard, yaml, *deps]))

    def run(command, name):
        result = subprocess.run(list(map(str, command)), cwd=output / 'synthetic', env=env, capture_output=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / (name + '.private.log')).write_bytes(result.stdout + result.stderr)
        require(result.returncode == 0, 'ORIGINAL_PLATFORM_STORAGE_' + name.upper() + '_FAILED')
        return result.stdout

    run([java / 'bin/javac.exe', '-proc:none', '--release', '8', '-encoding', 'UTF-8', '-cp', cp, '-d', output / 'classes', *sources], 'compile')
    fixture = run([java8 / 'bin/java.exe', '-Xmx64m', '-cp', cp, 'xnby.replica.PlatformStorageInventoryFixture'], 'topology-fixture')
    require(b'PLATFORM_STORAGE_INVENTORY_CHECKS=12' in fixture, 'TOPOLOGY_FIXTURE_INCOMPLETE')
    run([java8 / 'bin/java.exe', '-Xmx64m', '-cp', cp, 'xnby.replica.OriginalPlatformStorageInventory', archive, candidate, output / 'topology.properties'], 'topology')
    fixture = run([java8 / 'bin/java.exe', '-Xmx64m', '-cp', cp, 'xnby.replica.PlatformStorageOverlayFixture', output / 'synthetic'], 'overlay-fixture')
    require(b'PLATFORM_STORAGE_OVERLAY_CHECKS=23' in fixture, 'OVERLAY_FIXTURE_INCOMPLETE')
    (output / 'prepared-local-files').mkdir()
    prepared = output / 'prepared-application.private.properties'
    run([java8 / 'bin/java.exe', '-Xmx64m', '-cp', cp, 'xnby.replica.OriginalPlatformStorageOverlay', archive, candidate, connection, output / 'prepared-local-files', prepared], 'prepare-overlay')
    run([java8 / 'bin/java.exe', '-Xmx64m', '-cp', cp, 'xnby.replica.OriginalPlatformStorageInventory', archive, prepared, output / 'prepared-topology.properties'], 'prepared-topology')
    binding = run([java8 / 'bin/java.exe', '-Xmx96m', '-Dfile.encoding=UTF-8', '-Djava.io.tmpdir=' + str(output / 'prepared-local-files'), '-cp', cp, 'xnby.replica.PlatformStorageBindingFixture', prepared], 'original-binding-and-factory')
    require(b'PLATFORM_STORAGE_BINDING_CHECKS=23' in binding, 'ACTUAL_ORIGINAL_BINDING_CHECK_COUNT')
    phases = []
    for phase, count in (('write', 28), ('read-delete', 22)):
        raw = run([java8 / 'bin/java.exe', '-Xmx96m', '-Dfile.encoding=UTF-8', '-Djava.io.tmpdir=' + str(output / 'synthetic'), '-cp', cp, 'xnby.replica.OriginalPlatformLocalStorageFixture', output / 'synthetic', phase], phase)
        require(('ORIGINAL_LOCAL_STORAGE_CHECKS=' + str(count)).encode() in raw, 'ORIGINAL_STORAGE_PHASE_CHECK_COUNT')
        phases.append({'phase': phase, 'checks': count, 'naturalExitCode': 0})
    require(sha(archive) == SOURCE_PIN and sha(candidate) == before and sha(connection) == connection_pin, 'ORIGINAL_OR_CANDIDATE_CHANGED')
    topology = dict(line.split('=', 1) for line in (output / 'topology.properties').read_text('ascii').splitlines() if line and not line.startswith(('#', '!')))
    prepared_topology = dict(line.split('=', 1) for line in (output / 'prepared-topology.properties').read_text('ascii').splitlines() if line and not line.startswith(('#', '!')))
    require(prepared_topology['candidateEnabledProviders'] == '2' and prepared_topology['candidateRemappedPathSettings'] == '0' and prepared_topology['defaultPlatformPreserved'] == 'true', 'PREPARED_ORIGINAL_STORAGE_SEMANTICS_MISMATCH')
    result = {'recordedAt': datetime.datetime.now().astimezone().isoformat(), 'originalArchiveSHA256': SOURCE_PIN, 'candidateSHA256': before,
              'originalDependencies': original_deps, 'originalClassSHA256': original_classes, 'sourceSHA256': {p.name: sha(p) for p in sources},
              'topology': topology, 'preparedTopology': prepared_topology, 'topologyFixtureChecks': 12, 'overlayFixtureChecks': 23,
              'preparedOwnConnectionSHA256': connection_pin, 'preparedOverlaySHA256': sha(prepared), 'preparedOverlayNotApplied': True,
              'originalSpringBinderAndLocalFactoryChecks': 23, 'originalPlatformHTTPOrDatabaseRecordVerified': False,
              'preparedPhysicalRootIsTestDirectory': True, 'originalLocalProviderChecks': 50, 'phases': phases,
              'separateJVMReadbackExact': True, 'syntheticFilesDeletedByOriginalProvider': True, 'originalClassesModified': False,
              'sourceDatabaseConnected': False, 'applicationStarted': False, 'originalValuesWrittenToPublicReport': False,
              'originalLogicalPathsAndProviderIdentitiesWrittenToPrivateOverlay': True, 'originalStorageCredentialsOrPhysicalBaseCopied': False,
              'currentCandidateModified': False, 'authenticatedHTTPUploadVerified': False, 'historicalFilesRecovered': False, 'fullCloneReady': False}
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('workspace', 'candidate-properties', 'output', 'private-object-store-connection'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.workspace, args.candidate_properties, args.output, args.private_object_store_connection)))


if __name__ == '__main__':
    main()
