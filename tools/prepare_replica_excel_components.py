"""Extend the original-component candidate with real RiskLevel Excel transport."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reference-project',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
A=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-B','-X','utf8',str(A/'tools/prepare_replica_components.py'),'--reference-project',str(args.reference_project),'--output',str(args.output)],check=True)
P=args.output/'safety';E=args.output/'evidence';changes=[]
def edit(path,old,new):
 p=P/path;s=p.read_text('utf-8');assert old in s,(path,old[:50]);p.write_text(s.replace(old,new),encoding='utf-8');changes.append(path)
edit('src/api/hiddenInvestigate/riskAnalysisUnit/index.ts','request.post(base+"importExcel",params);','request.post(base+"importExcel",params,command(params));')
edit('src/components/ImportExcel/index.vue','<div class="el-upload__tip">请上传 .xls , .xlsx 标准格式文件，文件最大为 {{ parameter.fileSize }}M</div>','<div class="el-upload__tip">请上传 .xls , .xlsx 标准格式文件，文件最大为 {{ parameter.fileSize }}M</div>\n              <div v-if="parameter.rowLimit" class="el-upload__tip">本候选单次最多 {{ parameter.rowLimit }} 行；校验失败整批不写入，请按报错行修正后重传。</div>')
edit('src/components/ImportExcel/index.vue','  fileSize?: number;','  rowLimit?: number;\n  fileSize?: number;')
edit('src/views/hiddenInvestigate/riskAnalysisUnit/index.vue','    fileSuffix: ".xlsx",','    fileSuffix: ".xlsx",\n    rowLimit: 10000,')
edit('src/utils/request.ts','      error => {\n        if (error.response?.status === 401)','      async error => {\n        if (error.response?.status === 401)')
edit('src/utils/request.ts','const msg = error.response?.data?.message || error.response?.data?.msg || "请求失败";','let detail = error.response?.data;\n        if (detail instanceof Blob && detail.size < 1024 * 1024) {\n          try { detail = JSON.parse(await detail.text()); } catch {}\n        }\n        const msg = detail?.message || detail?.msg || "请求失败";')
edit('src/components/ImportExcel/index.vue','    <el-form class="drawer-multiColumn-form" label-width="100px">','    <el-form class="drawer-multiColumn-form" label-width="100px">\n      <el-alert v-if="importError" :title="importError" type="error" :closable="false" show-icon style="margin-bottom: 16px" />')
edit('src/components/ImportExcel/index.vue','const dialogVisible = ref(false);','const dialogVisible = ref(false);\nconst importError = ref("");')
edit('src/components/ImportExcel/index.vue','  parameter.value = { ...parameter.value, ...params };','  parameter.value = { ...parameter.value, ...params };\n  importError.value = "";')
edit('src/components/ImportExcel/index.vue','  await parameter.value.importApi!(excelFormData);\n  parameter.value.getTableList && parameter.value.getTableList();\n  dialogVisible.value = false;','  importError.value = "";\n  try {\n    await parameter.value.importApi!(excelFormData);\n    parameter.value.getTableList && parameter.value.getTableList();\n    dialogVisible.value = false;\n  } catch (error: any) {\n    importError.value = error.response?.data?.msg || error.response?.data?.message || "导入未完成，请检查网络和文件后重试";\n    throw error;\n  }')
(E/'excel_adapter_manifest.json').write_text(json.dumps({'files':[dict(path=p,sha256=hashlib.sha256((P/p).read_bytes()).hexdigest()) for p in sorted(set(changes))],'originalColumns':['部门名称','负责人','分析对象','分析单元','风险等级','坐标'],'fileFormats':['xls','xlsx'],'rowLimit':10000,'mapAccepted':False,'fullParity':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'excelAdaptedFiles':len(set(changes)),'mapAccepted':False}))
