"""Prepare the pinned async-controller RHI probe source; never build or start anything."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_native_manual_preview_source import checked_file, git_blobs
from native_parent_restore_failure_patch import patched_restore


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--application-repository', type=Path, required=True)
    p.add_argument('--engine-repository', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--baseline-controller', action='store_true')
    a = p.parse_args()
    tools = Path(__file__).resolve().parent
    output = a.output.resolve()
    for root in (a.application_repository.resolve(), a.engine_repository.resolve(), tools.parent):
        if output == root or output.is_relative_to(root):
            raise ValueError('Output must be outside both repositories')
    if output.exists():
        raise ValueError('Fresh output required')
    directory = tools / 'async_page_restore_probe'
    raw = (directory / 'source_manifest.json').read_bytes()
    recipe = json.loads(raw)
    if recipe.get('schema') != 'xnby.native.async-controller-probe.source.v1':
        raise ValueError('Wrong async probe recipe')
    expected = recipe['baselineSourceSHA256'] if a.baseline_controller else recipe['fixedSourceSHA256']
    if len(expected) != 53:
        raise ValueError('Wrong expected source count')
    subprocess.run([sys.executable, '-I', '-B', str(tools / 'prepare_native_page_rhi_probe.py'),
                    '--application-repository', str(a.application_repository),
                    '--engine-repository', str(a.engine_repository), '--output', str(output)], check=True)
    base = json.loads((output / 'source-receipt.json').read_text())
    for name, pin in base['sourceSHA256'].items():
        if sha((output / name).read_bytes()) != pin:
            raise ValueError('Base probe source changed')
    row = recipe['geometrySource']
    data = git_blobs(a.engine_repository, recipe['engineCommit'], [row])[row['path']]
    (output / row['path']).write_bytes(data)
    for name, target in [('async_page_restore_probe.cpp', 'async_page_restore_probe.cpp'),
                         ('production/native_family_restore_controls.inl', 'production/native_family_restore_controls.inl')]:
        (output / target).write_bytes(checked_file(directory, name, recipe['inputSHA256'][name]))
    name = 'production/native_retained_parent_restore.original.inl'
    original = checked_file(directory, name, recipe['inputSHA256'][name])
    (output / 'production/native_retained_parent_restore.inl').write_bytes(original if a.baseline_controller else patched_restore(original))
    cmake = output / 'CMakeLists.txt'
    cmake.write_bytes(cmake.read_bytes() + recipe['cmakeSuffix'].encode('ascii'))
    actual = {name: sha((output / name).read_bytes()) for name in expected}
    if actual != expected:
        raise ValueError('Prepared controller source differs from accepted compile input')
    receipt = {'sourceFiles': 53, 'sourceSHA256': actual, 'baselineController': a.baseline_controller,
               'recipeSHA256': sha(raw), 'builtOrStarted': False, 'GISOrRuntimeCopied': False}
    (output / 'async-controller-source-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'prepared': True, 'sourceFiles': 53, 'baselineController': a.baseline_controller, 'builtOrStarted': False}))


if __name__ == '__main__':
    main()
