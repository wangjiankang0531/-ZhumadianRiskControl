package xnby.replica;
import java.lang.reflect.Method;
import java.nio.file.*;
import org.springframework.context.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.boot.web.context.WebServerInitializedEvent;

/** Bounded interactive-candidate lifecycle for either original Spring generation. */
public final class CandidateLifecycleObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;for(Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.candidate.root"));
  final int seconds=Integer.getInteger("own.candidate.maximum-seconds",3600);
  if(seconds<60||seconds>7200)throw new IllegalArgumentException("OWN_CANDIDATE_LEASE_RANGE");
  context.addApplicationListener(event->{
   try {
    if(event instanceof WebServerInitializedEvent&&((WebServerInitializedEvent)event).getApplicationContext()==context)Files.write(root.resolve("candidate-http-port.txt"),Integer.toString(((WebServerInitializedEvent)event).getWebServer().getPort()).getBytes("US-ASCII"));
    if(event instanceof ContextClosedEvent&&((ContextClosedEvent)event).getApplicationContext()==context)Files.write(root.resolve("candidate-context-closed.txt"),"closed\n".getBytes("US-ASCII"));
    if(event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context) {
     Files.write(root.resolve("candidate-ready.txt"),"ready\n".getBytes("US-ASCII"));
     Thread watcher=new Thread(()->{try{long end=System.nanoTime()+seconds*1000000000L;while(context.isActive()&&System.nanoTime()<end){if(Files.exists(root.resolve("own-stop-requested.txt"))){context.close();return;}Thread.sleep(200);}if(context.isActive())context.close();}catch(Exception e){throw new IllegalStateException("OWN_CANDIDATE_CLOSE_WATCHER_FAILED",e);}},"own-candidate-bounded-close-watcher");
     watcher.setDaemon(true);watcher.start();
    }
   }catch(Exception e){throw new IllegalStateException("OWN_CANDIDATE_LIFECYCLE_OBSERVATION_FAILED",e);}
  });
 }
}
