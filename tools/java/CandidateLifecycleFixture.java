package xnby.replica;
import java.lang.reflect.*;
import java.nio.file.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.springframework.context.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Actual Spring event + file watcher test, without a Spring application or database. */
public final class CandidateLifecycleFixture {
 public interface ServletMarker{Object getServletContext();}
 static int checks;
 static void check(boolean yes){if(!yes)throw new AssertionError();checks++;}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath();System.setProperty("own.candidate.root",root.toString());
  final List<ApplicationListener> listeners=new ArrayList<>();final AtomicBoolean active=new AtomicBoolean(true);final AtomicInteger closes=new AtomicInteger();final ConfigurableApplicationContext[] holder=new ConfigurableApplicationContext[1];
  InvocationHandler handler=(proxy,method,values)->{
   switch(method.getName()){
    case "addApplicationListener":listeners.add((ApplicationListener)values[0]);return null;
    case "isActive":return active.get();
    case "close":if(active.compareAndSet(true,false)){closes.incrementAndGet();for(ApplicationListener l:listeners)l.onApplicationEvent(new ContextClosedEvent(holder[0]));}return null;
    case "getServletContext":return null;
    case "hashCode":return System.identityHashCode(proxy);
    case "equals":return proxy==values[0];
    case "toString":return "own-synthetic-context";
    default:return null;
   }
  };
  holder[0]=(ConfigurableApplicationContext)Proxy.newProxyInstance(CandidateLifecycleFixture.class.getClassLoader(),new Class<?>[]{ConfigurableApplicationContext.class,ServletMarker.class},handler);
  System.setProperty("own.candidate.maximum-seconds","0");boolean rejected=false;try{new CandidateLifecycleObservation().initialize(holder[0]);}catch(IllegalArgumentException expected){rejected=true;}check(rejected&&listeners.isEmpty());
  System.setProperty("own.candidate.maximum-seconds","43201");rejected=false;try{new CandidateLifecycleObservation().initialize(holder[0]);}catch(IllegalArgumentException expected){rejected=true;}check(rejected&&listeners.isEmpty());
  System.setProperty("own.candidate.maximum-seconds","43200");new CandidateLifecycleObservation().initialize(holder[0]);check(listeners.size()==1);
  ApplicationReadyEvent event=new ApplicationReadyEvent(new SpringApplication(),new String[0],holder[0],Duration.ZERO);
  for(ApplicationListener l:listeners)l.onApplicationEvent(event);
  check(Files.exists(root.resolve("candidate-ready.txt"))&&active.get());
  Files.write(root.resolve("own-stop-requested.txt"),"finish-own-fixture\n".getBytes("US-ASCII"));
  for(int i=0;i<100&&active.get();i++)Thread.sleep(20);
  check(!active.get()&&closes.get()==1&&Files.exists(root.resolve("candidate-context-closed.txt")));
  System.out.println("CANDIDATE_LIFECYCLE_FIXTURE_CHECKS="+checks);
 }
}
