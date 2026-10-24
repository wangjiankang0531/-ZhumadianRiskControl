"""Verify unchanged original attachment services against a pinned real owned MinIO process.

Uses synthetic objects in a fresh owned bucket, checks actual bytes, removes the
objects, and requests authenticated shutdown of this process only. No source
environment, database, browser session or existing application is modified.
"""
import argparse
import datetime
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time

MINIO_COMMIT = '9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a'


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def own_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def checked_owned_listeners(listeners, api_port):
    require(isinstance(listeners, list) and listeners, 'OWN_PROVIDER_LISTENERS_REQUIRED')
    require(all(isinstance(r, dict) and r.get('LocalAddress') in ('127.0.0.1', '::1') and
                type(r.get('LocalPort')) is int and r['LocalPort'] == api_port for r in listeners), 'OWN_PROVIDER_LISTENER_SCOPE_MISMATCH')
    require(any(r['LocalAddress'] == '127.0.0.1' for r in listeners), 'OWN_PROVIDER_IPV4_LISTENER_REQUIRED')
    return listeners


def request_owned_http(port, method, path, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=4)
    try:
        conn.request(method, path, headers=headers or {'Connection': 'close'})
        response = conn.getresponse(); body = response.read(16385)
        require(len(body) <= 16384, 'OWN_PROVIDER_HTTP_BODY_LIMIT')
        return response.status, body
    finally:
        conn.close()


