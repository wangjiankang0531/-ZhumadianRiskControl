"""Narrow deployment adaptations; original reference files and business modules stay intact."""
from contextlib import contextmanager
import hashlib
from pathlib import Path
import re
import struct
import sys
from urllib.parse import urlsplit
import zlib

COMMAND_URL='http://127.0.0.1:8767/?topic=emergency&mode=command'
ORIGINAL_COMMAND=b'window.open(`${item.path}?t=${token}&user=${userStore.info!.userName}`);'
DEPLOYED_COMMAND=b'window.open("'+COMMAND_URL.encode('ascii')+b'", "_blank", "noopener,noreferrer");'


@contextmanager
def local_command_override(project, pristine_source):
    project,pristine_source=Path(project).resolve(),Path(pristine_source).resolve()
    if project==pristine_source or project.is_relative_to(pristine_source) or pristine_source.is_relative_to(project):
        raise ValueError('Command override requires a distinct build copy')
    rel=Path('src/views/home/index.vue');target=project/rel;original=target.read_bytes()
    if not target.resolve(strict=True).is_relative_to(project) or target.samefile(pristine_source/rel):
        raise ValueError('Build input must not alias or escape the pristine reference')
    if original!=(pristine_source/rel).read_bytes() or original.count(ORIGINAL_COMMAND)!=1:
        raise ValueError('Pinned original command branch is missing or changed')
    patched=original.replace(ORIGINAL_COMMAND,DEPLOYED_COMMAND)
    receipt={'file':rel.as_posix(),'originalSHA256':hashlib.sha256(original).hexdigest(),
             'compiledInputSHA256':hashlib.sha256(patched).hexdigest(),'commandURL':COMMAND_URL,
             'onlyCommandTargetChanged':True,'publicLoginTokenForwarded':False,'sourceRestored':False}
    try:
        target.write_bytes(patched)
        yield receipt
    finally:
        target.write_bytes(original)
        if target.read_bytes()!=original:
            raise RuntimeError('Original build-copy input was not restored')
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
