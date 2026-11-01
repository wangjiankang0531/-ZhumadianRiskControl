from pathlib import Path
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
reader='''from pathlib import Path
import hashlib,json,re,sys,xml.etree.ElementTree as ET,zipfile
p=Path(sys.argv[1]).resolve(strict=True);expected=int(sys.argv[2]);root=Path('D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r129')
assert p.is_relative_to(root)and p.parent.name=='downloads'and p.suffix=='.xlsx'and p.stat().st_size<2097152 and 1<=expected<=10
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(p)as z:
 assert z.testzip()is None and sum(v.file_size for v in z.infolist())<16777216
 shared=[]
 if 'xl/sharedStrings.xml'in z.namelist():shared=[''.join(v.itertext())for v in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
 rows=[]
 for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('s:sheetData/s:row',ns):
  cells=[]
  for cell in row.findall('s:c',ns):
   value=cell.find('s:v',ns);text=value.text if value is not None else ''.join(cell.find('s:is',ns).itertext())if cell.find('s:is',ns)is not None else ''
   if cell.get('t')=='s':text=shared[int(text)]
   cells.append(text)
  if any(cells):rows.append(cells)
 assert '物资名称'in rows[0]and '物资数量'in rows[0]
 name_column=rows[0].index('物资名称');assert len(rows)-1==expected
 assert all(row[name_column].startswith('OWN_F_MAT_r7_valid_')for row in rows[1:])
print(json.dumps({'nativeExportOOXMLAndCRCPassed':True,'rows':len(rows)-1,'allNamesMatchExactOwnFilter':True,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
'''
(T/'verify_owned_material_export_r129_20261101.py').write_text(reader,encoding='utf-8')
p=T/'verify_full_controller_material_browser_r129_20261101.mjs';s=p.read_text(encoding='utf-8');anchor=" stage='actual-detail-click';"
extra=""" if(wire.variant==='guarded'){
  stage='actual-filtered-native-export';if(!await click('.table-box button','导出列表'))throw Error('OWN_EXPORT_BUTTON');await until(()=>evaluate('!!document.querySelector(".el-message-box")'));
  if(!await click('.el-message-box button','确定'))throw Error('OWN_EXPORT_CONFIRM');let exported;
  await until(async()=>{const n=(await fs.readdir(O+'/downloads')).find(n=>n.endsWith('.xlsx'));if(!n)return false;exported=O+'/downloads/'+n;return true});
  const exportProof=await nodeRun(R+'/_f/Application/runtime/python/python.exe',['-I','-B','-X','utf8',R+'/Application/tools/verify_owned_material_export_r129_20261101.py',exported,String(expected.total)]);
  await fs.writeFile(O+'/native-export-proof.json',JSON.stringify(exportProof,null,2));cases.push({case:'actual-chrome-filtered-export-valid-OOXML-and-exact-own-rows',passed:true,rows:exportProof.rows});
 }
"""
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor);p.write_text(s,encoding='utf-8');print('R129_ACTUAL_FILTERED_BROWSER_EXPORT_AND_INDEPENDENT_XLSX_READER_ADDED')
