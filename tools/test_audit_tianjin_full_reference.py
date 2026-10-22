import csv,json,tempfile,unittest
from pathlib import Path
from audit_tianjin_full_reference import audit,PROJECTS,JAVA,resolve

class ReferenceInventoryTests(unittest.TestCase):
 def test_metadata_keeps_fields_buttons_imports_and_excludes_config_and_build(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'reference';out=Path(t)/'output'
   for directory in PROJECTS.values():
    p=root/directory/'src/views/unit/index.vue';p.parent.mkdir(parents=True)
    p.write_text('<template><el-button @click="create">新增</el-button><el-input v-model="field.name" label="风险对象" /></template><script>import {getPage} from "@/api/unit";</script>',encoding='utf-8')
    api=root/directory/'src/api/unit/index.ts';api.parent.mkdir(parents=True)
    api.write_text('export const getPage=()=>request.get<ResPage<any>>("/serv/riskLevel/getPage");export const exportExcel=()=>request.download("/serv/riskLevel/export");',encoding='utf-8')
    (root/directory/'.env').write_text('DO_NOT_COPY=private-value',encoding='utf-8')
    ignored=root/directory/'src/node_modules/x.vue';ignored.parent.mkdir();ignored.write_text('private-value')
   java=root/JAVA/'Risk.java';java.parent.mkdir(parents=True)
   java.write_text('@RestController @RequestMapping("/riskLevel") public class RiskController { @GetMapping("/getPage") public Object getPage(){return null;} } @TableName("risk") class Risk {private String name;}',encoding='utf-8')
   result=audit(root,out);self.assertEqual(result['pageComponents'],4);self.assertEqual(result['controllers'],1);self.assertEqual(result['tableEntities'],1)
   document=json.loads((out/'source_inventory.json').read_text('utf-8'));page=next(x for x in document['projects']['safety']['files'] if x['path'].endswith('.vue'))
   self.assertIn('风险对象',[x['text'] for x in page['labels']]);self.assertEqual(page['buttons'][0]['text'],'新增');self.assertEqual(page['models'][0]['binding'],'field.name')
   self.assertEqual(page['transitiveApiSources'],['src/api/unit/index.ts'])
   api=next(x for x in document['projects']['safety']['files'] if '/api/' in x['path'])
   self.assertEqual([(x['method'],x['path']) for x in api['apiEndpoints']],[('GET','/serv/riskLevel/getPage'),('GET','/serv/riskLevel/export')])
   self.assertNotIn('private-value',(out/'source_inventory.json').read_text('utf-8'))
   with (out/'page_acceptance_matrix.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),4);self.assertTrue(all(r['visualParity']=='未验收' for r in rows))
 def test_import_resolution_refuses_escape_and_handles_directory_index(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'project';p=root/'src/views/a.vue';p.parent.mkdir(parents=True);p.write_text('')
   external=Path(t)/'outside.ts';external.write_text('')
   local=root/'src/api/unit/index.ts';local.parent.mkdir(parents=True);local.write_text('')
   self.assertIsNone(resolve(root,p,'../../../outside.ts'));self.assertEqual(resolve(root,p,'@/api/unit'),local.resolve())
if __name__=='__main__':unittest.main()
