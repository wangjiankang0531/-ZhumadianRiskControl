"""Compile the real owned builder and exercise it with synthetic configuration.

Set ORIGINAL_CONFIG_JDK and ORIGINAL_CONFIG_YAML to an existing JDK17 and
SnakeYAML jar. No application, database, login or network is started.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


class PublicLoginWireKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='own-login-config-')
        cls.root = Path(cls.temp.name).resolve()
        cls.java = Path(os.environ['ORIGINAL_CONFIG_JDK']) / 'bin'
        cls.yaml = Path(os.environ['ORIGINAL_CONFIG_YAML']).resolve(strict=True)
        if hashlib.sha256(cls.yaml.read_bytes()).hexdigest() != '1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b':
            raise ValueError('PINNED_YAML_REQUIRED')
        source = Path(__file__).parent / 'java' / 'OriginalPlatformConfigBuilder.java'
        if not source.is_file():
            source = Path(__file__).with_name('OriginalPlatformConfigBuilder.java')
        cls.classes = cls.root / 'classes'
        cls.classes.mkdir()
        run = subprocess.run([str(cls.java / 'javac.exe'), '-proc:none', '--release', '17',
                              '-encoding', 'UTF-8', '-cp', str(cls.yaml), '-d', str(cls.classes), str(source)],
                             capture_output=True, timeout=30)
        if run.returncode:
            raise AssertionError('OWN_BUILDER_COMPILATION_FAILED')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def prepare(self, wire_key):
        root = self.root / self._testMethodName
        root.mkdir()
        archive = root / 'synthetic.jar'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('BOOT-INF/classes/application.yml', 'spring:\n  profiles:\n    active: test\n')
            z.writestr('BOOT-INF/classes/application-test.yml',
                       'security:\n  SecurityKey: "' + wire_key + '"\n  EnablePreAuth: true\n'
                       'custom:\n  securityKey: synthetic-private-key\n  token: synthetic-token\n'
                       '  password: synthetic-password\n  client-secret: synthetic-secret\n'
                       '  endpoint: https://source.example.invalid/private\n')
        own = root / 'candidate'
        own.mkdir()
        public = root / 'public.pem'
        public.write_text('-----BEGIN PUBLIC KEY-----\nsynthetic-not-used-for-connections\n', encoding='ascii')
        (own / 'own-integration.properties').write_text(
            'ownSecret=own-synthetic-replacement-0000000\nmysqlPort=13306\nmysqlPassword=own-db\n'
            'redisPort=16379\nredisPassword=own-redis\nmysqlPublicKeyPath=' + public.as_posix() + '\n', encoding='ascii')
        run = subprocess.run([str(self.java / 'java.exe'), '-cp', os.pathsep.join([str(self.classes), str(self.yaml)]),
                              'xnby.platform.OriginalPlatformConfigBuilder', str(archive), str(own)],
                             capture_output=True, timeout=15)
        config = own / 'application.properties'
        values = {}
        if config.exists():
            # Fixture values and assertions are ASCII and contain no Java escapes.
            for line in config.read_text(encoding='iso-8859-1').splitlines():
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    values[key] = value
        return run, own, values

    def test_public_key_preserved_and_other_credentials_replaced(self):
        run, own, config = self.prepare('fixture-wire0016')
        # This fixture is deliberately 16 bytes; no real key appears in the test.
        self.assertEqual(run.returncode, 0, 'OWN_BUILDER_FAILED')
        self.assertEqual(config['security.SecurityKey'], 'fixture-wire0016')
        for key in ['custom.securityKey', 'custom.token', 'custom.password', 'custom.client-secret']:
            self.assertEqual(config[key], 'own-synthetic-replacement-0000000')
        self.assertEqual(config['security.EnablePreAuth'], 'true')
        self.assertEqual(config['custom.endpoint'], 'http\\://127.0.0.1\\:9/own-unavailable')
        names = (own / 'overridden-property-names.txt').read_text().splitlines()
        self.assertNotIn('security.SecurityKey', names)
        self.assertIn('custom.securityKey', names)

    def test_24_byte_public_key_supported(self):
        run, _, values = self.prepare('x' * 24)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(values['security.SecurityKey'], 'x' * 24)

    def test_32_byte_public_key_supported(self):
        run, _, values = self.prepare('x' * 32)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(values['security.SecurityKey'], 'x' * 32)

    def test_invalid_public_key_length_fails_before_config_publish(self):
        run, own, _ = self.prepare('invalid-wire-size')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b'CLIENT_WIRE_AES_KEY_LENGTH', run.stderr)
        self.assertFalse((own / 'application.properties').exists())


if __name__ == '__main__':
    unittest.main()
