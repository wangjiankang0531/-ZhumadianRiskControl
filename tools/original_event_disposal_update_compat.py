"""Extend only exact known updaters with pinned disposal classes and readiness gates."""
from pathlib import Path
import hashlib
Q=Path('D:/Zqa20261025/Application')
UPDATERS={'local-j57':'2b1911746458273abbc82d9412f97aafe3424ceef626eb3beafa4ebb92524f02','public-r14':'fc47653b44b8e9cd938317dbc7138472b3ac9b30e503e3135683ee86765989a8'}
REVISION='event-parent-record-atomic-v1'
SERVICE='payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class'
OBSERVER='payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class'
FACTORIES='payload/business/run-template/classes/META-INF/spring.factories'
CLASS_PIN='8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2'
OBSERVER_PIN='53ad7c1a3996ee2c353938414fb7d0d806d78647bd3f5b93274056f1220e789a'
INITIALIZER='xnby.replica.OriginalEventDisposalTransactionObservation'
REGISTRY_HELPER='''def _event_initializers(raw):
    require(isinstance(raw, bytes) and len(raw) <= 4096, 'BOUNDED_INITIALIZER_REGISTRY_REQUIRED')
    key = b'org.springframework.context.ApplicationContextInitializer='
    lines = [line for line in raw.splitlines() if line.startswith(key)]
    require(len(lines) == 1 and b'\\\\' not in lines[0], 'EXACT_SINGLE_LINE_INITIALIZER_REGISTRY')
    names = lines[0][len(key):].decode('ascii').split(',')
    require(0 < len(names) <= 32 and len(names) == len(set(names))
            and all(name and name.strip() == name and all(c.isalnum() or c in '._$' for c in name) for name in names),
            'UNIQUE_CANONICAL_RETAINED_INITIALIZERS_REQUIRED')
    return names


'''

READY_HELPER='''def event_disposal_observer_ready(app, row):
    release = read(app / 'release-manifest.json')
    if release.get('eventDisposalAtomicCandidate') is None:
        return None
    require(release.get('eventDisposalAtomicCandidate') == '__REVISION__'
            and release.get('eventDisposalObservationCandidate') == 'existing-singletons-manager-v1',
            'EXACT_EVENT_DISPOSAL_REVISION_REQUIRED')
    run = Path(row['run'])
    relative = run.relative_to(app).as_posix() + '/b/event-disposal-transaction-observation.json'
    path = regular(app, relative)
    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_EVENT_DISPOSAL_OBSERVER_REQUIRED')
    value = read(path)
    require(isinstance(value, dict), 'EVENT_DISPOSAL_REPORT_OBJECT_REQUIRED')
    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))
    require(value.get('schema') == 'xnby.event-disposal-transaction-observation.v1'
            and value.get('PID') == row.get('children', {}).get('business')
            and type(value.get('PID')) is int and value.get('run') == run.name
            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()
            and value.get('existingSingletonMetadataOnly') is True
            and value.get('businessMethodsInvoked') is False
            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False
            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False
            and value.get('existingTransactionManagerCount') == 1
            and type(value.get('existingTransactionManagerCount')) is int
            and value.get('allEventDisposalMethodsAndManagerMatched') is True,
            'EVENT_DISPOSAL_OBSERVER_OWNER_OR_ADVISOR_MISMATCH')
    group = value.get('disposal')
    require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True
            and group.get('existingSingletonMetadataOnly') is True
            and group.get('serviceType') == 'com.iemp.endanger.server.emergencyResponse.service.EventDisposalRecordService',
            'EXACT_EVENT_DISPOSAL_SERVICE_GROUP_REQUIRED')
    services = group.get('services')
    require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_EVENT_DISPOSAL_SERVICE_REQUIRED')
    bean = services[0]
    payload = read(app / 'payload-manifest.json')
    expected = payload.get('files', {}).get('__SERVICE__', {}).get('sha256')
    require(isinstance(bean, dict) and bean.get('existingSingleton') is True
            and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True
            and expected == '__CLASS_PIN__' and bean.get('targetClassSHA256') == expected,
            'EXACT_TESTED_EVENT_DISPOSAL_SINGLETON_CLASS_REQUIRED')
    checks = bean.get('methods')
    require(isinstance(checks, dict) and set(checks) == {'saveRecord'}
            and isinstance(checks['saveRecord'], dict)
            and checks['saveRecord'].get('matchingExceptionRollbackAdvisor') is True,
            'EVENT_DISPOSAL_SAVE_RECORD_ADVISOR_DETAIL_REQUIRED')
    return value


'''

