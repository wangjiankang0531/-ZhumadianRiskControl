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

/** Real Spring event API and owner/stop files; no original application or database. */
public final class ServerLifecycleFixture {
 public interface ServletMarker{Object getServletContext();}
 static int checks;
 static void check(boolean yes){if(!yes)throw new AssertionError();checks++;}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath();System.setProperty("own.candidate.root",root.toString());String id=UUID.randomUUID().toString();System.setProperty("own.server.owner",id);
  final List<ApplicationListener> listeners=new ArrayList<>();final AtomicBoolean active=new AtomicBoolean(true);final AtomicInteger closes=new AtomicInteger();final ConfigurableApplicationContext[] holder=new ConfigurableApplicationContext[1];
  InvocationHandler handler=(proxy,method,values)->{
   switch(method.getName()){
    case "addApplicationListener":listeners.add((ApplicationListener)values[0]);return null;
    case "isActive":return active.get();
    case "close":if(active.compareAndSet(true,false)){closes.incrementAndGet();for(ApplicationListener listener:listeners)listener.onApplicationEvent(new ContextClosedEvent(holder[0]));}return null;
    case "getServletContext":return null;
    case "hashCode":return System.identityHashCode(proxy);
    case "equals":return proxy==values[0];
    case "toString":return "owned-server-fixture";
    default:return null;
   }
  };
  holder[0]=(ConfigurableApplicationContext)Proxy.newProxyInstance(ServerLifecycleFixture.class.getClassLoader(),new Class<?>[]{ConfigurableApplicationContext.class,ServletMarker.class},handler);
  boolean rejected=false;try{new ServerLifecycleObservation().initialize(holder[0]);}catch(IllegalArgumentException expected){rejected=true;}check(rejected&&listeners.isEmpty());
  System.setProperty("own.server.lifecycle","persistent");rejected=false;try{new ServerLifecycleObservation().initialize(holder[0]);}catch(IllegalArgumentException expected){rejected=true;}check(rejected&&listeners.isEmpty());
  Files.write(root.resolve("server-owner.properties"),("schema=zhumadian.original.server.owner.v1\nownerId="+UUID.randomUUID()+"\n").getBytes("US-ASCII"));
  rejected=false;try{new ServerLifecycleObservation().initialize(holder[0]);}catch(IllegalArgumentException expected){rejected=true;}check(rejected&&listeners.isEmpty());
  Files.write(root.resolve("server-owner.properties"),("schema=zhumadian.original.server.owner.v1\nownerId="+id+"\n").getBytes("US-ASCII"));
  new ServerLifecycleObservation().initialize(holder[0]);check(listeners.size()==1);
  ApplicationReadyEvent ready=new ApplicationReadyEvent(new SpringApplication(),new String[0],holder[0],Duration.ZERO);for(ApplicationListener listener:listeners)listener.onApplicationEvent(ready);
  Thread.sleep(350);check(Files.exists(root.resolve("server-ready.txt"))&&active.get()&&closes.get()==0);
  Files.write(root.resolve("own-stop-requested.txt"),"stop-owned-server-fixture\n".getBytes("US-ASCII"));for(int i=0;i<100&&active.get();i++)Thread.sleep(20);
  check(!active.get()&&closes.get()==1&&Files.exists(root.resolve("server-context-closed.txt")));
  System.out.println("SERVER_LIFECYCLE_FIXTURE_CHECKS="+checks);
 }
}
