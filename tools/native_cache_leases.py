"""Short-lived web batch leases, renewed on downloads and released after upload."""

from contextlib import contextmanager
import re
import secrets
import threading
import time

if __package__:
    from . import native_cache_policy as policy
else:
    import native_cache_policy as policy


class LeaseRegistry:
    def __init__(self, ttl=180, maximum=256, janitor=True, *, read_only=False):
        self.ttl = ttl
        self.maximum = maximum
        self.read_only = read_only
        self.entries = {}
        self.caches = set()
        self.lock = threading.RLock()
        self.stop = threading.Event()
        if janitor:
            self.thread = threading.Thread(
                target=self._run, daemon=True, name="xnby-cache-leases"
            )
            self.thread.start()

    def _run(self):
        while not self.stop.wait(min(15, max(0.05, self.ttl / 2))):
            self.expire()

    def expire(self):
        roots = set()
        with self.lock:
            for token, (cache, name, guard, expiry) in list(self.entries.items()):
                if expiry <= time.monotonic():
                    del self.entries[token]
                    guard.__exit__(None, None, None)
                    roots.add(cache)
        with self.lock:
            roots.update(self.caches)
        if not self.read_only:
            for cache in roots:
                policy.maintain(cache)

    def _guard(self, cache, name):
        return (policy.readonly_bundle_lock(cache,name,timeout=0) if self.read_only
                else policy.bundle_lock(cache,name,timeout=0))

    def grant(self, cache, name, validate):
        self.expire()
        with self.lock:
            if len(self.entries) >= self.maximum:
                raise RuntimeError("cache reader capacity reached")
            guard = self._guard(cache, name)
            folder = guard.__enter__()
            try:
                if not validate():
                    raise FileNotFoundError("derived bundle changed before lease")
                if not self.read_only:
                    (folder / "complete.json").touch()
                token = secrets.token_hex(16)
                self.entries[token] = (cache, name, guard, time.monotonic() + self.ttl)
                self.caches.add(cache)
                return token
            except BaseException:
                guard.__exit__(None, None, None)
                raise

    @contextmanager
    def use(self, token, cache, name):
        with self.lock:
            row = self.entries.get(token)
            if (
                not row
                or row[0] != cache
                or row[1] != name
                or row[3] <= time.monotonic()
            ):
                raise PermissionError("expired or mismatched cache lease")
            guard = self._guard(cache, name)
            guard.__enter__()
            self.entries[token] = (*row[:3], time.monotonic() + self.ttl)
        try:
            yield
        finally:
            guard.__exit__(None, None, None)

    def release(self, token):
        with self.lock:
            row = self.entries.pop(token, None)
            if row:
                row[2].__exit__(None, None, None)
        if row and not self.read_only:
            policy.maintain(row[0])

    def close(self):
        self.stop.set()
        with self.lock:
            for row in self.entries.values():
                row[2].__exit__(None, None, None)
            self.entries.clear()
