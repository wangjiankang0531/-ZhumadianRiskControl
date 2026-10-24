"""Temporary original-H5 iframe viewport preview; no browser-wide resizing or application changes."""
import argparse,datetime,hashlib,html,http.server,json,pathlib,re,time,urllib.parse

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ready-receipt',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--port',type=int,default=18892);a=p.parse_args()
 if a.output.exists() or not 1024<=a.port<=65535:raise ValueError('FRESH_OUTPUT_AND_LOCAL_PORT_REQUIRED')
 ready=json.loads(a.ready_receipt.read_bytes());run=a.ready_receipt.parent
 if not ready.get('originalBusinessSemanticsAppliedToNewProcess') or ready.get('businessInternalPlatformObservation',{}).get('passed')!='true' or (run/'receipt.json').exists():raise ValueError('LIVE_ORIGINAL_SEMANTIC_CANDIDATE_REQUIRED')
 url=ready['mobileURL'];u=urllib.parse.urlsplit(url)
 if u.scheme!='http' or u.hostname!='127.0.0.1' or u.port is None or u.path!='/zhumadian/h5/' or u.query or u.fragment or u.username or u.password:raise ValueError('EXPLICIT_OWN_ORIGINAL_H5_REQUIRED')
 end=datetime.datetime.fromisoformat(ready['readyAt']).timestamp()+ready['remainingLeaseSeconds'];remaining=end-time.time()
 if not 1<remaining<=7200:raise ValueError('LIVE_REMAINING_LEASE_REQUIRED')
 a.output.mkdir();body=('''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>天津原版手机网页尺寸预览</title><style>body{margin:0;background:#eef2f7;color:#17324d;font:15px system-ui,sans-serif}header{text-align:center;padding:16px 12px}h1{font-size:20px;margin:0 0 10px}p{margin:8px 0}button,a{font:inherit}button{padding:7px 15px;margin:3px;border:1px solid #a9bed1;background:#fff;color:#17324d;border-radius:6px;cursor:pointer}button[aria-pressed=true]{background:#245d96;color:#fff}main{display:flex;justify-content:center;padding:0 10px 24px}iframe{display:block;width:390px;height:844px;border:1px solid #b8c7d6;background:#fff;box-shadow:0 5px 20px #1232;border-radius:8px}small{color:#526578}</style></head><body><header><h1>天津原版手机网页尺寸预览</h1><div><button data-width="375" aria-pressed="false">375 px</button><button data-width="390" aria-pressed="true">390 px</button><button data-width="430" aria-pressed="false">430 px</button></div><p><output id="size">390 × 844</output>　<a target="_blank" rel="noopener" href="'''+html.escape(url,quote=True)+'''">直接打开手机网页</a></p><small>以下为原手机网页的浏览器尺寸预览，仍需手机实机验收。</small></header><main><iframe id="phone" title="天津原版手机网页" src="'''+html.escape(url,quote=True)+'''"></iframe></main><script>const f=document.getElementById('phone'),s=document.getElementById('size');document.querySelectorAll('button[data-width]').forEach(b=>b.addEventListener('click',()=>{const w=Number(b.dataset.width);if(![375,390,430].includes(w))return;f.style.width=w+'px';s.textContent=w+' × 844';document.querySelectorAll('button[data-width]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));}));</script></body></html>''').encode('utf-8')
 (a.output/'preview.html').write_bytes(body)
 class Handler(http.server.BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   if self.path=='/':payload,kind,status=body,'text/html; charset=utf-8',200
   elif self.path=='/health':payload,kind,status=b'{"viewportPreviewOnly":true,"businessLoginVerified":false}','application/json',200
   else:payload,kind,status=b'Not found','text/plain',404
   self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
 server=http.server.HTTPServer(('127.0.0.1',a.port),Handler);server.timeout=.5
 result={'readyReceiptSHA256':hashlib.sha256(a.ready_receipt.read_bytes()).hexdigest(),'previewHTMLSHA256':hashlib.sha256(body).hexdigest(),'previewURL':'http://127.0.0.1:'+str(a.port)+'/','originalMobileURL':url,'iframeViewportWidths':[375,390,430],'iframeHeight':844,'browserWideViewportChanged':False,'originalFrontendOrGatewayChanged':False,'loginOrCaptchaSubmitted':False,'physicalMobileVerified':False,'fullCloneReady':False,'expiresAt':datetime.datetime.fromtimestamp(end).astimezone().isoformat()}
 (a.output/'ready.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
 try:
  while time.time()<end and not (run/'receipt.json').exists() and not (a.output/'stop').exists():server.handle_request()
 finally:
  server.server_close();result.update(stoppedAt=datetime.datetime.now().astimezone().isoformat(),stopped=True);(a.output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('OWN_MOBILE_VIEWPORT_PREVIEW_STOPPED',flush=True)
if __name__=='__main__':main()
