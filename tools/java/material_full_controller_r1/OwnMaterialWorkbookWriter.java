import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.context.AnalysisContext;
import com.alibaba.excel.read.listener.ReadListener;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.iemp.endanger.server.materials.entity.Materials;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.ss.usermodel.DataFormatter;
import java.io.*;import java.nio.file.*;import java.util.*;
/** Pure synthetic workbook construction and original-model parser proof. No SQL or authentication. */
public final class OwnMaterialWorkbookWriter {
 static final List<String> HEADERS=List.of("物资名称","物资类型","物资型号","物资数量","单位","所属部门","存放地点","责任人","联系方式","技术要求","备注","坐标");
 static void need(boolean b){if(!b)throw new IllegalArgumentException("OWN_MATERIAL_WORKBOOK_SCOPE_OR_CONTENT");}
 static Map<String,Object> parse(Path p)throws Exception{
  int[] count={0},named={0};EasyExcel.read(p.toFile(),Materials.class,new ReadListener<Materials>(){
   public void invoke(Materials m,AnalysisContext c){count[0]++;if(m.getMaterialName()!=null&&m.getMaterialName().startsWith("OWN_F_MAT_"))named[0]++;}
   public void doAfterAllAnalysed(AnalysisContext c){}
  }).sheet(0).doRead();
  return Map.of("parsedRows",count[0],"ownNamedRows",named[0]);
 }
 public static void main(String[]args)throws Exception{
  need(args.length==2);Path root=Path.of(args[0]).toAbsolutePath().normalize(),template=Path.of(args[1]).toAbsolutePath().normalize();
  need(root.getParent().getParent().equals(Path.of("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r128"))&&root.getFileName().toString().equals("material-browser")&&root.getParent().getFileName().toString().matches("r[1-9][0-9]*"));
  need(template.getParent().equals(root.resolve("downloads"))&&template.toString().endsWith(".xlsx")&&Files.size(template)<1048576);
  String prefix="OWN_F_MAT_"+root.getParent().getFileName()+"_";Map<String,Object> report=new LinkedHashMap<>();
  if(Files.isRegularFile(Path.of("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r128/r4/material-browser/own-valid.xlsx"))){
   Path previous=Path.of("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r128/r4/material-browser/own-valid.xlsx");
   need(Files.isRegularFile(previous));report.put("previousXmlWriterNativeParser",parse(previous));
  }
  for(String label:List.of("valid","partial")){
   int n=label.equals("valid")?3:3001;Path output=root.resolve("own-"+label+".xlsx");need(!Files.exists(output));
   try(var input=Files.newInputStream(template);var workbook=new XSSFWorkbook(input)){
    need(workbook.getNumberOfSheets()==1);var sheet=workbook.getSheetAt(0);var formatter=new DataFormatter(Locale.ROOT);
    need(sheet.getLastRowNum()==0);for(int k=0;k<HEADERS.size();k++)need(HEADERS.get(k).equals(formatter.formatCellValue(sheet.getRow(0).getCell(k))));
    for(int i=0;i<n;i++){
     String name=label.equals("partial")&&i==3000?"X".repeat(101):prefix+label+"_"+i;
     List<String> values=List.of(name,"OWN_TYPE","OWN_MODEL","12","个","OWN_DEPARTMENT","OWN_STORAGE","OWN_PERSON","00000000000","OWN_REQUIREMENT","仅独立合成验证","113.000,33.000");
     var row=sheet.createRow(i+1);for(int k=0;k<values.size();k++)row.createCell(k).setCellValue(values.get(k));
    }
    try(var out=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){workbook.write(out);}
   }
   var counts=parse(output);need(((Number)counts.get("parsedRows")).intValue()==n);need(((Number)counts.get("ownNamedRows")).intValue()==(n==3?3:3000));
   report.put(label,output.toString());report.put(label+"ParserProof",counts);
  }
  report.put("prefix",prefix);report.put("templateHeaders",12);report.put("templateRows",0);report.put("originalEasyExcelAndModelActuallyUsed",true);report.put("databasesReadOrWritten",false);
  byte[] json=new ObjectMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(report);
  Files.write(root.resolve("workbook-proof.json"),json,StandardOpenOption.CREATE_NEW);System.out.println("OWN_MATERIAL_WORKBOOK_JSON:"+new String(json,java.nio.charset.StandardCharsets.UTF_8));
 }
}
