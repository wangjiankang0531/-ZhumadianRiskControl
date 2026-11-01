"""Exact project-logo aliases for an already branded static gateway; no API or source-asset edits."""
from pathlib import Path
import hashlib

MARKER_BEGIN = '# zhumadian-static-header-logo-20261026-begin'
MARKER_END = '# zhumadian-static-header-logo-20261026-end'
PROJECT_NAME = '\u9a7b\u9a6c\u5e97\u91cd\u5927\u98ce\u9669\u9632\u63a7'
HEADER_PATH = '/zhumadian/assets/png/logo-CQaY_L7K.png'
MOBILE_PATH = '/zhumadian/h5/assets/logo-C4nOa3Mc.png'
H5_ICON_PATH = '/zhumadian/h5/project-icon-20261025.svg'
ICON_SHA256 = '509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d'
PREPARER_SHA256 = '0b6f8cd8344ad568b03fa2ee1b12e72eff04c740ea9a383b3c2520848f6cb979'


def checked_icon(icon):
    icon = Path(icon).absolute()
    if not icon.is_file() or icon.resolve(strict=True) != icon:
        raise ValueError('EXPLICIT_REGULAR_PROJECT_ICON_REQUIRED')
    for p in [icon, *icon.parents]:
        if p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('NO_ICON_REPARSE_ALLOWED')
    raw = icon.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ICON_SHA256:
        raise ValueError('PINNED_OWN_EMERGENCY_ICON_REQUIRED')
    value = icon.as_posix()
    if any(c in value for c in ('"', '$', ';', '{', '}', '\n', '\r')):
        raise ValueError('UNSUPPORTED_ICON_PATH')
    return value


def apply_header_branding(config, project_name, icon):
    if project_name != PROJECT_NAME or '# zhumadian-project-display-name-v1' not in config:
        raise ValueError('EXISTING_PROJECT_BRANDING_REQUIRED')
    if MARKER_BEGIN in config or MARKER_END in config:
        raise ValueError('DO_NOT_STACK_HEADER_BRANDING')
    icon_path = checked_icon(icon)
    paths = [HEADER_PATH, MOBILE_PATH]
    # Old installed generators lack the H5 SVG alias; new source generators already include it.
    if 'location = ' + H5_ICON_PATH + ' {' not in config:
        paths.append(H5_ICON_PATH)
    for path in paths:
        if 'location = ' + path + ' {' in config:
            raise ValueError('EXACT_LOGO_LOCATION_ALREADY_DEFINED')
    newline = '\r\n' if '\r\n' in config else '\n'
    inserted = [' ' + MARKER_BEGIN]
    for path in paths:
        inserted += [' location = ' + path + ' {',
                     '  alias "' + icon_path + '";',
                     '  types { }',
                     '  default_type image/svg+xml;',
                     '  add_header Cache-Control "no-store" always;',
                     '  etag off;',
                     '  if_modified_since off;',
                     ' }']
    inserted.append(' ' + MARKER_END)
    block = newline.join(inserted) + newline
    result = []
    server_names = 0
    for line in config.splitlines(keepends=True):
        result.append(line)
        if line.lstrip().startswith('server_name '):
            server_names += 1
            if not line.endswith(('\n', '\r')):
                raise ValueError('SERVER_LINE_MUST_END_WITH_NEWLINE')
            result.append(block)
    if server_names != 1:
        raise ValueError('EXACTLY_ONE_OWNED_SERVER_REQUIRED')
    output = ''.join(result)
    if output.replace(block, '', 1) != config:
        raise AssertionError('ONLY_EXACT_STATIC_LOCATION_INSERTION_ALLOWED')
    return output, {'revision': '20261026-static-header-logo', 'exactAliases': paths,
                    'headerLogoURL': HEADER_PATH, 'iconSHA256': ICON_SHA256,
                    'originalStaticFilesChanged': False, 'businessAPIChanged': False,
                    'projectDataOrCompanyPrintLogoChanged': False}


def patch_gateway_preparer(raw):
    if hashlib.sha256(raw).hexdigest() != PREPARER_SHA256:
        raise ValueError('FIXED_GATEWAY_PREPARER_REQUIRED')
    old = b'        config_text,branding=brand_static_config(config_text,project_name)\n'
    if raw.count(old) != 1:
        raise ValueError('EXACT_BRANDING_HOOK_REQUIRED')
    new = old + (b'        from original_header_branding import apply_header_branding\n'
                 b'        config_text,header_branding=apply_header_branding(config_text,project_name,Path(__file__).resolve().parents[1]/"deploy/branding/zhumadian-emergency.svg")\n'
                 b'        branding["headerLogo"]=header_branding\n')
    return raw.replace(old, new, 1)