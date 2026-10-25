package xnby.replica;

import java.lang.reflect.Method;
import java.nio.file.*;
import java.util.*;
import org.springframework.context.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.boot.web.context.WebServerInitializedEvent;

/** Explicit owned server lifecycle. Bounded interactive candidates keep their own initializer. */
public final class ServerLifecycleObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static Properties owner(Path root)throws Exception {
  Path marker=root.resolve("server-owner.properties");
  if(Files.isSymbolicLink(root)||!Files.isDirectory(root)||Files.isSymbolicLink(marker)||!Files.isRegularFile(marker)||Files.size(marker)>4096)throw new IllegalArgumentException("REGULAR_SERVER_OWNER_REQUIRED");
  Properties value=new Properties();try(java.io.InputStream in=Files.newInputStream(marker)){value.load(in);}
  if(value.size()!=2||!"zhumadian.original.server.owner.v1".equals(value.getProperty("schema")))throw new IllegalArgumentException("EXACT_SERVER_OWNER_REQUIRED");
  String expected=System.getProperty("own.server.owner");
  if(expected==null||!UUID.fromString(expected).toString().equals(expected)||!expected.equals(value.getProperty("ownerId")))throw new IllegalArgumentException("SERVER_OWNER_MISMATCH");
  return value;
 }
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;for(Method method:context.getClass().getMethods())if(method.getName().equals("getServletContext")&&method.getParameterCount()==0)servlet=true;if(!servlet)return;
  if(!"persistent".equals(System.getProperty("own.server.lifecycle")))throw new IllegalArgumentException("EXPLICIT_PERSISTENT_SERVER_MODE_REQUIRED");
  final Path root=Paths.get(System.getProperty("own.candidate.root")).toAbsolutePath().normalize();
  try{owner(root);if(Files.exists(root.resolve("own-stop-requested.txt")))throw new IllegalArgumentException("FRESH_SERVER_RUN_REQUIRED");}catch(Exception error){throw new IllegalArgumentException("SERVER_RUN_IDENTITY_REJECTED",error);}
  context.addApplicationListener(event->{
   try {
    if(event instanceof WebServerInitializedEvent&&((WebServerInitializedEvent)event).getApplicationContext()==context)Files.write(root.resolve("server-http-port.txt"),Integer.toString(((WebServerInitializedEvent)event).getWebServer().getPort()).getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
    if(event instanceof ContextClosedEvent&&((ContextClosedEvent)event).getApplicationContext()==context)Files.write(root.resolve("server-context-closed.txt"),"closed\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
    if(event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context) {
     Files.write(root.resolve("server-ready.txt"),"ready\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
     Thread watcher=new Thread(()->{
      try{while(context.isActive()){owner(root);if(Files.exists(root.resolve("own-stop-requested.txt"))){context.close();return;}Thread.sleep(250);}}
      catch(Exception error){try{Files.write(root.resolve("server-owner-failure.txt"),error.getClass().getName().getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){}if(context.isActive())context.close();}
     },"zhumadian-server-stop-watcher");watcher.setDaemon(true);watcher.start();
    }
   }catch(Exception error){throw new IllegalStateException("SERVER_LIFECYCLE_FAILED",error);}
  });
 }
}
