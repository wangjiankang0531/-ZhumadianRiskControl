"""Synthetic integrity/relocation fixtures, separate from the real Java payload check."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import uuid
import zipfile
import subprocess
import sys

import portable_reference_business_runtime as runtime


def jar_manifest(classpath):
    result=[]
    for key,value in [('Manifest-Version','1.0'),('Original-Main-Class','fixture.Main'),('Class-Path',classpath),
                      ('Created-By','synthetic-fixture-only'),('Source-Archive-SHA256',runtime.SOURCE_SHA),('Portable-Layout-Version','1')]:
        raw=(key+': '+value).encode();result.append(raw[:70]);raw=raw[70:]
        while raw:result.append(b' '+raw[:69]);raw=raw[69:]
    return b'\r\n'.join(result)+b'\r\n\r\n'


class RelativePaths(unittest.TestCase):
    def test_rejects_traversal_devices_and_ambiguous_windows_paths(self):
        for value in ['','.', '..','../x','/x','C:/x','lib\\x.jar','lib//x.jar','lib/./x.jar','lib/../x.jar',
                      'lib/x.jar.','lib/x.jar ','lib/NUL.jar','lib/COM1.jar','lib/a\x00.jar']:
            with self.subTest(path=value),self.assertRaises(ValueError):runtime.relative(value)
        self.assertEqual(runtime.relative('lib/a-1.2+test.jar'),'lib/a-1.2+test.jar')


class PortablePayloadIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'payload';self.root.mkdir();(self.root/'lib').mkdir()
        self.entries=[{'path':'fixture/Main.class','data':b'not-a-real-class'}]
        self.entries += [{'path':'fixture/C'+str(i)+'.class','data':b'synthetic-class-only'+str(i).encode()} for i in range(767)]
        self.entries += [{'path':'resources/r'+str(i)+'.txt','data':b'synthetic-resource'} for i in range(97)]
        self.files=[{'path':'application.jar'}]
        for i in range(220):
            name='lib/d'+str(i)+'.jar';path=self.root/name
            with zipfile.ZipFile(path,'w') as jar:jar.writestr('META-INF/MANIFEST.MF',b'Manifest-Version: 1.0\r\n\r\n')
            self.files.append({'path':name,'bytes':path.stat().st_size,'sha256':runtime.sha(path)})
        self.write_jar()
        self.spec={'kind':runtime.KIND,'ownerId':str(uuid.uuid4()),'referenceArchiveSHA256':runtime.REFERENCE_SHA,
            'sourceArchiveSHA256':runtime.SOURCE_SHA,'compiledClasses':768,'resourceCount':97,'dependencyCount':220,
            'sourceInputs':863,'sourceInputsSHA256':'1'*64,'sourceFlatJarSHA256':'2'*64,'mainClass':'fixture.Main',
            'files':self.files,'applicationEntries':[{'path':r['path'],'bytes':len(r['data']),'sha256':hashlib.sha256(r['data']).hexdigest()} for r in self.entries],
            'privateRuntimeArtifact':True,'originalConfigurationIncluded':True,
            'originalClassesOrResourceBytesChanged':False,'jarManifestOnlyChanged':True}
        self.save()

    def write_jar(self,classpath=None,omit_directory=False,change_class=False):
        with zipfile.ZipFile(self.root/'application.jar','w',zipfile.ZIP_DEFLATED) as jar:
            jar.writestr('META-INF/MANIFEST.MF',jar_manifest(classpath if classpath is not None else ' '.join(r['path'] for r in self.files[1:])))
            for name in ['META-INF/','fixture/','resources/']:
                if not (omit_directory and name=='fixture/'):jar.writestr(name,b'')
            for i,row in enumerate(self.entries):jar.writestr(row['path'],b'tampered-class' if change_class and i==0 else row['data'])
        app=self.root/'application.jar';self.files[0]={'path':'application.jar','bytes':app.stat().st_size,'sha256':runtime.sha(app)}

    def save(self):
        self.manifest=self.root/runtime.MANIFEST;self.manifest.write_text(json.dumps(self.spec),encoding='utf-8');self.pin=runtime.sha(self.manifest)

    def rejected(self,code):
        with self.assertRaisesRegex(ValueError,code):runtime.verify(self.manifest,self.pin)

    def test_complete_synthetic_payload_and_unicode_relocation(self):
        self.assertEqual(runtime.verify(self.manifest,self.pin)['payloadFiles'],221)
        target=self.root.parent/'中文 空格搬迁';self.root.rename(target);self.root=target;self.manifest=target/runtime.MANIFEST
        self.assertTrue(runtime.verify(self.manifest,self.pin)['allPayloadAndApplicationEntryBytesVerified'])

    def test_explicit_manifest_pin_required_and_checked(self):
        with self.assertRaisesRegex(ValueError,'EXPLICIT_PORTABLE_MANIFEST_PIN_REQUIRED'):runtime.verify(self.manifest,None)
        with self.assertRaisesRegex(ValueError,'PORTABLE_MANIFEST_PIN_MISMATCH'):runtime.verify(self.manifest,'0'*64)

    def test_dependency_tamper_is_rejected(self):
        (self.root/'lib/d0.jar').write_bytes(b'tampered');self.rejected('PORTABLE_FILE_SIZE_MISMATCH')

    def test_extra_or_missing_payload_file_is_rejected(self):
        (self.root/'unexpected.properties').write_bytes(b'synthetic');self.rejected('PORTABLE_FILE_SET_MISMATCH')
        (self.root/'unexpected.properties').unlink();(self.root/'lib/d0.jar').unlink();self.rejected('PORTABLE_FILE_SET_MISMATCH')

    def test_extra_directory_is_rejected(self):
        (self.root/'extra').mkdir();self.rejected('PORTABLE_DIRECTORY_SET_MISMATCH')

    def test_unsafe_or_case_colliding_record_is_rejected(self):
        original=copy.deepcopy(self.spec)
        self.spec['files'][1]['path']='../outside.jar';self.save();self.rejected('SAFE_RELATIVE_PAYLOAD_PATH_REQUIRED')
        self.spec=original;self.spec['files'][2]['path']=self.spec['files'][1]['path'].upper();self.save();self.rejected('PORTABLE_PATH_COLLISION')

    def test_manifest_cannot_downgrade_dependency_or_privacy_contract(self):
        self.spec['dependencyCount']=219;self.save();self.rejected('COMPLETE_REFERENCE_SOURCE_LAYOUT_REQUIRED')
        self.spec['dependencyCount']=220;self.spec['privateRuntimeArtifact']=False;self.save();self.rejected('PRIVATE_RUNTIME_ARTIFACT_REQUIRED')

    def test_absolute_manifest_classpath_rejected_even_with_new_jar_pin(self):
        self.write_jar(classpath='file:/C:/outside.jar');self.spec['files']=self.files;self.save();self.rejected('PORTABLE_CLASSPATH_MISMATCH')

    def test_class_byte_tamper_rejected_even_with_new_jar_pin(self):
        self.write_jar(change_class=True);self.spec['files']=self.files;self.save();self.rejected('PORTABLE_APPLICATION_BYTES_MISMATCH')

    def test_missing_package_directory_rejected(self):
        self.write_jar(omit_directory=True);self.spec['files']=self.files;self.save();self.rejected('PORTABLE_EXPLICIT_PACKAGE_DIRECTORIES_REQUIRED')

    def test_duplicate_json_key_rejected(self):
        raw=self.manifest.read_text('utf-8').replace('{','{"kind":"duplicate",',1);self.manifest.write_text(raw,encoding='utf-8');self.pin=runtime.sha(self.manifest)
        self.rejected('PORTABLE_JSON_DUPLICATE_KEY')

    def test_dependency_cannot_add_hidden_external_classpath(self):
        path=self.root/'lib/d0.jar'
        with zipfile.ZipFile(path,'w') as jar:jar.writestr('META-INF/MANIFEST.MF',b'Manifest-Version: 1.0\r\ncLaSs-PaTh: file:/C:/outside.jar\r\n\r\n')
        self.spec['files'][1].update(bytes=path.stat().st_size,sha256=runtime.sha(path));self.save()
        self.rejected('DEPENDENCY_SECONDARY_CLASSPATH_REFUSED')

    def test_large_signed_dependency_tail_does_not_hide_main_section(self):
        path=self.root/'lib/d0.jar'
        raw=b'Manifest-Version: 1.0\r\n\r\n'+b'Name: synthetic-entry\r\nSHA-256-Digest: synthetic\r\n\r\n'*4000
        self.assertGreater(len(raw),128*1024)
        with zipfile.ZipFile(path,'w') as jar:jar.writestr('META-INF/MANIFEST.MF',raw)
        self.spec['files'][1].update(bytes=path.stat().st_size,sha256=runtime.sha(path));self.save()
        self.assertTrue(runtime.verify(self.manifest,self.pin)['allPayloadAndApplicationEntryBytesVerified'])

    def test_standalone_cli_verification_uses_only_payload_and_pin(self):
        script=Path(__file__).with_name('portable_reference_business_runtime.py')
        result=subprocess.run([sys.executable,'-I','-B',str(script),'verify','--manifest',str(self.manifest),
            '--manifest-sha256',self.pin],capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['payloadFiles'],221)

    def test_uncontrolled_jar_main_entry_is_rejected(self):
        path=self.root/'application.jar'
        with zipfile.ZipFile(path) as jar:entries=[(i,jar.read(i)) for i in jar.infolist()]
        for extra in [b'Main-Class: fixture.Main',b'mAiN-ClAsS: fixture.Main',b'Launcher-Agent-Class: fixture.Agent']:
            with self.subTest(header=extra):
                with zipfile.ZipFile(path,'w') as jar:
                    for info,data in entries:
                        if info.filename=='META-INF/MANIFEST.MF':data=data.replace(b'\r\n\r\n',b'\r\n'+extra+b'\r\n\r\n',1)
                        jar.writestr(info,data)
                self.spec['files'][0].update(bytes=path.stat().st_size,sha256=runtime.sha(path));self.save()
                self.rejected('CONTROLLED_LAUNCH_MANIFEST_REQUIRED')

    def test_jar_index_can_reference_only_declared_payload_libraries(self):
        path=self.root/'lib/d0.jar'
        for header in ['d0.jar','d1.jar','../outside.jar','file:/C:/outside.jar','missing.jar']:
            with self.subTest(header=header):
                with zipfile.ZipFile(path,'w') as jar:
                    jar.writestr('META-INF/MANIFEST.MF',b'Manifest-Version: 1.0\r\n\r\n')
                    jar.writestr('META-INF/INDEX.LIST','JarIndex-Version: 1.0\n\n'+header+'\nfixture/package\n\n')
                self.spec['files'][1].update(bytes=path.stat().st_size,sha256=runtime.sha(path));self.save()
                if header in ['d0.jar','d1.jar']:
                    self.assertEqual(runtime.verify(self.manifest,self.pin)['dependencyJarIndexFilesChecked'],1)
                else:self.rejected('DEPENDENCY_JAR_INDEX_ESCAPES_PAYLOAD')


if __name__=='__main__':unittest.main()
