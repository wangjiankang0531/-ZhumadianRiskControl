"""Actual loopback checks for captured-byte serving; defaults only, not query/filter equivalence."""
import argparse
import http.client
import json
from pathlib import Path
import threading
from original_bigscreen_mock_snapshot import SnapshotServer,load_capture


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture-receipt',required=True);p.add_argument('--capture-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output)
    if out.exists():raise ValueError('FRESH_TEST_OUTPUT_REQUIRED')
    dataset=load_capture(a.capture_receipt,a.capture_sha256);server=SnapshotServer(dataset);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();port=server.server_address[1];checks=0
    def request(method,path):
        c=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
        try:c.request(method,path,headers={'Authorization':'bearer own-synthetic-only','Cookie':'token=own-synthetic-only'});r=c.getresponse();body=r.read(2*1024**2+1);return r.status,body
        finally:c.close()
    try:
        for route,expected in dataset.items():
            status,body=request('GET',server.prefix+route);assert status==200 and body==expected;checks+=1
        route=next(iter(dataset));status,body=request('GET',server.prefix+route+'?own-synthetic-filter=1');assert status==200 and body==dataset[route];checks+=1
        status,body=request('HEAD',server.prefix+route);assert status==200 and body==b'';checks+=1
        for route_path in (server.prefix+'/unknown',server.prefix+'/../private',server.prefix+'/%2e%2e/private','/outside'):
            status,_=request('GET',route_path);assert status==404;checks+=1
        status,_=request('POST',server.prefix+route);assert status==405;checks+=1
        rejected=False
        try:load_capture(a.capture_receipt,'0'*64)
        except ValueError:rejected=True
        assert rejected;checks+=1
    finally:server.shutdown();server.server_close();thread.join(timeout=3)
    assert not thread.is_alive();checks+=1
    result={'passedChecks':checks,'capturedRoutesServed':len(dataset),'allOriginalBytesExact':True,'onlyLoopbackListener':True,'realCookiesOrCredentialsUsed':False,'networkForwardingImplemented':False,'defaultSnapshotsOnly':True,'queryOrWriteSemanticsVerified':False,'serverClosed':True,'currentFrontendOrGatewayChanged':False,'fullCloneReady':False};out.mkdir();(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))


if __name__=='__main__':main()
