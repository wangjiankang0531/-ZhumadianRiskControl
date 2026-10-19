"""HTTPS ingress adapter for synthetic business, behind a fixed loopback proxy.

Never bind this service to a public interface. The TLS proxy must overwrite the
two ingress headers, reject non-HTTPS requests, and only route the fixed prefix.
"""
import argparse
import html
import json
import re
import secrets
import sys
import threading
from http.server import ThreadingHTTPServer
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.reference_access import AccessGate, COOKIE, LOGIN_COOKIE
from services.reference_demo import DemoError
from tools.serve_reference_demo import Handler, make_server


class BoundedPublicServer(ThreadingHTTPServer):
    """Bound slow inbound connections as well as password hashing and sessions."""
    def __init__(self, *args, **kwargs):
        self.request_slots = threading.BoundedSemaphore(32)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.request_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except Exception:
            self.request_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.request_slots.release()


def validate_config(config):
    if not isinstance(config, dict) or set(config) != {'schema', 'origin', 'prefix', 'port', 'proxyKey', 'users'}:
        raise ValueError('Invalid public-test configuration')
    u = urlsplit(config['origin'])
    if config['schema'] != 'xnby.reference.public.v1' or u.scheme != 'https' or not re.fullmatch(r'[a-z0-9.-]+', u.netloc) or u.path or u.query or u.fragment:
        raise ValueError('An exact HTTPS origin is required')
    if not re.fullmatch(r'/[a-z][a-z0-9-]{0,31}/', config['prefix']):
        raise ValueError('A single fixed directory prefix is required')
    if type(config['port']) is not int or not 1024 <= config['port'] <= 65535:
        raise ValueError('Invalid loopback port')
    if not isinstance(config['proxyKey'], str) or not re.fullmatch('[0-9a-f]{64}', config['proxyKey']):
        raise ValueError('A private random ingress key is required')
    return AccessGate(config['users'])


