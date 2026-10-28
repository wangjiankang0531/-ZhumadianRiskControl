package xnby.replica;
import com.fasterxml.jackson.databind.*;
import com.iemp.endanger.server.hidden.service.CheckInventoryService;
import com.iemp.endanger.server.hidden.service.impl.CheckInventoryServiceImpl;
import com.iemp.endanger.server.work.service.impl.WorkReservationBaseServiceImpl;
import com.iemp.endanger.server.safetyBasic.service.impl.ThirdPartyUnitInfoServiceImpl;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.aop.framework.ProxyFactory;
import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;
import org.springframework.transaction.interceptor.*;
import java.nio.file.*;
import java.util.*;

/** Existing singleton/advisor metadata only, never invokes a business method. */
@SuppressWarnings("removal")
public final class OriginalWorkTransactionObservationFixture {
 static void need(boolean yes,String code){if(!yes)throw new IllegalStateException(code);}
 static Object advised(Object target,OriginalTransactionObservationFixture.NoCallsTxManager manager,boolean attributes){
  var f=new ProxyFactory(target);f.setProxyTargetClass(true);TransactionAttributeSource source=attributes?new AnnotationTransactionAttributeSource():(method,type)->null;f.addAdvice(new TransactionInterceptor(manager,source));return f.getProxy();
 }
 public static void main(String[] args)throws Exception{
  need(args.length==1,"FRESH_OWN_FIXTURE_ROOT");Path root=Path.of(args[0]).toRealPath();var boundary=new OriginalProcessBoundary(root,Set.of(),false);System.setSecurityManager(boundary);var before=boundary.deniedCounts();var results=new ArrayList<Object>();var json=new ObjectMapper();
  for(String mode:List.of("matching","unproxied","no-attributes","missing-singletons")){
   Path folder=root.resolve(mode+"/Application/UserData/OriginalServer/runs/j1/b");Files.createDirectories(folder);String owner=UUID.randomUUID().toString();Files.writeString(folder.resolve("server-owner.properties"),"schema=zhumadian.original.server.owner.v1\nownerId="+owner+"\n");System.setProperty("own.candidate.root",folder.toString());
   var manager=new OriginalTransactionObservationFixture.NoCallsTxManager();
   try(var context=new GenericApplicationContext()){
    var original=new CheckInventoryServiceImpl(null,null);ProxyFactory inventory=new ProxyFactory(original);inventory.setInterfaces(CheckInventoryService.class);inventory.addAdvice(new TransactionInterceptor(manager,new AnnotationTransactionAttributeSource()));context.getBeanFactory().registerSingleton("inventory",inventory.getProxy());context.getBeanFactory().registerSingleton("transactionManager",manager);
    if(!mode.equals("missing-singletons")){
     var ctor=WorkReservationBaseServiceImpl.class.getDeclaredConstructors()[0];Object reservation=ctor.newInstance(new Object[ctor.getParameterCount()]);Object third=new ThirdPartyUnitInfoServiceImpl();
     if(!mode.equals("unproxied")){reservation=advised(reservation,manager,mode.equals("matching"));third=advised(third,manager,mode.equals("matching"));}
     context.getBeanFactory().registerSingleton("reservation",reservation);context.getBeanFactory().registerSingleton("thirdParty",third);
    }
    new OriginalTransactionObservation().initialize(context);context.refresh();Path report=folder.resolve("work-services-transaction-observation.json");JsonNode value=json.readTree(report.toFile());boolean expected=mode.equals("matching");
    for(String key:List.of("reservation","thirdParty"))need(value.path(key).path("allMethodsHaveMatchingTransactionAdvisor").asBoolean()==expected,"CORRECT_EXISTING_ADVISOR_CLASSIFICATION:"+mode+":"+key);
    need(value.path("existingSingletonMetadataOnly").asBoolean()&&!value.path("businessMethodsInvoked").asBoolean()&&!value.path("SQLOrNetworkRequestsIssuedByObserver").asBoolean()&&manager.calls==0,"NO_BUSINESS_METHOD_OR_TRANSACTION");byte[] first=Files.readAllBytes(report);context.publishEvent(new org.springframework.context.event.ContextRefreshedEvent(context));need(Arrays.equals(first,Files.readAllBytes(report)),"ONE_REPORT_NO_REPLAY");
    var row=new LinkedHashMap<String,Object>();row.put("mode",mode);row.put("matching",expected);row.put("transactionCalls",manager.calls);
    if(!mode.equals("missing-singletons"))for(String key:List.of("reservation","thirdParty"))row.put(key+"ClassSHA256",value.path(key).path("services").get(0).path("targetClassSHA256").asText());results.add(row);
   }
  }
  System.clearProperty("own.candidate.root");need(before.equals(boundary.deniedCounts()),"NO_UNEXPECTED_IO");Files.writeString(root.resolve("result.json"),json.writeValueAsString(Map.of("contexts",results,"noOriginalServiceMethodsOrTransactionsInvoked",true,"noNetworkOrDatabase",true))+"\n",StandardOpenOption.CREATE_NEW);System.out.println("WORK_TRANSACTION_OBSERVER_CONTEXTS=4");
 }
}
