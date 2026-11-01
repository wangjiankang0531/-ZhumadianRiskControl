package xnby.replica;
import java.nio.file.*;import java.time.*;import java.time.temporal.ChronoUnit;import java.util.*;import java.sql.SQLException;
import com.iemp.endanger.server.hidden.entity.RiskLevel;import com.iemp.endanger.server.hidden.service.RiskLevelService;
import org.springframework.context.ConfigurableApplicationContext;import org.springframework.aop.framework.Advised;import org.springframework.aop.support.AopUtils;import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;import org.springframework.transaction.interceptor.TransactionInterceptor;
public final class OriginalRiskBatchTimeFixture {
 static RiskLevel row(int suffix,String name){RiskLevel x=new RiskLevel();x.setId("a531"+String.format("%028x",suffix));x.setDepartment("Own risk department A");x.setPerson("Own risk contact A");x.setAnalysisObject(name);x.setAnalysisUnit("Own batch time unit");x.setRiskLevel("1");x.setCoordinate("113.0,32.0");return x;}
 static void require(boolean b,String m){if(!b)throw new IllegalStateException(m);}
 public static void verify(ConfigurableApplicationContext context,Path root)throws Exception{
  require(Boolean.getBoolean("own.fixture.risk.batch.verify")&&Boolean.getBoolean("own.direct.main")&&root.getFileName().toString().equals("b"),"OWN_BATCH_FIXTURE_SCOPE_REQUIRED");
  RiskLevelService service=context.getBean(RiskLevelService.class);Class<?> type=AopUtils.getTargetClass(service);
  require(OriginalPublicRiskObservation.sha(type).equals(System.getProperty("own.fixture.risk.sort.sha256")),"EXACT_DECLARED_BATCH_SERVICE_REQUIRED");
  var method=type.getDeclaredMethod("saveBatch",Collection.class,int.class);var tx=new AnnotationTransactionAttributeSource().getTransactionAttribute(method,type);
  require(tx!=null&&tx.rollbackOn(new Exception("OWN_TEST"))&&AopUtils.isAopProxy(service)&&service instanceof Advised,"REAL_BATCH_TRANSACTION_ATTRIBUTE_REQUIRED");
  require(Arrays.stream(((Advised)service).getAdvisors()).anyMatch(a->a.getAdvice() instanceof TransactionInterceptor),"ACTUAL_TRANSACTION_INTERCEPTOR_REQUIRED");
  long before=service.count();RiskLevel preserved=row(520001,"Own explicit batch time"),filled=row(520002,"Own missing batch time"),first=row(520003,"Own duplicate batch first"),second=row(520003,"Own duplicate batch second");
  var ids=List.of(preserved.getId(),filled.getId(),first.getId());require(service.listByIds(ids).isEmpty(),"OWN_BATCH_SAMPLE_IDS_MUST_BE_NEW");
  LocalDateTime explicit=LocalDateTime.of(2020,1,2,3,4,5),start=LocalDateTime.now().truncatedTo(ChronoUnit.SECONDS);preserved.setCreateTime(explicit);
  require(service.saveBatch(List.of(preserved,filled),1),"ACTUAL_TWO_ROW_BATCH_REQUIRED");
  RiskLevel a=service.getById(preserved.getId()),b=service.getById(filled.getId());LocalDateTime end=LocalDateTime.now().truncatedTo(ChronoUnit.SECONDS);
  require(a!=null&&b!=null&&explicit.equals(a.getCreateTime())&&explicit.equals(preserved.getCreateTime()),"PROVIDED_BATCH_TIME_MUST_BE_PRESERVED");
  require(b.getCreateTime()!=null&&filled.getCreateTime()!=null&&!b.getCreateTime().isBefore(start.minusSeconds(1))&&!b.getCreateTime().isAfter(end.plusSeconds(1))&&Math.abs(ChronoUnit.NANOS.between(filled.getCreateTime(),b.getCreateTime()))<=1_000_000_000L,"MISSING_BATCH_TIME_MUST_MATCH_SERVER_TIME_AT_TIMESTAMP_ZERO_PRECISION");
  require(service.count()==before+2,"ACTUAL_BATCH_ROWS_MUST_COMMIT");
  require(service.removeByIds(List.of(preserved.getId(),filled.getId()))&&service.listByIds(ids).isEmpty()&&service.count()==before,"ONLY_OWN_TWO_NORMAL_SAMPLES_REMOVED");
  boolean duplicate=false;
  try{service.saveBatch(List.of(first,second),1);}catch(RuntimeException failure){for(Throwable c=failure;c!=null;c=c.getCause()){if(c instanceof SQLException){SQLException sql=(SQLException)c;for(int i=0;sql!=null&&i<8;i++,sql=sql.getNextException())if(sql.getErrorCode()==1062)duplicate=true;}}if(!duplicate)throw failure;}
  require(duplicate,"SECOND_BATCH_MUST_FAIL_REAL_DUPLICATE_KEY");
  require(service.getById(first.getId())==null&&service.count()==before,"BATCH_FAILURE_MUST_ROLL_BACK_EVERY_ROW");
  boolean empty=service.saveBatch(Collections.emptyList(),1);require(service.count()==before,"EMPTY_BATCH_MUST_NOT_WRITE");
  var result=new TreeMap<String,Object>();result.put("databaseTimestampFractionalScale",0);result.put("actualTimeMatchesSuppliedAtExistingModelPrecision",true);result.put("providedTimePreservedInActualDatabase",true);result.put("missingTimeFilledInActualDatabase",true);result.put("twoRowsCommittedThenOnlyOwnSamplesRemoved",true);result.put("secondBatchActualMySQLDuplicate1062",true);result.put("entireFailingBatchRolledBack",true);result.put("transactionProxyAndRollbackForExceptionVerified",true);result.put("emptyBatchOriginalResult",empty);result.put("originalCountRestored",true);result.put("DDLOrOwnershipChanged",false);result.put("onlySyntheticDatabaseUsed",true);
  Files.writeString(root.resolve("risk-batch-service-integration.json"),new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(result));
 }
}
