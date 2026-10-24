package xnby.platform;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import javax.sql.DataSource;
import org.springframework.context.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Observe actual original datasource and closing threads, without replacing original beans. */
public final class PlatformWritableObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;
  for(java.lang.reflect.Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;
  if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.platform.root"));
  context.addApplicationListener(event->{
   try {
    if(event instanceof ApplicationReadyEvent&&((ApplicationReadyEvent)event).getApplicationContext()==context) {
     Properties result=new Properties();
     try(Connection c=context.getBean(DataSource.class).getConnection();Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@global.read_only,@@global.super_read_only,@@transaction_read_only,@@event_scheduler,DATABASE()")) {
      if(!r.next())throw new IllegalStateException("OWN_DATABASE_STATE_ROW_REQUIRED");
      result.setProperty("uuidMatches",Boolean.toString(r.getString(1).equals(System.getProperty("own.expected.database.uuid"))));
      result.setProperty("portMatches",Boolean.toString(r.getString(2).equals(System.getProperty("own.expected.database.port"))));
      result.setProperty("serverReadOnly",r.getString(3));result.setProperty("serverSuperReadOnly",r.getString(4));result.setProperty("transactionReadOnly",r.getString(5));
      result.setProperty("eventScheduler",r.getString(6));result.setProperty("databaseMatches","jnpf".equals(r.getString(7))?"true":"false");
      result.setProperty("jdbcReadOnly",Boolean.toString(c.isReadOnly()));
     }
     try(java.io.OutputStream output=Files.newOutputStream(root.resolve("actual-writable-datasource.properties"),StandardOpenOption.CREATE_NEW)){result.store(output,"Actual original platform datasource; no original records");}
    }
    if(event instanceof ContextClosedEvent&&((ContextClosedEvent)event).getApplicationContext()==context) {
     Thread observer=new Thread(()->{try{Thread.sleep(500);snapshot(root.resolve("closing-threads-500ms.private.log"));Thread.sleep(4500);snapshot(root.resolve("closing-threads-5s.private.log"));}catch(Exception e){throw new IllegalStateException("OWN_THREAD_OBSERVATION_FAILED",e);}},"own-closing-thread-observer");
     observer.setDaemon(true);observer.start();
    }
   } catch(Exception e){throw new IllegalStateException("OWN_WRITABLE_OBSERVATION_FAILED",e);}
  });
 }
 static void snapshot(Path destination)throws Exception {
  List<String> lines=new ArrayList<>();
  for(Map.Entry<Thread,StackTraceElement[]> row:Thread.getAllStackTraces().entrySet()) {
   Thread t=row.getKey();if(t.isDaemon())continue;
   lines.add("THREAD "+t.getName()+" STATE "+t.getState());
   for(StackTraceElement frame:row.getValue())lines.add("  "+frame.toString());
  }
  Files.write(destination,lines,StandardOpenOption.CREATE_NEW);
 }
}
