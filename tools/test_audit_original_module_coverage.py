import json
from pathlib import Path
import tempfile
import unittest
from audit_original_module_coverage import FIELDS,active,report,views

class ModuleCoverageTests(unittest.TestCase):
 def test_enabled_deleted_and_metadata_visibility_have_separate_meanings(self):
  self.assertTrue(active({'f_enabled_mark':'1','f_delete_mark':None}));self.assertFalse(active({'f_enabled_mark':'1','f_delete_mark':'1'}));self.assertFalse(active({'f_enabled_mark':'0','f_delete_mark':'0'}))
 def test_router_lookup_matches_only_actual_views_and_rejects_external_paths(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'src/views/a').mkdir(parents=True);(root/'src/views/a/index.vue').write_text('fixture')
   self.assertEqual(len(views(root,'/a/index')),1);self.assertEqual(len(views(root,'/a')),1)
   for value in ('//host/a','/../private','/a?secret=x','/a#x','/a%2f..','/C:/secret',None):self.assertEqual(views(root,value),[])
 def run_report(self,prior):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'src/views').mkdir(parents=True)
   rows={n:[] for n in FIELDS};rows['base_system']=[{'f_id':'s','f_en_code':'safety'}]
   rows['base_module']=[{'f_id':'m','f_type':'2','f_system_id':'s','f_full_name':'Fixture page','f_url_address':'/missing/index','f_visible':'1','f_enabled_mark':'1','f_delete_mark':'0'}]
   rows['base_db_link']=[{'f_id':'link-private-id','f_host':'private-host','f_service_name':'jnpf','f_db_schema':None,'f_port':'3306','f_db_type':'MySQL','f_delete_mark':'0'}]
   return report(rows,prior,{'security_pc':root})
 def test_missing_source_and_missing_capture_are_reported_without_claiming_broken_role(self):
  r=self.run_report([]);self.assertEqual(r['pageModulesWithoutSource'],1);self.assertEqual(r['uncapturedMetadataModules'],1);self.assertFalse(r['roleVisibilityVerified']);self.assertFalse(r['fullCloneReady'])
 def test_later_observed_capture_merges_without_discarding_prior_route_mismatch(self):
  r=self.run_report([('security_pc',[{'id':'m','urlAddress':'/wrong','originalUIObserved':False}]),('security_pc',[{'id':'m','urlAddress':'/missing/index','originalUIObserved':True}])]);self.assertEqual(r['capturedRouteMismatches'],1);self.assertTrue(r['modules'][0]['originalUIObservedInPriorCapture']);self.assertFalse(r['modules'][0]['candidateFunctionalParityVerified'])
 def test_report_contains_no_raw_link_id_host_or_authentication_fields(self):
  text=json.dumps(self.run_report([]));self.assertNotIn('private-host',text);self.assertNotIn('link-private-id',text)
  for names in FIELDS.values():self.assertNotIn('f_password',names);self.assertNotIn('f_user_name',names)
 def test_non_candidate_platform_is_counted_but_not_assumed_missing_vue(self):
  rows={n:[] for n in FIELDS};rows['base_system']=[{'f_id':'s','f_en_code':'workSystem'}];rows['base_module']=[{'f_id':'m','f_system_id':'s','f_type':'3','f_enabled_mark':'1','f_delete_mark':'0'}]
  r=report(rows,[],{});self.assertEqual(r['systems'][0]['activeMetadataModules'],1);self.assertEqual(r['pageModules'],0);self.assertEqual(r['pageModulesWithoutSource'],0)
 def test_missing_parent_does_not_establish_role_visible_menu(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'src/views').mkdir(parents=True)
   rows={n:[] for n in FIELDS};rows['base_system']=[{'f_id':'s','f_en_code':'safety'}]
   row={'f_id':'m','f_parent_id':'absent','f_system_id':'s','f_type':'2','f_full_name':'Page','f_url_address':'/missing','f_visible':'1','f_enabled_mark':'1','f_delete_mark':'0'};rows['base_module']=[row]
   r=report(rows,[],{'security_pc':root});self.assertEqual(r['modules'][0]['metadataAncestry'],'missing_parent');self.assertFalse(r['roleVisibilityVerified'])
   row['f_parent_id']='m';r=report(rows,[],{'security_pc':root});self.assertEqual(r['modules'][0]['metadataAncestry'],'cycle')
if __name__=='__main__':unittest.main()