class PublicHandler(Handler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, fmt, *args):
        # Do not log credentials, cookies, request bodies or business query strings.
        if len(args) >= 2:
            sys.stderr.write('synthetic-test request status=' + str(args[1]) + '\n')

    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        super().end_headers()

    def json(self, status, value):
        if status == 200 and isinstance(value, dict) and 'workFormSchema' in value and self.session_value:
            value = dict(value, deployment=dict(mode='public-business', user=self.session_value['user'], csrf=self.session_value['csrf']))
        super().json(status, value)

    def ingress(self):
        self.session_value = None
        for name in ('Host', 'X-XNBY-Ingress', 'X-XNBY-Public-Origin'):
            if len(self.headers.get_all(name, [])) != 1:
                raise DemoError(403, '测试入口无效')
        if self.headers['Host'] not in self.server.allowed_hosts or not secrets.compare_digest(self.headers['X-XNBY-Ingress'], self.server.public_config['proxyKey']) or self.headers['X-XNBY-Public-Origin'] != self.server.public_config['origin']:
            raise DemoError(403, '测试入口无效')
        if not self.path.startswith('/') or self.path.startswith('//'):
            raise DemoError(400, '请求路径无效')
        self.original_path = self.path
        prefix = self.server.public_config['prefix']
        if not urlsplit(self.path).path.startswith(prefix):
            raise DemoError(404, '资源不存在')
        self.path = '/' + self.path[len(prefix):]
        self.cookies = SimpleCookie()
        try:
            if len(self.headers.get('Cookie', '')) > 4096:
                raise DemoError(400, '请求头过长')
            self.cookies.load(self.headers.get('Cookie', ''))
        except CookieError:
            raise DemoError(400, 'Cookie无效')
        self.session_token = self.cookie(COOKIE)
        self.session_value = self.server.access_gate.session(self.session_token)

    def cookie(self, name):
        value = self.cookies.get(name)
        return value.value if value else ''

    def set_cookie(self, name, value, age):
        prefix = self.server.public_config['prefix']
        self.send_header('Set-Cookie', f'{name}={value}; Path={prefix}; Max-Age={age}; Secure; HttpOnly; SameSite=Strict')

    def empty(self, status, *, location=None, cookie=None):
        self.send_response(status)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', '0')
        if location:
            self.send_header('Location', self.server.public_config['prefix'] + location)
        if cookie:
            self.set_cookie(*cookie)
        self.end_headers()

    def trusted(self, write=False):
        if not self.session_value:
            raise DemoError(401, '测试登录已过期，请重新登录')
        if write and (self.headers.get_all('Origin', []) != [self.server.public_config['origin']] or self.headers.get_all('X-XNBY-Demo', []) != [self.server.demo_token]):
            raise DemoError(403, '模拟写入来源无效')

    def login_page(self):
        if self.session_value:
            return self.empty(303, location='')
        challenge = self.server.access_gate.challenge()
        if not challenge:
            return self.json(429, dict(error='登录请求较多，请稍后重试'))
        token, csrf = challenge
        prefix = html.escape(self.server.public_config['prefix'], quote=True)
        raw = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>信能本源 · 测试登录</title>
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:radial-gradient(at top right,#1d416d,#081628 65%);font:16px system-ui;color:#e8f1ff}}main{{max-width:390px;margin:24px;padding:38px;background:#11273b;border:1px solid #315774;border-radius:20px;box-shadow:0 25px 80px #0007}}b{{color:#70dfec;letter-spacing:.15em}}h1{{font-size:25px}}p{{color:#adc3d9;line-height:1.7}}label{{display:block;margin:20px 0 8px}}input{{box-sizing:border-box;width:100%;padding:13px;border:1px solid #456680;border-radius:8px;background:#081c30;color:white;font:inherit}}button{{width:100%;margin-top:25px;padding:14px;background:#57c9df;color:#062337;border:0;border-radius:8px;font:700 16px system-ui;cursor:pointer}}small{{display:block;margin-top:23px;color:#aac1d5;line-height:1.7}}</style>
<main><b>XNBY · 信能本源</b><h1>驻马店重大风险防控</h1><p>公网模拟业务测试。请使用分配的测试账号登录。</p><form method="post" action="{prefix}auth/login"><input type="hidden" name="csrf" value="{csrf}"><label for="user">测试账号</label><input id="user" name="username" maxlength="32" required autocomplete="username"><label for="pass">密码</label><input id="pass" type="password" name="password" maxlength="128" required autocomplete="current-password"><button type="submit">登录测试环境</button></form><small>本环境仅含合成企业与业务记录。三维测试继续在本地设备进行；测试账号不代表正式统一身份认证。</small></main></html>'''.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(raw)))
        self.set_cookie(LOGIN_COOKIE, token, 300)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        try:
            self.ingress()
            path = urlsplit(self.path).path
            if path == '/auth/login':
                return self.login_page()
            if not self.session_value and path in ('/', '/reference-demo.html'):
                return self.empty(303, location='auth/login')
            super().do_GET()
        except DemoError as e:
            self.json(e.status, dict(error=e.message))
        except (ValueError, TypeError):
            self.json(400, dict(error='请求格式无效'))

    def checked_body(self, maximum):
        if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
            raise DemoError(400, '请求长度无效')
        length = int(self.headers['Content-Length'])
        if not 1 <= length <= maximum:
            raise DemoError(413, '请求过大')
        raw = self.rfile.read(length)
        if len(raw) != length:
            raise DemoError(400, '请求未完整传输')
        return raw

    def do_POST(self):
        try:
            self.ingress()
            path = urlsplit(self.path).path
            if self.headers.get_all('Origin', []) != [self.server.public_config['origin']]:
                raise DemoError(403, '操作来源无效')
            if path == '/auth/login':
                if self.headers.get('Content-Type') != 'application/x-www-form-urlencoded':
                    raise DemoError(415, '登录格式无效')
                form = parse_qs(self.checked_body(2048).decode('utf-8'), max_num_fields=3, keep_blank_values=True)
                if set(form) != {'username', 'password', 'csrf'} or any(len(v) != 1 for v in form.values()):
                    raise DemoError(400, '登录格式无效')
                token, error = self.server.access_gate.login(self.cookie(LOGIN_COOKIE), form['csrf'][0], form['username'][0], form['password'][0])
                if error:
                    raise DemoError(429 if error == 'limited' else 401, '登录失败，请返回登录页重试')
                self.send_response(303)
                self.send_header('Location', self.server.public_config['prefix'])
                self.send_header('Content-Length', '0')
                self.send_header('Cache-Control', 'no-store')
                self.set_cookie(LOGIN_COOKIE, '', 0)
                self.set_cookie(COOKIE, token, 28_800)
                return self.end_headers()
            if path == '/auth/logout':
                if not self.session_value:
                    raise DemoError(401, '测试登录已过期')
                if self.headers.get_all('X-XNBY-CSRF', []) != [self.session_value['csrf']]:
                    raise DemoError(403, '操作来源无效')
                self.server.access_gate.logout(self.session_token)
                return self.empty(204, cookie=(COOKIE, '', 0))
            # Reject ambiguous framing before the existing bounded business parser reads the body.
            if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
                raise DemoError(400, '请求长度无效')
            super().do_POST()
        except DemoError as e:
            self.json(e.status, dict(error=e.message))
        except (ValueError, TypeError):
            self.json(400, dict(error='请求格式无效'))


def make_public_server(config, static, database):
    access = validate_config(config)
    server = make_server(config['port'], static, database, server_type=BoundedPublicServer, handler_type=PublicHandler)
    server.public_config = dict(config)
    server.access_gate = access
    return server


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--static', type=Path, required=True)
    p.add_argument('--database', type=Path, required=True)
    a = p.parse_args()
    config = json.loads(a.config.read_text('utf-8'))
    server = make_public_server(config, a.static, a.database)
    print(json.dumps(dict(loopback=f'127.0.0.1:{server.server_port}', origin=config['origin'], prefix=config['prefix'], synthetic=True)), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
