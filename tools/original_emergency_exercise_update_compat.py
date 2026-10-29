"""Extend only exact known updaters with pinned disposal classes and readiness gates."""
from pathlib import Path
import hashlib
Q=Path('D:/Zqa20261025/Application')
UPDATERS={'local-j58':'7c709a32fadba0381e8b5df36e558ff07156e1258b9994c1d6deb27a73837934','public-r15-with-event':'6b90439ae0b63e7212df91f16e9b8b8395ad925e7e96cd6d3ff34244552c4a51'}
REVISION='exercise-parent-files-atomic-v2'
SERVICE='payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class'
OBSERVER='payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class'
FACTORIES='payload/business/run-template/classes/META-INF/spring.factories'
CLASS_PIN='dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece'
OBSERVER_PIN='c242fbfa1d552afc19aceeae46cdc6c6d2c7176d39f57bd1cf41bc530cf4f07e'
INITIALIZER='xnby.replica.OriginalEmergencyExerciseTransactionObservation'
REGISTRY_HELPER='''def _exercise_initializers(raw):
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

READY_HELPER='''def emergency_exercise_observer_ready(app, row):
    release = read(app / 'release-manifest.json')
    if release.get('emergencyExerciseAtomicCandidate') is None:
        return None
    require(release.get('emergencyExerciseAtomicCandidate') == '__REVISION__'
            and release.get('emergencyExerciseObservationCandidate') == 'existing-singletons-manager-v1',
            'EXACT_EMERGENCY_EXERCISE_REVISION_REQUIRED')
    run = Path(row['run'])
    relative = run.relative_to(app).as_posix() + '/b/emergency-exercise-transaction-observation.json'
    path = regular(app, relative)
    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_EXERCISE_OBSERVER_REQUIRED')
    value = read(path)
    require(isinstance(value, dict), 'EXERCISE_REPORT_OBJECT_REQUIRED')
    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))
    require(value.get('schema') == 'xnby.emergency-exercise-transaction-observation.v1'
            and value.get('PID') == row.get('children', {}).get('business')
            and type(value.get('PID')) is int and value.get('run') == run.name
            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()
            and value.get('existingSingletonMetadataOnly') is True
            and value.get('businessMethodsInvoked') is False
            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False
            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False
            and value.get('existingTransactionManagerCount') == 1
            and type(value.get('existingTransactionManagerCount')) is int
            and value.get('allEmergencyExerciseMethodsAndManagerMatched') is True
            and value.get('nonNullUpdateStrategyMatched') is True,
            'EXERCISE_OBSERVER_OWNER_ADVISOR_OR_STRATEGY_MISMATCH')
    strategies = value.get('exerciseUpdateStrategies')
    expected_columns = {'emergency_plan_id', 'exercise_location', 'organize_department', 'commander_chief',
                        'exercise_time', 'participants', 'cooperating_unit', 'exercise_type', 'exercise_device',
                        'exercise_describe', 'exercise_special_situation', 'problems_andmeasures', 'created_at'}
    require(isinstance(strategies, dict) and set(strategies) == expected_columns
            and all(isinstance(item, dict) and item.get('updateStrategy') == 'NOT_NULL'
                    and item.get('withUpdateFill') is False for item in strategies.values()),
            'EXACT_EXERCISE_ACTUAL_FIELD_STRATEGIES_REQUIRED')
    groups = value.get('exercise')
    require(isinstance(groups, dict) and set(groups) == {'save', 'saveList', 'delete'}, 'THREE_EXERCISE_GROUPS_REQUIRED')
    payload = read(app / 'payload-manifest.json')
    expected = payload.get('files', {}).get('__SERVICE__', {}).get('sha256')
    require(expected == '__CLASS_PIN__', 'EXACT_TESTED_EXERCISE_PAYLOAD_CLASS_REQUIRED')
    for key, method in [('save', 'save'), ('saveList', 'saveEmergencyExerciseList'), ('delete', 'delete')]:
        group = groups[key]
        require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True
                and group.get('existingSingletonMetadataOnly') is True
                and group.get('serviceType') == 'com.iemp.endanger.server.emergency.service.EmergencyExerciseService',
                'EXACT_EXERCISE_SERVICE_GROUP_REQUIRED')
        services = group.get('services')
        require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_EXERCISE_SERVICE_REQUIRED')
        bean = services[0]
        require(isinstance(bean, dict) and bean.get('existingSingleton') is True
                and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True
                and bean.get('targetClassSHA256') == expected,
                'EXACT_TESTED_EXERCISE_SINGLETON_CLASS_REQUIRED')
        checks = bean.get('methods')
        require(isinstance(checks, dict) and set(checks) == {method}
                and isinstance(checks[method], dict)
                and checks[method].get('matchingExceptionRollbackAdvisor') is True,
                'EXERCISE_METHOD_ADVISOR_DETAIL_REQUIRED')
    return value


