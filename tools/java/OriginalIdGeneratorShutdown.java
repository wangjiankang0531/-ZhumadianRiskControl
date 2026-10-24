package xnby.platform;

import java.io.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import org.springframework.context.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Close the pinned original heartbeat pool only when its original context closes. */
public final class OriginalIdGeneratorShutdown implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static final String OWNER="jnpf.database.config.IdGeneratorConfig";
 static final String PIN="b7ed1fb8a39644f77b90a385d04fe6945e8e88b02f8d68ca87e6a196ecb746a3";
 static String digest(Class<?> owner)throws Exception {
  MessageDigest hash=MessageDigest.getInstance("SHA-256");
  try(InputStream in=owner.getResourceAsStream("/"+OWNER.replace('.','/')+".class")) {
   if(in==null)throw new IllegalStateException("OWN_OWNER_RESOURCE_MISSING");
   byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1)hash.update(buf,0,n);
  }
  StringBuilder text=new StringBuilder();for(byte b:hash.digest())text.append(String.format(Locale.ROOT,"%02x",b&255));return text.toString();
 }
 static ScheduledThreadPoolExecutor existingOwnedPool(ConfigurableApplicationContext context)throws Exception {
  Class<?> owner=Class.forName(OWNER,false,context.getClassLoader());
  if(!PIN.equals(digest(owner)))throw new IllegalStateException("OWN_OWNER_CLASS_PIN_MISMATCH");
  String[] names=context.getBeanNamesForType(owner,false,false);
  if(names.length!=1||!context.getBeanFactory().containsSingleton(names[0]))throw new IllegalStateException("OWN_EXISTING_ORIGINAL_OWNER_REQUIRED");
  Field field=owner.getDeclaredField("scheduledThreadPoolExecutor");
  if(field.getType()!=ScheduledThreadPoolExecutor.class||!Modifier.isStatic(field.getModifiers()))throw new IllegalStateException("OWN_ORIGINAL_POOL_FIELD_SHAPE");
  field.setAccessible(true);Object pool=field.get(null);
  if(!(pool instanceof ScheduledThreadPoolExecutor))throw new IllegalStateException("OWN_ORIGINAL_POOL_INSTANCE_REQUIRED");
  return (ScheduledThreadPoolExecutor)pool;
 }
 static void write(Path root,String name,Properties result)throws IOException {
  try(OutputStream out=Files.newOutputStream(root.resolve(name),StandardOpenOption.CREATE_NEW)){result.store(out,"Pinned original ID worker lifecycle; no credentials or original rows");}
 }
 public void initialize(final ConfigurableApplicationContext context) {
  if(!Boolean.getBoolean("own.platform.manage.id-generator-shutdown"))return;
  boolean servlet=false;for(Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;
  if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.platform.root"));
  context.addApplicationListener(event->{
   boolean ready=event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context;
   boolean closed=event instanceof ContextClosedEvent&&((ContextClosedEvent)event).getApplicationContext()==context;
   if(!ready&&!closed)return;
   Properties result=new Properties();result.setProperty("event",ready?"ready":"contextClosed");
   try {
    ScheduledThreadPoolExecutor pool=existingOwnedPool(context);
    result.setProperty("originalOwnerClassPinned","true");result.setProperty("originalPoolShutdownBefore",Boolean.toString(pool.isShutdown()));
    result.setProperty("queueSizeBefore",Integer.toString(pool.getQueue().size()));result.setProperty("completedTasksBefore",Long.toString(pool.getCompletedTaskCount()));
    if(closed) {
     pool.shutdown();
     result.setProperty("normalShutdownRequested","true");
     result.setProperty("terminatedWithinTwoSeconds",Boolean.toString(pool.awaitTermination(2,TimeUnit.SECONDS)));
     result.setProperty("queueSizeAfter",Integer.toString(pool.getQueue().size()));
    } else result.setProperty("startupBehaviorModified","false");
   } catch(Exception e) {
    // Unknown versions/owners remain untouched; preserve ordinary context cleanup.
    result.setProperty("failureClass",e.getClass().getName());
    if(e instanceof InterruptedException)Thread.currentThread().interrupt();
   }
   try{write(root,ready?"id-worker-ready-observation.properties":"id-worker-close-observation.properties",result);}catch(IOException e){throw new IllegalStateException("OWN_ID_WORKER_RECEIPT_FAILED",e);}
  });
 }
}
