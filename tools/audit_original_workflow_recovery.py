"""Find exact recovery evidence in a sealed export without SQL or raw-row output."""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
import pathlib
import re
import time
import xml.etree.ElementTree as ET

TABLE_COLUMNS = {
    'act_ge_bytearray': ['ID_', 'NAME_', 'DEPLOYMENT_ID_', 'BYTES_'],
    'act_re_procdef': ['ID_', 'KEY_', 'VERSION_', 'DEPLOYMENT_ID_', 'RESOURCE_NAME_'],
    'act_re_deployment': ['ID_'],
    'act_re_model': ['ID_', 'KEY_', 'DEPLOYMENT_ID_', 'EDITOR_SOURCE_VALUE_ID_'],
    'flow_run_add_node': ['F_PROCESSDEFINITIONID', 'F_INSTANCE_ID'],
    'flow_template_json': ['f_id', 'f_template_id', 'F_PROCESSDEFINITIONID', 'F_DEPLOYMENTID', 'f_flow_template_json'],
    'flow_template': ['f_id'],
    'flow_definition': ['F_PROCESSDEFINITIONID'],
    'flow_task': ['f_process_id', 'f_flow_id', 'f_template_id', 'f_flow_template_json'],
}
BPMN_PROCESS = '{http://www.omg.org/spec/BPMN/20100524/MODEL}process'

def require(test, code):
    if not test:
        raise ValueError(code)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def bpmn_keys(raw):
    """No DTD/entity processing or external resolution; return an explicit parse state."""
    if len(raw) > 2 * 1024**2:
        return set(), 'size_limit'
    ascii_markup = raw.replace(b'\x00', b'').upper()
    if b'<!DOCTYPE' in ascii_markup or b'<!ENTITY' in ascii_markup:
        return set(), 'dtd_or_entity_rejected'
    try:
        root = ET.fromstring(raw)
    except (ET.ParseError, ValueError):
        return set(), 'not_valid_xml'
    return {node.attrib['id'] for node in root.iter(BPMN_PROCESS) if node.attrib.get('id')}, 'parsed_xml'

def build_report(rows):
    definitions = {row[0] for row in rows['act_re_procdef']}
    refs = rows['flow_run_add_node']
    missing = sorted({row[0] for row in refs if row[0] not in definitions})
    require(all(isinstance(value, str) and len(value) < 512 for value in missing), 'MISSING_DEFINITION_ID_SHAPE')
    resource_info = []
    parse_states = collections.Counter()
    for ident, name, deployment, raw in rows['act_ge_bytearray']:
        if raw is None:
            raw = b''
        require(isinstance(raw, bytes), 'RESOURCE_BYTES_REQUIRED')
        keys, state = bpmn_keys(raw)
        parse_states[state] += 1
        resource_info.append((ident, name, deployment, raw, keys, state))
    groups = []
    for definition in missing:
        parts = definition.rsplit(':', 2)
        require(len(parts) == 3 and parts[1].isdigit() and parts[0], 'DEFINITION_ID_SHAPE')
        key = parts[0]
        suffix = key[len('activiti_'):] if key.startswith('activiti_') else None
        exact_resources = [row for row in resource_info if key in row[4]]
        raw_candidates = [row for row in resource_info if key.encode('utf-8') in row[3]]
        templates = rows['flow_template_json']
        candidates = {row[0]: row for row in [*raw_candidates, *exact_resources]}
        groups.append({
            'definitionSHA256': digest(definition.encode()),
            'temporaryRows': sum(row[0] == definition for row in refs),
            'exactBpmnProcessKeyResources': len(exact_resources),
            'rawKeySubstringResourceCandidates': len(raw_candidates),
            'resourceCandidates': [{'resourceIdSHA256': digest(row[0].encode()),
                                    'deploymentIdSHA256': digest(row[2].encode()) if row[2] else None,
                                    'bytesSHA256': digest(row[3]), 'bytes': len(row[3]),
                                    'exactBpmnProcessKey': key in row[4]} for row in candidates.values()],
            'flowTemplateJsonExactDefinitionRows': sum(row[2] == definition for row in templates),
            'flowTemplateJsonSuffixIdRows': sum(suffix is not None and row[0] == suffix for row in templates),
            'flowTemplateSuffixIdRows': sum(suffix is not None and row[0] == suffix for row in rows['flow_template']),
            'flowDefinitionExactReferenceRows': sum(row[0] == definition for row in rows['flow_definition']),
            'actReModelExactKeyRows': sum(row[1] == key for row in rows['act_re_model']),
            'modelJsonKeySubstringRows': sum(key in (row[4] or '') for row in templates),
            'taskFieldExactDefinitionRows': sum(definition in row[:3] for row in rows['flow_task']),
            'taskJsonKeySubstringRows': sum(key in (row[3] or '') for row in rows['flow_task']),
            # A process key or editor model cannot establish the missing exact definition/version.
            'exactDefinitionRecoveryProven': False,
        })
    return {'selectedTableRowCounts': {name: len(values) for name, values in rows.items()},
            'missingDefinitionGroups': groups, 'resourceParseStates': dict(parse_states),
            'bpmnProcessKeyCount': len(set().union(*(row[4] for row in resource_info))),
            'resourceSearchIncludesAllBytearrayRows': True,
            'rawPrivateIdsOrModelPayloadsIncludedInReport': False,
            'exactDefinitionRecoveryProven': False}

