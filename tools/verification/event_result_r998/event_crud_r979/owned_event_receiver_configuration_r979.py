"""A stopped, owned fixture's one-setting transaction and its two manifest pins.

The parent owns identity, resource, full-candidate and actual process validation.
After a code transaction applies its candidate, this transaction changes the task
setting and both manifest hashes. Restore this transaction after real process
exit, before restoring the outer code transaction. No services or SQL here.
"""
from pathlib import Path
import hashlib,json,re,uuid
from owned_candidate_code_transaction_r543 import atomic,pin,plain,need

CONFIG='private/server-configuration.json'
PAYLOAD='payload-manifest.json'
RELEASE='release-manifest.json'
NAMES=(CONFIG,PAYLOAD,RELEASE)
SCHEMA='xnby.owned-event-receiver-configuration-transaction.v1'

def encode(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def raw_pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def event_candidate(before,receiver_port):
    need(type(receiver_port)is int and 1024<receiver_port<65536 and receiver_port not in {8767,18891,18892},'EXACT_OWN_RECEIVER_PORT_REQUIRED')
    need(isinstance(before,dict)and set(before)==set(NAMES)and all(isinstance(v,bytes)for v in before.values()),'EXACT_EVENT_THREE_BYTES_REQUIRED')
    spec,payload,release=(json.loads(before[n])for n in NAMES)
    need(spec.get('schema')=='zhumadian.original.server.configuration.v1'and payload.get('schema')=='zhumadian.original.server.payload.v1'and release.get('schema')=='zhumadian.original.server.release.v1','ORIGINAL_EVENT_SCHEMAS_REQUIRED')
    need(payload['files'].get(CONFIG)==raw_pin(before[CONFIG])and release['payloadManifestSHA256']==raw_pin(before[PAYLOAD])['sha256']and payload['releaseId']==release['releaseId'],'EXACT_EVENT_MANIFEST_IDENTITY_REQUIRED')
    changed=json.loads(before[CONFIG]);keys=('riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird')
    need(isinstance(changed.get('configuration',{}).get('business'),dict),'BUSINESS_CONFIGURATION_REQUIRED')
    for key in keys:
        need(key+'Url'in changed['configuration']['business']and not any(key+'Url'in arg for arg in changed.get('businessArguments',[])),'NO_RECEIVER_OVERRIDE_OR_MISSING_BINDING')
        changed['configuration']['business'][key+'Url']='http://127.0.0.1:'+str(receiver_port)+'/own-event-crud-r979/'+key
    reversed_spec=json.loads(encode(changed))
    for key in keys:reversed_spec['configuration']['business'][key+'Url']=spec['configuration']['business'][key+'Url']
    need(reversed_spec==spec,'NO_OTHER_CONFIGURATION_CHANGE_ALLOWED')
    result={CONFIG:encode(changed)};p=json.loads(before[PAYLOAD]);r=json.loads(before[RELEASE])
    p['files'][CONFIG]=raw_pin(result[CONFIG]);result[PAYLOAD]=encode(p)
    r['payloadManifestSHA256']=raw_pin(result[PAYLOAD])['sha256'];result[RELEASE]=encode(r)
    p['files'][CONFIG]=payload['files'][CONFIG];r['payloadManifestSHA256']=release['payloadManifestSHA256']
    need(p==payload and r==release,'NO_OTHER_MANIFEST_CHANGE_ALLOWED')
    need(all(raw_pin(result[n])!=raw_pin(before[n])for n in NAMES),'ALL_EVENT_FILES_MUST_CHANGE')
    return result

class OwnedEventReceiverConfigurationTransaction:
    """File transaction only; processes_exited must be supplied by the real parent.

    Expected-before hashes must come from the parent's fixed candidate, not from
    an arbitrary observed target. The class cannot prove PID ownership or that
    its parent's callback is honest. Tests deliberately label callback doubles.
    """
    def __init__(self,application,attempt,expected_before,*,receiver_port,processes_exited):
        self.app=plain(application);self.attempt=plain(attempt);self.exited=processes_exited
        need(self.app.name=='Application'and self.app.is_dir()and not self.attempt.is_relative_to(self.app)
             and not self.app.is_relative_to(self.attempt),'DISTINCT_OWN_TASK_ATTEMPT_REQUIRED')
        need(callable(processes_exited),'PARENT_ACTUAL_EXIT_PROOF_REQUIRED')
        need(isinstance(expected_before,dict)and set(expected_before)==set(NAMES),'EXACT_TASK_THREE_FILE_PINS_REQUIRED')
        for p in expected_before.values():
            need(isinstance(p,dict)and set(p)=={'bytes','sha256'}and type(p['bytes'])is int and p['bytes']>0
                 and isinstance(p['sha256'],str)and re.fullmatch('[0-9a-f]{64}',p['sha256']),'EXACT_TASK_FILE_PIN_REQUIRED')
        self.receiver_port=receiver_port
        self.before=json.loads(json.dumps(expected_before))
        self.scope=hashlib.sha256(encode({'application':str(self.app),'attempt':str(self.attempt),'before':self.before,'receiverPort':self.receiver_port})).hexdigest()
        self.journal=self.attempt/'journal.private.json'
        # Match the real atomic writer's temporary name before allocating any
        # backup. Ordinary Windows paths over this limit failed in the probe.
        writes=[self.journal,*[self.app/n for n in NAMES],*[self.attempt/'before'/n for n in NAMES]]
        self.max_atomic_path_characters=max(len(str(p.with_name('.'+p.name+'.own-'+'0'*32+'.tmp')))for p in writes)
        need(self.max_atomic_path_characters<260,'TASK_ATOMIC_PATH_LIMIT_EXCEEDED_BEFORE_ALLOCATION')

    def stopped(self):need(self.exited()is True,'ACTUAL_OWN_PROCESS_EXIT_REQUIRED_BEFORE_TASK_FILE_OPERATION')
    def current(self):
        result={}
        for n in NAMES:
            p=plain(self.app/n);need(p.is_file(),'EXISTING_TASK_FILE_REQUIRED:'+n);result[n]=pin(p)
        return result
    def save(self,state):atomic(self.journal,encode(state))
    def state(self):
        state=json.loads(plain(self.journal).read_bytes())
        need(state.get('schema')==SCHEMA and state.get('application')==str(self.app)
             and state.get('attempt')==str(self.attempt)
             and state.get('scopeSHA256')==self.scope and state.get('before')==self.before,'EXACT_TASK_JOURNAL_REQUIRED')
        need(isinstance(state.get('owner'),str)and re.fullmatch('[0-9a-f]{32}',state['owner']),'TASK_JOURNAL_OWNER_REQUIRED')
        return state
    def backup_bytes(self):
        raw={}
        for n in NAMES:
            p=plain(self.attempt/'before'/n)
            need(p.is_file()and pin(p)==self.before[n],'TASK_BACKUP_CHANGED_REFUSE_ALL_WRITES:'+n)
            raw[n]=p.read_bytes();need(raw_pin(raw[n])==self.before[n],'TASK_BACKUP_READ_DRIFT:'+n)
        return raw
    def candidates(self,state):
        result=event_candidate(self.backup_bytes(),self.receiver_port)
        need({n:raw_pin(result[n])for n in NAMES}==state.get('after'),'TASK_CANDIDATE_PIN_MISMATCH')
        return result
    def prepare(self):
        self.stopped();need(not self.attempt.exists(),'NEW_TASK_ATTEMPT_REQUIRED')
        need(self.current()==self.before,'TASK_PREIMAGE_CHANGED')
        raw={n:(self.app/n).read_bytes()for n in NAMES}
        need({n:raw_pin(raw[n])for n in NAMES}==self.before,'TASK_PREIMAGE_READ_DRIFT')
        result=event_candidate(raw,self.receiver_port)
        self.attempt.mkdir(parents=True)
        state={'schema':SCHEMA,'owner':uuid.uuid4().hex,'application':str(self.app),'attempt':str(self.attempt),'scopeSHA256':self.scope,
               'before':self.before,'after':{n:raw_pin(result[n])for n in NAMES},'phase':'backup-in-progress','written':[]}
        self.save(state)
        for n in NAMES:
            self.stopped();need(self.current()==self.before,'TASK_DRIFT_DURING_BACKUP')
            atomic(self.attempt/'before'/n,raw[n])
        self.backup_bytes();need(self.current()==self.before,'TASK_DRIFT_AFTER_BACKUP')
        state['phase']='prepared';self.save(state)
        return {n:raw_pin(result[n])for n in NAMES}
    def apply(self,*,after_write=None):
        self.stopped();state=self.state()
        need(state.get('phase')=='prepared'and state.get('written')==[],'FRESH_TASK_PREPARED_STATE_REQUIRED')
        result=self.candidates(state);need(self.current()==self.before,'TASK_PREIMAGE_CHANGED')
        state['phase']='applying';self.save(state)
        for index,n in enumerate(NAMES,1):
            self.stopped()
            expected={p:(state['after'][p]if p in state['written']else self.before[p])for p in NAMES}
            need(self.current()==expected,'TASK_DRIFT_DURING_APPLY')
            atomic(self.app/n,result[n]);need(pin(self.app/n)==state['after'][n],'TASK_WRITE_VERIFICATION_FAILED')
            state['written'].append(n);self.save(state)
            if after_write is not None:after_write(index,n)
        need(self.current()==state['after'],'TASK_APPLIED_SET_MISMATCH')
        state['phase']='applied';self.save(state)
        return state['after']
    def inspect_restore(self):
        self.stopped();state=self.state()
        need(state.get('phase')in {'prepared','applying','applied','restoring'},'RESTORABLE_TASK_PHASE_REQUIRED')
        self.candidates(state)
        now=self.current()
        need(all(now[n]in [self.before[n],state['after'][n]]for n in NAMES),'FOREIGN_TASK_DRIFT_REFUSE_ALL_RESTORE')
        return state
    def restore(self,*,after_write=None):
        state=self.inspect_restore();raw=self.backup_bytes()
        state['phase']='restoring';self.save(state)
        for index,n in enumerate(reversed(NAMES),1):
            self.inspect_restore();self.stopped()
            if pin(self.app/n)!=self.before[n]:atomic(self.app/n,raw[n])
            need(pin(self.app/n)==self.before[n],'TASK_RESTORE_WRITE_MISMATCH')
            if after_write is not None:after_write(index,n)
        need(self.current()==self.before,'TASK_RESTORE_SET_MISMATCH')
        state.update(phase='restored',restored=True);self.save(state)
        return {'restored':True,'paths':3,'originalFileBytesRestored':True}
