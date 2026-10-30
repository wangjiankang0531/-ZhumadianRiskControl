"""Pinned sparse update for an existing original-system public test installation.

The updater preserves the installed database, object store, credentials and IIS.
It requires a clean owned shutdown before changing code. No forced termination.
"""
from pathlib import Path, PurePosixPath
import argparse, contextlib, datetime, hashlib, http.client, json, os, re, shutil
import subprocess, sys, time, uuid, xml.etree.ElementTree as ET

TARGET = Path('C:/inetpub/wwwroot/Zhumadian/Application')
HOST = 'www.joinlinksmart.com'
IIS = Path('C:/inetpub/wwwroot/Zhumadian/Application/iis')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def regular(root, relative=''):
    root = Path(root).absolute()
    if relative:
        parts = PurePosixPath(relative)
        require(str(parts) == relative and not parts.is_absolute() and all(
            p not in ('.', '..') and not re.search(r'[\\:\x00-\x1f]', p)
            and not p.endswith((' ', '.')) for p in parts.parts), 'EXACT_RELATIVE_PATH_REQUIRED')
        result = root.joinpath(*parts.parts)
    else:
        result = root
    # Check every ancestor too: an apparently regular root can sit below a junction.
    for candidate in [*reversed(result.parents), result]:
        if candidate.exists() or candidate.is_symlink():
            attrs = getattr(candidate.lstat(), 'st_file_attributes', 0)
            require(not candidate.is_symlink() and not attrs & 0x400, 'REDIRECTED_PATH_REFUSED')
    require(result.is_relative_to(root), 'OWNED_PATH_REQUIRED')
    return result

