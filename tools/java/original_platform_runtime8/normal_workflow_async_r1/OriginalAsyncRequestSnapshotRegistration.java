package xnby.platform;

import java.io.*;import java.lang.reflect.Field;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.security.MessageDigest;import java.util.*;import java.util.concurrent.ThreadPoolExecutor;import java.util.concurrent.atomic.AtomicLong;
import org.springframework.beans.BeansException;import org.springframework.beans.factory.config.BeanPostProcessor;import org.springframework.context.*;import org.springframework.core.task.TaskDecorator;import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;import org.springframework.web.context.request.*;

/** Retain the exact original executor/decorator; replace only its live request view while the decorated job executes. */
public final class OriginalAsyncRequestSnapshotRegistration implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static final AtomicLong captured=new AtomicLong(),started=new AtomicLong(),finished=new AtomicLong(),active=new AtomicLong();static Path root;
 static void need(boolean value,String code){if(!value)throw new IllegalStateException(code);}
 static String sha(Class<?> type)throws Exception {MessageDigest digest=MessageDigest.getInstance("SHA-256");InputStream in=type.getResourceAsStream("/"+type.getName().replace('.','/')+".class");try{byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))>0)digest.update(buffer,0,n);}finally{in.close();}StringBuilder value=new StringBuilder();for(byte b:digest.digest())value.append(String.format(Locale.ROOT,"%02x",b&255));return value.toString();}
 static synchronized void receipt() {if(root==null)return;try{Files.write(root.resolve("async-request-snapshot-state.properties"),Arrays.asList("schema=xnby.original-async-request-metadata.v1","originalDecoratorRetained=true","capturedJobs="+captured.get(),"startedJobs="+started.get(),"finishedJobs="+finished.get(),"activeJobs="+active.get(),"requestHeaderOrTokenValuesRecorded=false"),StandardCharsets.US_ASCII);}catch(IOException failure){throw new IllegalStateException("ASYNC_METADATA_RECEIPT_FAILED",failure);}}
 public static TaskDecorator wrap(final TaskDecorator original){need(original!=null,"ORIGINAL_ASYNC_DECORATOR_REQUIRED");return new TaskDecorator(){public Runnable decorate(final Runnable task){
  RequestAttributes current=RequestContextHolder.getRequestAttributes();final javax.servlet.http.HttpServletRequest copy;
  try{copy=current instanceof ServletRequestAttributes?OriginalAsyncHttpMetadata.capture(((ServletRequestAttributes)current).getRequest()):null;}catch(Exception failure){throw new IllegalStateException("ASYNC_HTTP_METADATA_CAPTURE_FAILED",failure);}
  if(copy==null)return original.decorate(task);captured.incrementAndGet();
  return original.decorate(new Runnable(){public void run(){RequestAttributes before=RequestContextHolder.getRequestAttributes();ServletRequestAttributes snapshot=new ServletRequestAttributes(copy);started.incrementAndGet();active.incrementAndGet();
   try{RequestContextHolder.setRequestAttributes(snapshot);task.run();}
   finally{try{snapshot.requestCompleted();}finally{if(before==null)RequestContextHolder.resetRequestAttributes();else RequestContextHolder.setRequestAttributes(before);active.decrementAndGet();finished.incrementAndGet();receipt();}}
  }});
 }};}
 @Override public void initialize(ConfigurableApplicationContext context){
  need("true".equals(System.getProperty("own.async.request.snapshot.enabled")),"EXPLICIT_ASYNC_METADATA_REVISION_REQUIRED");root=Paths.get(System.getProperty("own.platform.root"));
  try{String expected=System.getProperty("own.async.original.config.sha256");need(expected!=null&&expected.equals(sha(Class.forName("jnpf.config.AsyncConfig"))),"EXACT_ORIGINAL_ASYNC_CONFIG_REQUIRED");}catch(Exception failure){throw new IllegalStateException("ORIGINAL_ASYNC_CONFIG_PIN_REJECTED",failure);}
  context.getBeanFactory().addBeanPostProcessor(new BeanPostProcessor(){private final Set<Object> seen=Collections.newSetFromMap(new IdentityHashMap<Object,Boolean>());
   @Override public Object postProcessAfterInitialization(Object bean,String name)throws BeansException {
    if(!name.equals("threadPoolTaskExecutor")||!(bean instanceof ThreadPoolTaskExecutor))return bean;
    synchronized(seen){if(!seen.add(bean))return bean;}
    ThreadPoolTaskExecutor executor=(ThreadPoolTaskExecutor)bean;need(executor.getCorePoolSize()==10&&executor.getMaxPoolSize()==50&&executor.getKeepAliveSeconds()==30&&executor.getThreadNamePrefix().equals("sysTaskExecutor")&&executor.getThreadPoolExecutor().getRejectedExecutionHandler() instanceof ThreadPoolExecutor.CallerRunsPolicy,"ORIGINAL_ASYNC_EXECUTOR_SETTINGS_REQUIRED");
    try{Field field=ThreadPoolTaskExecutor.class.getDeclaredField("taskDecorator");field.setAccessible(true);TaskDecorator original=(TaskDecorator)field.get(executor);executor.setTaskDecorator(wrap(original));receipt();}catch(Exception failure){throw new IllegalStateException("ORIGINAL_ASYNC_DECORATOR_INSTALL_FAILED",failure);}return bean;
   }
  });
 }
}
