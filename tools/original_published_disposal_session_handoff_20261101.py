"""Only the owned synthetic UI driver may refresh its HTTP test user's session in memory."""
import contextlib,hmac,json,re,secrets,threading,urllib.parse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import verify_emergency_business_http_20261030 as c

@contextlib.contextmanager
def handoff(root,request,headers,platform_port,business_port,phase,account):
    assert re.fullmatch(r'full-business-main-r[1-9][0-9]*',root.name)
    assert root.parent==c.W and phase in ('task-dispose','task-reopen')
    own=c.read(root/'own-normal-login.private.json')
    assert own['credentialsSynthetic']and set(headers)=={'own_operator_a','own_reviewer_b'}
    assert account in ('own_operator_a','own_reviewer_b')
    operator=own['accounts'][account]
    assert re.fullmatch(r'a531[0-9a-f]{28}',operator['id'])
    expected_id,expected_role,system=operator['id'],operator['roleId'],own['systemCode'];own.clear()
    nonce=secrets.token_urlsafe(32);used=False;lock=threading.Lock()
    record={'phase':phase,'accepted':False,'wrongNonceRejected':0,'replayRejected':0,
        'sameSyntheticOperatorAndOriginalRoleRequired':True,'tokenOrNonceWrittenToCoordinatorEvidence':False}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def answer(self,status,accepted=False):
            body=json.dumps({'accepted':accepted}).encode()
            self.send_response(status);self.send_header('Content-Type','application/json')
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def do_POST(self):
            nonlocal used
            self.connection.settimeout(5)
            if self.client_address[0]!='127.0.0.1'or self.path!='/owned-compiled-login-session':
                self.answer(404);return
            supplied=self.headers.get('X-Own-Handoff-Nonce','')
            if not hmac.compare_digest(supplied.encode(),nonce.encode()):
                record['wrongNonceRejected']+=1;self.answer(403);return
            with lock:
                if used:record['replayRejected']+=1;self.answer(409);return
                used=True
            parsed={};stage='bounded-json'
            try:
                n=int(self.headers.get('Content-Length','0'));assert 1<=n<=8192
                parsed=json.loads(self.rfile.read(n));assert set(parsed)=={'token'}
                token=parsed['token'];stage='authorization-grammar'
                assert isinstance(token,str)and 16<len(token)<=4096
                record['authorizationHasOrdinarySpace']=' 'in token
                assert token.isascii()and all(32<=ord(x)<127 for x in token)
                stage='original-current-user'
                status,value=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode='+urllib.parse.quote(system,safe=''),authorization=token)
                info=(value.get('data')or{}).get('userInfo')or{}
                record.update(currentUserHTTPStatus=status,currentUserBusinessCode=value.get('code'),
                    syntheticUserIdMatched=info.get('userId')==expected_id,
                    syntheticRoleMatched=expected_role in(info.get('roleIds')or[]))
                stage='original-owner-and-role'
                assert status==200 and value.get('code')==200 and info.get('userId')==expected_id
                assert expected_role in(info.get('roleIds')or[])and str(info.get('isAdministrator')).lower()in('false','0')
                previous=headers[account]
                stage='previous-session-probe'
                old_status,old_value=request(business_port,'GET','/serv/riskLevel/getPage?current=1&size=5',authorization=previous)
                headers[account]=token
                record.update(accepted=True,originalCurrentUserAndRoleVerified=True,
                    tokenChanged=not hmac.compare_digest(previous,token),
                    previousTokenHTTPStatus=old_status,previousTokenBusinessCode=old_value.get('code'),
                    previousTokenRejected=old_status==401 and old_value.get('code')==200001)
                previous='';token='';self.answer(200,True)
            except Exception as error:
                record.update(ownerValidationFailed=True,failureStage=stage,failureType=type(error).__name__);self.answer(403)
            finally:parsed.clear()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.05},daemon=True);thread.start()
    descriptor={'url':'http://127.0.0.1:'+str(server.server_port)+'/owned-compiled-login-session','nonce':nonce}
    try:yield descriptor,record
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);descriptor.clear();nonce=''
        record['serverStopped']=not thread.is_alive()
        c.dump(root/('compiled-ui-session-handoff-'+phase+'.json'),record)
        assert record['serverStopped'],'OWN_HANDOFF_SERVER_STOP_REQUIRED'
