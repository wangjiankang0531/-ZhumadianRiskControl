import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from prepare_original_shared_redis import prepare


class SharedRedisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.business = self.root / 'business.properties'
        self.platform = self.root / 'platform.properties'
        self.connection = self.root / 'private.json'
        self.output = self.root / 'joint'
        self.business.write_text(self.config('spring.data.redis', 51111, 'business-private'), encoding='ascii')
        self.platform.write_text(self.config('spring.redis', 52222, 'platform-private'), encoding='ascii')
        self.own = {'schema': 'zhumadian.original.joint-redis.v1', 'ownerId': str(uuid.uuid4()),
                    'host': '127.0.0.1', 'port': 53333, 'database': 3, 'password': 'new-owned-private-' + 'x' * 32}
        self.save()

    @staticmethod
    def config(prefix, port, password):
        return '\n'.join(['server.address=127.0.0.1', 'server.port=0',
                          prefix+'.host=127.0.0.1', prefix+'.port='+str(port), prefix+'.database=0',
                          prefix+'.password='+password, 'security.original=untouched',
                          'config.file-storage.minio[0].enable-storage=false']) + '\n'

    def save(self):
        self.connection.write_text(json.dumps(self.own), encoding='utf-8')

    def run_prepare(self):
        return prepare(self.output, self.business, self.platform, self.connection)

    def test_distinct_namespaces_produce_same_owned_endpoint_and_preserve_inputs(self):
        paths = (self.business, self.platform, self.connection)
        before = [p.read_bytes() for p in paths]
        result = self.run_prepare()
        self.assertFalse(result['existingConfigurationsShareRedis'])
        self.assertTrue(result['configurationAligned'])
        for name, prefix in [('business','spring.data.redis'), ('platform','spring.redis')]:
            lines = (self.output/(name+'-redis.properties')).read_text().splitlines()[1:]
            got = dict(line.split('=', 1) for line in lines)
            self.assertEqual(got, {prefix+'.'+key: str(self.own[key]) for key in ('host','port','database','password')})
        self.assertEqual(before, [p.read_bytes() for p in paths])
        for flag in ('runtimeStarted','runtimeReady','authenticatedBusinessVerified','fullCloneReady',
                     'originalAuthenticationChanged','originalPermissionsChanged'):
            self.assertFalse(result[flag])
        public = json.dumps(result)
        for private in ('business-private','platform-private',self.own['password']):
            self.assertNotIn(private, public)

    def test_equal_existing_endpoint_detected(self):
        self.platform.write_text(self.config('spring.redis', 51111, 'business-private'),encoding='ascii')
        self.assertTrue(self.run_prepare()['existingConfigurationsShareRedis'])

    def test_reject_external_or_ambiguous_inputs_before_writing(self):
        original = self.business.read_text()
        for candidate in (original.replace('127.0.0.1','192.168.0.107'),
                          original+'spring.data.redis.port=51112\n',
                          original+'spring.redis.host=127.0.0.1\n',
                          original+'spring.data.redis.url=redis://127.0.0.1:50000\n',
                          original+'spring.data.redis.cluster.nodes=127.0.0.1:50000\n',
                          original.replace('server.port=0','server.port=8767'),
                          original.replace('server.address=127.0.0.1','server.address=0.0.0.0')):
            with self.subTest(candidate=candidate):
                self.business.write_text(candidate,encoding='ascii')
                with self.assertRaises(ValueError): self.run_prepare()
                self.assertFalse(self.output.exists())

    def test_reject_invalid_owned_metadata_before_writing(self):
        for key, value in [('host','192.168.0.107'),('port',876),('port',True),('database',False),
                           ('database',16),('password','short'),('password','bad\n'+'x'*40),
                           ('ownerId','not-an-owner'),('schema','untrusted')]:
            original = dict(self.own)
            with self.subTest(key=key,value=value):
                self.own[key] = value; self.save()
                with self.assertRaises(ValueError): self.run_prepare()
                self.assertFalse(self.output.exists())
            self.own = original

    def test_preexisting_output_and_overlapping_input_rejected(self):
        with self.assertRaises(ValueError):
            prepare(self.root,self.business,self.platform,self.connection)
        self.output.mkdir()
        with self.assertRaises(ValueError): self.run_prepare()

    def test_duplicate_connection_fields_rejected(self):
        raw = json.dumps(self.own)
        self.connection.write_text(raw[:-1]+',"port":54444}',encoding='ascii')
        with self.assertRaises(ValueError): self.run_prepare()
        self.assertFalse(self.output.exists())

    def test_error_cli_does_not_echo_private_values(self):
        self.own['password'] = 'DO-NOT-ECHO-THIS-PRIVATE-CONTENT\n'
        self.save()
        run = subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('prepare_original_shared_redis.py')),
                              '--output',str(self.output),'--business',str(self.business),
                              '--platform',str(self.platform),'--connection',str(self.connection)],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertNotIn('DO-NOT-ECHO',run.stdout+run.stderr)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
