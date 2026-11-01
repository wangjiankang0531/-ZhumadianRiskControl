package xnby.replica;
import java.nio.file.*;import java.io.*;import java.util.*;
import org.springframework.context.ConfigurableApplicationContext;import org.springframework.aop.support.AopUtils;import org.springframework.aop.framework.Advised;import org.springframework.transaction.interceptor.TransactionInterceptor;import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;import org.springframework.web.multipart.MultipartFile;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;import com.iemp.endanger.server.hidden.entity.RiskLevel;import com.iemp.endanger.server.hidden.service.RiskLevelService;import com.iemp.endanger.server.hidden.controller.RiskLevelController;import com.iemp.endanger.util.response.ServiceException;
public final class OriginalRiskWholeImportFixture {
 static void require(boolean b,String message){if(!b)throw new IllegalStateException(message);}
 static QueryWrapper<RiskLevel> own(){return new QueryWrapper<RiskLevel>().eq("department","Own atom import dept");}
 static void clean(RiskLevelService service,long expected,long original){var rows=service.list(own());require(rows.size()==expected,"EXACT_OWN_IMPORT_CLEANUP_COUNT_REQUIRED");for(var row:rows)require(row.getAnalysisObject()!=null&&row.getAnalysisObject().startsWith("Own atomic row "),"ONLY_OWN_IMPORT_PREFIX_CAN_BE_REMOVED");if(!rows.isEmpty())require(service.removeByIds(rows.stream().map(RiskLevel::getId).toList()),"NORMAL_OWN_IMPORT_CLEANUP_REQUIRED");require(service.count()==original&&service.count(own())==0,"OWN_IMPORT_CLEANUP_MUST_RESTORE_BASELINE");}
 record OwnWorkbook(byte[] bytes) implements MultipartFile {
  public String getName(){return "file";}public String getOriginalFilename(){return "own-risk-import.xlsx";}public String getContentType(){return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";}public boolean isEmpty(){return bytes.length==0;}public long getSize(){return bytes.length;}public byte[] getBytes(){return bytes.clone();}public InputStream getInputStream(){return new ByteArrayInputStream(bytes);}public void transferTo(File destination){throw new UnsupportedOperationException("NO_UPLOAD_FILE_WRITE_IN_OWN_FIXTURE");}
 }
 public static void verify(ConfigurableApplicationContext context,Path root)throws Exception {
  require(Boolean.getBoolean("own.direct.main")&&Boolean.getBoolean("own.fixture.risk.import.verify")&&root.getFileName().toString().equals("b"),"OWN_FULL_IMPORT_FIXTURE_SCOPE_REQUIRED");
  var service=context.getBean(RiskLevelService.class);var controller=context.getBean(RiskLevelController.class);var type=AopUtils.getTargetClass(controller);boolean atomic=Boolean.getBoolean("own.fixture.risk.import.atomic");
  require(OriginalPublicRiskObservation.sha(type).equals(System.getProperty("own.fixture.risk.import.controller.sha256")),"EXACT_DECLARED_RISK_IMPORT_CONTROLLER_REQUIRED");
  var method=type.getDeclaredMethod("importExcel",MultipartFile.class);var tx=new AnnotationTransactionAttributeSource().getTransactionAttribute(method,type);
  if(atomic)require(tx!=null&&tx.rollbackOn(new Exception("OWN_CHECK"))&&controller instanceof Advised&&Arrays.stream(((Advised)controller).getAdvisors()).anyMatch(a->a.getAdvice() instanceof TransactionInterceptor),"REAL_OUTER_IMPORT_TRANSACTION_REQUIRED");else require(tx==null,"BASELINE_CONTROLLER_MUST_HAVE_NO_OUTER_TRANSACTION");
  long original=service.count();require(service.count(own())==0,"FRESH_OWN_IMPORT_NAMESPACE_REQUIRED");
  Path files=root.resolve("own-import-fixtures");controller.importExcel(new OwnWorkbook(Files.readAllBytes(files.resolve("risk-import-3001-valid.xlsx"))));
  var valid=service.list(own());require(valid.size()==3001&&service.count()==original+3001,"ACTUAL_NATIVE_TWO_BATCH_3001_IMPORT_REQUIRED");
  for(var row:valid)require(row.getCreateTime()!=null&&row.getPerson().equals("Own atom contact")&&row.getAnalysisUnit().equals("Own atomic unit")&&row.getRiskLevel().equals("1")&&row.getCoordinate().equals("113.0,32.0"),"ALL_VALID_BATCH_FIELDS_AND_CREATE_TIMES_REQUIRED");clean(service,3001,original);
  boolean rejected=false;try{controller.importExcel(new OwnWorkbook(Files.readAllBytes(files.resolve("risk-import-3001-last-invalid.xlsx"))));}catch(ServiceException failure){rejected=true;}
  require(rejected,"LAST_ROW_NATIVE_IMPORT_MUST_REJECT");long retained=service.count(own());require(retained==(atomic?0:3000)&&service.count()==original+retained,"WHOLE_FILE_IMPORT_COMMIT_BOUNDARY_REQUIRED");clean(service,retained,original);
  var result=new TreeMap<String,Object>();result.put("expectedOuterAtomicTransaction",atomic);result.put("controllerClassSHA256",OriginalPublicRiskObservation.sha(type));result.put("actualNativeExcelUtilAndServiceUsed",true);result.put("valid3001RowsAcrossTwoBatchesCommittedWithTimesAndFields",true);result.put("lastInvalidRowRejectedByNativeController",true);result.put("firstChunkRowsLeftAfterFailure",retained);result.put("wholeFileFailureRolledBack",retained==0);result.put("ownSamplesOnlyCleanedAndOriginalCountRestored",true);result.put("DDLOrOriginalDataChanged",false);result.put("multipartDirectBeanCallNotHTTP",true);
  Files.writeString(root.resolve("risk-whole-import-integration.json"),new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(result));
 }
}