def stop_owned_provider(port, access, secret):
    # Matches the fixed source's madmin v3 ServiceStopV2 request.
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); day = stamp[:8]
    path = '/minio/admin/v3/service'; query = 'action=stop&dry-run=false&type=2'
    payload = hashlib.sha256(b'').hexdigest(); host = '127.0.0.1:' + str(port)
    signed = 'host;x-amz-content-sha256;x-amz-date'
    headers = 'host:' + host + '\nx-amz-content-sha256:' + payload + '\nx-amz-date:' + stamp + '\n'
    canonical = '\n'.join(('POST', path, query, headers, signed, payload))
    scope = day + '/us-east-1/s3/aws4_request'
    to_sign = 'AWS4-HMAC-SHA256\n' + stamp + '\n' + scope + '\n' + hashlib.sha256(canonical.encode()).hexdigest()
    key = ('AWS4' + secret).encode()
    for value in (day, 'us-east-1', 's3', 'aws4_request'):
        key = hmac.new(key, value.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = 'AWS4-HMAC-SHA256 Credential=' + access + '/' + scope + ', SignedHeaders=' + signed + ', Signature=' + signature
    status, body = request_owned_http(port, 'POST', path + '?' + query, {'Host': host, 'X-Amz-Content-Sha256': payload, 'X-Amz-Date': stamp, 'Authorization': authorization, 'Connection': 'close'})
    return {'status': status, 'responseSHA256': hashlib.sha256(body).hexdigest(), 'requestTargetIsOwnedLoopback': True}


def verify(workspace, provider_receipt, provider_receipt_pin, output):
    w, provider_receipt, root = map(lambda p: Path(p).resolve(), (workspace, provider_receipt, output))
    require(not root.exists(), 'FRESH_OUTPUT_REQUIRED')
    require(sha(provider_receipt) == provider_receipt_pin, 'EXPLICIT_PROVIDER_RECEIPT_PIN_MISMATCH')
    provider = json.loads(provider_receipt.read_bytes()); binary = Path(provider['binary']).resolve()
    require(provider['minioCommit'] == MINIO_COMMIT and provider['buildExitCode'] == 0, 'FIXED_OFFICIAL_PROVIDER_COMMIT_REQUIRED')
    require(binary == w / 'own-minio-source-build-r1/bin/minio.exe' and sha(binary) == provider['binarySHA256'], 'OWN_PROVIDER_BINARY_PIN_MISMATCH')
    require(('-' + MINIO_COMMIT[:12]).encode() in (provider_receipt.parent / 'minio-buildinfo.txt').read_bytes(), 'INDEPENDENT_PROVIDER_BUILDINFO_COMMIT_CHECK')
    flat = w / 'original-shared-runtime-r1_20261024/flat'; jar = flat / 'application.jar'; meta = json.loads((flat / 'receipt.json').read_bytes())
    require(sha(jar) == meta['applicationJarSHA256'] == 'c4637e950664ff2ee26746b80366ca12e8c1f36f69288d35e126871f9afe30ae', 'ORIGINAL_FLAT_JAR_PIN_MISMATCH')
    for row in meta['dependencies']:
        require(sha(flat / row['relativePath']) == row['sha256'], 'ORIGINAL_DEPENDENCY_PIN_MISMATCH')
    dbmeta = json.loads((w / 'own-mysql-r13/fixture_compile.json').read_bytes()); boundary = Path(dbmeta['boundaryJar'])
    require(sha(boundary) == dbmeta['boundaryJarSHA256'] == '3f5b36ef4a48714a0424b7470d7a1aecf7bd1beb385a4843fd08adc02bd16bb9', 'EXISTING_BOUNDARY_PIN_MISMATCH')
    java = Path(json.loads((w / 'own-pboot-r32/preparation.json').read_bytes())['javaHome']); source = Path(__file__).parent / 'java/OriginalFileRoundtripFixture.java'
    require(source.is_file(), 'EXPLICIT_OWN_JAVA_FIXTURE_REQUIRED')
    root.mkdir(parents=True)
    for name in ('data', 'tmp', 'certs', 'classes', 'appdata', 'localappdata', 'profile'):
        (root / name).mkdir()
    access = 'own-' + secrets.token_hex(8); secret = secrets.token_hex(24); bucket = 'own-attachment-' + secrets.token_hex(6)
    port = own_port(); console = own_port(); require(port != console, 'DISTINCT_PROVIDER_PORTS_REQUIRED')
    private = root / 'own-minio.private.properties'; private.write_text('endpoint=http://127.0.0.1:' + str(port) + '\naccessKey=' + access + '\nsecretKey=' + secret + '\nbucket=' + bucket + '\n', encoding='utf-8')
    minimal = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS')}
    minimal.update({'PATH': str(Path(os.environ['SystemRoot']) / 'System32'), 'TEMP': str(root / 'tmp'), 'TMP': str(root / 'tmp'),
                    'APPDATA': str(root / 'appdata'), 'LOCALAPPDATA': str(root / 'localappdata'), 'USERPROFILE': str(root / 'profile')})
    env = {**minimal, 'MINIO_ROOT_USER': access, 'MINIO_ROOT_PASSWORD': secret, 'MINIO_BROWSER': 'off', 'MINIO_UPDATE': 'off', 'MINIO_CALLHOME_ENABLE': 'off', 'GOMAXPROCS': '2'}
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    command = [str(binary), '--quiet', '--certs-dir', str(root / 'certs'), 'server', '--address', '127.0.0.1:' + str(port), '--console-address', '127.0.0.1:' + str(console), str(root / 'data')]
    receipt = {'startedAt': datetime.datetime.now().astimezone().isoformat(), 'providerBinarySHA256': sha(binary), 'providerCommit': MINIO_COMMIT,
               'providerBind': 'loopback-only', 'configuredProviderAddress': '127.0.0.1', 'providerPort': port, 'sourceObjectsOrCredentialsUsed': False, 'originalApplicationStarted': False,
               'historicalObjectsRecovered': False, 'fullCloneReady': False, 'forcedTermination': False}
    result = None; stop = None; process = None
    logback = root / 'own-logback.xml'; logback.write_text('<configuration><root level="OFF"/></configuration>', encoding='ascii')
    try:
        with (root / 'provider.private.log').open('wb') as log:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        receipt['ownedPID'] = process.pid
        (root / 'started.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            require(process.poll() is None, 'OWN_PROVIDER_EXITED_DURING_START')
            try:
                if request_owned_http(port, 'GET', '/minio/health/live')[0] == 200:
                    break
            except OSError:
                pass
            time.sleep(.2)
        else:
            raise RuntimeError('OWN_PROVIDER_HEALTH_TIMEOUT')
        # Independently verify listening sockets belong to this exact Popen PID.
        ps = 'Get-NetTCPConnection -State Listen -OwningProcess ' + str(process.pid) + ' | Select-Object LocalAddress,LocalPort | ConvertTo-Json -Compress'
        ownership = subprocess.run([str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'), '-NoProfile', '-NonInteractive', '-Command', ps], capture_output=True, timeout=15, creationflags=flags)
        require(ownership.returncode == 0, 'OWN_PROVIDER_LISTENER_OWNER_CHECK_FAILED')
        listeners = json.loads(ownership.stdout.decode('utf-8-sig')); listeners = listeners if isinstance(listeners, list) else [listeners]
        receipt['observedListenersBeforeScopeCheck'] = listeners
        checked_owned_listeners(listeners, port)
        receipt['listenerOwnershipVerified'] = True; receipt['listeners'] = listeners
        cp = os.pathsep.join(map(str, (root / 'classes', boundary, jar)))
        def run(cmd, name):
            value = subprocess.run(list(map(str, cmd)), cwd=root, env=minimal, capture_output=True, timeout=90, creationflags=flags)
            (root / (name + '.private.log')).write_bytes(value.stdout + value.stderr)
            require(value.returncode == 0, 'ORIGINAL_FILE_' + name.upper() + '_FAILED')
            return value.stdout
        run([java / 'bin/javac.exe', '-proc:none', '-encoding', 'UTF-8', '-cp', os.pathsep.join(map(str, (boundary, jar))), '-d', root / 'classes', source], 'compile')
        raw = run([java / 'bin/java.exe', '-Xmx256m', '-Dlogback.configurationFile=' + str(logback), '-Djava.io.tmpdir=' + str(root / 'tmp'), '-cp', cp,
                   'xnby.replica.OriginalFileRoundtripFixture', root, sha(private), jar], 'roundtrip')
        prefix = b'ORIGINAL_FILE_ROUNDTRIP_RESULT '
        result = json.loads(next(line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)))
        require(result['passedChecks'] == 48 and len(result['cases']) == 4 and result['ownedBucketAndObjectsRemoved'], 'ORIGINAL_FILE_ROUNDTRIP_INCOMPLETE')
        receipt['originalServiceRoundtrip'] = result; receipt['fixtureSourceSHA256'] = sha(source)
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    stop = stop_owned_provider(port, access, secret)
                    receipt['authenticatedOwnStop'] = stop
                    if stop['status'] == 200:
                        process.wait(timeout=15)
                except Exception as error:
                    receipt['stopErrorType'] = type(error).__name__
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=10); receipt['forcedTermination'] = True
            receipt['ownProviderExitCode'] = process.poll()
        receipt['finishedAt'] = datetime.datetime.now().astimezone().isoformat()
        (root / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    require(result is not None and stop is not None and stop['status'] == 200 and receipt['ownProviderExitCode'] == 0 and not receipt['forcedTermination'], 'NORMAL_PROVIDER_SHUTDOWN_UNVERIFIED')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('workspace', 'provider-receipt', 'provider-receipt-sha256', 'output'):
        p.add_argument('--' + name, required=True)
    a = p.parse_args(); print(json.dumps(verify(a.workspace, a.provider_receipt, a.provider_receipt_sha256, a.output)))


if __name__ == '__main__':
    main()
