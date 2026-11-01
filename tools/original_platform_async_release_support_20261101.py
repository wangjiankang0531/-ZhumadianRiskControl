"""Enable one exactly declared async metadata extension without changing authentication.

Old releases are a strict no-op. Runtime artifacts, launcher, original native JAR
and original authentication adapter must match before a new JVM is requested.
No arguments, configuration values, credentials or request metadata are logged.
"""
from pathlib import Path
import copy
import hashlib
import re

FIELD = 'platformAsyncRequestMetadata'
INITIALIZER = 'xnby.platform.OriginalAsyncRequestSnapshotRegistration'
OLD_MAIN = 'xnby.platform.OriginalPersistentPlatformLaunch'
NEW_MAIN = 'xnby.platform.OriginalAsyncPersistentPlatformLaunch'
NATIVE_SHA256 = '294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8'
ADAPTER_SHA256 = 'eae7642792992da2ed4d2f6ff94f55001bda649888c754ffb0aeba4a39ae19d5'
CONTRACT = {'revision': 'original-async-request-by-value-v1', 'files': {'payload/platform/run-template/own-platform-async-request.jar': {'bytes': 11183, 'sha256': '027f4c83709fe23116aa5add92a612e75f15f287a9d95fdca37fd45e5999348f'}, 'payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalAsyncPersistentPlatformLaunch.class': {'bytes': 6959, 'sha256': '5786e6b82ffd0faba74e53bfc62dcad3d41f13d83235b9f3ad404937741d659e'}}, 'originalAsyncConfigSHA256': 'b692d97a18bee115146d705e411610db8f1b1ea5bd4ee13184d4a53bdd8734d4'}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def descriptor(release):
    if FIELD not in release:
        return None
    value = release[FIELD]
    need(isinstance(value, dict) and value == CONTRACT, 'EXACT_DECLARED_ASYNC_EXTENSION_REQUIRED')
    return value


def _initializers(value):
    need(isinstance(value, str) and value.isascii() and len(value) <= 8192, 'PLATFORM_INITIALIZER_LIST_REQUIRED')
    items = value.split(',') if value else []
    need(all(re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+', x) for x in items)
         and len(set(items)) == len(items), 'EXACT_UNIQUE_PLATFORM_INITIALIZERS_REQUIRED')
    return items


def configure_platform(release, spec, *, callback_enabled):
    value = descriptor(release)
    if value is None:
        return spec
    need(callback_enabled is True, 'PINNED_ORIGINAL_CALLBACK_OVERLAY_REQUIRED')
    need(isinstance(spec, dict) and isinstance(spec.get('configuration'), dict)
         and isinstance(spec['configuration'].get('platform'), dict), 'PLATFORM_CONFIGURATION_REQUIRED')
    arguments = spec.get('platformArguments')
    need(isinstance(arguments, list) and all(isinstance(x, str) for x in arguments), 'PLATFORM_ARGUMENT_LIST_REQUIRED')
    need(not any(x.startswith('-Down.async.') for x in arguments), 'UNDECLARED_EXISTING_ASYNC_ARGUMENT_REFUSED')
    need(arguments.count(OLD_MAIN) == 1 and NEW_MAIN not in arguments, 'EXACT_ORIGINAL_PLATFORM_MAIN_REQUIRED')
    items = _initializers(spec['configuration']['platform'].get('context.initializer.classes', ''))
    need(INITIALIZER not in items, 'ASYNC_INITIALIZER_ALREADY_PRESENT')
    result = copy.deepcopy(spec)
    result['configuration']['platform']['context.initializer.classes'] = ','.join([*items, INITIALIZER])
    return result


def _regular(path):
    path = Path(path).absolute()
    need(path.resolve(strict=True) == path and path.is_file(), 'EXACT_REGULAR_RUNTIME_CODE_REQUIRED')
    for item in [*path.parents, path]:
        need(not item.is_symlink() and not getattr(item.lstat(), 'st_file_attributes', 0) & 0x400,
             'REDIRECTED_RUNTIME_CODE_REFUSED')
    return path


def _property(arguments, name):
    prefix = '-D' + name + '='
    selected = [x[len(prefix):] for x in arguments if x.startswith(prefix)]
    need(len(selected) == 1, 'ONE_ORIGINAL_PLATFORM_PATH_PROPERTY_REQUIRED')
    return selected[0]


def adapt_platform_launch(application, release, platform_run, prepared):
    value = descriptor(release)
    if value is None:
        return prepared
    app, root = Path(application).absolute(), Path(platform_run).absolute()
    need(app.name == 'Application' and root.parent == app / 'UserData/TianjinOriginalPlatform/runs'
         and re.fullmatch(r'j[1-9][0-9]{0,3}', root.name), 'OWN_PLATFORM_RUNTIME_LAYOUT_REQUIRED')
    for relative, pin in value['files'].items():
        sub = relative.split('/run-template/', 1)[1]
        path = _regular(root / sub)
        need(path.stat().st_size == pin['bytes'] and sha(path) == pin['sha256'], 'DECLARED_ASYNC_RUNTIME_CODE_CHANGED')
    need(sha(_regular(root / 'own-platform-observation.jar')) == ADAPTER_SHA256, 'ORIGINAL_AUTH_ADAPTER_REQUIRED')
    need(isinstance(prepared, dict) and prepared.get('side') == 'platform'
         and Path(prepared.get('runtime', '')).absolute() == root, 'EXACT_PREPARED_PLATFORM_RUNTIME_REQUIRED')
    items = _initializers(prepared.get('configuration', {}).get('context.initializer.classes', ''))
    need(items.count(INITIALIZER) == 1, 'DECLARED_ASYNC_INITIALIZER_REQUIRED')
    arguments = prepared.get('arguments')
    need(isinstance(arguments, list) and all(isinstance(x, str) for x in arguments)
         and arguments.count(OLD_MAIN) == 1 and NEW_MAIN not in arguments, 'EXACT_ORIGINAL_PLATFORM_MAIN_REQUIRED')
    need(not any(x.startswith('-Down.async.') for x in arguments), 'ASYNC_ARGUMENT_OVERRIDE_REFUSED')
    index = arguments.index(OLD_MAIN)
    need(index >= 2 and index + 3 == len(arguments) and '-cp' in arguments[:index], 'EXACT_ORIGINAL_LAUNCHER_ARGUMENT_SHAPE_REQUIRED')
    need(Path(arguments[-1]).absolute() == root, 'EXACT_PLATFORM_MAIN_RUNTIME_REQUIRED')
    native = _regular(Path(arguments[-2]))
    need(sha(native) == NATIVE_SHA256, 'ORIGINAL_NATIVE_PLATFORM_JAR_REQUIRED')
    need(Path(_property(arguments[:index], 'own.platform.root')).absolute() == root
         and Path(_property(arguments[:index], 'own.platform.source.path')).absolute() == native,
         'ORIGINAL_PLATFORM_PATH_ARGUMENTS_REQUIRED')
    rewritten = list(arguments)
    rewritten[index] = NEW_MAIN
    support = next(pin for name, pin in value['files'].items() if name.endswith('/own-platform-async-request.jar'))
    flags = ['-Down.async.request.snapshot.enabled=true',
             '-Down.async.original.config.sha256=' + value['originalAsyncConfigSHA256'],
             '-Down.async.support.sha256=' + support['sha256']]
    result = dict(prepared)
    result['arguments'] = flags + rewritten
    return result
