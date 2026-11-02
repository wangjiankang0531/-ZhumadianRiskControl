"""Explicit SHA-pinned source callable for the bounded RAM page builder."""
import hashlib
import json
from pathlib import Path
import re
from PIL import Image,JpegImagePlugin,features,__version__ as PIL_VERSION
import osgb_v80_data_reader
import osgb_v80_memory_frame
import osgb_memory_reader


def digest(raw):return hashlib.sha256(raw).hexdigest()


class PinnedOSGBDataReader:
    def __init__(self,source_root):
        self.source_root=Path(source_root).resolve(strict=True)
        if self.source_root.name!='Data' or not self.source_root.is_dir():
            raise ValueError('Explicit original Data root is required')
        self.code={
            'reader':Path(osgb_v80_data_reader.__file__),
            'frame':Path(osgb_v80_memory_frame.__file__),
            'callable':Path(__file__),
            'frameValidator':Path(osgb_memory_reader.__file__),
            'PIL.Image':Path(Image.__file__),
            'PIL.JpegImagePlugin':Path(JpegImagePlugin.__file__),
            'PIL.codec':Path(Image.core.__file__),
        }
        self.hashes={key:self._code_hash(path) for key,path in self.code.items()}
        self.identity=digest(json.dumps(dict(backend='python_osgb_v80_data_v1',code=self.hashes,Pillow=PIL_VERSION,JPEG=features.version_codec('jpg')),
                                       sort_keys=True,separators=(',',':')).encode())

    @staticmethod
    def _code_hash(path):
        if path.is_symlink() or not 0<path.stat().st_size<=16*1048576:
            raise ValueError('Invalid pinned data-reader code file')
        return digest(path.read_bytes())

    def verify_runtime(self):
        if any(self._code_hash(path)!=self.hashes[key] for key,path in self.code.items()):
            raise ValueError('Pinned data-reader implementation changed')

    def __call__(self,tile,name,record):
        if type(tile) is not int or not 1<=tile<=2346 or not isinstance(name,str) or not re.fullmatch(rf'Tile_{tile}_L[0-9]+_0[0-9u]+\.osgb',name):
            raise ValueError('Invalid relative original-source request')
        expected=record.get('sha256');size=record.get('bytes')
        if not isinstance(expected,str) or not re.fullmatch('[0-9a-f]{64}',expected) or type(size) is not int or not 0<size<=64*1048576:
            raise ValueError('Original source requires bounded pinned identity')
        self.verify_runtime();source=self.source_root/f'Tile_{tile}'/name
        for path in (self.source_root,source.parent,source):
            stat=path.lstat()
            if path.is_symlink() or getattr(stat,'st_file_attributes',0)&0x400:
                raise ValueError('Original source links are forbidden')
        if not source.is_file() or not source.resolve(strict=True).is_relative_to(self.source_root):
            raise ValueError('Source is outside the original Data root')
        before=source.stat()
        if before.st_size!=size:raise ValueError('Original source size differs')
        with source.open('rb') as stream:raw=stream.read(size+1)
        if len(raw)!=size or digest(raw)!=expected:raise ValueError('Original source SHA differs')
        descriptor,payload=osgb_v80_memory_frame.build_parsed_frame(raw,f'Tile_{tile}/{name}')
        after=source.stat()
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
            raise ValueError('Original source changed during decode')
        with source.open('rb') as stream:after_raw=stream.read(size+1)
        if len(after_raw)!=size or digest(after_raw)!=expected:raise ValueError('Original source changed during decode')
        self.verify_runtime()
        return descriptor,payload
