"""Owned original-object-store lifecycle and exact loopback transport helpers."""
import datetime,hashlib,hmac,http.client,json,os,re,secrets,socket,subprocess,time,uuid
from pathlib import Path
from urllib.parse import quote

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

def request_owned_http(port, method, path, headers=None, body=None):
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=4)
    try:
        conn.request(method, path, body=body, headers=headers or {'Connection': 'close'})
        response = conn.getresponse(); body = response.read(16385)
        require(len(body) <= 16384, 'OWN_PROVIDER_HTTP_BODY_LIMIT')
        return response.status, body
    finally:
        conn.close()

def signed_owned_request(port, access, secret, method, path, query='', body=b''):
    require(type(port) is int and 1024 <= port <= 65535 and method in ('GET','HEAD','PUT','POST','DELETE'), 'OWN_SIGNED_REQUEST_SCOPE')
    require(path.startswith('/') and not any(c in path+query for c in ('\r','\n','#')) and '?' not in path, 'OWN_SIGNED_REQUEST_PATH')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); day = stamp[:8]
    payload = hashlib.sha256(body).hexdigest(); host = '127.0.0.1:' + str(port)
    signed = 'host;x-amz-content-sha256;x-amz-date'
    headers = 'host:' + host + '\nx-amz-content-sha256:' + payload + '\nx-amz-date:' + stamp + '\n'
    canonical = '\n'.join((method, path, query, headers, signed, payload))
    scope = day + '/us-east-1/s3/aws4_request'
    to_sign = 'AWS4-HMAC-SHA256\n' + stamp + '\n' + scope + '\n' + hashlib.sha256(canonical.encode()).hexdigest()
    key = ('AWS4' + secret).encode()
    for value in (day, 'us-east-1', 's3', 'aws4_request'):
        key = hmac.new(key, value.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = 'AWS4-HMAC-SHA256 Credential=' + access + '/' + scope + ', SignedHeaders=' + signed + ', Signature=' + signature
    return request_owned_http(port, method, path + ('?' + query if query else ''), {'Host': host, 'X-Amz-Content-Sha256': payload, 'X-Amz-Date': stamp, 'Authorization': authorization, 'Connection': 'close'}, body=body)


def stop_owned_provider(port, access, secret):
    # Matches the fixed source's madmin v3 ServiceStopV2 request.
    status, body = signed_owned_request(port, access, secret, 'POST', '/minio/admin/v3/service', 'action=stop&dry-run=false&type=2')
    return {'status': status, 'responseSHA256': hashlib.sha256(body).hexdigest(), 'requestTargetIsOwnedLoopback': True}


def load_provider(workspace, receipt_path, receipt_pin):
    workspace, receipt_path = Path(workspace).resolve(), Path(receipt_path).resolve()
    require(re.fullmatch('[a-f0-9]{64}', receipt_pin) and sha(receipt_path) == receipt_pin, 'OWN_PROVIDER_RECEIPT_PIN_MISMATCH')
    spec = json.loads(receipt_path.read_bytes()); binary = Path(spec['binary']).resolve()
    require(spec['minioCommit'] == MINIO_COMMIT and spec['buildExitCode'] == 0, 'OWN_FIXED_PROVIDER_COMMIT_REQUIRED')
    require(binary == workspace / 'own-minio-source-build-r1/bin/minio.exe' and sha(binary) == spec['binarySHA256'], 'OWN_PROVIDER_BINARY_PIN_MISMATCH')
    require(('-' + MINIO_COMMIT[:12]).encode() in (receipt_path.parent / 'minio-buildinfo.txt').read_bytes(), 'OWN_PROVIDER_BUILDINFO_COMMIT_MISMATCH')
    return binary, spec


class OwnedObjectStore:
    """One lease-scoped process, with persistent owned application data and credentials."""
    def __init__(self, workspace, run_root, provider_receipt, provider_pin):
        self.workspace = Path(workspace).resolve(); self.root = Path(run_root).resolve()
        self.binary, self.spec = load_provider(self.workspace, provider_receipt, provider_pin)
        require(not self.root.exists() and self.root.is_relative_to(self.workspace), 'FRESH_OWN_STORE_RUNTIME_ROOT_REQUIRED')
        self.data_root = self.workspace.parents[1] / 'UserData/TianjinOriginalObjectStore'
        self.process = None; self.lock = None; self.locked = False; self.log = None; self.port = None
        self.result = {'providerCommit': MINIO_COMMIT, 'providerBinarySHA256': self.spec['binarySHA256'],
                       'dataRoot': str(self.data_root), 'applicationDataIsPersistent': True,
                       'sourceDataOrCredentialsUsed': False, 'forcedTermination': False}

    def start(self):
        import msvcrt
        require(self.data_root.resolve().is_relative_to(self.workspace.parents[1]) and not self.data_root.is_symlink(), 'OWN_STORE_DATA_ROOT_ESCAPES_APPLICATION')
        if not self.data_root.exists():
            self.data_root.mkdir(parents=True)
            own = {'accessKey': 'own-' + secrets.token_hex(8), 'secretKey': secrets.token_hex(24)}
            credentials = self.data_root / 'credentials.private.json'
            credentials.write_text(json.dumps(own), encoding='ascii')
            (self.data_root / 'data').mkdir()
            identity = {'schema': 'xnby.original.object-store-data.v1', 'ownerId': str(uuid.uuid4()),
                        'credentialsSHA256': sha(credentials), 'sourceEnvironment': False}
            (self.data_root / 'identity.json').write_text(json.dumps(identity), encoding='ascii')
        require(self.data_root.is_dir() and not self.data_root.is_symlink(), 'OWN_STORE_DATA_ROOT_REQUIRED')
        identity_path = self.data_root / 'identity.json'; private_path = self.data_root / 'credentials.private.json'
        require(identity_path.is_file() and private_path.is_file() and (self.data_root / 'data').is_dir(), 'OWN_STORE_DATA_IDENTITY_REQUIRED')
        identity = json.loads(identity_path.read_bytes())
        require(identity['schema'] == 'xnby.original.object-store-data.v1' and identity['sourceEnvironment'] is False and sha(private_path) == identity['credentialsSHA256'], 'OWN_STORE_DATA_IDENTITY_MISMATCH')
        own = json.loads(private_path.read_bytes())
        require(re.fullmatch('own-[a-f0-9]{16}', own['accessKey']) and re.fullmatch('[a-f0-9]{48}', own['secretKey']), 'OWN_STORE_CREDENTIAL_FORMAT')
        self.access, self.secret = own['accessKey'], own['secretKey']
        self.lock = (self.data_root / 'owner.lock').open('a+b'); self.lock.seek(0); self.lock.write(b'0'); self.lock.flush(); self.lock.seek(0)
        msvcrt.locking(self.lock.fileno(), msvcrt.LK_NBLCK, 1)
        self.locked = True
        self.root.mkdir()
        for name in ('tmp', 'certs', 'profile', 'appdata', 'localappdata'):
            (self.root / name).mkdir()
        self.port = own_port(); console = own_port(); require(self.port != console, 'OWN_STORE_DISTINCT_PORTS')
        env = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS')}
        env.update({'PATH': str(Path(os.environ['SystemRoot']) / 'System32'), 'TEMP': str(self.root / 'tmp'), 'TMP': str(self.root / 'tmp'),
                    'APPDATA': str(self.root / 'appdata'), 'LOCALAPPDATA': str(self.root / 'localappdata'), 'USERPROFILE': str(self.root / 'profile'),
                    'MINIO_ROOT_USER': self.access, 'MINIO_ROOT_PASSWORD': self.secret, 'MINIO_BROWSER': 'off', 'MINIO_UPDATE': 'off', 'MINIO_CALLHOME_ENABLE': 'off', 'GOMAXPROCS': '2'})
        command = [str(self.binary), '--quiet', '--certs-dir', str(self.root / 'certs'), 'server', '--address', '127.0.0.1:' + str(self.port), '--console-address', '127.0.0.1:' + str(console), str(self.data_root / 'data')]
        self.log = (self.root / 'provider.private.log').open('wb')
        self.process = subprocess.Popen(command, cwd=self.root, env=env, stdout=self.log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.result.update(ownedPID=self.process.pid, providerPort=self.port, dataOwnerId=identity['ownerId'])
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            require(self.process.poll() is None, 'OWN_STORE_EXITED_DURING_START')
            try:
                if request_owned_http(self.port, 'GET', '/minio/health/live')[0] == 200:
                    break
            except OSError:
                pass
            time.sleep(.2)
        else:
            raise RuntimeError('OWN_STORE_HEALTH_TIMEOUT')
        ps = 'Get-NetTCPConnection -State Listen -OwningProcess ' + str(self.process.pid) + ' | Select-Object LocalAddress,LocalPort | ConvertTo-Json -Compress'
        check = subprocess.run([str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'), '-NoProfile', '-NonInteractive', '-Command', ps], capture_output=True, timeout=15, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        require(check.returncode == 0, 'OWN_STORE_LISTENER_OWNER_CHECK')
        listeners = json.loads(check.stdout.decode('utf-8-sig')); listeners = listeners if isinstance(listeners, list) else [listeners]
        self.result['listeners'] = checked_owned_listeners(listeners, self.port)
        self.result['ready'] = True
        (self.root / 'ready.json').write_text(json.dumps(self.result, indent=2), encoding='utf-8')
        return self

    def write_private_connection(self, path):
        require(self.process is not None and self.process.poll() is None and self.result.get('ready'), 'OWN_READY_STORE_REQUIRED')
        path = Path(path); require(not path.exists(), 'FRESH_PRIVATE_STORE_CONNECTION_REQUIRED')
        path.write_text('endpoint=http://127.0.0.1:' + str(self.port) + '\naccessKey=' + self.access + '\nsecretKey=' + self.secret + '\n', encoding='ascii')

    def stop(self):
        import msvcrt
        try:
            if self.process is not None:
                if self.process.poll() is None:
                    try:
                        self.result['authenticatedStop'] = stop_owned_provider(self.port, self.access, self.secret)
                        if self.result['authenticatedStop']['status'] == 200:
                            self.process.wait(timeout=15)
                    except Exception as error:
                        self.result['stopErrorType'] = type(error).__name__
                    if self.process.poll() is None:
                        self.process.terminate(); self.process.wait(timeout=10); self.result['forcedTermination'] = True
                self.result.update(exited=True, exitCode=self.process.poll())
            else:
                self.result.update(exited=True, exitCode=None)
        finally:
            if self.log is not None:
                self.log.close()
            if self.lock is not None:
                if self.locked:
                    self.lock.seek(0); msvcrt.locking(self.lock.fileno(), msvcrt.LK_UNLCK, 1)
                self.lock.close(); self.lock = None; self.locked = False
            if self.root.exists():
                (self.root / 'receipt.json').write_text(json.dumps(self.result, indent=2), encoding='utf-8')
        return self.result

    def cleanup_spring_probe(self, observation, owner):
        require(self.process is not None and self.process.poll() is None, 'OWN_STORE_NOT_LIVE')
        require(observation.get('passed') == 'true' and observation.get('probeOwner') == owner and re.fullmatch('[a-f0-9-]{36}', owner), 'OWN_SPRING_PROBE_OWNER_MISMATCH')
        bucket, obj = observation['bucket'], observation['object']
        require(re.fullmatch('[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]', bucket) and re.fullmatch('[a-fA-F0-9-]{36}\\.txt', obj), 'OWN_SPRING_PROBE_OBJECT_SCOPE')
        target = '/' + quote(bucket, safe='') + '/' + quote(obj, safe='')
        status, raw = signed_owned_request(self.port, self.access, self.secret, 'GET', target)
        expected = ('owned-original-spring-file-probe:' + owner).encode('ascii')
        require(status == 200 and raw == expected, 'OWN_PROBE_BYTES_REQUIRED_BEFORE_DELETE')
        require(signed_owned_request(self.port, self.access, self.secret, 'DELETE', target)[0] == 204, 'OWN_PROBE_DELETE_FAILED')
        require(signed_owned_request(self.port, self.access, self.secret, 'HEAD', target)[0] == 404, 'OWN_PROBE_STILL_EXISTS')
        return {'onlyOwnedSyntheticProbeRemoved': True, 'signedS3HeadAfterDelete': 404, 'otherObjectsOrBucketRemoved': False}
