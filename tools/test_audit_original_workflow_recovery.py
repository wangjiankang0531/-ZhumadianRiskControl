import hashlib
import json
import pathlib
import tempfile
import unittest
import audit_original_workflow_recovery as audit

NS = 'http://www.omg.org/spec/BPMN/20100524/MODEL'

def xml(key):
    return ('<definitions xmlns="'+NS+'"><process id="'+key+'"/></definitions>').encode()

def rows(resources):
    result = {name: [] for name in audit.TABLE_COLUMNS}
    result['flow_run_add_node'] = [('activiti_own_private_key:2:own-private-definition-id', 'own-private-instance')]
    result['act_ge_bytearray'] = resources
    return result

class RecoveryAuditTests(unittest.TestCase):
    def test_bpmn_namespace_and_exact_key(self):
        self.assertEqual(audit.bpmn_keys(xml('exact'))[0], {'exact'})
        self.assertEqual(audit.bpmn_keys(b'<definitions><process id="exact"/></definitions>')[0], set())

    def test_dtd_entity_rejected_in_utf8_and_utf16(self):
        text='<!DOCTYPE definitions [<!ENTITY x SYSTEM "file:///C:/private-canary">]><definitions>&x;</definitions>'
        for raw in (text.encode(), text.encode('utf-16'), text.encode('utf-16-be')):
            self.assertEqual(audit.bpmn_keys(raw)[1], 'dtd_or_entity_rejected')

    def test_binary_and_oversized_resources_are_explicit(self):
        self.assertEqual(audit.bpmn_keys(b'\x89PNG\0\xff')[1], 'not_valid_xml')
        self.assertEqual(audit.bpmn_keys(b' '*(2*1024**2+1))[1], 'size_limit')

    def test_key_substring_is_not_exact_model_or_recovery(self):
        data=rows([('own-resource-a','process.xml','own-deployment',xml('activiti_own_private_key_extra'))])
        report=audit.build_report(data);group=report['missingDefinitionGroups'][0]
        self.assertEqual(group['rawKeySubstringResourceCandidates'],1)
        self.assertEqual(group['exactBpmnProcessKeyResources'],0)
        self.assertFalse(report['exactDefinitionRecoveryProven'])

    def test_utf16_exact_resource_survives_union_with_raw_substring(self):
        data=rows([('own-resource-a','process.xml','own-deployment',xml('activiti_own_private_key_extra')),
                   ('own-resource-b','process.xml','own-deployment',xml('activiti_own_private_key').decode().encode('utf-16'))])
        group=audit.build_report(data)['missingDefinitionGroups'][0]
        self.assertEqual(group['exactBpmnProcessKeyResources'],1)
        self.assertEqual(len(group['resourceCandidates']),2)
        self.assertEqual(sum(r['exactBpmnProcessKey'] for r in group['resourceCandidates']),1)
        self.assertFalse(group['exactDefinitionRecoveryProven'])

    def test_report_omits_private_keys_and_payloads(self):
        report=audit.build_report(rows([('own-private-resource-id','own-private-name','own-private-deployment',xml('activiti_own_private_key'))]))
        encoded=json.dumps(report)
        for secret in ('activiti_own_private_key','own-private-instance','own-private-resource-id','own-private-name','own-private-deployment','<definitions'):
            self.assertNotIn(secret,encoded)

    def test_manifest_cannot_select_outside_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder)
            for name in ('catalog.json','jnpf.rows.jsonl.gz'):(root/name).write_bytes(b'')
            raw=json.dumps({'files':[{'name':'../outside'},{'name':'catalog.json'},{'name':'jnpf.rows.jsonl.gz'}]}).encode()
            (root/'manifest.json').write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'EXPORT_PAYLOAD_SCOPE'):
                audit.audit(root,hashlib.sha256(raw).hexdigest())

if __name__ == '__main__':
    unittest.main()