def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the sibling temporary name short even when the target basename is long.
    temp = path.with_name('.zmd-' + uuid.uuid4().hex + '.tmp')
    try:
        with temp.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def write_json(path, value):
    atomic(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

@contextlib.contextmanager
def server_lock(app):
    import msvcrt
    with regular(app, 'UserData/OriginalServer/server-owner.lock').open('r+b') as lock:
        lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            yield
        finally:
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

def check_file(root, name, pin, size=None):
    path = regular(root, name)
    require(path.is_file() and sha(path) == pin and
            (size is None or path.stat().st_size == size), 'FILE_PIN_MISMATCH:' + name)
    return path

def load_bundle(app, bundle, pin, *, expected_target=TARGET, expected_port=18892):
    regular(app); regular(bundle)
    require(re.fullmatch('[0-9a-f]{64}', pin or '') is not None, 'MANIFEST_PIN_REQUIRED')
    check_file(bundle, 'update-manifest.json', pin)
    plan = read(bundle / 'update-manifest.json')
    require(plan['schema'] == 'zhumadian.public-test-update.v1'
            and plan['targetApplication'] == Path(expected_target).as_posix()
            and plan['gatewayPort'] == expected_port
            and plan['databaseUploadsCredentialsGISOrDependenciesIncluded'] is False,
            'EXACT_PUBLIC_TEST_UPDATE_REQUIRED')
    old_pin = sha(regular(app, 'release-manifest.json'))
    require(old_pin in plan['acceptedOldReleases'], 'UNKNOWN_INSTALLED_RELEASE_NO_FILES_CHANGED')
    old = read(app / 'release-manifest.json')
    accepted = plan['acceptedOldReleases'][old_pin]
    require(old['releaseId'] == plan['releaseId'] and
            old['payloadManifestSHA256'] == accepted['payloadManifestSHA256'] ==
            plan['basePayloadManifestSHA256'], 'ORIGINAL_PAYLOAD_BASE_REQUIRED')
    check_file(app, 'payload-manifest.json', old['payloadManifestSHA256'])
    for name, digest in accepted['controllerFiles'].items():
        check_file(app, name, digest)
    require(len(plan['files']) <= 1000 and
            sum(row['bytes'] for row in plan['files'].values()) <= 32 * 1024 ** 2,
            'SPARSE_UPDATE_LIMIT_EXCEEDED')
    require(not set(plan['files']).intersection(plan['removedFrontendFiles']), 'REPLACEMENT_REMOVAL_COLLISION')
    changes = {}
    for name, row in plan['files'].items():
        allowed = name.startswith(('frontend/security_pc/', 'frontend/emergency_pc/',
            'frontend/mobile/', 'payload/callback-overlay/20261026-password-identity/')) or name in (
            'release-manifest.json', 'payload-manifest.json', 'Start_Original_Server.cmd',
            'Deploy_Original_Server.cmd', 'Rollback_Original_Server.cmd', 'Start_Callback_Candidate.cmd',
            'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class',
            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class',
            'payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class',
            'payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeTrainServiceImpl.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeExamServiceImpl.class',
            'payload/business/run-template/classes/xnby/replica/OriginalTrainingTransactionObservation.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkSignServiceImpl.class',
            'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkMeasuresRelevanceServiceImpl.class',
            'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class',
            'payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class',
            'payload/business/run-template/classes/xnby/replica/OriginalFindingFailureObservation.class',
            'payload/business/run-template/classes/xnby/replica/OriginalFindingFailureObservation$Resolver.class',
            'payload/business/run-template/own-finding-observation.enabled',
            'payload/business/run-template/classes/META-INF/spring.factories') or name in (
                read(bundle / 'payload/release-manifest.json')['controllerFiles'])
        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),
                'UNEXPECTED_UPDATE_PATH:' + name)
        check_file(bundle / 'payload', name, row['SHA256'], row['bytes'])
        target = regular(app, name)
        before = None
        if name in accepted['controllerFiles']:
            before = accepted['controllerFiles'][name]
        elif name in plan['oldPayloadFiles']:
            before = plan['oldPayloadFiles'][name]['sha256']
        elif name == 'release-manifest.json':
            before = old_pin
        elif name == 'payload-manifest.json':
            before = old['payloadManifestSHA256']
        elif name in plan['legacyEntrySHA256']:
            require(target.is_file() and sha(target) in plan['legacyEntrySHA256'][name],
                    'UNKNOWN_OLD_ENTRY_SCRIPT')
            before = sha(target)
        if before is None:
            require(not target.exists(), 'NEW_PATH_ALREADY_EXISTS:' + name)
        else:
            check_file(app, name, before)
        changes[name] = {'before': before, 'after': row['SHA256']}
    check_file(bundle / 'payload', 'release-manifest.json', plan['newReleaseSHA256'])
    check_file(bundle / 'payload', 'payload-manifest.json', plan['newPayloadManifestSHA256'])
    release = read(bundle / 'payload/release-manifest.json')
    require(release['releaseId'] == old['releaseId'] and release['payloadManifestSHA256'] ==
            plan['newPayloadManifestSHA256'], 'NEW_RELEASE_IDENTITY_MISMATCH')
    payload = read(bundle / 'payload/payload-manifest.json')
    require(payload['releaseId'] == release['releaseId'], 'NEW_PAYLOAD_IDENTITY_MISMATCH')
    point_class = 'payload/business/run-template/classes/com/iemp/endanger/server/inspection/service/impl/InspectionPointsServiceImpl.class'
    if point_class in plan['files']:
        require(release.get('inspectionPointEditCandidate') == 'stable-child-ids-atomic-v1',
                'EXPLICIT_INSPECTION_POINT_CANDIDATE_REQUIRED')
        declared = payload['files'].get(point_class)
        actual = plan['files'][point_class]
        require(declared == {'bytes': actual['bytes'], 'sha256': actual['SHA256']},
                'INSPECTION_POINT_CLASS_PAYLOAD_PIN_REQUIRED')
    atomic_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkReservationBaseServiceImpl.class'
    if atomic_class_0 in plan['files']:
        require(release.get('reservationEndTimeCandidate') == 'original-end-time-atomic-v2',
                'EXPLICIT_RESERVATION_END_TIME_CANDIDATE_REQUIRED')
        row = plan['files'][atomic_class_0]
        require(payload['files'].get(atomic_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'RESERVATION_END_TIME_CLASS_PAYLOAD_PIN_REQUIRED')
    atomic_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/ThirdPartyUnitInfoServiceImpl.class'
    if atomic_class_1 in plan['files']:
        require(release.get('thirdPartyCredentialsCandidate') == 'original-credentials-atomic-v2',
                'EXPLICIT_THIRD_PARTY_CREDENTIALS_CANDIDATE_REQUIRED')
        row = plan['files'][atomic_class_1]
        require(payload['files'].get(atomic_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'THIRD_PARTY_CREDENTIALS_CLASS_PAYLOAD_PIN_REQUIRED')
    atomic_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalTransactionObservation.class'
    if atomic_class_2 in plan['files']:
        require(release.get('workTransactionObservationCandidate') == 'work-services-existing-singletons-v1',
                'EXPLICIT_WORK_TRANSACTION_OBSERVER_CANDIDATE_REQUIRED')
        row = plan['files'][atomic_class_2]
        require(payload['files'].get(atomic_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'WORK_TRANSACTION_OBSERVER_CLASS_PAYLOAD_PIN_REQUIRED')
    training_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeTrainServiceImpl.class'
    if training_class_0 in plan['files']:
        require(release.get('trainingEmployeeEditCandidate') == 'parent-first-atomic-v1',
                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')
        row = plan['files'][training_class_0]
        require(payload['files'].get(training_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')
    training_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/EmployeeExamServiceImpl.class'
    if training_class_1 in plan['files']:
        require(release.get('trainingEmployeeEditCandidate') == 'parent-first-atomic-v1',
                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')
        row = plan['files'][training_class_1]
        require(payload['files'].get(training_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')
    training_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalTrainingTransactionObservation.class'
    if training_class_2 in plan['files']:
        require(release.get('trainingTransactionObservationCandidate') == 'parent-first-atomic-v1',
                'EXPLICIT_TRAINING_CANDIDATE_REQUIRED')
        row = plan['files'][training_class_2]
        require(payload['files'].get(training_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']},
                'TRAINING_CLASS_PAYLOAD_PIN_REQUIRED')
    safety_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkSignServiceImpl.class'
    if safety_class_0 in plan['files']:
        require(release.get('workSafetyBatchEditCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')
        row = plan['files'][safety_class_0]
        require(payload['files'].get(safety_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')
    safety_class_1 = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/WorkMeasuresRelevanceServiceImpl.class'
    if safety_class_1 in plan['files']:
        require(release.get('workSafetyBatchEditCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')
        row = plan['files'][safety_class_1]
        require(payload['files'].get(safety_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')
    safety_class_2 = 'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class'
    if safety_class_2 in plan['files']:
        require(release.get('workSafetyBatchObservationCandidate') == 'work-safety-batch-atomic-v1', 'EXPLICIT_SAFETY_BATCH_CANDIDATE_REQUIRED')
        row = plan['files'][safety_class_2]
        require(payload['files'].get(safety_class_2) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'SAFETY_CLASS_PAYLOAD_PIN_REQUIRED')
    emergency_class_0 = 'payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class'
    if emergency_class_0 in plan['files']:
        require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXPLICIT_EMERGENCY_TEAM_CANDIDATE_REQUIRED')
        row = plan['files'][emergency_class_0]
        require(payload['files'].get(emergency_class_0) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'EMERGENCY_TEAM_CLASS_PAYLOAD_PIN_REQUIRED')
    emergency_class_1 = 'payload/business/run-template/classes/xnby/replica/OriginalEmergencyTeamTransactionObservation.class'
    if emergency_class_1 in plan['files']:
        require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXPLICIT_EMERGENCY_TEAM_CANDIDATE_REQUIRED')
        row = plan['files'][emergency_class_1]
        require(payload['files'].get(emergency_class_1) == {'bytes': row['bytes'], 'sha256': row['SHA256']}, 'EMERGENCY_TEAM_CLASS_PAYLOAD_PIN_REQUIRED')
    if 'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class' in plan['files']:
        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1', 'EXPLICIT_EVENT_DISPOSAL_CANDIDATE_REQUIRED')
        event_class_row = plan['files']['payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class']
        require(event_class_row['SHA256'] == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2' and payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')
    if 'payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class' in plan['files']:
        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1', 'EXPLICIT_EVENT_DISPOSAL_CANDIDATE_REQUIRED')
        event_class_row = plan['files']['payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class']
        require(event_class_row['SHA256'] == '53ad7c1a3996ee2c353938414fb7d0d806d78647bd3f5b93274056f1220e789a' and payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')
    if release.get('eventDisposalAtomicCandidate') is not None:
        require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1' and release.get('eventDisposalObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EVENT_DISPOSAL_METADATA_REQUIRED')
        require(payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class', {}).get('sha256') == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')
        require(payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEventDisposalTransactionObservation.class', {}).get('sha256') == '53ad7c1a3996ee2c353938414fb7d0d806d78647bd3f5b93274056f1220e789a', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')
        event_factory_name = 'payload/business/run-template/classes/META-INF/spring.factories'
        event_prior_initializers = _event_initializers(regular(app, event_factory_name).read_bytes())
        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)
        event_next_initializers = _event_initializers(event_composed_factory.read_bytes())
        require('xnby.replica.OriginalEventDisposalTransactionObservation' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')
    if 'payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class' in plan['files']:
        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2', 'EXPLICIT_EMERGENCY_EXERCISE_CANDIDATE_REQUIRED')
        event_class_row = plan['files']['payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class']
        require(event_class_row['SHA256'] == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece' and payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')
    if 'payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class' in plan['files']:
        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2', 'EXPLICIT_EMERGENCY_EXERCISE_CANDIDATE_REQUIRED')
        event_class_row = plan['files']['payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class']
        require(event_class_row['SHA256'] == 'c242fbfa1d552afc19aceeae46cdc6c6d2c7176d39f57bd1cf41bc530cf4f07e' and payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class') == {'bytes': event_class_row['bytes'], 'sha256': event_class_row['SHA256']}, 'EXACT_TESTED_EVENT_CLASS_PAYLOAD_REQUIRED')
    if release.get('emergencyExerciseAtomicCandidate') is not None:
        require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2' and release.get('emergencyExerciseObservationCandidate') == 'existing-singletons-manager-v1', 'EXACT_EMERGENCY_EXERCISE_METADATA_REQUIRED')
        require(payload['files'].get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class', {}).get('sha256') == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')
        require(payload['files'].get('payload/business/run-template/classes/xnby/replica/OriginalEmergencyExerciseTransactionObservation.class', {}).get('sha256') == 'c242fbfa1d552afc19aceeae46cdc6c6d2c7176d39f57bd1cf41bc530cf4f07e', 'PINNED_RETAINED_OR_NEW_EVENT_CLASS_REQUIRED')
        event_factory_name = 'payload/business/run-template/classes/META-INF/spring.factories'
        event_prior_initializers = _exercise_initializers(regular(app, event_factory_name).read_bytes())
        event_composed_factory = regular(bundle / 'payload', event_factory_name) if event_factory_name in plan['files'] else regular(app, event_factory_name)
        event_next_initializers = _exercise_initializers(event_composed_factory.read_bytes())
        require('xnby.replica.OriginalEmergencyExerciseTransactionObservation' in event_next_initializers and set(event_prior_initializers).issubset(event_next_initializers), 'ALL_EXISTING_AND_EVENT_INITIALIZERS_REQUIRED_BEFORE_DOWNTIME')
    # Verify the composed installation before downtime, including retained dependencies.
    # Seed data has already been moved into the installation's mutable database directory.
    for name, row in payload['files'].items():
        if name.startswith('seed/mysql/'):
            continue
        root = bundle / 'payload' if name in plan['files'] else app
        check_file(root, name, row['sha256'], row['bytes'])
    for name, value in release['controllerFiles'].items():
        root = bundle / 'payload' if name in plan['files'] else app
        check_file(root, name, value)
    for name, row in plan['removedFrontendFiles'].items():
        require(name.startswith(('frontend/security_pc/', 'frontend/emergency_pc/', 'frontend/mobile/')),
                'ONLY_OBSOLETE_FRONTEND_REMOVAL_ALLOWED')
        check_file(app, name, row['SHA256'], row['bytes'])
        changes[name] = {'before': row['SHA256'], 'after': None}
    return plan, old_pin, changes

def backup_code(app, attempt, changes):
    attempt = regular(attempt)
    require(not attempt.exists(), 'FRESH_BACKUP_REQUIRED')
    attempt.mkdir(parents=True)
    for name, row in changes.items():
        if row['before'] is not None:
            source = check_file(app, name, row['before'])
            dest = regular(attempt / 'before', name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
            check_file(attempt / 'before', name, row['before'])
    write_json(attempt / 'changes.json', changes)

def replace_code(app, bundle, changes, after_each=None):
    # The release pointer changes last, after its complete code and payload manifest.
    names = sorted(changes, key=lambda name: (name == 'release-manifest.json', name))
    for name in names:
        row = changes[name]; target = regular(app, name)
        if row['before'] is None:
            require(not target.exists(), 'CONCURRENT_NEW_PATH:' + name)
        else:
            check_file(app, name, row['before'])
        if row['after'] is None:
            target.unlink()
        else:
            source = check_file(bundle / 'payload', name, row['after'])
            atomic(target, source.read_bytes())
        if after_each:
            after_each(name)

def restore_code(app, attempt, changes):
    # Preflight all paths before restoring any: refuse an unrelated concurrent edit.
    for name, row in changes.items():
        target = regular(app, name)
        current = sha(target) if target.is_file() else None
        require(current in (row['before'], row['after']), 'ROLLBACK_FILE_DRIFT:' + name)
        if row['before'] is not None:
            check_file(attempt / 'before', name, row['before'])
    for name in sorted(changes, key=lambda name: (name == 'release-manifest.json', name)):
        row = changes[name]; target = regular(app, name)
        if row['before'] is None:
            if target.exists():
                target.unlink()
        else:
            atomic(target, (attempt / 'before' / name).read_bytes())

def process_owned(pid, app, pin):
    if type(pid) is not int or pid <= 0:
        return False
    command = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
               "Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(pid) +
               "' | Select-Object ExecutablePath,CommandLine | ConvertTo-Json -Compress")
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command],
        capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode or not result.stdout.strip():
        return False
    row = json.loads(result.stdout.decode('utf-8-sig'))
    text = row.get('CommandLine') or ''
    return (Path(row.get('ExecutablePath') or '').absolute() == app / 'runtime/python/python.exe'
            and str(app / 'tools/serve_original_server_release.py') in text and pin in text)

def owned_ready(app, pin, *, gateway_port=18892):
    row = read(regular(app, 'UserData/OriginalServer/current-run.json'))
    run = Path(row['run']).absolute()
    require(run.parent == app / 'UserData/OriginalServer/runs' and
            re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None, 'OWNED_RUN_REQUIRED')
    regular(run)
    require(row.get('ready') is True and row.get('gatewayPort') == gateway_port and
            row.get('releaseId') == read(app / 'release-manifest.json')['releaseId'] and
            process_owned(row.get('controllerPID'), app, pin), 'EXACT_READY_PUBLIC_CONTROLLER_REQUIRED')
    return row

def normal_stop(app, pin, row):
    require(process_owned(row['controllerPID'], app, pin), 'CONTROLLER_OWNERSHIP_CHANGED')
    run = regular(app, Path(row['run']).relative_to(app).as_posix())
    print('STOP: requesting normal shutdown of the owned public controller', flush=True)
    atomic(run / 'stop-requested.txt', b'stop\n')
    end = time.monotonic() + 180
    while time.monotonic() < end:
        receipt = run / 'receipt.json'
        if receipt.exists() and not process_owned(row['controllerPID'], app, pin):
            final = read(receipt)
            require(final.get('controllerPID') == row['controllerPID'] and
                    final.get('normalOwnedShutdown') is True and
                    final.get('allOwnedChildrenExited') is True and
                    set(final.get('exitCodesBeforeJobClose', {})) ==
                    {'store', 'mysql', 'redis', 'platform', 'business', 'gateway'} and
                    all(v == 0 for v in final['exitCodesBeforeJobClose'].values()),
                    'UNCLEAN_SHUTDOWN_NO_FILES_CHANGED')
            return final
        time.sleep(1)
    raise RuntimeError('NORMAL_SHUTDOWN_TIMEOUT_NO_FORCE_TERMINATION')

def http_check(port, path):
    client = http.client.HTTPConnection('127.0.0.1', port, timeout=12)
    try:
        client.request('GET', path, headers={'Connection': 'close'})
        response = client.getresponse(); body = response.read(4 * 1024 ** 2 + 1)
        require(len(body) <= 4 * 1024 ** 2, 'BOUNDED_HTTP_RESPONSE_REQUIRED')
        return response.status, body
    finally:
        client.close()

def marker(path):
    return dict(line.split('=', 1) for line in Path(path).read_text('ascii').splitlines()
                if '=' in line and not line.startswith(('#', '!')))

def finding_observer_ready(app, row):
    if read(app / 'release-manifest.json').get('findingFailureObservationExperimental') is not True:
        return None
    path = regular(app, Path(row['run']).relative_to(app).as_posix() + '/b/own-finding-observer-ready.json')
    require(path.is_file() and path.stat().st_size <= 1024, 'FINDING_OBSERVER_READY_REQUIRED')
    value = read(path)
    require(value.get('schema') == 'xnby.finding-observer-ready.v1'
            and value.get('PID') == row.get('children', {}).get('business')
            and type(value.get('PID')) is int
            and value.get('route') == '/checkPlan/saveCheckHiddenDanger'
            and value.get('maximumRecords') == 32
            and value.get('maximumRecordBytes') == 16384
            and value.get('originalResolversContinue') is True,
            'FINDING_OBSERVER_READY_IDENTITY_MISMATCH')
    return value


def training_observer_ready(app, row):
    """Validate startup-only existing singleton metadata; no business calls."""
    release = read(regular(app, 'release-manifest.json'))
    revision = release.get('trainingEmployeeEditCandidate')
    if revision is None:
        return None
    require(revision == release.get('trainingTransactionObservationCandidate') == 'parent-first-atomic-v1',
            'EXACT_TRAINING_RUNTIME_REVISION_REQUIRED')
    run = regular(Path(row['run']))
    path = regular(run / 'b', 'training-transaction-observation.json')
    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_TRAINING_OBSERVER_REPORT_REQUIRED')
    value = read(path)
    require(value.get('schema') == 'xnby.training-transaction-observation.v1'
            and type(value.get('PID')) is int and value['PID'] == row['children']['business']
            and value.get('run') == run.name
            and value.get('ownerIdSHA256') == hashlib.sha256(row['ownerId'].encode('ascii')).hexdigest()
            and value.get('existingSingletonMetadataOnly') is True
            and value.get('businessMethodsInvoked') is False
            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False
            and value.get('actualRollbackOrHTTPOrAuthenticationVerified') is False,
            'TRAINING_OBSERVER_IDENTITY_OR_SCOPE_MISMATCH')
    pins = {
        'Train': '83d9f3c831073ac16c8b42cef8442a9649081b11aae0353a2ba8e351a0d89c3d',
        'Exam': 'ddf82926cedbb6419c771b384d7e1c63f3210a401f68d984dc28ff7e30cb34e3',
    }
    payload = read(regular(app, 'payload-manifest.json'))
    require(sha(app / 'payload-manifest.json') == release['payloadManifestSHA256'],
            'TRAINING_RUNTIME_PAYLOAD_MANIFEST_PIN_REQUIRED')
    for kind, pin in pins.items():
        name = 'payload/business/run-template/classes/com/iemp/endanger/server/safetyBasic/service/impl/Employee' + kind + 'ServiceImpl.class'
        declaration = payload['files'].get(name)
        require(isinstance(declaration, dict) and declaration.get('sha256') == pin,
                'TRAINING_RUNTIME_CLASS_DECLARATION_REQUIRED')
        check_file(app, name, pin, declaration['bytes'])
        group = value.get(kind)
        require(isinstance(group, dict) and group.get('existingSingletonMetadataOnly') is True
                and group.get('allMethodsHaveMatchingTransactionAdvisor') is True
                and len(group.get('services', [])) == 1,
                'ONE_MATCHING_TRAINING_SERVICE_REQUIRED')
        bean = group['services'][0]
        require(bean.get('existingSingleton') is True and bean.get('isAopProxy') is True
                and bean.get('targetClass') == 'com.iemp.endanger.server.safetyBasic.service.impl.Employee' + kind + 'ServiceImpl'
                and bean.get('targetClassSHA256') == pin
                and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True
                and bean.get('methods', {}).get('updateById', {}).get('matchingExceptionRollbackAdvisor') is True,
                'TRAINING_TARGET_CLASS_OR_TRANSACTION_ADVISOR_MISMATCH')
    return value



def safety_batch_observer_ready(app, row):
    """Require owned startup metadata and exact loaded classes, without business calls."""
    release = read(regular(app, 'release-manifest.json'))
    revision = release.get('workSafetyBatchEditCandidate')
    observation = release.get('workSafetyBatchObservationCandidate')
    if revision is None and observation is None:
        return None
    require(revision == observation == 'work-safety-batch-atomic-v1', 'EXACT_SAFETY_RUNTIME_REVISION_REQUIRED')
    run = regular(Path(row['run']))
    path = regular(run / 'b', 'work-safety-batch-observation.json')
    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_SAFETY_OBSERVER_REPORT_REQUIRED')
    value = read(path)
    require(value.get('schema') == 'xnby.work-safety-batch-observation.v1'
            and type(value.get('PID')) is int and value['PID'] == row['children']['business']
            and value.get('run') == run.name
            and value.get('ownerIdSHA256') == hashlib.sha256(row['ownerId'].encode('ascii')).hexdigest()
            and value.get('existingSingletonMetadataOnly') is True
            and value.get('businessMethodsInvoked') is False
            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False
            and value.get('actualRollbackHTTPOrPermitAcceptanceVerified') is False,
            'SAFETY_OBSERVER_IDENTITY_OR_SCOPE_MISMATCH')
    payload = read(regular(app, 'payload-manifest.json'))
    require(sha(app / 'payload-manifest.json') == release['payloadManifestSHA256'], 'SAFETY_RUNTIME_PAYLOAD_PIN_REQUIRED')
    pins = {
        'signBatch': ('WorkSign', 'e04f7605d831547e4ca4a548d07ea1a4df95cdfcbc9f4c14787581e52c0774e5'),
        'measureBatch': ('WorkMeasuresRelevance', '4d66b3232241e8f0d7e65e9d8fe11ab920c77d641a82021b18b5c2a62dcd6579'),
    }
    observer = 'payload/business/run-template/classes/xnby/replica/OriginalWorkSafetyTransactionObservation.class'
    observer_pin = '9074d6476eab2a65af528f65c4553373126c8136916ecf703f08df3ebb05f238'
    declared = payload['files'].get(observer)
    require(isinstance(declared, dict) and declared.get('sha256') == observer_pin, 'SAFETY_OBSERVER_CLASS_DECLARATION_REQUIRED')
    check_file(app, observer, observer_pin, declared['bytes'])
    for key, (short, pin) in pins.items():
        name = 'payload/business/run-template/classes/com/iemp/endanger/server/work/service/impl/' + short + 'ServiceImpl.class'
        declared = payload['files'].get(name)
        require(isinstance(declared, dict) and declared.get('sha256') == pin, 'SAFETY_RUNTIME_CLASS_DECLARATION_REQUIRED')
        check_file(app, name, pin, declared['bytes'])
        group = value.get(key)
        require(isinstance(group, dict) and group.get('existingSingletonMetadataOnly') is True
                and group.get('serviceType') == 'com.iemp.endanger.server.work.service.' + short + 'Service'
                and group.get('matchingSaveBatchExceptionRollbackAdvisor') is True
                and len(group.get('services', [])) == 1, 'ONE_MATCHING_SAFETY_SERVICE_REQUIRED')
        bean = group['services'][0]
        require(bean.get('existingSingleton') is True and bean.get('isAopProxy') is True
                and bean.get('targetClass') == 'com.iemp.endanger.server.work.service.impl.' + short + 'ServiceImpl'
                and bean.get('targetClassSHA256') == pin
                and bean.get('matchingSaveBatchExceptionRollbackAdvisor') is True,
                'SAFETY_TARGET_CLASS_OR_TRANSACTION_ADVISOR_MISMATCH')
        advisors = bean.get('advisors')
        require(isinstance(advisors, list) and 1 <= len(advisors) <= 32
                and any(isinstance(a, dict) and a.get('metadataMatched') is True
                        and a.get('staticPointcutMatches') is True and a.get('runtimePointcut') is False for a in advisors),
                'SAFETY_STATIC_EXCEPTION_ROLLBACK_ADVISOR_DETAILS_REQUIRED')
    return value


def emergency_team_observer_ready(app, row):
    release = read(app / 'release-manifest.json')
    if release.get('emergencyTeamAtomicCandidate') is None:
        return None
    require(release.get('emergencyTeamAtomicCandidate') == 'parent-first-save-edit-atomic-v1', 'EXACT_TEAM_REVISION_REQUIRED')
    run = Path(row['run'])
    relative = run.relative_to(app).as_posix() + '/b/emergency-team-transaction-observation.json'
    path = regular(app, relative)
    require(path.is_file() and path.stat().st_size <= 65536, 'BOUNDED_TEAM_OBSERVER_REQUIRED')
    value = read(path)
    owner = marker(regular(app, run.relative_to(app).as_posix() + '/b/server-owner.properties'))
    require(value.get('schema') == 'xnby.emergency-team-transaction-observation.v1'
            and value.get('PID') == row.get('children', {}).get('business')
            and type(value.get('PID')) is int and value.get('run') == run.name
            and value.get('ownerIdSHA256') == hashlib.sha256(owner['ownerId'].encode('ascii')).hexdigest()
            and value.get('existingSingletonMetadataOnly') is True
            and value.get('businessMethodsInvoked') is False
            and value.get('SQLOrNetworkRequestsIssuedByObserver') is False
            and value.get('existingTransactionManagerCount') == 1
            and type(value.get('existingTransactionManagerCount')) is int
            and value.get('allEmergencyTeamMethodsAndManagerMatched') is True,
            'TEAM_OBSERVER_OWNER_OR_ADVISOR_MISMATCH')
    group = value.get('team')
    require(isinstance(group, dict) and group.get('allMethodsHaveMatchingTransactionAdvisor') is True,
            'TEAM_METHOD_ADVISORS_REQUIRED')
    services = group.get('services')
    require(isinstance(services, list) and len(services) == 1, 'EXACT_SINGLE_TEAM_SERVICE_REQUIRED')
    bean = services[0]
    payload = read(app / 'payload-manifest.json')
    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class', {}).get('sha256')
    require(isinstance(bean, dict) and bean.get('existingSingleton') is True
            and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True
            and expected == '69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4' and bean.get('targetClassSHA256') == expected,
            'EXACT_TESTED_TEAM_SINGLETON_CLASS_REQUIRED')
    checks = bean.get('methods')
    require(isinstance(checks, dict) and all(isinstance(checks.get(name), dict)
            and checks[name].get('matchingExceptionRollbackAdvisor') is True
            for name in ('save', 'updateById')), 'BOTH_TEAM_METHOD_DETAILS_REQUIRED')
    return value


def _event_initializers(raw):
    require(isinstance(raw, bytes) and len(raw) <= 4096, 'BOUNDED_INITIALIZER_REGISTRY_REQUIRED')
    key = b'org.springframework.context.ApplicationContextInitializer='
    lines = [line for line in raw.splitlines() if line.startswith(key)]
    require(len(lines) == 1 and b'\\' not in lines[0], 'EXACT_SINGLE_LINE_INITIALIZER_REGISTRY')
    names = lines[0][len(key):].decode('ascii').split(',')
    require(0 < len(names) <= 32 and len(names) == len(set(names))
            and all(name and name.strip() == name and all(c.isalnum() or c in '._$' for c in name) for name in names),
            'UNIQUE_CANONICAL_RETAINED_INITIALIZERS_REQUIRED')
    return names


def event_disposal_observer_ready(app, row):
    release = read(app / 'release-manifest.json')
    if release.get('eventDisposalAtomicCandidate') is None:
        return None
    require(release.get('eventDisposalAtomicCandidate') == 'event-parent-record-atomic-v1'
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
    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/service/impl/EventDisposalRecordServiceImpl.class', {}).get('sha256')
    require(isinstance(bean, dict) and bean.get('existingSingleton') is True
            and bean.get('isAopProxy') is True and bean.get('allMethodsHaveMatchingTransactionAdvisor') is True
            and expected == '8f862d0498d4248901f56dfb3262856a12d504d8d3fcba0472158d067802e3b2' and bean.get('targetClassSHA256') == expected,
            'EXACT_TESTED_EVENT_DISPOSAL_SINGLETON_CLASS_REQUIRED')
    checks = bean.get('methods')
    require(isinstance(checks, dict) and set(checks) == {'saveRecord'}
            and isinstance(checks['saveRecord'], dict)
            and checks['saveRecord'].get('matchingExceptionRollbackAdvisor') is True,
            'EVENT_DISPOSAL_SAVE_RECORD_ADVISOR_DETAIL_REQUIRED')
    return value


def _exercise_initializers(raw):
    require(isinstance(raw, bytes) and len(raw) <= 4096, 'BOUNDED_INITIALIZER_REGISTRY_REQUIRED')
    key = b'org.springframework.context.ApplicationContextInitializer='
    lines = [line for line in raw.splitlines() if line.startswith(key)]
    require(len(lines) == 1 and b'\\' not in lines[0], 'EXACT_SINGLE_LINE_INITIALIZER_REGISTRY')
    names = lines[0][len(key):].decode('ascii').split(',')
    require(0 < len(names) <= 32 and len(names) == len(set(names))
            and all(name and name.strip() == name and all(c.isalnum() or c in '._$' for c in name) for name in names),
            'UNIQUE_CANONICAL_RETAINED_INITIALIZERS_REQUIRED')
    return names


def emergency_exercise_observer_ready(app, row):
    release = read(app / 'release-manifest.json')
    if release.get('emergencyExerciseAtomicCandidate') is None:
        return None
    require(release.get('emergencyExerciseAtomicCandidate') == 'exercise-parent-files-atomic-v2'
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
    expected = payload.get('files', {}).get('payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.class', {}).get('sha256')
    require(expected == 'dcccbefe5a7d88d0bcd61153f3d9651beb5dc5bd45b443b86eaf21ea06fa0ece', 'EXACT_TESTED_EXERCISE_PAYLOAD_CLASS_REQUIRED')
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


def health(app, row, guarded=True, *, gateway_port=18892):
    for path in ['/zhumadian/home', '/zhumadian/h5/', '/zhumadian/project-icon-20261025.svg',
                 '/zhumadian/api/jnpf/oauth/getLoginConfig']:
        status, body = http_check(gateway_port, path)
        require(status == 200, 'OWN_GATEWAY_HTTP_FAILED:' + path)
        if path.endswith('getLoginConfig'):
            require(json.loads(body).get('code') == 200, 'LOGIN_CONFIG_FAILED')
    if guarded:
        status, body = http_check(gateway_port, '/zhumadian/api/serv/checkInventory/page?current=1&size=1')
        result = json.loads(body)
        require(status == 200 and result.get('code') == 600 and result.get('data') is None,
                'MISSING_AUTH_CONTRACT_FAILED')
        run = Path(row['run']); platform = Path(row['platformRun'])
        regular(run); regular(platform)
        guard = marker(run / 'b/missing-auth-guard-ready.properties')
        password = marker(platform / 'password-identity-claims-ready.properties')
        require(guard.get('guardCount') == guard.get('originalSecurityInterceptorCount') == '1'
                and guard.get('guardBeforeOriginal') == 'true' and
                guard.get('tokenValidationReplaced') == 'false', 'ORIGINAL_AUTH_CHAIN_REQUIRED')
        require(password.get('passwordBeanAdapted') ==
                password.get('originalPasswordAuthenticationInherited') ==
                password.get('originalSigningAndSessionsInherited') == 'true',
                'ORIGINAL_PASSWORD_AND_SESSION_CHAIN_REQUIRED')
    finding_observer_ready(app, row)
    emergency_team_observer_ready(app, row)
    emergency_exercise_observer_ready(app, row)
    event_disposal_observer_ready(app, row)
    training_observer_ready(app, row)
    safety_batch_observer_ready(app, row)

def installed_overlay(app, pin):
    """Preserve the installed callback/auth overlay when restarting or restoring code."""
    check_file(app, 'release-manifest.json', pin)
    release = read(app / 'release-manifest.json')
    digest = release.get('missingAuthOverlayManifestSHA256')
    if digest is None:
        return None
    require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) is not None,
            'INSTALLED_CALLBACK_OVERLAY_PIN_REQUIRED')
    relative = 'payload/callback-overlay/20261026-password-identity/manifest.json'
    check_file(app, relative, digest)
    return relative, digest

def launch(app, pin, folder, overlay=None, *, gateway_port=18892):
    selected = installed_overlay(app, pin)
    require(overlay is None or overlay == selected, 'CALLBACK_OVERLAY_RELEASE_MISMATCH')
    overlay = selected
    log_path = folder / ('controller-' + uuid.uuid4().hex + '.log')
    args = [str(app / 'runtime/python/python.exe'), '-I', '-B',
            str(app / 'tools/serve_original_server_release.py'), '--application', str(app),
            '--release-manifest-sha256', pin, '--gateway-port', str(gateway_port)]
    if overlay:
        args += ['--callback-overlay', str(app / overlay[0]), '--callback-overlay-sha256', overlay[1]]
    with log_path.open('xb') as output:
        process = subprocess.Popen(args, cwd=app, stdout=output, stderr=subprocess.STDOUT,
            close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)
    write_json(folder / 'launch-state.json', {'controllerPID': process.pid,
        'releaseSHA256': pin, 'log': str(log_path), 'ready': False})
    print('START: controller PID=' + str(process.pid) + '; waiting for real ready', flush=True)
    end = time.monotonic() + 600; next_progress = 0
    while time.monotonic() < end:
        if process.poll() is not None:
            raise RuntimeError('NEW_CONTROLLER_EXITED_INSPECT_LOG:' + str(log_path))
        current = app / 'UserData/OriginalServer/current-run.json'
        if current.exists():
            row = read(current)
            if row.get('controllerPID') == process.pid and row.get('ready'):
                write_json(folder / 'launch-state.json', dict(row, releaseSHA256=pin))
                return owned_ready(app, pin, gateway_port=gateway_port)
        if time.monotonic() >= next_progress:
            print('START: waiting; log=' + str(log_path), flush=True)
            next_progress = time.monotonic() + 10
        time.sleep(1)
    # Never kill a controller or restore code underneath running components.
    raise RuntimeError('START_TIMEOUT_CONTROLLER_RETAINED_INSPECT_LOG:' + str(log_path))

def ingress_preflight(app, plan, report):
    regular(IIS)
    check_file(IIS, 'App_Code/XnbyReferenceProxy.cs', plan['iisProxySHA256'])
    config = ET.fromstring((IIS / 'web.config').read_bytes())
    require(any(r.get('type') == 'XnbyReferenceProxy' for r in
                config.findall('./system.webServer/handlers/add')), 'EXISTING_ORIGINAL_IIS_HANDLER_REQUIRED')
    # The existing installer contains the verified certificate/SNI and site checks.
    ingress_relative = 'tools/install_original_server_ingress.py'
    ingress_pin = read(app / 'release-manifest.json')['controllerFiles'].get(ingress_relative)
    if ingress_pin is None:
        # R5 omitted this already-installed helper from its release manifest.
        # A SHA-pinned update plan may name the independently verified old file.
        ingress_pin = plan.get('existingIngressToolSHA256')
    require(isinstance(ingress_pin, str) and re.fullmatch('[0-9a-f]{64}', ingress_pin),
            'PINNED_EXISTING_INGRESS_TOOL_REQUIRED')
    check_file(app, ingress_relative, ingress_pin)
    sys.path.insert(0, str(app / 'tools'))
    import install_original_server_ingress as ingress
    address = ingress.preflight(app, IIS, report)
    require(ingress.tls_local(address, '/zhumadian/home')[0] == 200,
            'CURRENT_PUBLIC_HOME_REQUIRED')
    return ingress, address

def refresh_deployment_owner(app, row):
    path = regular(app, 'UserData/OriginalDeployment/active-deployment.private.json')
    require(path.is_file(), 'EXISTING_DEPLOYMENT_OWNER_REQUIRED')
    value = read(path)
    require(value.get('releaseId') == row['releaseId'], 'EXISTING_DEPLOYMENT_RELEASE_REQUIRED')
    value.update(controllerPID=row['controllerPID'], run=row['run'])
    write_json(path, value)

def preserve_previous_update(app, attempt, old_pin):
    path = regular(app, 'UserData/OriginalPublicUpdates/latest.json')
    if not path.exists():
        return False
    require(path.stat().st_size <= 64 * 1024, 'BOUNDED_PREVIOUS_UPDATE_RECEIPT_REQUIRED')
    previous = read(path)
    require(previous.get('newReleaseSHA256') == old_pin and previous.get('ready') is True
            and not previous.get('rolledBack'), 'EXACT_PREVIOUS_ACTIVE_UPDATE_REQUIRED')
    atomic(attempt / 'previous-latest.json', path.read_bytes())
    return True

def restore_previous_update(app, attempt, restored):
    path = regular(attempt, 'previous-latest.json')
    if not path.exists():
        return False
    require(path.stat().st_size <= 64 * 1024, 'BOUNDED_PREVIOUS_UPDATE_RECEIPT_REQUIRED')
    previous = read(path)
    require(previous.get('newReleaseSHA256') == sha(app / 'release-manifest.json')
            and previous.get('ready') is True and not previous.get('rolledBack'),
            'RESTORED_ACTIVE_RELEASE_RECEIPT_REQUIRED')
    previous.update(controllerPID=restored['controllerPID'], run=restored['run'],
                    publicAccepted=False, userNormalLoginPending=True)
    write_json(app / 'UserData/OriginalPublicUpdates/latest.json', previous)
    return True

def apply_update(app, bundle, pin):
    print('CHECK: validating sparse files and installed release; public service remains running', flush=True)
    plan, old_pin, changes = load_bundle(app, bundle, pin)
    require(shutil.disk_usage(app).free >= 12 * 1024 ** 3, 'TWELVE_GIB_SERVER_FREE_REQUIRED')
    row = owned_ready(app, old_pin)
    identity = read(regular(app, 'UserData/OriginalServer/installation.json'))
    require(identity['releaseId'] == plan['releaseId'] and identity['databaseUUID'] == row['databaseUUID'],
            'EXISTING_DATA_IDENTITY_REQUIRED')
    deployment = read(regular(app, 'UserData/OriginalDeployment/active-deployment.private.json'))
    require(deployment['releaseId'] == plan['releaseId'], 'EXISTING_DEPLOYMENT_RECORD_REQUIRED')
    ingress, address = ingress_preflight(app, plan, {})
    attempt = regular(app, 'UserData/OriginalPublicUpdates/' + uuid.uuid4().hex)
    backup_code(app, attempt, changes)
    preserve_previous_update(app, attempt, old_pin)
    report = {'schema': 'zhumadian.public-test-update.receipt.v1', 'updateId': plan['updateId'],
        'oldReleaseSHA256': old_pin, 'newReleaseSHA256': plan['newReleaseSHA256'],
        'callbackOverlay': plan['callbackOverlay'], 'callbackOverlaySHA256': plan['callbackOverlaySHA256'],
        'databaseUUID': identity['databaseUUID'], 'attempt': str(attempt), 'codeApplied': False,
        'iisChanged': False, 'databaseOrUploadsCopied': False, 'publicAccepted': False,
        'startedAt': datetime.datetime.now().astimezone().isoformat()}
    write_json(attempt / 'result.json', report)
    write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)
    try:
        normal_stop(app, old_pin, row)
        report['oldNormalShutdownCompleted'] = True
        # Revalidate after shutdown to detect changes between preflight and mutation.
        with server_lock(app):
            load_bundle(app, bundle, pin)
            report['mutationStarted'] = True
            replace_code(app, bundle, changes)
        report['codeApplied'] = True
        new = launch(app, plan['newReleaseSHA256'], attempt,
                     (plan['callbackOverlay'], plan['callbackOverlaySHA256']))
        health(app, new)
        for path in ['/zhumadian/home', '/zhumadian/h5/',
                     '/zhumadian/api/jnpf/oauth/getLoginConfig']:
            status, body = ingress.tls_local(address, path)
            require(status == 200, 'SERVER_TLS_GATEWAY_CHECK_FAILED')
            if path.endswith('getLoginConfig'):
                require(json.loads(body).get('code') == 200, 'SERVER_TLS_LOGIN_CONFIG_FAILED')
        status, body = ingress.tls_local(address,
            '/zhumadian/api/serv/checkInventory/page?current=1&size=1')
        require(status == 200 and json.loads(body).get('code') == 600,
                'SERVER_TLS_MISSING_AUTH_CHECK_FAILED')
        require(read(app / 'UserData/OriginalServer/installation.json') == identity,
                'INSTALLED_DATA_IDENTITY_CHANGED')
        refresh_deployment_owner(app, new)
        report.update(ready=True, controllerPID=new['controllerPID'], run=new['run'],
            serverLocalTLSVerified=True, externalPublicVerificationPending=True,
            userNormalLoginPending=True)
        write_json(app / 'UserData/OriginalPublicUpdates/latest.json', report)
        write_json(app / 'UserData/OriginalPublicUpdates/pending.json', dict(report, completed=True))
        print(plan['updateId'] + '_READY: server TLS passed; external verification and normal user login remain pending', flush=True)
    except BaseException as error:
        report.update(failureType=type(error).__name__, failure=str(error), ready=False)
        # Leave a running/unknown startup untouched. Rollback requires a proven normal stop.
        report['manualRecoveryRequired'] = bool(report.get('oldNormalShutdownCompleted') or
                                                report.get('mutationStarted'))
        print('UPDATE_STOPPED: inspect ' + str(attempt / 'result.json') + '; do not repeat the CMD', flush=True)
        raise
    finally:
        report['endedAt'] = datetime.datetime.now().astimezone().isoformat()
        write_json(attempt / 'result.json', report)
        write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)

def start_installed(app):
    latest = read(regular(app, 'UserData/OriginalPublicUpdates/latest.json'))
    require(sha(app / 'release-manifest.json') == latest['newReleaseSHA256'], 'LATEST_RELEASE_PIN_REQUIRED')
    current = read(app / 'UserData/OriginalServer/current-run.json')
    if process_owned(current.get('controllerPID'), app, latest['newReleaseSHA256']):
        health(app, owned_ready(app, latest['newReleaseSHA256']))
        print('R5_ALREADY_RUNNING: no duplicate controller started', flush=True)
        return
    require((Path(current['run']) / 'receipt.json').is_file(), 'PRIOR_RUN_RECEIPT_REQUIRED')
    previous = read(Path(current['run']) / 'receipt.json')
    require(previous.get('normalOwnedShutdown') and previous.get('allOwnedChildrenExited'),
            'PRIOR_NORMAL_SHUTDOWN_REQUIRED')
    row = launch(app, latest['newReleaseSHA256'], Path(latest['attempt']),
                 (latest['callbackOverlay'], latest['callbackOverlaySHA256']))
    health(app, row); refresh_deployment_owner(app, row)
    print('R5_RESTART_READY', flush=True)

def rollback_latest(app):
    latest = read(regular(app, 'UserData/OriginalPublicUpdates/latest.json'))
    require(not latest.get('directoryMigration'), 'USE_DIRECTORY_MIGRATION_COORDINATOR_FOR_LAYOUT_ROLLBACK')
    attempt = Path(latest['attempt']).absolute()
    require(attempt.parent == app / 'UserData/OriginalPublicUpdates', 'OWNED_UPDATE_BACKUP_REQUIRED')
    regular(attempt)
    require(not latest.get('rolledBack'), 'ROLLBACK_ALREADY_COMPLETED')
    row = owned_ready(app, latest['newReleaseSHA256'])
    changes = read(attempt / 'changes.json')
    # Check backup hashes and post-update file pins before requesting downtime.
    for name, change in changes.items():
        if change['after'] is not None:
            check_file(app, name, change['after'])
        else:
            require(not regular(app, name).exists(), 'REMOVED_PATH_RECREATED')
        if change['before'] is not None:
            check_file(attempt / 'before', name, change['before'])
    normal_stop(app, latest['newReleaseSHA256'], row)
    with server_lock(app):
        restore_code(app, attempt, changes)
    require(sha(app / 'release-manifest.json') == latest['oldReleaseSHA256'], 'RESTORED_RELEASE_PIN_REQUIRED')
    old = launch(app, latest['oldReleaseSHA256'], attempt)
    health(app, old, guarded=False); refresh_deployment_owner(app, old)
    latest.update(rolledBack=True, publicAccepted=False)
    write_json(attempt / 'rollback-result.json', latest)
    if not restore_previous_update(app, attempt, old):
        write_json(app / 'UserData/OriginalPublicUpdates/latest.json', latest)
    print('OLD_CODE_RESTORED: installed database and uploads retained', flush=True)

def recover_pending(app):
    """Recover a failed update only when its controller is ready or fully gone.

    An unknown or still-starting controller is deliberately left alone.
    """
    report = read(regular(app, 'UserData/OriginalPublicUpdates/pending.json'))
    require(report.get('failureType') and not report.get('ready') and
            not report.get('recovered'), 'FAILED_UPDATE_REQUIRED')
    attempt = Path(report['attempt']).absolute()
    require(attempt.parent == app / 'UserData/OriginalPublicUpdates', 'OWNED_UPDATE_BACKUP_REQUIRED')
    regular(attempt)
    old_pin = report['oldReleaseSHA256']; new_pin = report['newReleaseSHA256']
    current = read(app / 'UserData/OriginalServer/current-run.json')
    if process_owned(current.get('controllerPID'), app, new_pin):
        normal_stop(app, new_pin, owned_ready(app, new_pin))
    elif process_owned(current.get('controllerPID'), app, old_pin):
        require(not report.get('mutationStarted'), 'OLD_CONTROLLER_RUNNING_DURING_MUTATION')
        print('OLD_VERSION_STILL_RUNNING: no code recovery necessary', flush=True)
        return
    state_path = attempt / 'launch-state.json'
    if state_path.exists():
        launch_state = read(state_path)
        require(not process_owned(launch_state.get('controllerPID'), app,
                launch_state['releaseSHA256']), 'STARTING_CONTROLLER_RETAINED_NO_RECOVERY')
    # No database owner may remain, even after a controller-level startup failure.
    if report.get('mutationStarted') and state_path.exists():
        launch_state = read(state_path)
        receipts = []
        for receipt_path in (app / 'UserData/OriginalServer/runs').glob('j*/receipt.json'):
            regular(receipt_path)
            value = read(receipt_path)
            if value.get('controllerPID') == launch_state['controllerPID']:
                receipts.append(value)
        require(len(receipts) == 1 and receipts[0].get('allOwnedChildrenExited') is True
                and receipts[0].get('exitCodesBeforeJobClose', {}).get('mysql') == 0,
                'STARTUP_NORMAL_DATABASE_SHUTDOWN_RECEIPT_REQUIRED')
    with server_lock(app):
        require(sha(app / 'release-manifest.json') in (old_pin, new_pin), 'RECOVERY_RELEASE_DRIFT')
        if report.get('mutationStarted'):
            restore_code(app, attempt, read(attempt / 'changes.json'))
    row = launch(app, old_pin, attempt)
    health(app, row, guarded=False); refresh_deployment_owner(app, row)
    report.update(recovered=True, manualRecoveryRequired=False)
    restore_previous_update(app, attempt, row)
    write_json(attempt / 'recovery-result.json', report)
    write_json(app / 'UserData/OriginalPublicUpdates/pending.json', report)
    print('FAILED_UPDATE_RECOVERED_TO_OLD_CODE: database and uploads retained', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--apply', type=Path); mode.add_argument('--start', action='store_true')
    mode.add_argument('--rollback-latest', action='store_true')
    mode.add_argument('--recover-pending', action='store_true')
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args(); app = args.application.absolute()
    require(os.name == 'nt' and app == TARGET and app.resolve(strict=True) == app,
            'EXACT_EXISTING_SERVER_INSTALLATION_REQUIRED')
    import msvcrt
    lock_path = regular(app, 'UserData/OriginalPublicUpdates/update.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a+b') as lock:
        lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            if args.apply:
                apply_update(app, args.apply.absolute(), args.manifest_sha256)
            elif args.start:
                start_installed(app)
            elif args.recover_pending:
                recover_pending(app)
            else:
                rollback_latest(app)
        finally:
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

if __name__ == '__main__':
    main()
