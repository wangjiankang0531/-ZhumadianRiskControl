"""Prepare the isolated synthetic RHI page probe from exact source pins; never build or run it."""
from pathlib import Path
import argparse
import json
import re
import sys
import os
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_native_manual_preview_source import checked_file, digest, git_blobs, relative_path

SCHEMA = 'xnby.native.page-rhi-probe.source.v1'
PROBE_FILES = {'CMakeLists.txt', 'native_page_rhi_probe.cpp', 'page.vert', 'page.frag',
               'production/native_retained_page_draw.hpp',
               'production/native_retained_page_identity.inl',
               'production/native_retained_page_lifecycle.inl'}

def write_probe(output, values, receipt):
    if output.exists() or not output.parent.is_dir():
        raise ValueError('Fresh output and existing parent required')
    for name in values:
        if name not in PROBE_FILES:
            relative_path(name)
    with tempfile.TemporaryDirectory(prefix=output.name + '.prepare-', dir=output.parent) as temporary:
        payload = Path(temporary) / 'payload'
        payload.mkdir()
        for name, data in values.items():
            target = payload / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (payload / 'source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        if output.exists():
            raise ValueError('Output appeared during preparation')
        os.rename(payload, output)

def prepare(application, engine, output):
    application, engine, output = application.resolve(), engine.resolve(), output.resolve()
    own_application = Path(__file__).resolve().parent.parent
    for root in (application, engine, own_application):
        if output == root or output.is_relative_to(root):
            raise ValueError('Output must be outside both repositories')
    if output.exists():
        raise ValueError('Fresh output required; no files changed')
    directory = own_application / 'tools/rhi_page_lifecycle_probe'
    raw = (directory / 'source_manifest.json').read_bytes()
    recipe = json.loads(raw)
    if recipe.get('schema') != SCHEMA or set(recipe['probeFiles']) != PROBE_FILES:
        raise ValueError('Invalid probe recipe')
    rows = recipe['engineFiles']
    if not 1 <= len(rows) <= 128 or any(not r['path'].startswith('XNBYEngine/') for r in rows):
        raise ValueError('Invalid engine source list')
    names = [r['path'].casefold() for r in rows]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate engine source path')
    values = git_blobs(engine, recipe['engineCommit'], rows)
    for name, pin in recipe['probeFiles'].items():
        if not re.fullmatch(r'[0-9a-f]{64}', pin):
            raise ValueError('Invalid probe source SHA')
        values[name] = checked_file(directory, name, pin)
    receipt = {'schema': SCHEMA, 'engineCommit': recipe['engineCommit'],
               'recipeSHA256': digest(raw), 'sourceFiles': len(values),
               'sourceSHA256': {name: digest(data) for name, data in sorted(values.items())},
               'engineWorktreeUsed': False, 'syntheticInputsOnly': True,
               'GISOrRuntimeCopied': False, 'builtOrStarted': False}
    write_probe(output, values, receipt)
    return receipt

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--application-repository', type=Path, required=True)
    p.add_argument('--engine-repository', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    r = prepare(a.application_repository, a.engine_repository, a.output)
    print(json.dumps({'prepared': True, 'sourceFiles': r['sourceFiles'], 'builtOrStarted': False}))

if __name__ == '__main__':
    main()
