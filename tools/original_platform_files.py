"""Identity and exclusive ownership for original-platform local files and per-run runtime roots."""
import hashlib
import json
from pathlib import Path
import re
import uuid


def require(value, code):
    if not value:
        raise ValueError(code)


def regular_directory(path):
    path = Path(path)
    if path.exists():
        stat = path.lstat()
        require(path.is_dir() and not path.is_symlink() and not getattr(stat, 'st_file_attributes', 0) & 0x400,
                'PLATFORM_DATA_DIRECTORY_MUST_NOT_REDIRECT')


class OwnedPlatformFiles:
    def __init__(self, app, name):
        self.app = Path(app).resolve(strict=True)
        require(self.app.name == 'Application' and (self.app / 'tools/reference_flat_runtime.py').is_file(), 'KNOWN_APPLICATION_ROOT_REQUIRED')
        require(re.fullmatch(r'own-j[1-9][0-9]{0,3}', name), 'OWN_PLATFORM_RUN_NAME_REQUIRED')
        self.root = self.app / 'UserData/TianjinOriginalPlatform'
        self.files = self.root / 'files'
        self.run_root = self.root / 'runs' / name.removeprefix('own-')
        self.lock = None
        self.identity = None

    def acquire(self):
        import msvcrt
        require(self.lock is None, 'PLATFORM_OWNER_ALREADY_ACQUIRED')
        for path in (self.root.parent, self.root, self.files, self.root / 'runs'):
            regular_directory(path)
        existed = self.root.exists()
        if existed:
            require((self.root / 'identity.json').is_file(), 'EXISTING_PLATFORM_DATA_IDENTITY_REQUIRED')
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.root / 'owner.lock'
        if lock_path.exists():
            require(lock_path.is_file() and not lock_path.is_symlink() and not getattr(lock_path.lstat(), 'st_file_attributes', 0) & 0x400, 'REGULAR_PLATFORM_OWNER_LOCK_REQUIRED')
        handle = lock_path.open('a+b')
        try:
            handle.seek(0); handle.write(b'0'); handle.flush(); handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except Exception:
            handle.close()
            raise
        self.lock = handle
        try:
            identity_path = self.root / 'identity.json'
            if existed:
                stat = identity_path.lstat()
                require(not identity_path.is_symlink() and not getattr(stat, 'st_file_attributes', 0) & 0x400 and stat.st_size <= 4096, 'REGULAR_PLATFORM_IDENTITY_REQUIRED')
                identity = json.loads(identity_path.read_bytes())
                require(set(identity) == {'schema', 'ownerId', 'filesRelativePath'} and identity['schema'] == 'xnby.original.platform.local-data.v1' and identity['filesRelativePath'] == 'files/', 'PLATFORM_DATA_IDENTITY_SHAPE')
                require(str(uuid.UUID(identity['ownerId'])) == identity['ownerId'], 'PLATFORM_DATA_OWNER_UUID_REQUIRED')
            else:
                identity = {'schema': 'xnby.original.platform.local-data.v1', 'ownerId': str(uuid.uuid4()), 'filesRelativePath': 'files/'}
                with identity_path.open('x', encoding='ascii') as stream:
                    json.dump(identity, stream, indent=2)
            java_identity = 'schema=' + identity['schema'] + '\nownerId=' + identity['ownerId'] + '\nfilesRelativePath=files/\n'
            java_path = self.root / 'identity.properties'
            if java_path.exists():
                require(java_path.is_file() and not java_path.is_symlink() and not getattr(java_path.lstat(), 'st_file_attributes', 0) & 0x400 and java_path.read_text('ascii') == java_identity, 'PLATFORM_JAVA_IDENTITY_MISMATCH')
            else:
                with java_path.open('x', encoding='ascii') as stream:
                    stream.write(java_identity)
            self.files.mkdir(exist_ok=True)
            (self.root / 'runs').mkdir(exist_ok=True)
            require(not self.run_root.exists(), 'FRESH_PLATFORM_RUNTIME_ROOT_REQUIRED')
            self.run_root.mkdir()
            self.identity = identity
            return self
        except Exception:
            self.release()
            raise

    def release(self):
        if self.lock is not None:
            import msvcrt
            self.lock.seek(0)
            msvcrt.locking(self.lock.fileno(), msvcrt.LK_UNLCK, 1)
            self.lock.close()
            self.lock = None

    def observation(self):
        require(self.identity is not None and self.lock is not None, 'LIVE_PLATFORM_DATA_OWNER_REQUIRED')
        return {'dataOwnerId': self.identity['ownerId'], 'dataRoot': str(self.root), 'filesRoot': str(self.files),
                'runRoot': str(self.run_root), 'identitySHA256': hashlib.sha256((self.root / 'identity.json').read_bytes()).hexdigest(),
                'retainedAfterStop': True}
