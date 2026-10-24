package xnby.replica;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.Connection;
import java.util.*;
import org.springframework.context.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Observe exact bound business parameters and two anonymous GETs from the business process. */
public final class OriginalInternalPlatformObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static final String[][] BINDINGS={
  {"safety.hiddenDangerFormCode","getHiddenDangerFormCode"},{"safety.checkLedgerFormCode","getCheckLedgerFormCode"},{"safety.roleId","getRoleId"},{"safety.auditRoleId","getAuditRoleId"},{"safety.flow-category","getFlowCategory"},{"safety.env-role-id","getEnvRoleId"},{"safety.safety-report-days","getSafetyReportDays"},{"safety.hidden-danger-days","getHiddenDangerDays"},
  {"flow.workCode","getWorkCode"},{"flow.inspectionHandle","getInspectionHandle"},{"flow.workReservation","getWorkReservation"},{"flow.workProgramme","getWorkProgramme"},{"flow.eventInfoHandle","getEventInfoHandle"},{"flow.eventTaskHandle","getEventTaskHandle"}
 };
 static void require(boolean value,String message){if(!value)throw new IllegalStateException(message);}
 static void publish(Path root,Properties result)throws Exception {
  Path target=root.resolve("internal-platform-observation.properties"),pending=root.resolve("internal-platform-observation.pending");if(Files.exists(target))throw new FileAlreadyExistsException(target.toString());
  try(OutputStream out=Files.newOutputStream(pending,StandardOpenOption.CREATE_NEW)){result.store(out,"Boolean/count/hash only; no business values or credentials");}Files.move(pending,target,StandardCopyOption.ATOMIC_MOVE);
 }
 static int anonymous(String base,String path,Properties result,String prefix)throws Exception {
  HttpURLConnection c=(HttpURLConnection)new URL(base+path).openConnection();c.setConnectTimeout(3000);c.setReadTimeout(3000);c.setInstanceFollowRedirects(false);c.setRequestMethod("GET");
  try {
   int status=c.getResponseCode();require(status==200,"OWN_PLATFORM_ANONYMOUS_HTTP_STATUS");byte[] raw;
   try(InputStream stream=c.getInputStream()){ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[512];int n;while((n=stream.read(buffer))!=-1){require(bytes.size()+n<=4096,"OWN_PLATFORM_REPLY_SIZE");bytes.write(buffer,0,n);}raw=bytes.toByteArray();}
   Object json=Class.forName("com.alibaba.fastjson.JSON").getMethod("parseObject",String.class).invoke(null,new String(raw,"UTF-8"));int code=((Number)json.getClass().getMethod("getInteger",String.class).invoke(json,"code")).intValue();
   StringBuilder sha=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))sha.append(String.format("%02x",b&255));result.setProperty(prefix+".httpStatus",Integer.toString(status));result.setProperty(prefix+".applicationCode",Integer.toString(code));result.setProperty(prefix+".bodyBytes",Integer.toString(raw.length));result.setProperty(prefix+".bodySHA256",sha.toString());return code;
  } finally {c.disconnect();}
 }
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;for(java.lang.reflect.Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.candidate.root"));
  context.addApplicationListener(event->{if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;
   Thread worker=new Thread(()->{
    Properties result=new Properties();
    try {
     Properties expected=new Properties();try(InputStream input=Files.newInputStream(root.resolve("application.properties"))){expected.load(input);}
     for(String[] item:BINDINGS){Object bean=context.getBean(Class.forName(item[0].startsWith("safety.")?"com.iemp.endanger.base.entity.SystemParams":"com.iemp.endanger.util.flow.FlowConfig"));Object actual=bean.getClass().getMethod(item[1]).invoke(bean);String want=expected.getProperty(item[0]);require(want!=null&&actual!=null,"OWN_BOUND_BUSINESS_KEY_MISSING");require(actual instanceof Number?Long.parseLong(want)==((Number)actual).longValue():want.equals(String.valueOf(actual)),"OWN_BOUND_BUSINESS_VALUE_MISMATCH");}
     result.setProperty("originalBeanBusinessBindingsMatched","14");
     String base=System.getProperty("own.internal.platform.base");URI uri=new URI(base);require("http".equals(uri.getScheme())&&"127.0.0.1".equals(uri.getHost())&&uri.getPort()>=1024&&uri.getPort()<=65535&&uri.getRawUserInfo()==null&&uri.getRawQuery()==null&&uri.getRawFragment()==null&&(uri.getRawPath()==null||uri.getRawPath().isEmpty()),"OWN_INTERNAL_PLATFORM_BASE");
     require(Arrays.asList(System.getProperty("own.allowed.loopback.ports").split(",")).contains(Integer.toString(uri.getPort())),"OWN_PLATFORM_PORT_NOT_PERMITTED");
     for(String key:new String[]{"safety.jnpfUrl","flow.url"}){String configured=context.getEnvironment().getProperty(key);Object bean=context.getBean(Class.forName(key.startsWith("safety.")?"com.iemp.endanger.base.entity.SystemParams":"com.iemp.endanger.util.flow.FlowConfig"));Object value=bean.getClass().getMethod(key.startsWith("safety.")?"getJnpfUrl":"getUrl").invoke(bean);require(configured!=null&&configured.equals(value),"OWN_INTERNAL_BEAN_URL_NOT_BOUND");URI actual=new URI(configured);require(Objects.equals(actual.getHost(),uri.getHost())&&actual.getPort()==uri.getPort()&&"http".equals(actual.getScheme()),"OWN_INTERNAL_BEAN_URL_MISMATCH");}
     result.setProperty("originalBeanInternalURLsMatched","2");
     Object router=context.getBean(javax.sql.DataSource.class);
     for(String side:new String[]{"master","tow"}){
      javax.sql.DataSource ds=(javax.sql.DataSource)router.getClass().getMethod("getDataSource",String.class).invoke(router,side);
      try(Connection c=ds.getConnection()){String url=c.getMetaData().getURL();String want=expected.getProperty("spring.datasource.dynamic.datasource."+side+".url");require(want.equals(url),"OWN_EFFECTIVE_JDBC_URL_MISMATCH");require(url.contains("serverTimezone=GMT%2B8"),"OWN_ORIGINAL_JDBC_TIMEZONE_NOT_RESTORED");result.setProperty("jdbcOriginalTimezoneApplied."+side,"true");}
     }
     require(anonymous(base,"/api/oauth/getLoginConfig",result,"anonymousConfig")==200,"OWN_PLATFORM_CONFIG_CODE");require(anonymous(base,"/api/oauth/CurrentUser?systemCode=safety",result,"anonymousCurrentUser")==600,"OWN_ANONYMOUS_AUTHENTICATION_CHANGED");
     result.setProperty("businessProcessAnonymousPlatformHTTPVerified","true");result.setProperty("passed","true");
    }catch(Exception e){result.setProperty("passed","false");result.setProperty("failureClass",e.getClass().getName());try{StringWriter writer=new StringWriter();e.printStackTrace(new PrintWriter(writer));Files.write(root.resolve("internal-platform-failure.private.log"),writer.toString().getBytes("UTF-8"),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){}}
    result.setProperty("loginOrJwtAttempted","false");result.setProperty("authenticatedBusinessVerified","false");result.setProperty("fullCloneReady","false");
    try {publish(root,result);}catch(Exception e){throw new IllegalStateException("OWN_INTERNAL_OBSERVATION_WRITE_FAILED",e);}
   },"own-business-internal-platform-observer");worker.setDaemon(true);worker.start();
  });
 }
}
