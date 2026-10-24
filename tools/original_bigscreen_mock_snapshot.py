"""Serve captured original default Mock JSON locally; no network forwarding or credential handling."""
import hashlib
import http.server
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def load_capture(receipt_path, receipt_pin):
    receipt_path=Path(receipt_path).resolve(strict=True)
    raw=receipt_path.read_bytes()
    if not re.fullmatch('[0-9a-f]{64}',receipt_pin) or hashlib.sha256(raw).hexdigest()!=receipt_pin:
        raise ValueError('EXPLICIT_CAPTURE_PIN_REQUIRED')
    capture=json.loads(raw)
    if capture.get('privateProjectParametersCookiesOrTokensSent') is not False or capture.get('requestedRoutes')!=16:
        raise ValueError('KNOWN_ANONYMOUS_SIXTEEN_ROUTE_CAPTURE_REQUIRED')
    root=receipt_path.parent;dataset={};total=0
    for row in capture['routes']:
        route=row['route'];relative=row.get('responseFile','')
        if row.get('authorizationOrCookiesSent') is not False or row.get('queryParametersSent') is not False or row.get('redirectsFollowed') is not False:raise ValueError('ANONYMOUS_DEFAULT_CAPTURE_REQUIRED')
        if not re.fullmatch('/[A-Za-z0-9/_-]{1,200}',route) or '..' in route or '//' in route or route in dataset:
            raise ValueError('EXACT_UNIQUE_CAPTURED_ROUTE_REQUIRED')
        if not re.fullmatch('responses/[0-9a-f]{64}[.]json',relative):
            raise ValueError('CAPTURE_RESPONSE_FILE_SCOPE_REQUIRED')
        file=root/relative;stat=file.lstat()
        if not file.is_file() or file.is_symlink() or getattr(stat,'st_file_attributes',0)&0x400 or file.resolve().parent!=(root/'responses').resolve() or stat.st_size>2*1024**2:
            raise ValueError('REGULAR_BOUNDED_CAPTURE_REQUIRED')
        body=file.read_bytes();total+=len(body)
        if hashlib.sha256(body).hexdigest()!=row['sha256'] or row.get('status')!=200 or json.loads(body).get('success') is not True:
            raise ValueError('ORIGINAL_CAPTURE_BYTES_OR_RESPONSE_MISMATCH')
        if total>32*1024**2:raise ValueError('CAPTURE_TOTAL_LIMIT')
        dataset[route]=body
    if len(dataset)!=16:raise ValueError('ALL_CAPTURED_ROUTES_REQUIRED')
    return dataset


class SnapshotServer(http.server.ThreadingHTTPServer):
    def __init__(self,dataset,port=0,prefix='/zhumadian/api/reference-mock'):
        if not re.fullmatch('/[A-Za-z0-9_/-]+',prefix) or '//' in prefix or '..' in prefix:
            raise ValueError('OWN_MOCK_MOUNT_REQUIRED')
        self.dataset=dict(dataset);self.prefix=prefix.rstrip('/')
        class Handler(http.server.BaseHTTPRequestHandler):
            timeout=2
            def log_message(self,*args):pass
            def reply(self,head=False):
                route=urlsplit(self.path).path
                key=route[len(self.server.prefix):] if route.startswith(self.server.prefix+'/') else None
                body=self.server.dataset.get(key)
                status=200 if body is not None else 404
                if body is None:body=b'{"code":404,"success":false}'
                self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('Connection','close');self.end_headers();self.close_connection=True
                if not head:
                    try:self.wfile.write(body)
                    except (BrokenPipeError,ConnectionResetError):pass
            def do_GET(self):self.reply()
            def do_HEAD(self):self.reply(head=True)
            def do_POST(self):
                self.send_response(405);self.send_header('Allow','GET, HEAD');self.send_header('Content-Length','0');self.send_header('Connection','close');self.end_headers();self.close_connection=True
        super().__init__(('127.0.0.1',port),Handler)
