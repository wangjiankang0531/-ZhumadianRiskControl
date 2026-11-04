"""Read-only predecessor proof for the next owned task lifecycle; no runtime adoption or SQL."""
import hashlib, json, re, struct

def need(value, code):
    if not value: raise ValueError(code)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def pairs(items):
    result={}
    for k,v in items:
        need(k not in result,'DUPLICATE_CHAIN_METADATA_KEY'); result[k]=v
    return result

def object_json(raw):
    need(isinstance(raw,bytes) and 0<len(raw)<=1048576,'BOUNDED_CHAIN_JSON_REQUIRED')
    result=json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=lambda _:need(False,'NONFINITE_CHAIN_JSON'))
    need(isinstance(result,dict),'CHAIN_OBJECT_REQUIRED'); return result

def properties(raw):
    need(isinstance(raw,bytes) and 0<len(raw)<16384,'BOUNDED_CHAIN_JOURNAL_REQUIRED')
    output={}
    def decode(value):
        result=''; i=0
        while i<len(value):
            c=value[i];i+=1
            if c=='\\':
                need(i<len(value),'TRUNCATED_JOURNAL_ESCAPE'); c=value[i];i+=1
                if c=='u':
                    need(i+4<=len(value) and re.fullmatch('[0-9a-fA-F]{4}',value[i:i+4]),'INVALID_JOURNAL_UNICODE_ESCAPE')
                    c=chr(int(value[i:i+4],16));i+=4
                else:c={'t':'\t','r':'\r','n':'\n','f':'\f'}.get(c,c)
            need(ord(c)>=32 and ord(c)!=127,'JOURNAL_CONTROL_CHARACTER_REFUSED'); result+=c
        return result
    for line in raw.decode('ascii').splitlines():
        if not line or line.startswith(('#','!')):continue
        need('=' in line,'EXPLICIT_JOURNAL_KEY_VALUE_REQUIRED')
        k,v=line.split('=',1); need(re.fullmatch('[A-Za-z][A-Za-z0-9]*',k) and k not in output,'DUPLICATE_OR_INVALID_JOURNAL_KEY')
        output[k]=decode(v)
    return output

def rows_sha256(rows):
    need(isinstance(rows,list) and len(rows)==2,'EXACT_TWO_CHAIN_ROWS_REQUIRED')
    digest=hashlib.sha256(); ids=set(); codes=set()
    for row in rows:
        need(isinstance(row,list) and len(row)==17 and all(v is None or isinstance(v,str) for v in row),'EXACT_CHAIN_ROW_FIELDS_REQUIRED')
        need(isinstance(row[0],str) and re.fullmatch('a546[0-9a-f]{28}',row[0]) and row[1]=='OWN_MANAGER_CALLBACK_'+row[0], 'OWN_CHAIN_CALLBACK_ID_REQUIRED')
        need(row[0] not in ids and row[1] not in codes,'DISTINCT_CHAIN_CALLBACK_ROWS_REQUIRED');ids.add(row[0]);codes.add(row[1])
        need(row[3]=='3' and row[4]=='3' and row[8]=='1' and isinstance(row[5],str) and len(row[5])<=131072,'ORIGINAL_CHAIN_CALLBACK_KIND_REQUIRED')
        for value in row:
            if value is None:digest.update(struct.pack('>i',-1))
            else:
                raw=value.encode('utf8');digest.update(struct.pack('>i',len(raw)));digest.update(raw)
    return digest.hexdigest()

def verify_predecessor(plan_raw,journal_raw,result_raw,*,expected_journal_sha256,expected_release_sha256,expected_application,expected_stage_root,expected_data_directory):
    need(re.fullmatch('[0-9a-f]{64}',expected_journal_sha256 or '') and sha(journal_raw)==expected_journal_sha256,'PINNED_PREDECESSOR_JOURNAL_REQUIRED')
    p=object_json(plan_raw); j=properties(journal_raw); r=object_json(result_raw)
    keys={'schema','attemptId','databaseUUID','dataDirectory','releaseSHA256','controllerPID','planSHA256','beforeRowsSHA256','afterRowsSHA256','stage','journalPath','phase'}
    need(set(j)==keys and j['schema']=='xnby.owned-callback-provisioning.r658.v1','EXACT_PREDECESSOR_JOURNAL_SCHEMA_REQUIRED')
    need(r.get('passed') is True and r.get('actualJobDescendantsZero') is True and r.get('mutationRetried') is False and r.get('journalSHA256')==expected_journal_sha256,'SUCCESSFUL_PREDECESSOR_RESULT_REQUIRED')
    need(j['phase']=='readback-verified' and j['stage']=='normal-restart' and p.get('stage')=='normal-restart','VERIFIED_PREDECESSOR_PHASE_REQUIRED')
    need(j['planSHA256']==sha(plan_raw),'PREDECESSOR_PLAN_BINDING_REQUIRED')
    need(p.get('schema')=='xnby.owned-original-callback-plan.r662.v1' and p.get('onlyOwnedRuntimeFixture') is True and p.get('application')==expected_application and p.get('attempt')==expected_stage_root,'EXACT_PREDECESSOR_APPLICATION_AND_STAGE_REQUIRED')
    need(j['journalPath']==expected_stage_root+'\\callback-normal-restart-journal.private.properties' and j['dataDirectory']==expected_data_directory,'EXACT_PREDECESSOR_STORAGE_SCOPE_REQUIRED')
    need(p.get('releaseSHA256')==expected_release_sha256 and j['releaseSHA256']==expected_release_sha256,'EXACT_PREDECESSOR_RELEASE_REQUIRED')
    need(re.fullmatch('[0-9a-f]{32}',j['attemptId']) and p.get('attemptId')==j['attemptId'],'PREDECESSOR_ATTEMPT_BINDING_REQUIRED')
    need(re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',j['databaseUUID']) and p.get('databaseUUID')==j['databaseUUID'],'PREDECESSOR_DATABASE_BINDING_REQUIRED')
    need(type(p.get('controllerPID')) is int and p['controllerPID']>0 and j['controllerPID']==str(p['controllerPID']),'PREDECESSOR_CONTROLLER_BINDING_REQUIRED')
    need(j['beforeRowsSHA256']==rows_sha256(p.get('beforeRows')) and j['afterRowsSHA256']==rows_sha256(p.get('afterRows')),'PREDECESSOR_CALLBACK_ROWS_BINDING_REQUIRED')
    for key in ['businessPort','previousBusinessPort','databasePort','gatewayPort']:
        need(type(p.get(key)) is int and 1024<p[key]<65536 and p[key] not in (8767,18891,18892),'PREDECESSOR_OWN_PORT_REQUIRED')
    # This proves only an immutable predecessor, never that its old processes
    # or ports remain active. The future SQL executor must attest the new held
    # controller and exact live DB, and compare both rows before any write.
    return {'verified':True,'planSHA256':sha(plan_raw),'journalSHA256':expected_journal_sha256,
      'afterRowsSHA256':j['afterRowsSHA256'],'releaseSHA256':expected_release_sha256,
      'provesLiveRuntime':False,'authorizesSQL':False,'oldPortMayBeReusedWithoutObservation':False}
