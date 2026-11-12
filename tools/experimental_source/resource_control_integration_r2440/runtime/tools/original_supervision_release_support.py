"""Optional pinned supervision module integration; legacy releases are a no-op.

Never logs arguments, properties or credentials. No process or database access.
The controller must call preflight before resource allocation, then adapt the
materialized business launch and require readiness before exposing its gateway.
"""
from pathlib import Path
import copy
import hashlib
import re

FIELD = 'businessSupervisionPdf'
INITIALIZER = 'xnby.replica.supervision.OriginalSupervisionInitializerR504'
MAIN = 'xnby.replica.OriginalBusinessLaunch'
MODULE = 'payload/business/run-template/own-supervision-pdf.jar'
ORIGINAL_SHA = '363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a'
MODULE_SHA = '12b5023faf68bdbca1d462df66be75b507d9f40b02721b419a074f7645df3fcd'
MODULE_BYTES = 20041203
CONTRACT = {'revision': 'original-supervision-spring-factories-v1',
            'file': MODULE, 'bytes': MODULE_BYTES, 'sha256': MODULE_SHA,
            'originalBusinessJarSHA256': ORIGINAL_SHA}
READY = {'schema': 'xnby.supervision-pdf.v1', 'installed': 'true',
         'originalServiceAndFileClassesPinned': 'true',
         'onlyAddPdfAndUploadPdfOverridden': 'true',
         'existingTransactionManagerCount': '1',
         'rollbackCleanupBestEffort': 'true',
         'normalRoleHTTPAcceptedByStartup': 'false'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def descriptor(release):
    if FIELD not in release:
        return None
    need(release[FIELD] == CONTRACT, 'EXACT_SUPERVISION_DESCRIPTOR_REQUIRED')
    return release[FIELD]


def regular(path):
    path = Path(path).absolute()
    need('..' not in path.parts and path.resolve(strict=True) == path
         and path.is_file(), 'EXACT_SUPERVISION_REGULAR_FILE_REQUIRED')
    for item in [path, *path.parents]:
        need(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400,
             'SUPERVISION_REPARSE_PATH_REFUSED')
    return path


def initializers(value):
    need(isinstance(value, str) and value.isascii() and len(value) <= 8192,
         'BUSINESS_INITIALIZER_LIST_REQUIRED')
    items = value.split(',') if value else []
    need(len(items) == len(set(items)) and all(re.fullmatch(
        r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+', x) for x in items),
        'UNIQUE_BUSINESS_INITIALIZERS_REQUIRED')
    return items


def launch_shape(arguments):
    need(isinstance(arguments, list) and all(isinstance(x, str) for x in arguments)
         and arguments.count(MAIN) == 1, 'ORIGINAL_BUSINESS_MAIN_REQUIRED')
    index = arguments.index(MAIN)
    need(index + 2 == len(arguments) and arguments[:index].count('-cp') == 1,
         'ORIGINAL_BUSINESS_LAUNCH_SHAPE_REQUIRED')
    cp = arguments.index('-cp')
    need(cp + 2 == index, 'ORIGINAL_BUSINESS_CLASSPATH_POSITION_REQUIRED')
    need(not any(x.startswith(('-Down.supervision.', '-Dcontext.initializer.classes=',
                               '-Dspring.context.initializer.classes='))
                 or x in ('-classpath', '--class-path', '-jar')
                 for x in arguments[:cp]), 'SUPERVISION_LAUNCH_OVERRIDE_REFUSED')
    entries = arguments[cp + 1].split(';')
    need(all(entries) and len(entries) == len(set(entries)) and not any(
        'own-supervision-pdf.jar' in x for x in entries), 'UNIQUE_ORIGINAL_CLASSPATH_REQUIRED')
    return cp, entries


def configure_business(release, spec):
    if descriptor(release) is None:
        return spec
    launch_shape(spec.get('businessArguments'))
    values = spec.get('configuration', {}).get('business')
    need(isinstance(values, dict), 'BUSINESS_CONFIGURATION_REQUIRED')
    need(not any(k.startswith('own.supervision.') for k in values),
         'SUPERVISION_CONFIGURATION_OVERRIDE_REFUSED')
    items = initializers(values.get('context.initializer.classes', ''))
    need(INITIALIZER not in items, 'SUPERVISION_INITIALIZER_ALREADY_PRESENT')
    result = copy.deepcopy(spec)
    # Keep the exact original lifecycle/missing-auth property contract. The
    # pinned module discovers its initializer through META-INF/spring.factories.
    need(result['configuration']['business']==values,'UNCHANGED_BUSINESS_CONFIGURATION_REQUIRED')
    return result


def preflight(application, release, spec):
    if descriptor(release) is None:
        return None
    configure_business(release, spec)
    app = Path(application).absolute()
    need(app.name == 'Application', 'OWN_SUPERVISION_APPLICATION_REQUIRED')
    original = regular(app / 'payload/business/application.jar')
    module = regular(app / MODULE)
    need(sha(original) == ORIGINAL_SHA, 'ORIGINAL_SUPERVISION_APPLICATION_JAR_CHANGED')
    need(module.stat().st_size == MODULE_BYTES and sha(module) == MODULE_SHA,
         'PINNED_SUPERVISION_MODULE_CHANGED')
    # The whole archive digest pins both class entries and unmodified OFL font.
    return {'modulePinned': True, 'originalJarPinned': True}


def _property(arguments, name):
    prefix = '-D' + name + '='
    items = [x[len(prefix):] for x in arguments if x.startswith(prefix)]
    need(len(items) == 1, 'ONE_SUPERVISION_RUNTIME_PROPERTY_REQUIRED')
    return items[0]


def runtime_root(application, business_run):
    app, root = Path(application).absolute(), Path(business_run).absolute()
    need(app.name == 'Application' and root.name == 'b'
         and root.parent.parent == app / 'UserData/OriginalServer/runs'
         and re.fullmatch(r'j[1-9][0-9]{0,3}', root.parent.name),
         'OWN_SUPERVISION_RUNTIME_LAYOUT_REQUIRED')
    return app, root


def adapt_business_launch(application, release, business_run, prepared):
    if descriptor(release) is None:
        return prepared
    app, root = runtime_root(application, business_run)
    module = regular(root / 'own-supervision-pdf.jar')
    need(module.stat().st_size == MODULE_BYTES and sha(module) == MODULE_SHA,
         'SUPERVISION_RUNTIME_MODULE_CHANGED')
    need(sha(regular(app / 'payload/business/application.jar')) == ORIGINAL_SHA,
         'ORIGINAL_SUPERVISION_APPLICATION_JAR_CHANGED')
    need(prepared.get('side') == 'business' and Path(prepared.get('runtime', '')).absolute() == root,
         'PREPARED_SUPERVISION_BUSINESS_RUNTIME_REQUIRED')
    need(initializers(prepared.get('configuration', {}).get('context.initializer.classes', '')).count(INITIALIZER) == 0,
         'SUPERVISION_PREPARED_INITIALIZER_REQUIRED')
    args = prepared.get('arguments')
    cp, entries = launch_shape(args)
    need(Path(args[-1]).absolute() == root and
         Path(_property(args, 'own.candidate.root')).absolute() == root,
         'SUPERVISION_LAUNCH_ROOT_MISMATCH')
    owner = _property(args, 'own.server.owner')
    need(re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', owner),
         'SUPERVISION_CANONICAL_OWNER_REQUIRED')
    owner_path = regular(root / 'server-owner.properties')
    need(owner_path.stat().st_size <= 1024, 'SUPERVISION_OWNER_FILE_TOO_LARGE')
    lines = owner_path.read_text('ascii').splitlines()
    need(len(lines) == 2 and set(lines) == {'schema=zhumadian.original.server.owner.v1', 'ownerId=' + owner},
         'SUPERVISION_RUNTIME_OWNER_MISMATCH')
    original = app / 'payload/business/application.jar'
    need(sum(Path(x).absolute() == original for x in entries) == 1,
         'ORIGINAL_BUSINESS_JAR_CLASSPATH_REQUIRED')
    result = dict(prepared)
    rewritten = list(args)
    rewritten[cp + 1] = ';'.join([str(module), *entries])
    result['arguments'] = ['-Down.supervision.pdf.enabled=true', *rewritten]
    return result


def require_ready(application, release, business_run):
    if descriptor(release) is None:
        return None
    _, root = runtime_root(application, business_run)
    report = regular(root / 'supervision-pdf-ready.properties')
    need(report.stat().st_size <= 2048, 'SUPERVISION_READY_FILE_TOO_LARGE')
    lines = report.read_text('ascii').splitlines()
    need(len(lines) == len(READY) and set(lines) == {k + '=' + v for k, v in READY.items()},
         'EXACT_SUPERVISION_READINESS_REQUIRED')
    return {'installed': True, 'rollbackCleanupBestEffort': True,
            'normalRoleHTTPAcceptedByStartup': False}
