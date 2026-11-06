"""Own the existing six synthetic loopback destinations before starting G."""
from pathlib import Path
import http.server,json,threading,urllib.parse
G=Path('D:/Project/Zhumadian/_g/Application')
class OwnedDockReceiver:
 def __init__(self):self.server=None;self.thread=None;self.requests=0
 def start(self):
  cfg=json.loads((G/'private/server-configuration.json').read_bytes());paths=set()
  for k in ['riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird']:
   u=urllib.parse.urlsplit(cfg['configuration']['business'][k+'Url'])
   assert u.scheme=='http'and u.hostname=='127.0.0.1'and u.port==18990 and not u.username and not u.password
   paths.add(u.path or '/')
  cfg=None;owner=self
  class Handler(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def handle_read(self):
    self.connection.settimeout(5)
    n=int(self.headers.get('Content-Length','0'));assert 0<=n<=1024*1024
    if n:self.rfile.read(n)
    owner.requests+=1;valid=urllib.parse.urlsplit(self.path).path in paths
    raw=b'{"code":200,"success":true}'if valid else b'{"code":404}'
    self.send_response(200 if valid else 404);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
   do_GET=handle_read;do_POST=handle_read
  class Server(http.server.HTTPServer):allow_reuse_address=False
  # A failed bind is a pre-install refusal; never reuse or stop an unknown listener.
  self.server=Server(('127.0.0.1',18990),Handler)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def close(self):
  if self.server:self.server.shutdown();self.server.server_close()
  if self.thread:self.thread.join(8);assert not self.thread.is_alive()
