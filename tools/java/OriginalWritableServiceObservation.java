package xnby.replica;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import org.springframework.context.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Read actual original services and writable-clone identity; expose no business records. */
public final class OriginalWritableServiceObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;for(java.lang.reflect.Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.candidate.root"));
  context.addApplicationListener(event->{
   if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;
   Properties result=new Properties();
   try {
    javax.sql.DataSource ds=context.getBean(javax.sql.DataSource.class);
    try(Connection c=ds.getConnection();Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT DATABASE(),@@server_uuid,@@port,@@transaction_read_only,@@global.super_read_only")) {
     if(!r.next())throw new IllegalStateException("OWN_WRITABLE_IDENTITY_ROW");
     result.setProperty("databaseMatches",Boolean.toString("tj_endanger".equals(r.getString(1))));result.setProperty("uuidMatches",Boolean.toString(System.getProperty("own.expected.database.uuid").equals(r.getString(2))));result.setProperty("portMatches",Boolean.toString(System.getProperty("own.expected.database.port").equals(r.getString(3))));
     result.setProperty("transactionReadOnly",r.getString(4));result.setProperty("serverSuperReadOnly",r.getString(5));result.setProperty("jdbcReadOnly",Boolean.toString(c.isReadOnly()));
    }
    for(String name:new String[]{"checkItemsServiceImpl","checkPlanServiceImpl"}) {
     Object bean=context.getBean(name);result.setProperty(name+".count",String.valueOf(((Number)bean.getClass().getMethod("count").invoke(bean)).longValue()));
    }
    Class<?> wrapper=Class.forName("com.baomidou.mybatisplus.core.conditions.Wrapper");
    for(String name:new String[]{"checkPlanItemsMapper","organizeMapper"}) {
     Object bean=context.getBean(name);result.setProperty(name+".count",String.valueOf(((Number)bean.getClass().getMethod("selectCount",wrapper).invoke(bean,new Object[]{null})).longValue()));
    }
    result.setProperty("passed",Boolean.toString("true".equals(result.getProperty("databaseMatches"))&&"true".equals(result.getProperty("uuidMatches"))&&"true".equals(result.getProperty("portMatches"))&&"0".equals(result.getProperty("transactionReadOnly"))&&"0".equals(result.getProperty("serverSuperReadOnly"))&&"false".equals(result.getProperty("jdbcReadOnly"))&&"266".equals(result.getProperty("checkItemsServiceImpl.count"))&&"145".equals(result.getProperty("checkPlanServiceImpl.count"))&&"3306".equals(result.getProperty("checkPlanItemsMapper.count"))&&"12".equals(result.getProperty("organizeMapper.count"))));
   }catch(Exception e){result.setProperty("passed","false");result.setProperty("failureClass",e.getClass().getName());}
   try(java.io.OutputStream out=Files.newOutputStream(root.resolve("original-writable-service-observation.properties"),StandardOpenOption.CREATE_NEW)){result.store(out,"Counts/identity only; no HTTP authentication bypass or database writes");}catch(Exception e){throw new IllegalStateException("OWN_WRITABLE_SERVICE_RECEIPT_FAILED",e);}
  });
 }
}
