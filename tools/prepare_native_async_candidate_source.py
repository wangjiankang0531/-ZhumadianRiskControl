"""Prepare a pinned full PNG2 editor plus async restoration repair; source only."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--application-repository', type=Path, required=True)
    p.add_argument('--engine-repository', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    tools = Path(__file__).resolve().parent
    output = a.output.resolve()
    for root in (a.application_repository.resolve(), a.engine_repository.resolve(), tools.parent):
        if output == root or output.is_relative_to(root):
            raise ValueError('Output must be outside both repositories')
    if output.exists():
        raise ValueError('Fresh output required')
    directory = tools / 'experimental_source'
    recipe = json.loads((directory / 'native_async_restore_candidate.json').read_bytes())
    patch = directory / 'native_async_restore_candidate.patch'
    if recipe.get('schema') != 'xnby.native.async-restore.full-source.v1' or sha(patch.read_bytes()) != recipe['patchSHA256']:
        raise ValueError('Wrong full source recipe or patch identity')
    subprocess.run([sys.executable, '-I', '-B', str(tools / 'prepare_native_png_preview_source.py'),
                    '--application-repository', str(a.application_repository),
                    '--engine-repository', str(a.engine_repository), '--output', str(output)], check=True)
    receipt = json.loads((output / 'png-dialog-source-receipt.json').read_text())
    if receipt['sourceSHA256'] != recipe['baseSourceSHA256'] or len(receipt['sourceSHA256']) != 392:
        raise ValueError('Wrong fixed PNG2 source base')
    for name, pin in recipe['baseSourceSHA256'].items():
        if sha((output / name).read_bytes()) != pin:
            raise ValueError('Fixed source base changed')
    for row in recipe['changes']:
        parts = Path(row).parts
        if not parts or parts[0] not in ('Application', 'XNBYEngine') or '..' in parts or ':' in row or '\\' in row:
            raise ValueError('Unsafe patch source path')
    for check in (True, False):
        command = ['git', '-c', 'core.autocrlf=false', '-C', str(output), 'apply']
        if check:
            command.append('--check')
        subprocess.run(command + [str(patch)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    expected = recipe['sourceSHA256']
    actual = {name: sha((output / name).read_bytes()) for name in expected}
    if len(actual) != 411 or actual != expected:
        raise ValueError('Full source differs from actual accepted compile input')
    result = {'sourceFiles': 411, 'sourceSHA256': actual, 'patchSHA256': recipe['patchSHA256'],
              'builtOrStarted': False, 'GISOrRuntimeCopied': False, 'heldWorktreeUsed': False}
    (output / 'async-full-source-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'prepared': True, 'sourceFiles': 411, 'builtOrStarted': False}))


if __name__ == '__main__':
    main()
