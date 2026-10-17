"""Verify business-reference editing through the editor's own regression mode."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True)
    parser.add_argument('--layers', required=True, help='Test copy with at least one point in the first layer')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    layers = Path(args.layers).resolve()
    before = hashlib.sha256(layers.read_bytes()).hexdigest()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / 'native_business_probe.json'
    with (output / 'native_business_probe.log').open('wb') as log:
        subprocess.run([str(Path(args.exe).resolve()), '--editor-business-probe',
                        '--layers=' + str(layers), '--stats=' + str(report_path)],
                       cwd=output, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    report = json.loads(report_path.read_text(encoding='utf-8'))
    required = ['passed', 'apply', 'undo_redo', 'invalid_preserves_document',
                'locked_preserves_document', 'unbind_preserves_identity', 'save_reopen',
                'object_id_unchanged', 'geometry_unchanged']
    if not all(report.get(key) is True for key in required) or report.get('invalid_cases_rejected') != 8:
        raise RuntimeError('Business editing regression failed: ' + json.dumps(report))
    if hashlib.sha256(layers.read_bytes()).hexdigest() != before:
        raise RuntimeError('Input layer file changed during regression')
    print('BUSINESS EDIT / UNDO / LOCK / SAVE / SPATIAL IDENTITY PASS')


if __name__ == '__main__':
    main()
