"""Prove owned real object-store persistence and exclusive ownership across normal restarts."""
import argparse,hashlib,json,secrets
from pathlib import Path
from original_object_store_runtime import OwnedObjectStore,signed_owned_request,require,sha


def verify(workspace, provider, pin, output):
    w,output=Path(workspace).resolve(),Path(output).resolve()
    require(not output.exists() and output.is_relative_to(w),'FRESH_OWN_LIFECYCLE_OUTPUT_REQUIRED');output.mkdir()
    bucket='own-persistence-'+secrets.token_hex(6);target='/'+bucket+'/marker.txt';payload=('owned persistence '+secrets.token_hex(16)).encode('ascii')
    first=second=contender=None;checks=0;result={'sourceEnvironmentOrCredentialsUsed':False,'sourceApplicationOrDatabaseStarted':False,'syntheticBucketOnly':True,'fullCloneReady':False}
    def check(value,code):
        nonlocal checks
        require(value,code);checks+=1
    def call(store,method,path,body=b''):
        return signed_owned_request(store.port,store.access,store.secret,method,path,body=body)
    try:
        first=OwnedObjectStore(w,output/'first',provider,pin);first.start()
        identity=first.result['dataOwnerId'];credentials_pin=sha(first.data_root/'credentials.private.json')
        check(call(first,'PUT','/'+bucket)[0]==200,'OWN_PERSISTENCE_BUCKET_CREATE')
        check(call(first,'PUT',target,payload)[0]==200,'OWN_PERSISTENCE_OBJECT_PUT')
        status,raw=call(first,'GET',target);check(status==200 and raw==payload,'OWN_PERSISTENCE_INITIAL_READBACK')
        contender=OwnedObjectStore(w,output/'contender',provider,pin);rejected=False
        try:contender.start()
        except OSError:rejected=True
        finally:contender.stop()
        check(rejected,'OWN_STORE_CONCURRENT_OWNER_NOT_REJECTED');check(contender.process is None,'CONTENDER_MUST_FAIL_BEFORE_PROCESS_START');check(first.process.poll() is None,'FIRST_OWNER_NOT_PRESERVED')
        one=first.stop();check(one.get('authenticatedStop',{}).get('status')==200 and one['exitCode']==0 and not one['forcedTermination'],'FIRST_OWNER_NATURAL_STOP')
        second=OwnedObjectStore(w,output/'second',provider,pin);second.start()
        check(second.result['dataOwnerId']==identity,'OWN_STORE_IDENTITY_NOT_REUSED');check(second.data_root==first.data_root,'OWN_STORE_DATA_ROOT_NOT_REUSED');check(sha(second.data_root/'credentials.private.json')==credentials_pin,'OWN_STORE_CREDENTIALS_CHANGED')
        status,raw=call(second,'GET',target);check(status==200 and raw==payload and hashlib.sha256(raw).digest()==hashlib.sha256(payload).digest(),'OWN_STORE_PERSISTENT_BYTES_CHANGED')
        check(call(second,'DELETE',target)[0]==204,'OWN_PERSISTENCE_PROBE_DELETE');check(call(second,'HEAD',target)[0]==404,'OWN_PERSISTENCE_PROBE_NOT_REMOVED');check(call(second,'DELETE','/'+bucket)[0]==204,'OWN_PERSISTENCE_BUCKET_REMOVE')
        two=second.stop();check(two.get('authenticatedStop',{}).get('status')==200 and two['exitCode']==0 and not two['forcedTermination'],'SECOND_OWNER_NATURAL_STOP')
        result.update(passedChecks=checks,actualProviderStarts=2,concurrentOwnerRejectedBeforePopen=True,sameDataAndCredentialsReused=True,objectBytesPreservedAcrossRestart=True,payloadBytes=len(payload),payloadSHA256=hashlib.sha256(payload).hexdigest(),syntheticObjectAndBucketRemoved=True,bothSignedStopsAndNaturalExit0=True)
    finally:
        for item in (contender,second,first):
            if item is not None and item.process is not None and item.process.poll() is None:item.stop()
        (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    require(checks==15,'OWN_PERSISTENCE_CHECK_COUNT');return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('workspace','provider-receipt','provider-receipt-sha256','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(verify(a.workspace,a.provider_receipt,a.provider_receipt_sha256,a.output)))


if __name__=='__main__':main()
