from pathlib import Path
import hashlib
import os
import struct
import tempfile
import unittest
import zlib
from original_frontend_deployment_assets import (
    COMMAND_URL,ORIGINAL_COMMAND,local_command_override,mobile_entry_url,deployment_qr_png)
from prepare_original_frontend_gateway import checked_base_path,prepare


class DeploymentAdapters(unittest.TestCase):
    def test_local_command_isolated_and_restored_even_on_build_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);original=root/'reference';project=root/'build'
            source=b'<script>\r\nconst token="fixture-only";\r\n'+ORIGINAL_COMMAND+b'\r\n</script>'
            for folder in (original,project):
                (folder/'src/views/home').mkdir(parents=True);(folder/'src/views/home/index.vue').write_bytes(source)
            with self.assertRaisesRegex(RuntimeError,'compiler failed'):
                with local_command_override(project,original) as receipt:
                    edited=(project/'src/views/home/index.vue').read_bytes()
                    self.assertNotIn(ORIGINAL_COMMAND,edited)
                    self.assertIn(COMMAND_URL.encode(),edited)
                    self.assertIn(b'noopener,noreferrer',edited)
                    self.assertEqual((original/'src/views/home/index.vue').read_bytes(),source)
                    raise RuntimeError('compiler failed')
            self.assertTrue(receipt['sourceRestored'])
            self.assertEqual((project/'src/views/home/index.vue').read_bytes(),source)

    def test_ambiguous_or_hardlinked_command_input_cannot_modify_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);original=root/'reference';project=root/'build'
            for folder in (original,project):(folder/'src/views/home').mkdir(parents=True)
            source=ORIGINAL_COMMAND*2
            (original/'src/views/home/index.vue').write_bytes(source);(project/'src/views/home/index.vue').write_bytes(source)
            with self.assertRaises(ValueError):
                with local_command_override(project,original):pass
            (original/'src/views/home/index.vue').write_bytes(ORIGINAL_COMMAND)
            (project/'src/views/home/index.vue').unlink()
            os.link(original/'src/views/home/index.vue',project/'src/views/home/index.vue')
            with self.assertRaises(ValueError):
                with local_command_override(project,original):pass
            self.assertEqual((original/'src/views/home/index.vue').read_bytes(),ORIGINAL_COMMAND)

    def test_qr_entry_rejects_credentials_session_queries_and_invalid_routes(self):
        url='https://www.joinlinksmart.com/zhumadian/h5/'
        self.assertEqual(mobile_entry_url(url),url)
        for value in ['javascript:alert(1)','//example.com/app/h5/','https://user:pass@example.com/app/h5/',
                      url+'?token=private',url+'#private','https://example.com/../h5/',
                      'https://example.com/app//h5/','https://example.com:0/app/h5/',
                      'https://example.com:bad/app/h5/','https://example.com\\other/app/h5/']:
            with self.subTest(value=value),self.assertRaises(ValueError):mobile_entry_url(value)

    def test_mobile_qr_is_a_valid_grayscale_png_with_quiet_zone(self):
        raw=deployment_qr_png('https://www.joinlinksmart.com/zhumadian/h5/')
        self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n');position=8;chunks={}
        while position<len(raw):
            count=struct.unpack('!I',raw[position:position+4])[0];name=raw[position+4:position+8]
            payload=raw[position+8:position+8+count];crc=struct.unpack('!I',raw[position+8+count:position+12+count])[0]
            self.assertEqual(crc,zlib.crc32(name+payload)&0xffffffff);chunks[name]=payload;position+=12+count
        width,height,depth,kind,_,_,_=struct.unpack('!IIBBBBB',chunks[b'IHDR'])
        self.assertEqual((width,depth,kind),(height,8,0));pixels=zlib.decompress(chunks[b'IDAT'])
        self.assertEqual(len(pixels),height*(width+1))
        self.assertEqual(pixels[0],0);self.assertEqual(pixels[1:width+1],b'\xff'*width)
        self.assertIn(0,pixels[32*(width+1)+33:33*(width+1)])

    def test_public_gateway_prefix_does_not_rewrite_filesystem_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);runtime=root/'nginx';(runtime/'conf').mkdir(parents=True)
            (runtime/'nginx.exe').write_bytes(b'fixture');(runtime/'conf/mime.types').write_text('types {}')
            roots={name:root/'tianjinrisk'/name for name in ['security_pc','emergency_pc','mobile','bigscreen','tiles']}
            for name,folder in roots.items():
                folder.mkdir(parents=True)
                if name!='tiles':(folder/'index.html').write_text(name)
            receipt=prepare(root/'output',runtime,roots,12000,base_path='/zhumadian')
            text=(root/'output/nginx.conf').read_text('utf-8')
            self.assertEqual(receipt['appBasePath'],'/zhumadian')
            self.assertIn('location ^~ /zhumadian/api/jnpf/',text)
            self.assertIn('location = /zhumadian/h5/',text)
            self.assertEqual(text.count('location = /zhumadian/ {'),1)
            self.assertIn(roots['security_pc'].resolve().as_posix(),text)
            self.assertNotIn('location = /tianjinrisk',text)
            for value in ['/', '/app/', '//app','/app/../other','/app?token=x','/app;return','/app\nnext']:
                with self.subTest(value=value),self.assertRaises(ValueError):checked_base_path(value)


if __name__=='__main__':unittest.main()