'''


def need(value,code):
 if not value:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def initializers(raw):
 ns={'require':need};exec(REGISTRY_HELPER,ns);return ns['_exercise_initializers'](raw)
def adapt_factories(raw):
 names=initializers(raw);need(INITIALIZER not in names,'EMERGENCY_EXERCISE_INITIALIZER_ALREADY_REGISTERED');key=b'org.springframework.context.ApplicationContextInitializer=';line=next(line for line in raw.splitlines() if line.startswith(key));need(raw.count(line)==1,'ONE_EXACT_RETAINED_REGISTRY_LINE');new=raw.replace(line,line+b','+INITIALIZER.encode(),1);need(initializers(new)==names+[INITIALIZER],'ALL_PRIOR_INITIALIZERS_AND_ORDER_MUST_BE_RETAINED');return new

def adapt_updater(raw):
 if digest(raw)=='f285468d95473c1dfe14301bca1b4a3e8ddb26a751fd0bb8283d7bebc36dd7e2':
  prior=b'dda137b63282602b4aec75f399efe662a2cae1fa2cd461f325e5a77be95fab47';need(raw.count(prior)==2,'EXACT_PRIOR_EXERCISE_OBSERVER_PIN_REFERENCES');updated=raw.replace(prior,OBSERVER_PIN.encode());compile(updated,'own_exercise_quoted_identifier_metadata_repair.py','exec');return updated
 need(digest(raw) in UPDATERS.values(),'EXACT_KNOWN_LOCAL_J58_UPDATER_REQUIRED');nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode().replace('\r\n','\n');anchor="            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class',\n";need(text.count(anchor)==1,'EXACT_PRIOR_TEAM_CLASS_ALLOWLIST_ANCHOR');text=text.replace(anchor,anchor+''.join("            '"+name+"',\n" for name in (SERVICE,OBSERVER)),1)
 guards=''
 for name,pin in [(SERVICE,CLASS_PIN),(OBSERVER,OBSERVER_PIN)]:
  guards+="    if '"+name+"' in plan['files']:\n        require(release.get('emergencyExerciseAtomicCandidate') == '"+REVISION+"', 'EXPLICIT_EMERGENCY_EXERCISE_CANDIDATE_REQUIRED')\n        event_class_row = plan['files']['"+name+"']\n        require(event_class_row['SHA256'] == '"+pin+"' and payload['files'].get('"+name+"') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')\n"
 guards+="    if release.get('emergencyExerciseAtomicCandidate') is not None:\n        require(release.get('emergencyExerciseAtomicCandidate') == '"+REVISION+"' and release.get('emergencyExerciseObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EMERGENCY_EXERCISE_METADATA_REQUIRED')\n"
 for name,pin in [(SERVICE,CLASS_PIN),(OBSERVER,OBSERVER_PIN)]:guards+="        require(payload['files'].get('"+name+"', {}).get('sha256') == '"+pin+"', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')\n"
 guards+="        event_factory_name = '"+FACTORIES+"'\n        event_prior_initializers = _exercise_initializers(regular(app, event_factory_name).read_bytes())\n        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)\n        event_next_initializers = _exercise_initializers(event_composed_factory.read_bytes())\n        require('"+INITIALIZER+"' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')\n"
 anchor='    # Verify the composed installation before downtime, including retained dependencies.\n';need(text.count(anchor)==1,'EXACT_COMPOSED_PIN_BOUNDARY');text=text.replace(anchor,guards+anchor,1);helper=REGISTRY_HELPER+READY_HELPER.replace('__REVISION__',REVISION).replace('__SERVICE__',SERVICE).replace('__CLASS_PIN__',CLASS_PIN);anchor='def health(app, row, guarded=True, *, gateway_port=18892):\n';need(text.count(anchor)==1,'EXACT_EXISTING_HEALTH_SIGNATURE');text=text.replace(anchor,helper+anchor,1);anchor='    emergency_team_observer_ready(app, row)\n';need(text.count(anchor)==1,'EXACT_TEAM_READY_CALL');text=text.replace(anchor,anchor+'    emergency_exercise_observer_ready(app, row)\n',1);updated=text.replace('\n',nl).encode();compile(updated,'own_emergency_exercise_pinned_updater.py','exec');return updated

def module(raw):
 ns={'__name__':'own_emergency_exercise_pinned_updater','__file__':str(Q/'tools/original_public_test_update.py')};exec(compile(raw,'own_emergency_exercise_pinned_updater.py','exec'),ns);return ns
