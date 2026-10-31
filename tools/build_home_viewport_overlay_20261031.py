"""Build a reviewable home CSS overlay; this tool never installs or publishes."""
from pathlib import Path
import argparse
import hashlib
import json
import re

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def build(index, expected, output, input_kind):
    index = Path(index).resolve(strict=True)
    output = Path(output).resolve()
    css_path = Path(__file__).resolve().parent / 'frontend/home-viewport.css'
    raw = index.read_bytes()
    css = css_path.read_bytes()
    if not re.fullmatch('[0-9a-f]{64}', expected) or sha(raw) != expected:
        raise ValueError('EXACT_INDEX_INPUT_REQUIRED')
    if raw.count(b'</head>') != 1 or b'data-xnby-home-viewport=' in raw:
        raise ValueError('SINGLE_UNPATCHED_HTML_HEAD_REQUIRED')
    if output.exists() or output == index.parent or output.is_relative_to(index):
        raise ValueError('FRESH_OUTPUT_REQUIRED')
    name = 'xnby-home-viewport-' + sha(css)[:12] + '.css'
    eol = b'\r\n' if b'\r\n' in raw else b'\n'
    link = ('<link rel="stylesheet" data-xnby-home-viewport="20261031" href="/zhumadian/' + name + '">').encode()
    updated = raw.replace(b'</head>', link + eol + b'  </head>', 1)
    output.mkdir(parents=True)
    (output / name).write_bytes(css)
    (output / 'index.html').write_bytes(updated)
    result = {
        'kind': 'home-viewport-overlay-review-candidate',
        'inputKind': input_kind,
        'beforeIndexSHA256': expected,
        'files': {name: {'bytes': len(css), 'sha256': sha(css)},
                  'index.html': {'bytes': len(updated), 'sha256': sha(updated)}},
        'cssBytesExactlyVerifiedSource': True,
        'originalIndexOtherwisePreserved': True,
        'serverPhysicalIndexAndReleaseMetadataVerified': False,
        'runtimeInstalled': False, 'publicDeployed': False,
        'deploymentReady': False,
        'nextStep': 'Verify physical server files and release manifests before composing a deployable update.',
    }
    (output / 'overlay-review-manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--expected-index-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--input-kind', choices=['disk', 'anonymous-https-snapshot'], required=True)
    args = parser.parse_args()
    result = build(args.index, args.expected_index_sha256, args.output, args.input_kind)
    print(json.dumps({'files': len(result['files']), 'publicDeployed': False, 'deploymentReady': False}))
