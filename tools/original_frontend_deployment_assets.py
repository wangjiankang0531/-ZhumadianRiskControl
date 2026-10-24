"""Narrow deployment adaptations; original reference files and business modules stay intact."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from urllib.parse import urlsplit
import zlib

COMMAND_URL='http://127.0.0.1:8767/?topic=emergency&mode=command'
ORIGINAL_COMMAND=b'window.open(`${item.path}?t=${token}&user=${userStore.info!.userName}`);'
DEPLOYED_COMMAND=b'window.open("'+COMMAND_URL.encode('ascii')+b'", "_blank", "noopener,noreferrer");'
ORIGINAL_HOME_OPEN=b'window.open(item.path, "_blank");'
HOME_HANDLER=b'const handleTo = item => {'


def home_navigation_adapter(base_path,admin_home=None):
    if (not isinstance(base_path,str) or len(base_path)>128
            or not re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',base_path)):
        raise ValueError('Explicit same-origin application base required')
    if admin_home is not None and admin_home!=base_path+'/admin':
        raise ValueError('Admin deployment entry must be the same application admin base')
    declaration='const deploymentHomePath = value => {' if admin_home is None else 'const deploymentHomePath = (value, code) => {'
    admin_branch='' if admin_home is None else '  if (code === "syslink") return '+json.dumps(admin_home+'/')+';\n'
    return (declaration+'\n'+admin_branch+'''
  if (typeof value !== "string") return value;
  const legacy = "/tianjinrisk";
  const deployed = '''+json.dumps(base_path)+''';
  const delimiter = value.search(/[?#]/);
  const path = delimiter < 0 ? value : value.slice(0, delimiter);
  if (path === legacy || path.startsWith(legacy + "/")) {
    return deployed + value.slice(legacy.length);
  }
  return value;
};

''').encode('utf-8')


@contextmanager
def home_deployment_override(project, pristine_source, use_local_command=False, home_base=None,admin_home=None):
    project,pristine_source=Path(project).resolve(),Path(pristine_source).resolve()
    if project==pristine_source or project.is_relative_to(pristine_source) or pristine_source.is_relative_to(project):
        raise ValueError('Command override requires a distinct build copy')
    rel=Path('src/views/home/index.vue');target=project/rel;original=target.read_bytes()
    if not target.resolve(strict=True).is_relative_to(project) or target.samefile(pristine_source/rel):
        raise ValueError('Build input must not alias or escape the pristine reference')
    if original!=(pristine_source/rel).read_bytes():
        raise ValueError('Original home build input differs from pristine source')
    if admin_home is not None:home_navigation_adapter(home_base,admin_home)
    if not use_local_command and home_base is None:
        raise ValueError('At least one explicit home deployment adapter required')
    if use_local_command and original.count(ORIGINAL_COMMAND)!=1:
        raise ValueError('Pinned original command branch is missing or changed')
    patched=original
    if use_local_command:patched=patched.replace(ORIGINAL_COMMAND,DEPLOYED_COMMAND)
    if home_base is not None:
        if original.count(HOME_HANDLER)!=1 or original.count(ORIGINAL_HOME_OPEN)!=1:
            raise ValueError('Pinned original home navigation branch is missing or changed')
        patched=patched.replace(HOME_HANDLER,home_navigation_adapter(home_base,admin_home)+HOME_HANDLER)
        deployed_open=b'window.open(deploymentHomePath(item.path), "_blank");' if admin_home is None else b'window.open(deploymentHomePath(item.path, item.enCode), "_blank");'
        patched=patched.replace(ORIGINAL_HOME_OPEN,deployed_open)
    receipt={'file':rel.as_posix(),'originalSHA256':hashlib.sha256(original).hexdigest(),
             'compiledInputSHA256':hashlib.sha256(patched).hexdigest(),'commandURL':COMMAND_URL if use_local_command else None,
             'onlyCommandTargetChanged':home_base is None,'homeNavigationBase':home_base,
             'legacyHomePrefix':'/tianjinrisk' if home_base is not None else None,
             'externalHomeLinksRewritten':admin_home is not None,'menuRowsChanged':False,
             'adminHomeBase':admin_home,'adminLoginTokenOrUserForwarded':False,
             'publicLoginTokenForwarded':not use_local_command,'sourceRestored':False}
    try:
        target.write_bytes(patched)
        yield receipt
    finally:
        target.write_bytes(original)
        if target.read_bytes()!=original:
            raise RuntimeError('Original build-copy input was not restored')
        receipt['sourceRestored']=True


@contextmanager
def local_command_override(project, pristine_source):
    with home_deployment_override(project,pristine_source,use_local_command=True) as receipt:
        yield receipt


def map_tile_path(value):
    if (not isinstance(value,str) or len(value)>160
            or not re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/map/',value)):
        raise ValueError('Explicit same-origin application map path required')
    return value


@contextmanager
def map_tile_override(project, pristine_source, tile_base):
    tile_base=map_tile_path(tile_base)
    project,pristine_source=Path(project).resolve(),Path(pristine_source).resolve()
    if project==pristine_source or project.is_relative_to(pristine_source) or pristine_source.is_relative_to(project):
        raise ValueError('Map override requires a distinct build copy')
    rel=Path('src/components/Map/index.vue');target=project/rel;original=target.read_bytes()
    if not target.resolve(strict=True).is_relative_to(project) or target.samefile(pristine_source/rel):
        raise ValueError('Map build input must not alias or escape the pristine reference')
    marker=b'"/tianjinrisk/map/"'
    if original!=(pristine_source/rel).read_bytes() or original.count(marker)!=1:
        raise ValueError('Pinned original map URL is missing or changed')
    patched=original.replace(marker,json.dumps(tile_base).encode('ascii'))
    receipt={'file':rel.as_posix(),'originalSHA256':hashlib.sha256(original).hexdigest(),
             'compiledInputSHA256':hashlib.sha256(patched).hexdigest(),'tileBase':tile_base,
             'onlyMapURLChanged':True,'coordinateAndDrawingLogicChanged':False,'sourceRestored':False}
    try:
        target.write_bytes(patched)
        yield receipt
    finally:
        target.write_bytes(original)
        if target.read_bytes()!=original:raise RuntimeError('Original map build input was not restored')
        receipt['sourceRestored']=True


def mobile_entry_url(value):
    if not isinstance(value,str) or len(value)>2048 or any(ord(c)<33 for c in value):
        raise ValueError('Explicit mobile entry URL required')
    parsed=urlsplit(value)
    try:port=parsed.port
    except ValueError:raise ValueError('Invalid mobile entry port') from None
    if (parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment
            or not re.fullmatch(r'[A-Za-z0-9.-]+',parsed.hostname) or port==0 or '//' in parsed.path
            or not re.fullmatch(r'/[A-Za-z0-9_/-]+/h5/',parsed.path)):
        raise ValueError('Mobile QR URL must be a credential-free application H5 entry')
    return value


def deployment_qr_png(value,scale=8):
    value=mobile_entry_url(value)
    if isinstance(scale,bool) or not isinstance(scale,int) or not 2<=scale<=16:
        raise ValueError('QR scale outside supported range')
    sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
    from qrcodegen import QrCode
    code=QrCode.encode_text(value,QrCode.Ecc.MEDIUM);modules=code.get_size();size=(modules+8)*scale
    raw=bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            mx,my=x//scale-4,y//scale-4
            raw.append(0 if 0<=mx<modules and 0<=my<modules and code.get_module(mx,my) else 255)
    def chunk(name,data):
        return struct.pack('!I',len(data))+name+data+struct.pack('!I',zlib.crc32(name+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',size,size,8,0,0,0,0))
            +chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b''))


def replace_output_mobile_qr(dist,value):
    target=Path(dist)/'qrcode.png'
    if not target.is_file():
        raise ValueError('Expected original public QR output is missing')
    before=target.read_bytes();data=deployment_qr_png(value);target.write_bytes(data)
    return {'file':'qrcode.png','originalSHA256':hashlib.sha256(before).hexdigest(),
            'deployedSHA256':hashlib.sha256(data).hexdigest(),'url':value,'bytes':len(data),
            'originalReferenceModified':False,'requiresPhoneScanVerification':True}
