"""Build a fixed official MinIO source release with a verified portable Go SDK.

Builds only, never starts a server or touches the original environment.
All toolchain/cache/output paths are explicit and isolated on the selected drive.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import zipfile

GO_VERSION = 'go1.26.10'
GO_FILENAME = GO_VERSION + '.windows-amd64.zip'
GO_SHA256 = '7ecd2d7260e82c59bcbd7f1077a07cee2dea607295b858df67195a1e4e09629b'
MINIO_RELEASE = 'RELEASE.2025-10-15T17-29-55Z'
MINIO_MODULE = 'github.com/minio/minio@' + MINIO_RELEASE
PEAK_BYTES = 4 * 1024 ** 3


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'XNBY-owned-runtime-build/1'}), timeout=20) as response:
        raw = response.read(1024 * 1024 + 1)
    require(len(raw) <= 1024 * 1024, 'OFFICIAL_METADATA_LIMIT')
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def prepare(output):
    root = Path(output).resolve()
    require(not root.exists(), 'FRESH_BUILD_ROOT_REQUIRED')
    require(root.drive.upper() == 'D:', 'EXPLICIT_D_DRIVE_REQUIRED')
    usage = shutil.disk_usage(root.anchor)
    require(usage.free >= PEAK_BYTES + 2 * 1024 ** 3, 'INSUFFICIENT_BUILD_PEAK_SPACE')
    versions, metadata_pin = get_json('https://go.dev/dl/?mode=json')
    rows = [f for v in versions if v['version'] == GO_VERSION for f in v['files'] if f['filename'] == GO_FILENAME]
    require(len(rows) == 1 and rows[0]['sha256'] == GO_SHA256 and rows[0]['size'] <= 128 * 1024 ** 2, 'OFFICIAL_GO_SDK_PIN_MISMATCH')
    release, release_pin = get_json('https://api.github.com/repos/minio/minio/releases/tags/' + MINIO_RELEASE)
    require(release['tag_name'] == MINIO_RELEASE and not release['draft'] and not release['prerelease'], 'OFFICIAL_MINIO_RELEASE_MISMATCH')
    ref, ref_pin = get_json('https://api.github.com/repos/minio/minio/git/ref/tags/' + MINIO_RELEASE)
    require(ref['object']['type'] == 'commit', 'EXPLICIT_OFFICIAL_TAG_COMMIT_REQUIRED')
    commit = ref['object']['sha']
    require(len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'OFFICIAL_COMMIT_FORMAT')
    root.mkdir(parents=True)
    preflight = {'recordedAt': datetime.datetime.now().astimezone().isoformat(), 'expectedTemporaryPeakBytes': PEAK_BYTES,
                 'freeBytesBefore': usage.free, 'goVersion': GO_VERSION, 'goArchiveSHA256': GO_SHA256,
                 'goMetadataSHA256': metadata_pin, 'minioRelease': MINIO_RELEASE, 'minioCommit': commit,
                 'releaseMetadataSHA256': release_pin, 'tagRefMetadataSHA256': ref_pin,
                 'sourceURL': release['html_url'], 'originalResourcesCopied': False, 'serverStarted': False}
    (root / 'preflight.json').write_text(json.dumps(preflight, indent=2) + '\n', encoding='utf-8')
    archive = root / GO_FILENAME
    total = 0
    with urllib.request.urlopen('https://go.dev/dl/' + GO_FILENAME, timeout=20) as response, archive.open('xb') as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk); require(total <= rows[0]['size'], 'GO_DOWNLOAD_SIZE_LIMIT'); f.write(chunk)
    require(total == rows[0]['size'] and sha(archive) == GO_SHA256, 'GO_ARCHIVE_VERIFICATION_FAILED')
    print('OFFICIAL_GO_ARCHIVE_VERIFIED', flush=True)
    sdk = root / 'sdk'; sdk.mkdir()
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        require(sum(e.file_size for e in entries) <= 1024 ** 3, 'GO_EXPANSION_LIMIT')
        for entry in entries:
            name = entry.filename
            require(name.startswith('go/') and '\\' not in name and ':' not in name and not any(p in ('.', '..') for p in name.split('/')), 'GO_ARCHIVE_PATH_SCOPE')
            require(((entry.external_attr >> 16) & 0o170000) != 0o120000, 'GO_ARCHIVE_LINK_REJECTED')
        z.extractall(sdk)
    go = sdk / 'go/bin/go.exe'; require(go.is_file(), 'GO_EXECUTABLE_MISSING')
    directories = {n: root / n for n in ('gopath', 'cache', 'tmp', 'bin', 'appdata', 'localappdata')}
    for p in directories.values():
        p.mkdir()
    env = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'ALL_PROXY')}
    env.update({'PATH': str(go.parent) + os.pathsep + str(Path(os.environ['SystemRoot']) / 'System32'),
                'GOROOT': str(sdk / 'go'), 'GOPATH': str(directories['gopath']), 'GOMODCACHE': str(directories['gopath'] / 'pkg/mod'),
                'GOCACHE': str(directories['cache']), 'GOTMPDIR': str(directories['tmp']), 'GOBIN': str(directories['bin']),
                'TMP': str(directories['tmp']), 'TEMP': str(directories['tmp']), 'APPDATA': str(directories['appdata']),
                'LOCALAPPDATA': str(directories['localappdata']), 'GOENV': 'off', 'GOTOOLCHAIN': 'local', 'GOTELEMETRY': 'off',
                'CGO_ENABLED': '0', 'GOOS': 'windows', 'GOARCH': 'amd64', 'GOMAXPROCS': '2',
                'GOPROXY': 'https://proxy.golang.org', 'GOSUMDB': 'sum.golang.org', 'GOPRIVATE': '', 'GONOPROXY': '', 'GONOSUMDB': '',
                'GIT_TERMINAL_PROMPT': '0'})
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    version = subprocess.run([str(go), 'version'], cwd=root, env=env, capture_output=True, timeout=10, creationflags=flags)
    (root / 'go-version.log').write_bytes(version.stdout + version.stderr)
    require(version.returncode == 0 and GO_VERSION.encode() in version.stdout, 'VERIFIED_GO_EXECUTION_FAILED')
    print('BUILD_FIXED_OFFICIAL_MINIO_SOURCE', flush=True)
    command = [str(go), 'install', '-p=2', '-trimpath', MINIO_MODULE]
    started = time.monotonic()
    with (root / 'build.log').open('wb') as log:
        process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        (root / 'build-started.json').write_text(json.dumps({'pid': process.pid, 'command': command, 'sourceRef': MINIO_RELEASE, 'originalApplicationOrDataOnBuildPath': False}) + '\n', encoding='utf-8')
        try:
            while process.poll() is None:
                require(time.monotonic() - started < 900, 'BUILD_TIME_LIMIT')
                require(usage.free - shutil.disk_usage(root.anchor).free < PEAK_BYTES, 'BUILD_PEAK_LIMIT')
                time.sleep(2)
        finally:
            if process.poll() is None:
                process.terminate(); process.wait(timeout=15)
    require(process.returncode == 0, 'PINNED_MINIO_SOURCE_BUILD_FAILED')
    binary = directories['bin'] / 'minio.exe'; require(binary.is_file() and binary.stat().st_size <= 256 * 1024 ** 2, 'MINIO_BINARY_SIZE_LIMIT')
    info = subprocess.run([str(go), 'version', '-m', str(binary)], cwd=root, env=env, capture_output=True, timeout=15, creationflags=flags)
    require(info.returncode == 0 and b'github.com/minio/minio' in info.stdout and ('-' + commit[:12]).encode() in info.stdout, 'MINIO_BUILDINFO_FIXED_COMMIT_MISMATCH')
    (root / 'minio-buildinfo.txt').write_bytes(info.stdout)
    receipt = {**preflight, 'goExecutableSHA256': sha(go), 'binary': str(binary), 'binarySHA256': sha(binary),
               'binaryBytes': binary.stat().st_size, 'buildInfoSHA256': sha(root / 'minio-buildinfo.txt'),
               'buildSeconds': round(time.monotonic() - started, 3), 'buildExitCode': process.returncode,
               'moduleChecksumVerificationEnabled': True, 'serverStarted': False,
               'cacheCleanupPending': True, 'fileServiceVerified': False, 'fullCloneReady': False}
    (root / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt), flush=True)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output', type=Path, required=True)
    prepare(p.parse_args().output)


if __name__ == '__main__':
    main()
