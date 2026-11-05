"""Anonymous public HTTPS checks. Never authenticates, invokes business APIs or deploys."""
from pathlib import Path
import argparse
import datetime
import hashlib
import http.client
import importlib.util
import json
import socket
import ssl
import time

V=Path(__file__).resolve().parent
WRAPPER=Path('D:/Project/Zhumadian/Document/Deployment/public_test_event_write_results_r48_20261105/delivery/deploy_event_write_results_r48.py')
MANIFEST=WRAPPER.parent/'delivery-manifest.json'
MANIFEST_SHA='ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a'
HOST='www.joinlinksmart.com'
ADDRESS='101.201.65.94'
LIMIT=4*1024*1024

def save(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def load_contract():
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest()==MANIFEST_SHA
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
    assert hashlib.sha256(WRAPPER.read_bytes()).hexdigest()==manifest['files'][WRAPPER.name]['sha256']
    spec=importlib.util.spec_from_file_location('r48_static_contract_r1045',WRAPPER)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert len(module.STATIC_EXPECTED)==9
    return module

def fetch(path,accept):
    assert path.startswith('/zhumadian/') and '?'not in path and '..'not in path
    started=time.perf_counter()
    tls=ssl.create_default_context().wrap_socket(socket.create_connection((ADDRESS,443),timeout=20),server_hostname=HOST)
    conn=http.client.HTTPConnection(HOST,timeout=30)
    conn.sock=tls
    try:
        conn.request('GET',path,headers={'Host':HOST,'Accept-Encoding':accept,'Connection':'close','User-Agent':'XNBY-Scoped-Public-Static-Verification/1.0'})
        response=conn.getresponse()
        first=time.perf_counter()-started
        body=response.read(LIMIT+1)
        assert len(body)<=LIMIT,'RESPONSE_SIZE_BOUND'
        headers={k.lower():v for k,v in response.getheaders()}
        return response.status,headers,body,{'ttfbSeconds':round(first,4),'totalSeconds':round(time.perf_counter()-started,4)}
    finally:
        conn.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--observe-entry-only',action='store_true')
    options=parser.parse_args()
    contract=load_contract()
    root=V/('r48-public-entry-observation-r1045'if options.observe_entry_only else'r48-public-static-acceptance-r1045')
    root.mkdir(exist_ok=False)
    rows=[]
    try:
        for path in ['/zhumadian/home','/zhumadian/emergency/home/index']:
            status,headers,body,timing=fetch(path,'identity')
            row={'path':path,'status':status,'wireBytes':len(body),'bodySHA256':hashlib.sha256(body).hexdigest(),
                'htmlNoStore':'no-store'in headers.get('cache-control',''),
                'containsR48EmergencyEntry':b'wf-index-C-9ICbMl.js'in body,
                'containsNewHomeTransferStyle':b'xnby-home-transfer-162b8ebe4004d78f.css'in body,**timing}
            rows.append(row)
            save(root/'measurements.json',rows)
            assert status==200 and row['htmlNoStore'],'HTML_STATUS_OR_CACHE_POLICY'
            if not options.observe_entry_only:
                assert row['containsR48EmergencyEntry']if '/emergency/'in path else row['containsNewHomeTransferStyle'],'EXACT_R48_HTML_ENTRY'
        if not options.observe_entry_only:
            for path,expected in contract.STATIC_EXPECTED.items():
                requested=expected.get('encoding','gzip')
                encodings=[('gzip','gzip'),('gzip;q=0, *;q=1','identity')]if requested=='gzip'else[('identity','identity')]
                for accept,decoded_mode in encodings:
                    status,headers,body,timing=fetch(path,accept)
                    item=contract.validate_static_response(path,decoded_mode,status,headers,body)
                    item.update(path=path,**timing)
                    rows.append(item)
                    save(root/'measurements.json',rows)
        report={'schema':'xnby.r48.external-static-verification.v1',
            'measuredAt':datetime.datetime.now().astimezone().isoformat(),'passed':True,
            'observationOnly':options.observe_entry_only,'checks':len(rows),'rows':rows,
            'manifestSHA256':MANIFEST_SHA,'actualExternalHTTPS':True,'TLSCertificateAndHostVerified':True,
            'DNSBypassedButTLSNotBypassed':True,'cookieOrAuthorizationSent':False,
            'businessAPIsOrRowsRead':False,'publicMutation':False,
            'serverDeploymentPerformedByThisTool':False,'normalLoginUIAccepted':False,
            'browserWarmCacheOrAllModulePerformanceAccepted':False,'fullCloneReady':False}
        save(root/'verified-result.json',report)
        print(json.dumps({k:v for k,v in report.items()if k!='rows'},ensure_ascii=False))
        if options.observe_entry_only:print(json.dumps(rows,ensure_ascii=False))
    except BaseException as exc:
        save(root/'failure.json',{'type':type(exc).__name__,'completedChecks':len(rows),
            'observationOnly':options.observe_entry_only,'noDeploymentOrBusinessWrites':True})
        raise

if __name__=='__main__':main()
