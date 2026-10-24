"""Prepare Redis overlays for one isolated JNPF + IEMP run; never start a service.

The original two Spring Boot versions use different property namespaces. Only
the four Redis connection properties are emitted. No token, permissions, source
database, workflow, or original application files are modified.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import uuid

NAMESPACES = {'business': 'spring.data.redis', 'platform': 'spring.redis'}
FIELDS = ('host', 'port', 'database', 'password')


def own_properties(path: Path) -> dict[str, str]:
    """Read the flat, explicit key=value format from our isolation builders.

    Deliberately does not interpret general Java property files or environment
    expansion. Unexpected syntax fails instead of guessing at effective values.
    """
    raw = path.read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError('Isolation configuration exceeds size limit')
    text = raw.decode('ascii')
    result = {}
    for line in text.splitlines():
        if not line or line.startswith(('#', '!')):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Za-z0-9_-]+(?:\[[0-9]+\])?(?:\.[A-Za-z0-9_-]+(?:\[[0-9]+\])?)*', key):
            raise ValueError('Only explicit isolation-builder properties are supported')
        if key in result:
            raise ValueError('Duplicate isolation property')
        if line.endswith('\\'):
            raise ValueError('Continued properties are not supported')
        result[key] = value
    if result.get('server.address') != '127.0.0.1' or result.get('server.port') != '0':
        raise ValueError('A loopback-only ephemeral application configuration is required')
    return result


def endpoint(values: dict[str, str], namespace: str) -> tuple[str, int, int, str]:
    keys = [namespace + '.' + field for field in FIELDS]
    if any(key not in values for key in keys):
        raise ValueError('Explicit Redis host, port, database and password required')
    host, port, database, password = (values[key] for key in keys)
    if host != '127.0.0.1' or not re.fullmatch(r'[0-9]{4,5}', port) or not 1024 <= int(port) <= 65535:
        raise ValueError('Only an explicit loopback Redis endpoint is supported')
    if not re.fullmatch(r'[0-9]+', database) or not 0 <= int(database) <= 15:
        raise ValueError('Explicit Redis database 0..15 required')
    if not password or any(c in password for c in '\\${'):
        raise ValueError('Isolation-builder Redis password must be explicit')
    if any(values.get(namespace + '.' + alias) for alias in ('url', 'cluster.nodes', 'sentinel.master')):
        raise ValueError('Redis URL, cluster and sentinel settings must not override the owned endpoint')
    return host, int(port), int(database), password


def connection_file(path: Path) -> dict:
    if path.stat().st_size > 4096:
        raise ValueError('Owned Redis connection metadata exceeds size limit')
    def unique_fields(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate owned connection field')
            result[key] = value
        return result
    item = json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_fields)
    if not isinstance(item, dict):
        raise ValueError('Owned Redis connection object required')
    if set(item) != {'schema', 'ownerId', 'host', 'port', 'database', 'password'}:
        raise ValueError('Exact owned Redis connection schema required')
    if item['schema'] != 'zhumadian.original.joint-redis.v1':
        raise ValueError('Unknown owned Redis connection schema')
    try:
        owner = uuid.UUID(item['ownerId'])
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Explicit UUID owner required') from None
    if owner.version != 4 or str(owner) != item['ownerId']:
        raise ValueError('Canonical UUID4 owner required')
    if item['host'] != '127.0.0.1' or type(item['port']) is not int or not 1024 <= item['port'] <= 65535:
        raise ValueError('Nonprivileged owned loopback port required')
    if type(item['database']) is not int or not 0 <= item['database'] <= 15:
        raise ValueError('Owned Redis database 0..15 required')
    if not isinstance(item['password'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}', item['password']):
        raise ValueError('Fresh generated URL-safe Redis password required')
    return item


def prepare(output: Path, business: Path, platform: Path, connection: Path) -> dict:
    paths = {name: path.resolve(strict=True) for name, path in
             [('business', business), ('platform', platform), ('connection', connection)]}
    if len(set(paths.values())) != 3:
        raise ValueError('Distinct explicit input files required')
    if any(not path.is_file() or path.stat().st_size > (4096 if name == 'connection' else 1024 * 1024)
           for name, path in paths.items()):
        raise ValueError('Bounded explicit configuration files required')
    output = output.resolve()
    if output.exists():
        raise ValueError('Fresh output directory required')
    if any(path.is_relative_to(output) for path in paths.values()):
        raise ValueError('Output must not contain any input')
    originals = {name: path.read_bytes() for name, path in paths.items()}
    sources = {name: own_properties(paths[name]) for name in NAMESPACES}
    before = {name: endpoint(sources[name], prefix) for name, prefix in NAMESPACES.items()}
    # Reject an unexpected second namespace instead of letting Spring select it.
    for name, prefix in NAMESPACES.items():
        alternate = NAMESPACES['platform' if name == 'business' else 'business']
        if any(key.startswith(alternate + '.') for key in sources[name]):
            raise ValueError('Ambiguous alternate Redis namespace in isolation configuration')
    own = connection_file(paths['connection'])
    prepared = {}
    for name, prefix in NAMESPACES.items():
        text = '# Isolated owned Redis overlay; keep this file private.\n'
        text += ''.join(prefix + '.' + field + '=' + str(own[field]) + '\n' for field in FIELDS)
        prepared[name + '-redis.properties'] = text.encode('ascii')
    if any(path.read_bytes() != originals[name] for name, path in paths.items()):
        raise ValueError('Input changed during preparation')
    output.mkdir(parents=True)
    for name, raw in prepared.items():
        (output / name).write_bytes(raw)
    result = {
        'schema': 'zhumadian.original.joint-redis.preparation.v1',
        'recordedAt': datetime.now(timezone.utc).isoformat(),
        'ownerId': own['ownerId'], 'existingConfigurationsShareRedis': before['business'] == before['platform'],
        'configurationAligned': True, 'runtimeStarted': False, 'runtimeReady': False,
        'originalAuthenticationChanged': False, 'originalPermissionsChanged': False,
        'inputsUnchanged': all(path.read_bytes() == originals[name] for name, path in paths.items()),
        'applicationConfigSHA256': {name: hashlib.sha256(originals[name]).hexdigest() for name in NAMESPACES},
        'overlayFiles': list(prepared),
        'requiredOriginalSequence': ['Login', 'CurrentUser', 'authenticated-business-request'],
        'currentUserSharedCachePrefix': 'cqweh:opm:userInfo:',
        'originalSerializationCompatibilityVerified': False,
        'authenticatedBusinessVerified': False, 'fullCloneReady': False,
        'launchRequirement': 'One owned Redis process must use the private connection metadata. '
                             'Append the matching overlay last in each app configuration location list; '
                             'independently verify effective properties, readiness, and authenticated requests.'}
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not result['inputsUnchanged']:
        raise ValueError('Input changed while writing the overlays')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'business', 'platform', 'connection'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.output, args.business, args.platform, args.connection)
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError):
        # Do not echo private property lines, JSON values or exceptions containing them.
        raise SystemExit('Owned shared Redis preparation failed; inspect the explicit input format.') from None
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