def audit(source, manifest_pin, seconds=180):
    source = pathlib.Path(source)
    require(re.fullmatch('[0-9a-f]{64}', manifest_pin) is not None, 'MANIFEST_PIN_SHAPE')
    require(source.is_dir(), 'EXPORT_ROOT_REQUIRED')
    paths = {name: source / name for name in ('manifest.json', 'catalog.json', 'jnpf.rows.jsonl.gz')}
    for path in paths.values():
        stat = path.lstat()
        require(path.is_file() and not path.is_symlink() and not getattr(stat, 'st_file_attributes', 0) & 0x400, 'REGULAR_INPUT_REQUIRED')
    before = {name: (p.stat().st_size, p.stat().st_mtime_ns) for name, p in paths.items()}
    manifest_raw = paths['manifest.json'].read_bytes()
    require(len(manifest_raw) <= 1024**2 and digest(manifest_raw) == manifest_pin, 'MANIFEST_PIN_MISMATCH')
    manifest = json.loads(manifest_raw)
    require(len(manifest['files']) == 3, 'EXPORT_PAYLOAD_SCOPE')
    payloads = {row['name']: row for row in manifest['files']}
    require(set(payloads) == {'catalog.json', 'jnpf.rows.jsonl.gz', 'tj_endanger.rows.jsonl.gz'}, 'EXPORT_PAYLOAD_SCOPE')
    for name in ('catalog.json', 'jnpf.rows.jsonl.gz'):
        p = paths[name]
        require(p.stat().st_size == payloads[name]['bytes'] and p.stat().st_size <= 32 * 1024**2, 'PAYLOAD_SIZE_MISMATCH')
        with p.open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == payloads[name]['sha256'], 'PAYLOAD_SHA_MISMATCH')
    catalog = json.loads(paths['catalog.json'].read_bytes())
    indices = {}
    widths = {}
    for table in catalog['tablesAndViews']:
        name = table['TABLE_NAME']
        if table['TABLE_SCHEMA'] == 'jnpf' and name in TABLE_COLUMNS:
            columns = [c['COLUMN_NAME'] for c in table['columns'] if not c.get('GENERATION_EXPRESSION')]
            indices[name] = [columns.index(c) for c in TABLE_COLUMNS[name]]
            widths[name] = len(columns)
    require(set(indices) == set(TABLE_COLUMNS), 'EXPECTED_TABLES_MISSING')
    rows = {name: [] for name in TABLE_COLUMNS}
    prefixes = tuple(('[' + json.dumps(name) + ',').encode('ascii') for name in TABLE_COLUMNS)
    start = time.monotonic()
    stream_hash = hashlib.sha256()
    size = 0
    with gzip.open(paths['jnpf.rows.jsonl.gz'], 'rb') as stream:
        for line in iter(lambda: stream.readline(9 * 1024**2 + 1), b''):
            require(len(line) <= 9 * 1024**2 and time.monotonic() - start < seconds, 'STREAM_LIMIT')
            size += len(line)
            require(size <= 512 * 1024**2, 'UNCOMPRESSED_LIMIT')
            stream_hash.update(line)
            if not line.startswith(prefixes):
                continue
            name, values = json.loads(line)
            require(len(values) == widths[name], 'ROW_WIDTH_MISMATCH')
            selected = []
            for column, index in zip(TABLE_COLUMNS[name], indices[name]):
                value = values[index]
                raw = bytes.fromhex(value) if value is not None else None
                selected.append(raw if name == 'act_ge_bytearray' and column == 'BYTES_' else raw.decode('utf-8') if raw is not None else None)
            rows[name].append(tuple(selected))
    expected_counts = {(row['schema'], row['table']): row['rows'] for row in manifest['tableCounts']}
    require(all(expected_counts.get(('jnpf', name)) == len(values) for name, values in rows.items()), 'SELECTED_TABLE_ROW_COUNT_MISMATCH')
    result = build_report(rows)
    for name, p in paths.items():
        require((p.stat().st_size, p.stat().st_mtime_ns) == before[name], 'INPUT_CHANGED')
        if name == 'manifest.json':
            require(digest(p.read_bytes()) == manifest_pin, 'INPUT_CHANGED')
        else:
            with p.open('rb') as stream:
                require(hashlib.file_digest(stream, 'sha256').hexdigest() == payloads[name]['sha256'], 'INPUT_CHANGED')
    result.update(recordedAt=datetime.datetime.now().astimezone().isoformat(),
                  sourceManifestSHA256=manifest_pin, jnpfStreamSHA256=stream_hash.hexdigest(),
                  jnpfUncompressedBytes=size, sourceDatabaseConnected=False, sourceExportRepeated=False,
                  originalRowsCopiedToD=False, databaseWritten=False, applicationLaunched=False,
                  fullCloneReady=False, seconds=round(time.monotonic() - start, 2))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=pathlib.Path, required=True)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'FRESH_OUTPUT_REQUIRED')
    result = audit(args.export, args.manifest_sha256)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result), flush=True)

if __name__ == '__main__':
    main()
