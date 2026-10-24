from pathlib import Path
import hashlib
import os
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import zlib
from original_frontend_deployment_assets import (
    COMMAND_URL,ORIGINAL_COMMAND,HOME_HANDLER,ORIGINAL_HOME_OPEN,home_deployment_override,
    home_navigation_adapter,map_tile_override,map_tile_path,local_command_override,mobile_entry_url,deployment_qr_png)
from prepare_original_frontend_gateway import checked_base_path,prepare


class DeploymentAdapters(unittest.TestCase):
    def test_map_adapter_preserves_coordinates_drawing_and_restores_on_failure(self):
        source=b'const url = origin + (prod ? "/tianjinrisk/map/" : "/map/") + "{z}/{x}/{y}.png";\r\nconst point=[117.53,38.6789];'
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);original=root/'reference';project=root/'build'
            for folder in (original,project):
                (folder/'src/components/Map').mkdir(parents=True);(folder/'src/components/Map/index.vue').write_bytes(source)
            with self.assertRaisesRegex(RuntimeError,'compile failed'):
                with map_tile_override(project,original,'/zhumadian/map/') as receipt:
                    self.assertEqual((project/'src/components/Map/index.vue').read_bytes(),source.replace(b'"/tianjinrisk/map/"',b'"/zhumadian/map/"'))
                    self.assertEqual((original/'src/components/Map/index.vue').read_bytes(),source)
                    raise RuntimeError('compile failed')
            self.assertTrue(receipt['sourceRestored']);self.assertFalse(receipt['coordinateAndDrawingLogicChanged'])
            self.assertEqual((project/'src/components/Map/index.vue').read_bytes(),source)
            (project/'src/components/Map/index.vue').unlink()
            os.link(original/'src/components/Map/index.vue',project/'src/components/Map/index.vue')
            with self.assertRaisesRegex(ValueError,'alias'):
                with map_tile_override(project,original,'/zhumadian/map/'):pass
            for value in ['/map/','https://other/map/','/a/../map/','/a/map/?token=x','/a//map/']:
                with self.subTest(value=value),self.assertRaises(ValueError):map_tile_path(value)

    @unittest.skipUnless(shutil.which('node'),'Existing Node runtime required for actual JavaScript semantics')
    def test_original_home_click_handler_maps_paths_without_mutating_backend_menu(self):
        source=(HOME_HANDLER+b'\nif (!item.path) return;\nif (item.enCode == "mjyjzh") {\n'+
                ORIGINAL_COMMAND+b'\nreturn;\n}\n'+ORIGINAL_HOME_OPEN+b'\n};\n')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);original=root/'reference';project=root/'build'
            for folder in (original,project):
                (folder/'src/views/home').mkdir(parents=True);(folder/'src/views/home/index.vue').write_bytes(source)
            with home_deployment_override(project,original,True,'/zhumadian') as receipt:
                script=(project/'src/views/home/index.vue').read_text('utf-8')
                calls='''
const routes = [
 ["/tianjinrisk/workplace", "/zhumadian/workplace"],
 ["/tianjinrisk/emergency", "/zhumadian/emergency"],
 ["/tianjinrisk/emergency/emergencyResponse?view=open#row", "/zhumadian/emergency/emergencyResponse?view=open#row"],
 ["/tianjinrisk/workflow/flowTodo", "/zhumadian/workflow/flowTodo"],
 ["/tianjinrisk", "/zhumadian"], ["/tianjinrisk?x=1#top", "/zhumadian?x=1#top"],
 ["/tianjinrisk-other/work", "/tianjinrisk-other/work"],
 ["https://other.example/tianjinrisk/work", "https://other.example/tianjinrisk/work"],
 ["/zhumadian/work", "/zhumadian/work"]
];
for (const [before, after] of routes) {
 const item = Object.freeze({path:before,enCode:"fixture"});
 handleTo(item);
 const actual = opened.pop();
 if(actual[0] !== after || actual[1] !== "_blank" || item.path !== before) throw Error("Wrong route: " + before);
}
handleTo(Object.freeze({path:"http://old.example/command", enCode:"mjyjzh"}));
const command = opened.pop();
if (command[0] !== '''+json.dumps(COMMAND_URL)+''' || command[2] !== "noopener,noreferrer") throw Error("Wrong local command");
handleTo({path:null});
if (opened.length) throw Error("Empty menu navigation attempted");
console.log("home-handler-js-passed");
'''
                code='const opened=[];const window={open:(...args)=>opened.push(args)};\n'+script+calls
                run=subprocess.run([shutil.which('node'),'--input-type=module','-e',code],capture_output=True,text=True,timeout=15)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertIn('home-handler-js-passed',run.stdout)
                self.assertFalse(receipt['menuRowsChanged']);self.assertFalse(receipt['externalHomeLinksRewritten'])
                self.assertFalse(receipt['publicLoginTokenForwarded'])
            self.assertTrue(receipt['sourceRestored'])
            self.assertEqual((project/'src/views/home/index.vue').read_bytes(),source)
            self.assertEqual((original/'src/views/home/index.vue').read_bytes(),source)

    def test_home_adapter_requires_exact_original_marker_and_safe_base(self):
        for value in ['/','/zhumadian/','//other','/a/../b','/a?token=x','/a\\b','/a\nnext']:
            with self.subTest(value=value),self.assertRaises(ValueError):home_navigation_adapter(value)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);original=root/'reference';project=root/'build'
            source=HOME_HANDLER+b'\n'+ORIGINAL_HOME_OPEN*2+b'\n};'
            for folder in (original,project):
                (folder/'src/views/home').mkdir(parents=True);(folder/'src/views/home/index.vue').write_bytes(source)
            with self.assertRaisesRegex(ValueError,'Pinned original home navigation'):
                with home_deployment_override(project,original,False,'/zhumadian'):pass
            self.assertEqual((project/'src/views/home/index.vue').read_bytes(),source)

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
