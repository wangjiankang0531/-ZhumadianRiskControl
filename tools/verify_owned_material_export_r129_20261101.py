from pathlib import Path
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
