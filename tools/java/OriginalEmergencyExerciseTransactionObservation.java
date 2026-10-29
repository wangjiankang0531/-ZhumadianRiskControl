package xnby.replica;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.*;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.transaction.PlatformTransactionManager;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
/** Existing singleton/advisor metadata only; no service, transaction, SQL or network invocation. */
public final class OriginalEmergencyExerciseTransactionObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static String identifier(String name){return name!=null&&name.matches("`[a-z_][a-z0-9_]*`")?name.substring(1,name.length()-1):name;}
 public void initialize(ConfigurableApplicationContext context){
  String configured=System.getProperty("own.candidate.root");if(configured==null)return;
  final Path root;try{root=OriginalTransactionObservation.root(configured);}catch(Exception e){System.err.println("OWN_EXERCISE_OBSERVATION_OWNER_REJECTED "+e.getClass().getSimpleName());return;}
  AtomicBoolean once=new AtomicBoolean();context.addApplicationListener((ApplicationListener<ContextRefreshedEvent>)event->{
   if(event.getApplicationContext()!=context||once.get())return;
   if(context.getBeanFactory().getBeanNamesForType(com.iemp.endanger.server.hidden.service.CheckInventoryService.class,false,false).length==0)return;
   if(!once.compareAndSet(false,true))return;
   try{
    String service="com.iemp.endanger.server.emergency.service.EmergencyExerciseService";
    Map<String,Object> methods=new LinkedHashMap<>();
    methods.put("save",OriginalTransactionObservation.additional(context,service,"com.iemp.endanger.server.emergency.entity.EmergencyExerciseEntity",List.of("save")));
    methods.put("saveList",OriginalTransactionObservation.additional(context,service,"com.iemp.endanger.server.emergency.entity.dto.EmergencyExerciseSave",List.of("saveEmergencyExerciseList")));
    methods.put("delete",OriginalTransactionObservation.additional(context,service,"java.lang.String",List.of("delete")));
    String[] names=context.getBeanFactory().getBeanNamesForType(PlatformTransactionManager.class,false,false);OriginalTransactionObservation.require(names.length<=16,"BOUNDED_EXERCISE_MANAGERS");int managers=0;for(String name:names)if(context.getBeanFactory().getSingleton(name) instanceof PlatformTransactionManager)managers++;
    boolean matched=managers==1;for(Object value:methods.values())matched&=Boolean.TRUE.equals(((Map<?,?>)value).get("allMethodsHaveMatchingTransactionAdvisor"));
    var table=com.baomidou.mybatisplus.core.metadata.TableInfoHelper.getTableInfo(com.iemp.endanger.server.emergency.entity.EmergencyExerciseEntity.class);
    Map<String,Object> strategies=new LinkedHashMap<>();boolean strategyMatched=table!=null&&"emergency_exercise".equals(identifier(table.getTableName()))&&"id".equals(identifier(table.getKeyColumn()));
    if(table!=null)for(var field:table.getFieldList()){
     strategies.put(identifier(field.getColumn()),Map.of("mappedColumn",field.getColumn(),"updateStrategy",field.getUpdateStrategy().name(),"withUpdateFill",field.isWithUpdateFill()));
     strategyMatched&=field.getUpdateStrategy()==com.baomidou.mybatisplus.annotation.FieldStrategy.NOT_NULL&&!field.isWithUpdateFill();
    }
    strategyMatched&=strategies.keySet().equals(Set.of("emergency_plan_id","exercise_location","organize_department","commander_chief","exercise_time","participants","cooperating_unit","exercise_type","exercise_device","exercise_describe","exercise_special_situation","problems_andmeasures","created_at"));
    matched&=strategyMatched;
    Properties owner=new Properties();try(var in=Files.newInputStream(root.resolve("server-owner.properties"))){owner.load(in);}
    Map<String,Object> report=new LinkedHashMap<>();report.put("schema","xnby.emergency-exercise-transaction-observation.v1");report.put("exercise",methods);report.put("exerciseUpdateStrategies",strategies);report.put("nonNullUpdateStrategyMatched",strategyMatched);report.put("existingTransactionManagerCount",managers);report.put("allEmergencyExerciseMethodsAndManagerMatched",matched);report.put("PID",ProcessHandle.current().pid());report.put("run",root.getParent().getFileName().toString());report.put("ownerIdSHA256",OriginalTransactionObservation.sha(owner.getProperty("ownerId").getBytes(StandardCharsets.US_ASCII)));report.put("existingSingletonMetadataOnly",true);report.put("businessMethodsInvoked",false);report.put("SQLOrNetworkRequestsIssuedByObserver",false);report.put("actualRollbackOrHTTPOrAuthenticationVerified",false);
    byte[] raw=new ObjectMapper().writeValueAsBytes(report);OriginalTransactionObservation.require(raw.length<=65536,"EXERCISE_METADATA_SIZE_BOUND");Files.write(root.resolve("emergency-exercise-transaction-observation.json"),raw,StandardOpenOption.CREATE_NEW);
   }catch(Exception e){System.err.println("OWN_EMERGENCY_EXERCISE_OBSERVATION_FAILED "+e.getClass().getSimpleName());}
  });
 }
}
