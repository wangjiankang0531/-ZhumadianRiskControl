"""Project display-name adaptation for static frontend responses only."""
import argparse
import hashlib
import json
from pathlib import Path

PROJECT_NAME = '驻马店重大风险防控'
MARKER = '# zhumadian-project-display-name-v1'
ASSET_VERSION = 'branding-20261025'
ICON_NAME = 'project-icon-20261025.svg'
ORIGINAL_NAMES = ('天津南港危化品智慧物流综合服务中心', '天津南港危化品智慧物流园', '天津南港危化物流园')


def static_directives(project_name):
    if project_name != PROJECT_NAME:
        raise ValueError('Expected the explicitly selected project display name')
    replacements = [(name, project_name) for name in ORIGINAL_NAMES]
    replacements += [('<title></title>', '<title>' + project_name + '</title>'),
                     ('<title>敏捷应急指挥平台</title>', '<title>' + project_name + ' · 敏捷应急指挥</title>'),
                     ('"安全风险智能管控平台"', '"' + project_name + '"'),
                     ('"敏捷应急管理"', '"' + project_name + '"')]
    icon_url = '/zhumadian/' + ICON_NAME
    replacements += [
        # uni-image resolves absolute image paths against its own H5 base.
        ('/zhumadian/h5/assets/logo-C4nOa3Mc.png', '/zhumadian/h5/' + ICON_NAME),
        ('href="/zhumadian/favicon.ico"', 'href="' + icon_url + '"'),
        ('href="/zhumadian/emergency/favicon.ico"', 'href="' + icon_url + '"'),
        ('href="/zhumadian/h5/assets/favicon-CB3x86W5.ico" type="image/x-icon"',
         'href="' + icon_url + '" type="image/svg+xml"'),
        ('href="logo.png"', 'href="' + icon_url + '"')]
    # Matching escaped Unicode covers future compiler escaping without changing
    # unrelated city names, company records, geography or API payloads.
    for old in ORIGINAL_NAMES:
        replacements.append((json.dumps(old, ensure_ascii=True)[1:-1], project_name))
    for mount in ('/zhumadian/', '/zhumadian/emergency/', '/zhumadian/h5/'):
        replacements.append((mount + 'assets/', mount + ASSET_VERSION + '/assets/'))
    def quote(text):
        return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'
    lines = [MARKER, 'sub_filter_once off;',
             'sub_filter_types application/javascript text/javascript application/json;',
             'sub_filter_last_modified off;', 'if_modified_since off;', 'etag off;',
             'add_header Cache-Control "no-store" always;']
    lines += ['sub_filter ' + quote(old) + ' ' + quote(new) + ';' for old, new in replacements]
    return lines


def brand_static_config(config, project_name):
    """Attach filters only to locations serving explicit static roots.

    Upstream business/platform/admin API locations have no root and remain
    byte-for-byte identical. Original static files and manifests stay sealed.
    """
    directives = static_directives(project_name)
    icon = Path(__file__).resolve().parents[1] / 'deploy/branding/zhumadian-emergency.svg'
    if not icon.is_file() or icon.is_symlink() or icon.resolve() != icon:
        raise ValueError('Explicit regular project icon asset required')
    icon_path = icon.as_posix()
    if any(c in icon_path for c in ('"', '$', ';', '{', '}', '\n', '\r')):
        raise ValueError('Unsupported project icon deployment path')
    if MARKER in config:
        raise ValueError('Project branding is already present; do not stack filters')
    result = []; count = 0; servers = 0
    for line in config.splitlines():
        result.append(line)
        if line.lstrip().startswith('server_name '):
            result.append(' rewrite ^/(zhumadian(?:/emergency|/h5)?)/' + ASSET_VERSION + '/(assets/.*)$ /$1/$2 last;')
            result.extend([' location = /zhumadian/' + ICON_NAME + ' {',
                           '  alias "' + icon_path + '";',
                           '  default_type image/svg+xml;',
                           '  add_header Cache-Control "no-store" always;',
                           ' }'])
            result.extend([' location = /zhumadian/h5/' + ICON_NAME + ' {',
                           '  alias "' + icon_path + '";',
                           '  default_type image/svg+xml;',
                           '  add_header Cache-Control "no-store" always;',
                           ' }'])
            servers += 1
        if line.lstrip().startswith('root '):
            prefix = line[:len(line) - len(line.lstrip())]
            result.extend(prefix + item for item in directives)
            count += 1
    if count == 0 or servers != 1:
        raise ValueError('No explicit static frontend locations found')
    newline = '\r\n' if '\r\n' in config else '\n'
    return newline.join(result) + newline, {'projectName': project_name, 'staticLocations': count,
             'originalStaticFilesChanged': False, 'businessDatabaseChanged': False,
             'originalReferenceChanged': False, 'upstreamResponseFiltersAdded': False,
             'staticAssetVersion': ASSET_VERSION,
             'projectIconURL': '/zhumadian/' + ICON_NAME,
             'projectIconSHA256': hashlib.sha256(icon.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--input-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.input_sha256:
        raise ValueError('Input gateway configuration differs')
    content, receipt = brand_static_config(raw.decode('utf-8'), PROJECT_NAME)
    with args.output.open('xb') as stream:
        stream.write(content.encode('utf-8'))
    print(json.dumps(receipt, ensure_ascii=False))
