"""Cross-check actual Java export bytes with the Python artifact verifier.

Uses an explicitly pinned existing own exporter JAR and in-memory JDBC proxy.
Does not launch the exporter GUI, inspect original configuration, or connect.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

from verify_original_database_export import verify


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run(java_home, exporter, exporter_sha, yaml, yaml_sha, output):
    java_home, exporter, yaml = [Path(p).resolve(strict=True) for p in (java_home, exporter, yaml)]
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Fresh fixture output required')
    if sha(exporter) != exporter_sha or sha(yaml) != yaml_sha:
        raise ValueError('Pinned existing dependency SHA mismatch')
    source = Path(__file__).with_name('java') / 'xnby/export/ReadOnlyExportArtifactFixture.java'
    if not source.is_file():
        raise FileNotFoundError('Missing own Java artifact fixture source')
    if output.is_relative_to(Path(__file__).parent.resolve()):
        raise ValueError('Generated fixture artifacts must stay outside tools sources')
    output.mkdir()
    classes, temp = output / 'classes', output / 'temp'
    classes.mkdir(); temp.mkdir()
    env = {k: v for k, v in os.environ.items() if k.upper() not in
           ('CLASSPATH', 'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS')
           and not k.upper().startswith('LOADER_')}
    env['TEMP'] = env['TMP'] = str(temp)
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

    def execute(label, args):
        result = subprocess.run(list(map(str, args)), env=env, cwd=output,
                                capture_output=True, timeout=60, creationflags=flags)
        (output / (label + '.log')).write_bytes(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(label + ' failed; retained own fixture log')
        return result.stdout

    cp = os.pathsep.join(map(str, (exporter, yaml)))
    execute('compile', [java_home / 'bin/javac.exe', '--release', '17', '-encoding', 'UTF-8',
                        '-cp', cp, '-d', classes, source])
    stdout = execute('producer', [java_home / 'bin/java.exe', '-Xmx128m', '-Djava.awt.headless=true',
                       '-Dfile.encoding=UTF-8', '-cp', str(classes) + os.pathsep + cp,
                       'xnby.export.ReadOnlyExportArtifactFixture', output / 'export'])
    producer = json.loads(stdout.decode('utf-8'))
    if not (producer['actualProducerInvoked'] and producer['JDBCResultsAreOwnFixtures']
            and producer['realDatabaseConnections'] == 0 and producer['GUIStarted'] is False
            and producer['rollbackCount'] == 1 and producer['connectionClosed']):
        raise RuntimeError('Unexpected producer scope or fixture lifecycle')
    result = verify(output / 'export', producer['manifestSHA256'])
    if (result['tables'], result['rows'], result['views'], result['sqlNullValues'], result['nonNullEmptyValues']) != (3, 3, 1, 2, 2):
        raise RuntimeError('Cross-language fixture counts differ')
    (output / 'artifact_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    receipt = {'actualJavaProducerUsed': True, 'ownJDBCFixtureOnly': True, 'sourceConfigurationRead': False,
               'originalDatabaseConnections': 0, 'GUIStarted': False, 'sealedExporterJARChanged': False,
               'exporterSHA256': exporter_sha, 'yamlSHA256': yaml_sha, 'fixtureSourceSHA256': sha(source),
               'verifierSourceSHA256': sha(Path(__file__).with_name('verify_original_database_export.py')),
               'producer': producer, 'verifiedTables': result['tables'], 'verifiedRows': result['rows'],
               'fieldTypeRestorationVerified': False, 'realMySQLRoundtripVerified': False, 'fullCloneReady': False}
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if sha(exporter) != exporter_sha or sha(yaml) != yaml_sha:
        raise RuntimeError('Pinned dependency changed during fixture')
    print(json.dumps(receipt))
    return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--java-home', type=Path, required=True)
    ap.add_argument('--exporter-jar', type=Path, required=True)
    ap.add_argument('--exporter-sha256', required=True)
    ap.add_argument('--yaml-jar', type=Path, required=True)
    ap.add_argument('--yaml-sha256', required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    run(a.java_home, a.exporter_jar, a.exporter_sha256, a.yaml_jar, a.yaml_sha256, a.output)


if __name__ == '__main__':
    main()
