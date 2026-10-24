package xnby.platform;
import xnby.compat.Java8IO;
import org.springframework.context.*;
import org.springframework.context.event.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.boot.web.context.WebServerInitializedEvent;
import org.springframework.beans.factory.support.BeanDefinitionRegistry;
import org.springframework.scheduling.annotation.ScheduledAnnotationBeanPostProcessor;
import java.nio.file.*;
import java.util.*;

/** Original Boot2 context observation, no replacement auth/data beans or original service invocation. */
public final class PlatformStartupObservation implements ApplicationContextInitializer<ConfigurableApplicationContext>{
 public void initialize(ConfigurableApplicationContext context){
  Path root=Paths.get(System.getProperty("own.platform.root"));
  try{
   List<String> loaders=new ArrayList<>();ObservedPlatformBeanNameGenerator.loader(loaders,"context",context.getClassLoader());ObservedPlatformBeanNameGenerator.loader(loaders,"TCCL",Thread.currentThread().getContextClassLoader());
   Files.write(root.resolve("initial-context-loaders.tsv"),loaders,StandardOpenOption.CREATE_NEW);
  }catch(Exception error){throw new IllegalStateException("OWN_PLATFORM_LOADER_OBSERVATION_FAILED",error);}
  context.addBeanFactoryPostProcessor(factory->{
   List<String> definitions=new ArrayList<>();
   try{
    if(factory instanceof BeanDefinitionRegistry){BeanDefinitionRegistry registry=(BeanDefinitionRegistry)factory;for(String name:factory.getBeanNamesForType(ScheduledAnnotationBeanPostProcessor.class,true,false))registry.removeBeanDefinition(name);}
    for(String name:factory.getBeanDefinitionNames()){org.springframework.beans.factory.config.BeanDefinition definition=factory.getBeanDefinition(name);definitions.add(name+"\t"+definition.getBeanClassName()+"\t"+definition.getFactoryBeanName()+"\t"+definition.getFactoryMethodName());}
    Collections.sort(definitions);Files.write(root.resolve("platform-bean-definitions.tsv"),definitions);
   }catch(Exception e){throw new IllegalStateException("OWN_PLATFORM_BEAN_OBSERVATION_FAILED",e);}
  });
  if(Arrays.stream(context.getClass().getMethods()).noneMatch(m->m.getName().equals("getServletContext")&&m.getParameterCount()==0))return;
  context.addApplicationListener(event->{
   try{
    if(event instanceof WebServerInitializedEvent&&((WebServerInitializedEvent)event).getApplicationContext()==context)Java8IO.writeString(root.resolve("own-platform-http-port.txt"),Integer.toString(((WebServerInitializedEvent)event).getWebServer().getPort()));
    if(event instanceof ContextRefreshedEvent&&((ContextRefreshedEvent)event).getApplicationContext()==context)Java8IO.writeString(root.resolve("own-platform-context-refreshed.txt"),"refreshed\n");
    if(event instanceof ContextClosedEvent&&((ContextClosedEvent)event).getApplicationContext()==context)Java8IO.writeString(root.resolve("own-platform-context-closed.txt"),"closed\n");
    if(event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context){
     Java8IO.writeString(root.resolve("own-platform-ready.txt"),"ready\n");
     Thread watcher=new Thread(()->{try{for(int i=0;i<1800;i++){if(Files.exists(root.resolve("own-stop-requested.txt"))){context.close();return;}Thread.sleep(100);}}catch(Exception e){throw new IllegalStateException(e);}});watcher.setDaemon(true);watcher.start();
    }
   }catch(Exception e){throw new IllegalStateException("OWN_PLATFORM_LIFECYCLE_OBSERVATION_FAILED",e);}
  });
 }
}
