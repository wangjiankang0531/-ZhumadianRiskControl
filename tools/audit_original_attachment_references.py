"""Inventory attachment references in an explicitly pinned sealed export, without SQL or raw values.

This is evidence for object restoration planning, not a file-service substitute.
Personal photos, signatures, users and authentication tables are outside the scope.
"""
import argparse
from collections import Counter
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import unquote, urlsplit

FIELDS = {
    'jnpf': {
        'base_notice': ('f_files',), 'base_schedule': ('f_files',),
        'ext_document': ('f_file_path',), 'ext_order': ('f_file_json',),
        'flow_comment': ('f_image', 'f_file'),
        'flow_task_operator_record': ('f_file_list',),
    },
    'tj_endanger': {
        'base_file': ('file_url',), 'event_disposal_record': ('attachments',),
        'event_info': ('file_url',), 'inspection_issue': ('attachment', 'result_attachment'),
        'safety_administrative_permit_documents': ('file_address',),
        'safety_manage_file': ('file_address',),
        'work_supervise': ('file_url',),
    },
}
REFERENCE_KEYS = {'url', 'fileurl', 'filepath', 'fileaddress', 'path', 'previewurl', 'downloadurl'}
# These separators come from the supplied original forms, not filename guesses.
DELIMITERS = {
    ('tj_endanger', 'event_disposal_record', 'attachments'): ',',
    ('tj_endanger', 'event_info', 'file_url'): ',',
    ('tj_endanger', 'inspection_issue', 'attachment'): ';',
    ('tj_endanger', 'inspection_issue', 'result_attachment'): ';',
    ('tj_endanger', 'work_supervise', 'file_url'): ',',
}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference_kind(value):
    """Classify without resolving a URL, exposing an origin, or reading an object."""
    if any(ord(c) < 32 for c in value) or len(value) > 8192:
        return 'unsupported-reference'
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        return 'unsupported-reference'
    if parsed.scheme and parsed.scheme not in ('http', 'https'):
        return 'unsupported-scheme'
    path = unquote(parsed.path)
    if '\\' in path or any(p in ('.', '..') for p in path.split('/')):
        return 'unsafe-relative-path'
    if parsed.username is not None or parsed.password is not None:
        return 'url-with-userinfo'
    if re.search(r'(?:^|/)sys-file/[^/]+/[^/]+$', path):
        return 'business-sys-file-object'
    if re.search(r'(?:^|/)sys-file/local/file/[^/]+$', path):
        return 'business-classpath-template'
    if re.search(r'(?:^|/)api/file/', path, re.I):
        return 'platform-file-api'
    if parsed.netloc:
        return 'http-object-url' if parsed.scheme else 'network-path-reference'
    if path.startswith('/'):
        return 'absolute-path-reference'
    if '/' in path:
        return 'relative-path-reference'
    return 'opaque-file-token'


def field_inventory(value, delimiter=None):
    require(delimiter in (None, ',', ';'), 'EXPLICIT_SUPPORTED_DELIMITER_REQUIRED')
    result = {'nonEmpty': False, 'format': 'empty', 'references': [], 'unrecognizedStructured': False}
    if value is None or not value.strip() or value.strip() in ('null', '[]', '{}', '""'):
        return result
    require(len(value.encode('utf-8')) <= 1024 * 1024, 'ATTACHMENT_FIELD_LIMIT')
    result['nonEmpty'] = True
    text = value.strip()
    structured = text[:1] in ('[', '{', '"')
    try:
        content = json.loads(text) if structured else text
    except (ValueError, RecursionError):
        result['format'] = 'malformed-json'
        result['unrecognizedStructured'] = True
        return result
    result['format'] = 'json' if structured else 'plain'
    leaves = []
    budget = [0]

    def walk(node, depth=0, hint=False):
        budget[0] += 1
        require(depth <= 16 and budget[0] <= 10000, 'ATTACHMENT_STRUCTURE_LIMIT')
        if isinstance(node, str):
            if node.strip() and (hint or node.startswith(('/', 'http://', 'https://'))):
                leaves.append(node)
        elif isinstance(node, list):
            for child in node:
                walk(child, depth + 1, hint)
        elif isinstance(node, dict):
            for key, child in node.items():
                normalized = re.sub('[^a-z]', '', key.lower())
                walk(child, depth + 1, normalized in REFERENCE_KEYS)

    if not structured and delimiter is not None:
        result['format'] = 'delimited-plain'
        for part in content.split(delimiter):
            walk(part.strip(), hint=True)
    else:
        walk(content, hint=isinstance(content, str))
    result['unrecognizedStructured'] = structured and not leaves
    for value in leaves:
        kind = reference_kind(value)
        entry = {'sha256': sha(value.encode('utf-8')), 'kind': kind}
        if kind == 'business-sys-file-object':
            match = re.search(r'(?:^|/)sys-file/([^/]+)/([^/]+)$', unquote(urlsplit(value).path))
            entry['bucketSHA256'] = sha(match[1].encode('utf-8'))
            entry['objectKeySHA256'] = sha(match[2].encode('utf-8'))
        result['references'].append(entry)
    return result


