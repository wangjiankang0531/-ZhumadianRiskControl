from pathlib import Path
import tempfile
import unittest
from verify_original_file_roundtrip import checked_owned_listeners, verify


class OwnFileProviderScope(unittest.TestCase):
    def test_ipv4_and_actual_dual_loopback_are_allowed_on_exact_api_port(self):
        for rows in ([{'LocalAddress': '127.0.0.1', 'LocalPort': 12000}],
                     [{'LocalAddress': '::1', 'LocalPort': 12000}, {'LocalAddress': '127.0.0.1', 'LocalPort': 12000}]):
            self.assertEqual(checked_owned_listeners(rows, 12000), rows)

    def test_wildcard_external_and_mapped_addresses_are_rejected(self):
        for address in ('0.0.0.0', '::', '192.168.0.107', '::ffff:127.0.0.1', 'localhost'):
            with self.subTest(address=address), self.assertRaisesRegex(ValueError, 'LISTENER_SCOPE'):
                checked_owned_listeners([{'LocalAddress': '127.0.0.1', 'LocalPort': 12000}, {'LocalAddress': address, 'LocalPort': 12000}], 12000)

    def test_other_port_console_and_malformed_rows_are_rejected(self):
        for row in ({'LocalAddress': '127.0.0.1', 'LocalPort': 12001},
                    {'LocalAddress': '127.0.0.1', 'LocalPort': '12000'},
                    {'LocalAddress': '127.0.0.1'}, None):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, 'LISTENER_SCOPE'):
                checked_owned_listeners([row], 12000)

    def test_empty_or_ipv6_only_cannot_satisfy_expected_ipv4_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'LISTENERS_REQUIRED'):
            checked_owned_listeners([], 12000)
        with self.assertRaisesRegex(ValueError, 'IPV4_LISTENER_REQUIRED'):
            checked_owned_listeners([{'LocalAddress': '::1', 'LocalPort': 12000}], 12000)

    def test_wrong_provider_receipt_pin_does_not_create_or_start_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); receipt = root / 'provider.json'; receipt.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'RECEIPT_PIN_MISMATCH'):
                verify(root, receipt, '0' * 64, root / 'output')
            self.assertFalse((root / 'output').exists())
            self.assertEqual(receipt.read_text(), '{}')


if __name__ == '__main__':
    unittest.main()