def need(value,code):
 if not value:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def initializers(raw):
 ns={'require':need};exec(REGISTRY_HELPER,ns);return ns['_event_initializers'](raw)
def adapt_factories(raw):
 names=initializers(raw);need(INITIALIZER not in names,'EVENT_DISPOSAL_INITIALIZER_ALREADY_REGISTERED');key=b'org.springframework.context.ApplicationContextInitializer=';line=next(line for line in raw.splitlines() if line.startswith(key));need(raw.count(line)==1,'ONE_EXACT_RETAINED_REGISTRY_LINE');new=raw.replace(line,line+b','+INITIALIZER.encode(),1);need(initializers(new)==names+[INITIALIZER],'ALL_PRIOR_INITIALIZERS_AND_ORDER_MUST_BE_RETAINED');return new

def adapt_updater(raw):
 need(digest(raw) in UPDATERS.values(),'EXACT_KNOWN_LOCAL_J57_OR_PUBLIC_R14_UPDATER_REQUIRED');nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode().replace('\r\n','\n');anchor="            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class',\n";need(text.count(anchor)==1,'EXACT_PRIOR_TEAM_CLASS_ALLOWLIST_ANCHOR');text=text.replace(anchor,anchor+''.join("            '"+name+"',\n" for name in (SERVICE,OBSERVER)),1)
 guards=''
 for name,pin in [(SERVICE,CLASS_PIN),(OBSERVER,OBSERVER_PIN)]:
  guards+="    if '"+name+"' in plan['files']:\n        require(release.get('eventDisposalAtomicCandidate') == '"+REVISION+"', 'EXPLICIT_EVENT_DISPOSAL_CANDIDATE_REQUIRED')\n        event_class_row = plan['files']['"+name+"']\n        require(event_class_row['SHA256'] == '"+pin+"' and payload['files'].get('"+name+"') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')\n"
 guards+="    if release.get('eventDisposalAtomicCandidate') is not None:\n        require(release.get('eventDisposalAtomicCandidate') == '"+REVISION+"' and release.get('eventDisposalObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EVENT_DISPOSAL_METADATA_REQUIRED')\n"
 for name,pin in [(SERVICE,CLASS_PIN),(OBSERVER,OBSERVER_PIN)]:guards+="        require(payload['files'].get('"+name+"', {}).get('sha256') == '"+pin+"', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')\n"
 guards+="        event_factory_name = '"+FACTORIES+"'\n        event_prior_initializers = _event_initializers(regular(app, event_factory_name).read_bytes())\n        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)\n        event_next_initializers = _event_initializers(event_composed_factory.read_bytes())\n        require('"+INITIALIZER+"' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')\n"
 anchor='    # Verify the composed installation before downtime, including retained dependencies.\n';need(text.count(anchor)==1,'EXACT_COMPOSED_PIN_BOUNDARY');text=text.replace(anchor,guards+anchor,1);helper=REGISTRY_HELPER+READY_HELPER.replace('__REVISION__',REVISION).replace('__SERVICE__',SERVICE).replace('__CLASS_PIN__',CLASS_PIN);anchor='def health(app, row, guarded=True, *, gateway_port=18892):\n';need(text.count(anchor)==1,'EXACT_EXISTING_HEALTH_SIGNATURE');text=text.replace(anchor,helper+anchor,1);anchor='    emergency_team_observer_ready(app, row)\n';need(text.count(anchor)==1,'EXACT_TEAM_READY_CALL');text=text.replace(anchor,anchor+'    event_disposal_observer_ready(app, row)\n',1);updated=text.replace('\n',nl).encode();compile(updated,'own_event_disposal_pinned_updater.py','exec');return updated

def module(raw):
 ns={'__name__':'own_event_disposal_pinned_updater','__file__':str(Q/'tools/original_public_test_update.py')};exec(compile(raw,'own_event_disposal_pinned_updater.py','exec'),ns);return ns
