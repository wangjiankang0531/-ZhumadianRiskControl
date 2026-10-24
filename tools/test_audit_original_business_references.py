import json,unittest
from audit_original_business_references import FIELDS,ROLES,FORMS,key,build_report
class ReferenceAuditTests(unittest.TestCase):
 def fixture(self):
  rows={n:[] for n in FIELDS};rows['base_role']=[{'f_id':'fixture-role','f_enabled_mark':'1','f_delete_mark':None}];rows['flow_form']=[{'f_id':'fixture-form','f_en_code':'fixture-code','f_flow_id':'unused-old-field','f_enabled_mark':'1','f_delete_mark':'0'}];rows['flow_form_relation']=[{'f_form_id':'fixture-form','f_flow_id':'fixture-template','f_delete_mark':None}];rows['flow_template']=[{'f_id':'fixture-template','f_enabled_mark':'1','f_delete_mark':None}];rows['flow_template_json']=[{'f_template_id':'fixture-template','F_PROCESSDEFINITIONID':'fixture-definition','f_enabled_mark':'1','f_delete_mark':None}];rows['act_re_procdef']=[{'ID_':'fixture-definition'}];expected={n:key('fixture-role' if n in ROLES else 'fixture-code') for n in ROLES+FORMS};return rows,expected
 def test_exact_unique_role_form_and_released_definition_are_separate_checks(self):
  rows,e=self.fixture();r=build_report(rows,e);self.assertEqual(r['uniqueNonDeletedReferences'],11);self.assertTrue(r['allConfiguredFormsHaveExistingReleasedDefinition']);self.assertFalse(r['workflowExecutionVerified'])
 def test_duplicates_are_reported_and_not_silently_selected(self):
  rows,e=self.fixture();rows['flow_form']*=2;r=build_report(rows,e);self.assertFalse(r['allConfiguredFormCodesExist']);self.assertFalse(r['allConfiguredFormsHaveExistingReleasedDefinition'])
 def test_deleted_role_is_not_a_valid_live_reference(self):
  rows,e=self.fixture();rows['base_role'][0]['f_delete_mark']='1';r=build_report(rows,e);self.assertFalse(r['allConfiguredRoleIdsExist']);self.assertEqual(r['configuredReferences'][0]['exactMatches'],1);self.assertEqual(r['configuredReferences'][0]['nonDeletedMatches'],0)
 def test_missing_template_or_definition_does_not_become_valid_from_unrelated_rows(self):
  rows,e=self.fixture();rows['flow_template'][0]['f_id']='other';self.assertFalse(build_report(rows,e)['allConfiguredFormsHaveExistingReleasedDefinition'])
  rows,e=self.fixture();rows['act_re_procdef']=[];r=build_report(rows,e);self.assertFalse(r['allConfiguredFormsHaveExistingReleasedDefinition']);self.assertEqual(r['configuredReferences'][-1]['releasedVersionsWithMissingDefinition'],1)
 def test_empty_or_partial_configuration_is_not_treated_as_complete(self):
  rows,e=self.fixture();e[FORMS[0]]='EMPTY';r=build_report(rows,e);self.assertFalse(r['allConfiguredFormCodesExist']);self.assertFalse(r['configuredReferences'][3]['configuredNonEmpty'])
  with self.assertRaises(ValueError):build_report(rows,{})
 def test_no_original_values_or_rows_are_exposed_and_disabled_versions_not_counted_as_released(self):
  rows,e=self.fixture();rows['flow_template_json'][0]['f_enabled_mark']='0';r=build_report(rows,e);self.assertFalse(r['allConfiguredFormsHaveExistingReleasedDefinition']);text=json.dumps(r)
  for value in ('fixture-role','fixture-code','fixture-template','fixture-definition'):self.assertNotIn(value,text)
 def test_original_relation_table_is_used_and_old_column_never_substituted(self):
  rows,e=self.fixture();self.assertTrue(build_report(rows,e)['allConfiguredFormsHaveExistingReleasedDefinition']);rows['flow_form_relation']=[];rows['flow_form'][0]['f_flow_id']='fixture-template';self.assertFalse(build_report(rows,e)['allConfiguredFormsHaveExistingReleasedDefinition'])
 def test_role_metadata_and_polymorphic_user_associations_are_not_conflated(self):
  rows,e=self.fixture();rows['base_role']=[];rows['base_user_relation']=[{'f_object_id':'fixture-role','f_object_type':'Role','f_delete_mark':None},{'f_object_id':'fixture-role','f_object_type':'Organize','f_delete_mark':None}];r=build_report(rows,e);self.assertFalse(r['allConfiguredRoleIdsExist']);self.assertEqual(r['configuredReferences'][0]['nonDeletedLiteralRoleAssociations'],1)
if __name__=='__main__':unittest.main()
