package xnby.replica;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.*;
import org.springframework.context.event.ContextRefreshedEvent;
import org.springframework.transaction.PlatformTransactionManager;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
/** Existing singleton/advisor metadata only; no service/transaction/SQL calls. */
public final class OriginalEventDisposalTransactionObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 public void initialize(ConfigurableApplicationContext context){
  String configured=System.getProperty("own.candidate.root");if(configured==null)return;
  final Path root;try{root=OriginalTransactionObservation.root(configured);}catch(Exception e){System.err.println("OWN_EVENT_DISPOSAL_OBSERVATION_OWNER_REJECTED "+e.getClass().getSimpleName());return;}
  AtomicBoolean once=new AtomicBoolean();context.addApplicationListener((ApplicationListener<ContextRefreshedEvent>)event->{
   if(event.getApplicationContext()!=context||once.get())return;
   if(context.getBeanFactory().getBeanNamesForType(com.iemp.endanger.server.hidden.service.CheckInventoryService.class,false,false).length==0)return;
   if(!once.compareAndSet(false,true))return;
   try{
    Map<String,Object> disposal=OriginalTransactionObservation.additional(context,"com.iemp.endanger.server.emergencyResponse.service.EventDisposalRecordService","com.iemp.endanger.server.emergencyResponse.entity.EventDisposalRecord",List.of("saveRecord"));
    String[] names=context.getBeanFactory().getBeanNamesForType(PlatformTransactionManager.class,false,false);OriginalTransactionObservation.require(names.length<=16,"BOUNDED_EVENT_DISPOSAL_MANAGERS");int managers=0;for(String name:names)if(context.getBeanFactory().getSingleton(name) instanceof PlatformTransactionManager)managers++;
    Properties owner=new Properties();try(var in=Files.newInputStream(root.resolve("server-owner.properties"))){owner.load(in);}
    Map<String,Object> report=new LinkedHashMap<>();report.put("schema","xnby.event-disposal-transaction-observation.v1");report.put("disposal",disposal);report.put("existingTransactionManagerCount",managers);report.put("allEventDisposalMethodsAndManagerMatched",Boolean.TRUE.equals(disposal.get("allMethodsHaveMatchingTransactionAdvisor"))&&managers==1);report.put("PID",ProcessHandle.current().pid());report.put("run",root.getParent().getFileName().toString());report.put("ownerIdSHA256",OriginalTransactionObservation.sha(owner.getProperty("ownerId").getBytes(StandardCharsets.US_ASCII)));report.put("existingSingletonMetadataOnly",true);report.put("businessMethodsInvoked",false);report.put("SQLOrNetworkRequestsIssuedByObserver",false);report.put("actualRollbackOrHTTPOrAuthenticationVerified",false);
    byte[] raw=new ObjectMapper().writeValueAsBytes(report);OriginalTransactionObservation.require(raw.length<=65536,"EVENT_DISPOSAL_METADATA_SIZE_BOUND");Files.write(root.resolve("event-disposal-transaction-observation.json"),raw,StandardOpenOption.CREATE_NEW);
   }catch(Exception e){System.err.println("OWN_EVENT_DISPOSAL_OBSERVATION_FAILED "+e.getClass().getSimpleName());}
  });
 }
}
