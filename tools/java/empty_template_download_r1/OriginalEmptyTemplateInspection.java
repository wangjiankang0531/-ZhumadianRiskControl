package xnby.replica;
import java.nio.file.*;
import java.io.*;
import java.lang.reflect.Proxy;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.poi.ss.usermodel.*;
import com.iemp.endanger.server.hidden.entity.RiskLevel;
import com.iemp.endanger.server.hidden.service.RiskLevelService;
import com.iemp.endanger.util.export.excel.ExcelUtil;
/** Read-only compatibility check for the one explicitly approved empty template. */
public final class OriginalEmptyTemplateInspection {
 public static void main(String[] args) throws Exception {
  Path file=Path.of(args[0]).toRealPath(), output=Path.of(args[1]);
  if(Files.size(file)>1000000)throw new AssertionError("BOUNDED_EMPTY_TEMPLATE_REQUIRED");
  String[] expected={"\u90e8\u95e8\u540d\u79f0","\u8d1f\u8d23\u4eba","\u5206\u6790\u5bf9\u8c61","\u5206\u6790\u5355\u5143","\u98ce\u9669\u7b49\u7ea7","\u5750\u6807"};
  try(InputStream input=Files.newInputStream(file);Workbook book=WorkbookFactory.create(input)) {
   if(book.getNumberOfSheets()!=1)throw new AssertionError("ONE_SHEET_REQUIRED");
   Sheet sheet=book.getSheetAt(0);Row header=sheet.getRow(0);
   if(header==null||header.getLastCellNum()!=6)throw new AssertionError("SIX_NATIVE_HEADERS_REQUIRED");
   DataFormatter formatter=new DataFormatter(Locale.ROOT);
   for(int i=0;i<6;i++)if(!expected[i].equals(formatter.formatCellValue(header.getCell(i))))throw new AssertionError("NATIVE_HEADER_MISMATCH");
   for(Row row:sheet)if(row.getRowNum()>0)for(Cell cell:row)if(!formatter.formatCellValue(cell).isBlank())throw new AssertionError("NOT_AN_EMPTY_TEMPLATE");
  }
  AtomicInteger saves=new AtomicInteger();
  RiskLevelService service=(RiskLevelService)Proxy.newProxyInstance(RiskLevelService.class.getClassLoader(),new Class[]{RiskLevelService.class},(proxy,method,values)->{
   if(method.getName().equals("saveBatch")){
    if(values==null||values.length==0||!(values[0] instanceof Collection)||!((Collection<?>)values[0]).isEmpty())throw new AssertionError("EMPTY_TEMPLATE_MUST_NOT_CONTAIN_RECORDS");
    saves.incrementAndGet();return true;
   }
   if(method.getName().equals("toString"))return "OWN_EMPTY_TEMPLATE_READ_ONLY_SERVICE";
   throw new AssertionError("UNEXPECTED_SERVICE_OPERATION_"+method.getName());
  });
  try(InputStream input=Files.newInputStream(file)){ExcelUtil.readFirst(input,RiskLevel.class,service);}
  Map<String,Object> result=new LinkedHashMap<>();result.put("actualOriginalPOIWorkbookFactoryReadPassed",true);result.put("originalExcelUtilReadFirstPassed",true);result.put("nativeSixHeadersMatched",true);result.put("businessDataRows",0);result.put("emptySaveBatchCalls",saves.get());result.put("databaseOrNetworkAccess",false);result.put("inputFileChanged",false);result.put("publicImportOrBusinessWritePerformed",false);
  Files.writeString(output,new ObjectMapper().writeValueAsString(result));System.out.println("ORIGINAL_EMPTY_TEMPLATE_READ_ONLY_COMPATIBILITY_PASSED");
 }
}
