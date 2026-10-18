"""Temporary synthetic-test access gate; not the enterprise IAM adapter.

Credentials are salted PBKDF2 hashes in private deployment configuration.
Sessions and login challenges are bounded, memory-only and lost on restart.
"""
import hashlib
import re
import secrets
import threading
import time

ITERATIONS = 600_000
COOKIE = 'XNBY_TEST_SESSION'
LOGIN_COOKIE = 'XNBY_TEST_LOGIN'


def password_record(password):
    if not isinstance(password, str) or not 16 <= len(password) <= 128:
        raise ValueError('Test password must contain 16 to 128 characters')
    salt = secrets.token_bytes(24)
    return dict(salt=salt.hex(), digest=hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS).hex())


class AccessGate:
    def __init__(self, users, *, clock=time.monotonic):
        if not isinstance(users, dict) or not 1 <= len(users) <= 20:
            raise ValueError('Configure between one and twenty test accounts')
        for name, record in users.items():
            if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{2,31}', name):
                raise ValueError('Invalid test account name')
            if not isinstance(record, dict) or set(record) != {'salt', 'digest'}:
                raise ValueError('Invalid test password record')
            if not re.fullmatch('[0-9a-f]{48}', record['salt']) or not re.fullmatch('[0-9a-f]{64}', record['digest']):
                raise ValueError('Invalid test password digest')
        self.users = {name: dict(record) for name, record in users.items()}
        self.clock = clock
        self.lock = threading.Lock()
        self.hash_slots = threading.BoundedSemaphore(2)
        self.challenges = {}
        self.sessions = {}
        self.attempts = {}
        self.global_attempts = []
        self.dummy = dict(salt='00'*24, digest='00'*32)

    def _expire(self):
        now = self.clock()
        for collection in (self.challenges, self.sessions):
            for key in list(collection):
                if collection[key]['expires'] <= now:
                    del collection[key]
        self.global_attempts[:] = [t for t in self.global_attempts if t > now-60]
        for key in list(self.attempts):
            self.attempts[key][:] = [t for t in self.attempts[key] if t > now-900]
            if not self.attempts[key]:
                del self.attempts[key]

    def challenge(self):
        with self.lock:
            self._expire()
            if len(self.challenges) >= 128:
                return None
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            self.challenges[token] = dict(csrf=csrf, expires=self.clock()+300)
            return token, csrf

    def login(self, challenge, csrf, username, password):
        if not all(isinstance(v, str) for v in (challenge, csrf, username, password)):
            return None, 'invalid'
        if len(username) > 32 or not 1 <= len(password) <= 128:
            return None, 'invalid'
        with self.lock:
            self._expire()
            entry = self.challenges.pop(challenge, None)
            if not entry or not secrets.compare_digest(entry['csrf'], csrf):
                return None, 'invalid'
            # Shared gateway has one network identity. Bound both total work and per-account retries.
            key = username if username in self.users else '<unknown>'
            attempts = self.attempts.setdefault(key, [])
            if len(attempts) >= 8 or len(self.global_attempts) >= 30:
                return None, 'limited'
            attempts.append(self.clock())
            self.global_attempts.append(self.clock())
        if not self.hash_slots.acquire(blocking=False):
            return None, 'limited'
        try:
            record = self.users.get(username, self.dummy)
            digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(record['salt']), ITERATIONS).hex()
            matched = secrets.compare_digest(digest, record['digest']) and username in self.users
        finally:
            self.hash_slots.release()
        if not matched:
            return None, 'invalid'
        with self.lock:
            self._expire()
            if len(self.sessions) >= 64:
                return None, 'limited'
            token = secrets.token_urlsafe(32)
            self.sessions[token] = dict(user=username, csrf=secrets.token_urlsafe(32), expires=self.clock()+28_800)
            self.attempts.pop(username, None)
            return token, None

    def session(self, token):
        with self.lock:
            self._expire()
            value = self.sessions.get(token)
            return dict(value) if value else None

    def logout(self, token):
        with self.lock:
            self.sessions.pop(token, None)
