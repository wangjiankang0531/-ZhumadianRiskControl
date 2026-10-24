"""Exercise a real preview subprocess with an idle TCP preconnection; no app or auth fixture."""
import argparse,concurrent.futures,hashlib,http.client,json,os,socket,subprocess,sys,time
from pathlib import Path


def run(server_script,ready,output,expect_serial_block=False):
    server_script,ready,output=map(Path,(server_script,ready,output))
    if output.exists():raise ValueError('FRESH_PREVIEW_TRANSPORT_OUTPUT_REQUIRED')
    output.mkdir(parents=True);runtime=output/'runtime';
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    log=(output/'process.private.log').open('wb');process=subprocess.Popen([sys.executable,'-B',str(server_script),'--ready-receipt',str(ready),'--output',str(runtime),'--port',str(port)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    idle=second=None;result={'transportOnly':True,'applicationOrLoginSynthesized':False,'expectSerialBlock':expect_serial_block,'serverSourceSHA256':hashlib.sha256(server_script.read_bytes()).hexdigest()}
    def get(path):
        connection=http.client.HTTPConnection('127.0.0.1',port,timeout=1)
        try:
            connection.request('GET',path,headers={'Connection':'close'});response=connection.getresponse();raw=response.read(16384);return {'path':path,'status':response.status,'bytes':len(raw),'bodySHA256':hashlib.sha256(raw).hexdigest()}
        finally:connection.close()
    try:
        deadline=time.monotonic()+8
        while not (runtime/'ready.json').exists():
            if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('OWN_PREVIEW_FIXTURE_NOT_READY')
            time.sleep(.05)
        idle=socket.create_connection(('127.0.0.1',port),timeout=1)
        # Give the serial baseline time to accept the deliberately empty client.
        time.sleep(.1)
        if expect_serial_block:
            blocked=False
            try:get('/health')
            except TimeoutError:blocked=True
            assert blocked,'SERIAL_IDLE_BLOCK_NOT_REPRODUCED'
            result['serialIdleConnectionBlockedOtherHTTP']=True
            idle.close();idle=None
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:responses=list(pool.map(get,['/','/health','/missing','/health']))
            assert [r['status'] for r in responses]==[200,200,404,200]
            assert responses[0]['bodySHA256']==json.loads((runtime/'ready.json').read_bytes())['previewHTMLSHA256']
            idle.settimeout(3);assert idle.recv(1)==b'';idle.close();idle=None
            result.update(parallelHTTPRequests=4,responses=responses,idleConnectionTimedOut=True,HTMLBytesUnchanged=True)
            second=socket.create_connection(('127.0.0.1',port),timeout=1);time.sleep(.1)
        (runtime/'stop').write_text('finish-owned-preview-transport-test\n',encoding='ascii')
        process.wait(timeout=4);assert process.returncode==0
        result.update(ownProcessNaturalExit0=True,stopWithSecondIdleConnectionDidNotHang=not expect_serial_block)
    finally:
        for connection in (idle,second):
            if connection is not None:connection.close()
        if process.poll() is None:
            if runtime.exists():(runtime/'stop').write_text('finish-owned-preview-transport-test\n',encoding='ascii')
            try:process.wait(timeout=3)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5);result['forcedTermination']=True
        log.close();result['exitCode']=process.poll();(output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--server-script',type=Path,required=True);p.add_argument('--ready-receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--expect-serial-block',action='store_true');a=p.parse_args();print(json.dumps(run(a.server_script,a.ready_receipt,a.output,a.expect_serial_block)))


if __name__=='__main__':main()
