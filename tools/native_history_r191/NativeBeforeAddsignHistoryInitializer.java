package xnby.platform.history;

import org.apache.ibatis.session.Configuration;
import org.apache.ibatis.session.SqlSessionFactory;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.*;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Add one targeted mapper interceptor to existing factories, without a new datasource. */
public final class NativeBeforeAddsignHistoryInitializer implements ApplicationContextInitializer<ConfigurableApplicationContext> {
  @Override public void initialize(ConfigurableApplicationContext context) {
    if(!Boolean.getBoolean("own.workflow.before-addsign.history.enabled"))
      throw new IllegalStateException("EXPLICIT_NATIVE_BEFORE_ADDSIGN_HISTORY_REQUIRED");
    final Path root;
    try {
      root=Paths.get(System.getProperty("own.platform.root")).toRealPath();
      if(!Files.isRegularFile(root.resolve("server-owner.properties")))
        throw new IllegalStateException("OWN_PLATFORM_RUNTIME_OWNER_REQUIRED");
      String resource="jnpf/engine/service/impl/FlowTaskNewServiceImpl.class";
      try(InputStream input=getClass().getClassLoader().getResourceAsStream(resource)){
        if(input==null)throw new IllegalStateException("ORIGINAL_NATIVE_WORKFLOW_SERVICE_REQUIRED");
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;
        while((count=input.read(buffer))!=-1){if(bytes.size()+count>262144)throw new IllegalStateException("ORIGINAL_NATIVE_WORKFLOW_SERVICE_SIZE_BOUND");bytes.write(buffer,0,count);}
        StringBuilder digest=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray()))digest.append(String.format(Locale.ROOT,"%02x",b&255));
        if(!digest.toString().equals("60e9d98921b21add75b5148af2b671e9302683d536896ce0d1f314fd1f0a709a"))
          throw new IllegalStateException("ORIGINAL_NATIVE_WORKFLOW_SERVICE_PIN_MISMATCH");
      }
    }catch(Exception failure){throw new IllegalArgumentException("NATIVE_HISTORY_SCOPE_OR_MODEL_REJECTED",failure);}
    Set<Configuration> installed=Collections.newSetFromMap(new IdentityHashMap<>());
    AtomicInteger factories=new AtomicInteger();
    context.addBeanFactoryPostProcessor(factory->factory.addBeanPostProcessor(new BeanPostProcessor(){
      @Override public Object postProcessAfterInitialization(Object bean,String name){
        if(bean instanceof SqlSessionFactory){
          Configuration configuration=((SqlSessionFactory)bean).getConfiguration();
          synchronized(installed){if(installed.add(configuration)){
            if(configuration.getInterceptors().stream().anyMatch(i->i instanceof OriginalBeforeAddsignHistoryInterceptor))
              throw new IllegalStateException("DUPLICATE_NATIVE_HISTORY_INTERCEPTOR_REFUSED");
            configuration.addInterceptor(new OriginalBeforeAddsignHistoryInterceptor());
            factories.incrementAndGet();
          }}
        }
        return bean;
      }
    }));
    context.addApplicationListener(event->{if(event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context){
      try{
        if(factories.get()<1)throw new IllegalStateException("NATIVE_HISTORY_FACTORY_INTERCEPTOR_NOT_INSTALLED");
        String report="schema=xnby.native-before-addsign-history.v1\ninstalled=true\nfactories="+factories.get()+"\noriginalEntityMapperAndServicePinned=true\noriginalTransactionAndConnectionUsed=true\nnewDatasourceOrDDL=false\nnormalRoleUIAcceptanceProvenByStartup=false\n";
        Files.write(root.resolve("before-addsign-history-ready.properties"),report.getBytes(StandardCharsets.US_ASCII),StandardOpenOption.CREATE_NEW);
      }catch(Exception failure){throw new IllegalStateException("NATIVE_HISTORY_READINESS_FAILED",failure);}
    }});
  }
}
