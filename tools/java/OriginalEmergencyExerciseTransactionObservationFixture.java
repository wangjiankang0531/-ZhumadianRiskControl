package xnby.replica;
import com.fasterxml.jackson.databind.*;
import com.iemp.endanger.server.hidden.service.impl.CheckInventoryServiceImpl;
import com.iemp.endanger.server.emergency.service.EmergencyExerciseService;
import com.iemp.endanger.server.emergency.controller.EmergencyExerciseController;
import com.iemp.endanger.server.emergency.entity.EmergencyExerciseEntity;
import org.springframework.context.annotation.*;
import org.springframework.context.support.GenericApplicationContext;
import org.springframework.aop.framework.ProxyFactory;
import org.springframework.transaction.*;
import org.springframework.transaction.annotation.EnableTransactionManagement;
import org.springframework.transaction.interceptor.*;
import org.springframework.transaction.support.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
@SuppressWarnings({"removal","unchecked","rawtypes"})
public final class OriginalEmergencyExerciseTransactionObservationFixture {
 @Configuration(proxyBeanMethods=false) @EnableTransactionManagement(proxyTargetClass=true)
 public static class TxConfig {}
 static final class NoCallsManager extends AbstractPlatformTransactionManager {
  int calls;protected Object doGetTransaction(){calls++;throw new IllegalStateException("NO_TRANSACTION_INVOCATION");}
  protected void doBegin(Object t,TransactionDefinition d){calls++;throw new IllegalStateException("NO_BEGIN");}
  protected void doCommit(DefaultTransactionStatus s){calls++;throw new IllegalStateException("NO_COMMIT");}
  protected void doRollback(DefaultTransactionStatus s){calls++;throw new IllegalStateException("NO_ROLLBACK");}
 }
 static void need(boolean v,String why){if(!v)throw new IllegalStateException(why);}
 static Object create(Class<?> cls){try{return cls.getConstructor(com.iemp.endanger.base.service.BaseFileService.class).newInstance(new com.iemp.endanger.base.service.impl.BaseFileServiceImpl());}catch(Exception e){throw new IllegalStateException(e);}}
 static Object mapper(Class<?> cls,AtomicInteger calls){return Proxy.newProxyInstance(cls.getClassLoader(),new Class<?>[]{cls},(o,m,a)->{if(m.getDeclaringClass()==Object.class)return switch(m.getName()){case "hashCode"->System.identityHashCode(o);case "equals"->o==a[0];case "toString"->"OWN_METADATA_ONLY_MAPPER";default->null;};calls.incrementAndGet();throw new IllegalStateException("NO_MAPPER_CALL");});}
 public static void main(String[] args)throws Exception{
  need(args.length==3,"FRESH_ROOT_MODE_EXPECTED_CLASS_SHA");Path root=Path.of(args[0]).toRealPath();boolean candidate=args[1].equals("candidate");need(candidate||args[1].equals("original"),"EXACT_MODE");var boundary=new OriginalProcessBoundary(root,Set.of(),false);System.setSecurityManager(boundary);var denied=boundary.deniedCounts();ObjectMapper json=new ObjectMapper();List<Object> cases=new ArrayList<>();Class<?> impl=Class.forName("com.iemp.endanger.server.emergency.service.impl.EmergencyExerciseServiceImpl");
  for(String mode:List.of("autoproxy","no-manager","unproxied","no-attributes","unchecked-only","duplicate-services","duplicate-managers","missing-service","missing-save-advisor","missing-bulk-advisor","missing-delete-advisor","bad-strategy","autoproxy-quoted","bad-column-format")){
   var cfg=new com.baomidou.mybatisplus.core.MybatisConfiguration();var global=new com.baomidou.mybatisplus.core.config.GlobalConfig();var db=new com.baomidou.mybatisplus.core.config.GlobalConfig.DbConfig();if(mode.equals("autoproxy-quoted"))db.setColumnFormat("`%s`");if(mode.equals("bad-column-format"))db.setColumnFormat("[%s]");if(mode.equals("bad-strategy"))db.setUpdateStrategy(com.baomidou.mybatisplus.annotation.FieldStrategy.ALWAYS);global.setDbConfig(db);com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils.setGlobalConfig(cfg,global);var assistant=new org.apache.ibatis.builder.MapperBuilderAssistant(cfg,"OWN_METADATA_ONLY");assistant.setCurrentNamespace("com.iemp.endanger.server.emergency.mapper.EmergencyExerciseMapper");com.baomidou.mybatisplus.core.metadata.TableInfoHelper.initTableInfo(assistant,EmergencyExerciseEntity.class);
   Path folder=root.resolve(mode+"/Application/UserData/OriginalServer/runs/j1/b");Files.createDirectories(folder);String owner=UUID.randomUUID().toString();Files.writeString(folder.resolve("server-owner.properties"),"schema=zhumadian.original.server.owner.v1\nownerId="+owner+"\n");System.setProperty("own.candidate.root",folder.toString());NoCallsManager manager=new NoCallsManager();AtomicInteger mapperCalls=new AtomicInteger();boolean auto=Set.of("autoproxy","no-manager","duplicate-services","duplicate-managers","missing-service","bad-strategy","autoproxy-quoted","bad-column-format").contains(mode);
   try(GenericApplicationContext context=auto?new AnnotationConfigApplicationContext():new GenericApplicationContext()){
    context.getBeanFactory().registerSingleton("inventory",new CheckInventoryServiceImpl(null,null));
    if(!mode.equals("no-manager"))context.getBeanFactory().registerSingleton("transactionManager",manager);
    if(mode.equals("duplicate-managers"))context.getBeanFactory().registerSingleton("otherTransactionManager",new NoCallsManager());
    if(auto){((AnnotationConfigApplicationContext)context).register(TxConfig.class);for(String name:List.of("EmergencyExerciseMapper")){Class cls=Class.forName("com.iemp.endanger.server.emergency.mapper."+name);context.registerBean(name,cls,()->mapper(cls,mapperCalls));}}
    if(!mode.equals("missing-service")){
     if(auto){context.registerBean("disposal",(Class)impl,()->create(impl));if(mode.equals("duplicate-services"))context.registerBean("otherTeam",(Class)impl,()->create(impl));}
     else{Object bean=create(impl);if(!mode.equals("unproxied")){ProxyFactory proxy=new ProxyFactory(bean);proxy.setProxyTargetClass(true);TransactionAttributeSource source=(m,t)->{
      if(mode.equals("no-attributes")||!Set.of("save","saveEmergencyExerciseList","delete").contains(m.getName())||m.getParameterCount()!=1)return null;
      String absent=mode.equals("missing-save-advisor")?"save":mode.equals("missing-bulk-advisor")?"saveEmergencyExerciseList":mode.equals("missing-delete-advisor")?"delete":"";
      if(m.getName().equals(absent))return null;
      if(mode.equals("unchecked-only"))return new DefaultTransactionAttribute(TransactionDefinition.PROPAGATION_REQUIRED);
      RuleBasedTransactionAttribute attr=new RuleBasedTransactionAttribute();attr.setRollbackRules(List.of(new RollbackRuleAttribute(Exception.class)));return attr;
     };proxy.addAdvice(new TransactionInterceptor(manager,source));bean=proxy.getProxy();}context.getBeanFactory().registerSingleton("disposal",bean);}
    }
    new OriginalEmergencyExerciseTransactionObservation().initialize(context);context.refresh();Path output=folder.resolve("emergency-exercise-transaction-observation.json");JsonNode report=json.readTree(output.toFile());boolean expected=candidate&&Set.of("autoproxy","autoproxy-quoted").contains(mode);need(report.path("allEmergencyExerciseMethodsAndManagerMatched").asBoolean()==expected,"EXACT_CONTEXT_CLASSIFICATION:"+mode);need(report.path("existingSingletonMetadataOnly").asBoolean()&&!report.path("businessMethodsInvoked").asBoolean()&&!report.path("SQLOrNetworkRequestsIssuedByObserver").asBoolean()&&manager.calls==0&&mapperCalls.get()==0,"NO_SERVICE_TX_OR_MAPPER_INVOCATION");
    if(!mode.equals("missing-service"))for(JsonNode row:report.path("exercise").path("save").path("services"))need(args[2].equals(row.path("targetClassSHA256").asText()),"EXACT_LOADED_SQL_CANDIDATE_OR_ORIGINAL_BYTES");
    need(report.path("nonNullUpdateStrategyMatched").asBoolean()==(!mode.equals("bad-strategy")&&!mode.equals("bad-column-format"))&&report.path("exerciseUpdateStrategies").size()==13,"ACTUAL_TABLEINFO_FIELD_STRATEGY_GUARD");
    if(mode.startsWith("missing-")&&mode.endsWith("-advisor"))for(String group:List.of("save","saveList","delete")){
     String absent=mode.equals("missing-save-advisor")?"save":mode.equals("missing-bulk-advisor")?"saveList":"delete";
     need(report.path("exercise").path(group).path("allMethodsHaveMatchingTransactionAdvisor").asBoolean()==!group.equals(absent),"ISOLATED_MISSING_METHOD_ADVISOR:"+group);
    }
    need(report.path("ownerIdSHA256").asText().equals(OriginalTransactionObservation.sha(owner.getBytes(java.nio.charset.StandardCharsets.US_ASCII))),"EXACT_OWNER");byte[] first=Files.readAllBytes(output);context.publishEvent(new org.springframework.context.event.ContextRefreshedEvent(context));need(Arrays.equals(first,Files.readAllBytes(output)),"ONCE_PER_CONTEXT");cases.add(Map.of("mode",mode,"allMatched",expected,"actualSpringAutoproxyInfrastructure",auto,"transactionCalls",manager.calls,"mapperCalls",mapperCalls.get()));
   }
  }
  System.clearProperty("own.candidate.root");List<Object> contracts=new ArrayList<>();
  for(String entry:List.of("save","saveList","removeById"))for(boolean value:List.of(false,true)){
   String method=entry.equals("saveList")?"saveEmergencyExerciseList":entry.equals("removeById")?"delete":"save";
   Object argument=entry.equals("saveList")?new com.iemp.endanger.server.emergency.entity.dto.EmergencyExerciseSave():entry.equals("removeById")?"OWN_EXERCISE_ID":new EmergencyExerciseEntity();
   Class<?> parameter=argument.getClass();AtomicInteger calls=new AtomicInteger();EmergencyExerciseService stub=(EmergencyExerciseService)Proxy.newProxyInstance(EmergencyExerciseService.class.getClassLoader(),new Class<?>[]{EmergencyExerciseService.class},(o,m,a)->{need(m.getName().equals(method)&&a.length==1&&a[0]==argument,"CLOSED_CONTROLLER_CONTRACT");calls.incrementAndGet();return value;});EmergencyExerciseController controller=new EmergencyExerciseController();Field f=EmergencyExerciseController.class.getDeclaredField("service");f.setAccessible(true);f.set(controller,stub);Object response=EmergencyExerciseController.class.getMethod(entry,parameter).invoke(controller,argument);JsonNode wire=json.readTree(json.writeValueAsBytes(response));need(wire.has("code")&&wire.path("code").isInt()&&wire.path("code").asInt()==0&&wire.path("data").isBoolean()&&wire.path("data").asBoolean()==value&&calls.get()==1,"ACTUAL_ORIGINAL_CONTROLLER_BOOLEAN_ENVELOPE");contracts.add(Map.of("method",entry,"code",0,"data",value,"originalControllerAndResponseSerialization",true,"serviceMockOnly",true));
  }
  need(denied.equals(boundary.deniedCounts())&&System.getSecurityManager()==boundary,"NO_UNEXPECTED_NETWORK_OR_PROCESS");Files.writeString(root.resolve("result.json"),json.writeValueAsString(Map.of("mode",args[1],"contexts",cases,"controllerContracts",contracts,"noSQLNetworkOrProductionRuntime",true,"noBusinessCallsByObserver",true,"controllerUsesMockServiceOnly",true,"candidateServiceBytes",args[2],"fullCloneReady",false))+"\n",StandardOpenOption.CREATE_NEW);System.out.println("EMERGENCY_EXERCISE_OBSERVER_CONTEXTS=14 CONTROLLER_BOOLEAN_CONTRACTS=6 MODE="+args[1]);
 }
}