def decode_row(raw, columns, wanted):
    table, values = json.loads(raw)
    require(len(values) == len(columns), 'ROW_WIDTH')
    result = {}
    for field in wanted:
        value = values[columns.index(field)]
        require(value is None or isinstance(value, str) and re.fullmatch(r'(?:[0-9A-Fa-f]{2})*', value) is not None, 'UTF8_HEX_REQUIRED')
        result[field] = bytes.fromhex(value).decode('utf-8', errors='strict') if value is not None else None
    return table, result


def audit(source, manifest_pin, output, object_snapshot_root=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    require(re.fullmatch('[0-9a-f]{64}', manifest_pin), 'EXPLICIT_MANIFEST_PIN_REQUIRED')
    require(not output.exists() and not output.is_relative_to(source) and not source.is_relative_to(output), 'FRESH_SEPARATE_OUTPUT_REQUIRED')
    snapshot = Path(object_snapshot_root).resolve() if object_snapshot_root is not None else None
    if snapshot is not None:
        require(snapshot.is_dir() and not snapshot.is_symlink() and not output.is_relative_to(snapshot) and not snapshot.is_relative_to(output), 'SEPARATE_OBJECT_SNAPSHOT_REQUIRED')
    manifest_path = source / 'manifest.json'
    manifest_raw = manifest_path.read_bytes()
    require(len(manifest_raw) <= 1024 ** 2 and sha(manifest_raw) == manifest_pin, 'MANIFEST_PIN_MISMATCH')
    manifest = json.loads(manifest_raw)
    payload = {r['name']: r for r in manifest['files']}
    require(set(payload) == {'catalog.json', 'jnpf.rows.jsonl.gz', 'tj_endanger.rows.jsonl.gz'}, 'PAYLOAD_SCOPE')
    names = ('manifest.json', *payload)
    before = {}
    for name in names:
        p = source / name
        require(p.is_file() and not p.is_symlink() and not getattr(p.lstat(), 'st_file_attributes', 0) & 0x400, 'REGULAR_INPUT_REQUIRED')
        before[name] = (p.stat().st_size, p.stat().st_mtime_ns)

    def verify_payload():
        require(sha(manifest_path.read_bytes()) == manifest_pin, 'MANIFEST_CHANGED')
        for name, entry in payload.items():
            p = source / name
            require(p.stat().st_size == entry['bytes'] and p.stat().st_size <= 128 * 1024 ** 2, 'PAYLOAD_SIZE_LIMIT')
            with p.open('rb') as f:
                require(hashlib.file_digest(f, 'sha256').hexdigest() == entry['sha256'], 'PAYLOAD_SHA_MISMATCH')
    verify_payload()
    catalog = json.loads((source / 'catalog.json').read_bytes())
    columns = {(t['TABLE_SCHEMA'], t['TABLE_NAME']): [c['COLUMN_NAME'] for c in t['columns'] if not c.get('GENERATION_EXPRESSION')]
               for t in catalog['tablesAndViews'] if t['TABLE_SCHEMA'] in FIELDS and t['TABLE_NAME'] in FIELDS[t['TABLE_SCHEMA']]}
    expected = {(s, t): fs for s, ts in FIELDS.items() for t, fs in ts.items()}
    require(set(columns) == set(expected) and all(set(fs) <= set(columns[k]) for k, fs in expected.items()), 'ATTACHMENT_COLUMNS_REQUIRED')
    counts = {(r['schema'], r['table']): r['rows'] for r in manifest['tableCounts']}
    reports = []
    stream_proofs = []
    unique = {}
    for schema, tables in FIELDS.items():
        table_counts = Counter()
        fields = {(table, field): {'rows': 0, 'nonEmptyRows': 0, 'formats': Counter(), 'referenceKinds': Counter(), 'unrecognizedStructuredRows': 0}
                  for table, fs in tables.items() for field in fs}
        prefixes = tuple(('[' + json.dumps(t) + ',').encode() for t in tables)
        stream_hash = hashlib.sha256(); size = 0; start = time.monotonic()
        with gzip.open(source / (schema + '.rows.jsonl.gz'), 'rb') as f:
            for raw in iter(lambda: f.readline(9 * 1024 ** 2 + 1), b''):
                require(len(raw) <= 9 * 1024 ** 2 and time.monotonic() - start < 180, 'STREAM_LIMIT')
                size += len(raw); require(size <= 768 * 1024 ** 2, 'UNCOMPRESSED_LIMIT'); stream_hash.update(raw)
                if not raw.startswith(prefixes):
                    continue
                table = json.loads(raw)[0]
                table, row = decode_row(raw, columns[schema, table], tables[table])
                table_counts[table] += 1
                for field, value in row.items():
                    item = fields[table, field]; inv = field_inventory(value, DELIMITERS.get((schema, table, field)))
                    item['rows'] += 1; item['nonEmptyRows'] += int(inv['nonEmpty']); item['formats'][inv['format']] += 1
                    item['unrecognizedStructuredRows'] += int(inv['unrecognizedStructured'])
                    for ref in inv['references']:
                        item['referenceKinds'][ref['kind']] += 1
                        unique[ref['sha256']] = ref
        require(all(table_counts[t] == counts[schema, t] for t in tables), 'SELECTED_TABLE_ROW_COUNTS')
        for (table, field), row in fields.items():
            reports.append({'schema': schema, 'table': table, 'field': field, **row})
        stream_proofs.append({'schema': schema, 'uncompressedBytes': size, 'streamSHA256': stream_hash.hexdigest(), 'selectedTableCounts': dict(table_counts)})
    verify_payload()
    for name in names:
        p = source / name
        require((p.stat().st_size, p.stat().st_mtime_ns) == before[name], 'INPUT_CHANGED')
    bucket_hashes = {r['bucketSHA256'] for r in unique.values() if 'bucketSHA256' in r}
    snapshot_observation = None
    if snapshot is not None:
        # Top level only. Do not enter MinIO internal metadata or open any objects.
        entries = list(snapshot.iterdir())
        require(len(entries) <= 10000, 'SNAPSHOT_TOP_LEVEL_LIMIT')
        directories = {sha(p.name.encode('utf-8')) for p in entries if not p.name.startswith('.') and p.is_dir() and not p.is_symlink()}
        snapshot_observation = {'topLevelBusinessDirectories': len(directories), 'referencedBucketFingerprints': len(bucket_hashes),
                                'referencedBucketDirectoryMatches': len(bucket_hashes & directories),
                                'internalMetadataOpened': False, 'objectContentsOpened': False,
                                'snapshotNotProofOfLiveStoreContents': True}
    result = {'recordedAt': datetime.datetime.now().astimezone().isoformat(), 'sourceManifestSHA256': manifest_pin,
              'streams': stream_proofs, 'fields': reports, 'uniqueReferenceCount': len(unique),
              'uniqueReferenceKinds': dict(Counter(r['kind'] for r in unique.values())),
              'referenceFingerprints': [v for k, v in sorted(unique.items())],
              'objectSnapshotObservation': snapshot_observation,
              'referenceScopeComplete': False, 'rawReferenceValuesWritten': False,
              'personalPhotoOrSignatureFieldsDecoded': False, 'originalObjectsRead': False,
              'sourceDatabaseConnected': False, 'sourceWritten': False,
              'objectsRecovered': False, 'fileServiceRuntimeVerified': False, 'fullCloneReady': False}
    output.mkdir(parents=True)
    (output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('export', 'manifest-sha256', 'output'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--object-snapshot-root')
    a = p.parse_args()
    result = audit(a.export, a.manifest_sha256, a.output, a.object_snapshot_root)
    print(json.dumps({k: v for k, v in result.items() if k not in ('referenceFingerprints', 'fields')}))


if __name__ == '__main__':
    main()
