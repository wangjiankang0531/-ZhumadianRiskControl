"""Fixed R50 -> R51 Home-only maintenance; original lifecycle stays authoritative.

All server modes require the fixed transport manifest hash and the exact host.
Apply/recover/rollback must be run by the separately qualified durable wrapper.
No private configuration, business data, models or GIS is shipped or removed.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib.util, json, os, socket, stat, sys, time, zipfile

HOST = 'izcdi578349jcez'
APP = Path('C:/inetpub/wwwroot/Zhumadian/Application')
TRANSPORT = Path('C:/FTP_Root/Zhumadian/Zhumadian_Home_Same_Window_20261112_R51')
OLD = 'c28b3dc4de2ce70ce4d4fdc1add37e606dd1c15c953225760e08d044f601e55d'
NEW = 'b36491663db37033ae2fc450b0209e864d5ebd7b7b7ed1bba7fda6a7e5545323'
TRANSITION = 'dd15eec05802016023b8ffa1583b0c96de27340da5dabbc015784ae5c68547eb'
PLAN = '746e1e5d0bb8b678271f58c286549b4ace86612f2d4d4b3634a5d7c75d0aa724'
UPDATE = '20261112-public-scene-same-window-r51'
SCHEMA = 'xnby.public.home.same-window.transport.v1'


def need(value, code):
    if not value:
        raise ValueError(code)


def regular(path):
    path = Path(path).absolute()
    need('..' not in path.parts, 'CANONICAL_PATH_REQUIRED')
    for item in [path, *path.parents]:
        if item.exists():
            need(not item.is_symlink() and not (getattr(item.lstat(), 'st_file_attributes', 0) & 1024), 'REPARSE_REFUSED')
    return path


def sha(path):
    with regular(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'DUPLICATE_JSON_KEY_REFUSED')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('NONFINITE_JSON_REFUSED')))


def read(path, limit=262144):
    with regular(path).open('rb') as stream:
        raw = stream.read(limit + 1)
    need(len(raw) <= limit, 'BOUNDED_JSON_REQUIRED')
    return strict_json(raw)


def put_new(path, value):
    with regular(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def row_check(path, row):
    need(set(row) == {'bytes', 'sha256'} and type(row['bytes']) is int and row['bytes'] >= 0, 'EXACT_FILE_ROW_REQUIRED')
    path = regular(path)
    need(path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'FIXED_FILE_MISMATCH')


def member_name(name):
    need(isinstance(name, str) and name and '\\' not in name and ':' not in name, 'ZIP_CANONICAL_NAME_REQUIRED')
    parts = PurePosixPath(name).parts
    need(parts and not name.startswith('/') and all(p not in ('.', '..') for p in parts)
         and '/'.join(parts) == name, 'ZIP_CANONICAL_NAME_REQUIRED')
    need(name in ('transition.json', 'same_window_incremental_runtime.py')
         or name.startswith(('runtime/tools/', 'baseline-runtime/tools/', 'bundle/payload/'))
         or name == 'bundle/update-manifest.json', 'ZIP_MEMBER_OUTSIDE_CODE_SCOPE')
    need(not any(p.lower() in ('private', 'userdata', 'seed') for p in parts), 'PRIVATE_TRANSPORT_REFUSED')
    return name


def archive_rows(archive, rows):
    need(isinstance(rows, dict) and 1 <= len(rows) <= 1000, 'BOUNDED_ARCHIVE_REQUIRED')
    need(sum(row['bytes'] for row in rows.values()) <= 128 * 1024**2, 'ARCHIVE_SIZE_BOUND_REQUIRED')
    with zipfile.ZipFile(regular(archive)) as zipped:
        infos = zipped.infolist()
        need(len(infos) == len(rows), 'EXACT_ARCHIVE_CLOSURE_REQUIRED')
        seen = set()
        for info in infos:
            name = member_name(info.filename)
            need(name.casefold() not in seen and name in rows, 'ZIP_DUPLICATE_OR_UNKNOWN_MEMBER')
            seen.add(name.casefold())
            need(not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16)
                 and not (info.flag_bits & 1), 'REGULAR_UNENCRYPTED_ZIP_REQUIRED')
            row = rows[name]
            need(set(row) == {'bytes', 'sha256'} and type(row['bytes']) is int
                 and 0 <= row['bytes'] <= 16 * 1024**2 and info.file_size == row['bytes'], 'EXACT_ZIP_MEMBER_SIZE_REQUIRED')
            digest = hashlib.sha256(); length = 0
            with zipped.open(info) as stream:
                while True:
                    block = stream.read(1024 * 1024)
                    if not block: break
                    length += len(block); need(length <= row['bytes'], 'ZIP_MEMBER_TOO_LARGE')
                    digest.update(block)
            need(length == row['bytes'] and digest.hexdigest() == row['sha256'], 'ZIP_MEMBER_SHA_MISMATCH')


def inspect_transport(root, scope_pin):
    root = regular(root); manifest = regular(root / 'prepared-manifest.json')
    need(len(scope_pin) == 64 and sha(manifest) == scope_pin, 'EXACT_TRANSPORT_MANIFEST_REQUIRED')
    value = read(manifest)
    need(set(value) == {'schema', 'revision', 'host', 'application', 'transportDirectory', 'oldReleaseSHA256',
                       'newReleaseSHA256', 'transitionSHA256', 'planSHA256', 'files', 'archiveMembers',
                       'writes', 'removes', 'privateGISModelsOrBusinessDataIncluded'}, 'EXACT_TRANSPORT_FIELDS_REQUIRED')
    need(value['schema'] == SCHEMA and value['revision'] == UPDATE and value['host'] == HOST
         and value['application'] == APP.as_posix() and value['transportDirectory'] == TRANSPORT.as_posix()
         and value['oldReleaseSHA256'] == OLD and value['newReleaseSHA256'] == NEW
         and value['transitionSHA256'] == TRANSITION and value['planSHA256'] == PLAN
         and type(value['writes']) is int and value['writes'] == 526
         and type(value['removes']) is int and value['removes'] == 520
         and value['privateGISModelsOrBusinessDataIncluded'] is False, 'EXACT_R51_TRANSPORT_REQUIRED')
    need(set(value['files']) == {'R51_Home_Same_Window.zip', 'public_home_r51_controller.py',
                                 'durable_original_operation_r2327.py'}, 'EXACT_THREE_TRANSPORT_PAYLOADS_REQUIRED')
    for name, row in value['files'].items(): row_check(root / name, row)
    archive_rows(root / 'R51_Home_Same_Window.zip', value['archiveMembers'])
    return value


def stage_check(stage, rows):
    stage = regular(stage)
    need(stage.is_dir(), 'PREPARED_STAGE_REQUIRED')
    actual = set()
    for base, dirs, files in os.walk(stage, followlinks=False):
        for name in dirs: regular(Path(base) / name)
        for name in files:
            path = regular(Path(base) / name); actual.add(path.relative_to(stage).as_posix())
    need(actual == set(rows), 'EXACT_EXTRACTED_CODE_CLOSURE_REQUIRED')
    for name, row in rows.items(): row_check(stage / member_name(name), row)


def prepare(root, value):
    stage = regular(root / '_stage-r51')
    need(not stage.exists(), 'STAGE_ALREADY_EXISTS_NO_OVERWRITE')
    stage.mkdir()
    with zipfile.ZipFile(root / 'R51_Home_Same_Window.zip') as zipped:
        for info in zipped.infolist():
            path = regular(stage / member_name(info.filename))
            path.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(info) as source, path.open('xb') as destination:
                while True:
                    block = source.read(1024 * 1024)
                    if not block: break
                    destination.write(block)
    stage_check(stage, value['archiveMembers'])


def load_runtime(stage, rows):
    stage_check(stage, rows)
    path = stage / 'same_window_incremental_runtime.py'
    spec = importlib.util.spec_from_file_location('qualified_r51_original_bridge', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.runtime(stage, TRANSITION)


def check(m, stage, scope_pin, root):
    plan, old, changes = m.load_bundle(APP, stage / 'bundle', PLAN)
    need(old == OLD and len(plan['files']) == 526 and len(plan['removedFrontendFiles']) == 520, 'EXACT_1046_CODE_PATHS_REQUIRED')
    budget = m.candidate_runtime_pool_preflight(APP, stage / 'bundle', plan)
    need(budget is not None, 'CANDIDATE_MAPPER_AND_POOL_REQUIRED')
    row = m.owned_ready(APP, OLD); m.health(APP, row)
    identity = m.read(m.regular(APP, 'UserData/OriginalServer/installation.json'))
    deployment = m.read(m.regular(APP, 'UserData/OriginalDeployment/active-deployment.private.json'))
    need(identity['releaseId'] == plan['releaseId'] == deployment['releaseId']
         and identity['databaseUUID'] == row['databaseUUID'], 'ORIGINAL_RUNTIME_DATA_IDENTITY_REQUIRED')
    m.ingress_preflight(APP, plan, {})
    need(m.shutil.disk_usage(APP).free >= 12 * 1024**3, 'TWELVE_GIB_SERVER_FREE_REQUIRED')
    put_new(root / 'preflight.json', {'schema': 'xnby.public.r51.preflight.v1', 'scopeSHA256': scope_pin,
        'oldReleaseSHA256': OLD, 'newReleaseSHA256': NEW, 'planSHA256': PLAN, 'updateId': UPDATE,
        'passed': True, 'checkedAtEpoch': time.time(), 'noServiceChanged': True,
        'completePayloadFiles': 16224, 'writes': 526, 'removes': 520,
        'originalDataIdentityMatched': True, 'originalMapperAndBudgetPassed': True})
    print('R51_PREFLIGHT_PASSED_EXACT_R50_NO_SERVICE_CHANGED', flush=True)


def prior_receipt(m, mode):
    key = 'pending.json' if mode == 'recover' else 'latest.json'
    value = m.read(m.regular(APP, 'UserData/OriginalPublicUpdates/' + key))
    need(value.get('updateId') == UPDATE and value.get('oldReleaseSHA256') == OLD
         and value.get('newReleaseSHA256') == NEW, 'ONLY_THIS_R51_OPERATION_ALLOWED')
    attempt = regular(value['attempt'])
    need(attempt.parent == regular(APP / 'UserData/OriginalPublicUpdates'), 'OWN_ATTEMPT_BACKUP_REQUIRED')
    actual = m.read(m.regular(attempt, 'result.json'))
    need(actual.get('updateId') == UPDATE and actual.get('attempt') == value['attempt']
         and actual.get('oldReleaseSHA256') == OLD and actual.get('newReleaseSHA256') == NEW,
         'EXACT_THIS_ATTEMPT_RECEIPT_REQUIRED')


def require_durable(root):
    import subprocess
    wrapped = getattr(subprocess.Popen, '__code__', None)
    need(wrapped is not None and wrapped.co_name == 'tracked'
         and regular(wrapped.co_filename) == regular(root / 'durable_original_operation_r2327.py')
         and sha(root / 'durable_original_operation_r2327.py') ==
         '54fab8eaa203e73fc70b92c5f9aebe2acc0f5b9319f33ff57dbd0d97f1da38ed',
         'QUALIFIED_DURABLE_CONTROLLER_HANDLE_TRACKER_REQUIRED')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'check', 'apply', 'recover', 'rollback'])
    parser.add_argument('--scope-sha256', required=True)
    args = parser.parse_args()
    need(os.name == 'nt' and socket.gethostname().casefold() == HOST, 'EXACT_PUBLIC_SERVER_REQUIRED')
    root = regular(Path(__file__).parent)
    need(root == regular(TRANSPORT), 'EXACT_SERVER_TRANSPORT_DIRECTORY_REQUIRED')
    value = inspect_transport(root, args.scope_sha256)
    if args.mode == 'prepare':
        prepare(root, value); print('R51_CODE_STAGE_PREPARED_NO_SERVICE_CHANGED', flush=True); return
    m = load_runtime(root / '_stage-r51', value['archiveMembers'])
    if args.mode == 'check':
        check(m, root / '_stage-r51', args.scope_sha256, root); return
    require_durable(root)
    if args.mode == 'apply':
        receipt = read(root / 'preflight.json')
        need(receipt.get('passed') is True and receipt.get('scopeSHA256') == args.scope_sha256
             and receipt.get('updateId') == UPDATE and receipt.get('planSHA256') == PLAN
             and type(receipt.get('checkedAtEpoch')) in (int, float)
             and 0 <= time.time() - receipt['checkedAtEpoch'] <= 3600, 'FRESH_EXACT_PREFLIGHT_REQUIRED')
        need(not (root / 'apply-started.json').exists(), 'NO_REPEAT_APPLY_REQUIRED')
        put_new(root / 'apply-started.json', {'updateId': UPDATE, 'scopeSHA256': args.scope_sha256})
        m.apply_update(APP, root / '_stage-r51/bundle', PLAN)
        need(sha(APP / 'release-manifest.json') == NEW, 'INSTALLED_R51_REQUIRED')
        print('R51_APPLIED_EXTERNAL_TLS_AND_NORMAL_USER_ACCEPTANCE_PENDING', flush=True)
    elif args.mode == 'recover':
        prior_receipt(m, args.mode); m.recover_pending(APP)
    else:
        prior_receipt(m, args.mode); m.rollback_latest(APP)


if __name__ == '__main__':
    main()
