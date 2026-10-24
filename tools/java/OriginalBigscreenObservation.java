package xnby.bigscreen;
import java.io.*;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
import org.springframework.context.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Validate the original SQLite/Hikvision beans and connection; no original external credentials used. */
public final class OriginalBigscreenObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static void require(boolean v,String code){if(!v)throw new IllegalStateException(code);}
 public void initialize(final ConfigurableApplicationContext context) {
  final Path root=Paths.get(System.getProperty("own.candidate.root"));
  final Path expected=root.resolve("data/working.db").toAbsolutePath().normalize();
  require(expected.toString().equals(context.getEnvironment().getProperty("sqlite.file")),"OWN_SQLITE_FILE_REQUIRED_BEFORE_BEANS");
  require("127.0.0.1".equals(context.getEnvironment().getProperty("server.address"))&&"0".equals(context.getEnvironment().getProperty("server.port")),"OWN_BIGSCREEN_LOOPBACK_EPHEMERAL_REQUIRED");
  require("127.0.0.1:9".equals(context.getEnvironment().getProperty("hkinfo.app-host")),"OWN_UNAVAILABLE_VIDEO_HOST_REQUIRED");
  context.addApplicationListener(event->{if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;
   Properties result=new Properties();
   try {
    Class<?> fileClass=Class.forName("com.hteis.tjwhyq.base.config.SqlitFileConfig");Object file=context.getBean(fileClass);require(expected.toString().equals(fileClass.getMethod("getFile").invoke(file)),"ORIGINAL_SQLITE_BEAN_BINDING_MISMATCH");
    Class<?> videoClass=Class.forName("com.hteis.tjwhyq.base.config.HkVideoConfig");Object video=context.getBean(videoClass);require("127.0.0.1:9".equals(videoClass.getMethod("getAppHost").invoke(video)),"ORIGINAL_VIDEO_HOST_BEAN_BINDING_MISMATCH");
    for(String[] item:new String[][]{{"getAppKey","hkinfo.app-key"},{"getAppSecret","hkinfo.app-secret"}})require(System.getProperty(item[1]).equals(videoClass.getMethod(item[0]).invoke(video)),"OWN_VIDEO_CREDENTIAL_BINDING_MISMATCH");
    Connection connection=(Connection)Class.forName("com.hteis.tjwhyq.base.utils.CommonUtil").getField("c").get(null);require(connection!=null&&!connection.isClosed(),"ORIGINAL_SQLITE_CONNECTION_REQUIRED");
    try(Statement statement=connection.createStatement();ResultSet rows=statement.executeQuery("PRAGMA database_list")){require(rows.next()&&Paths.get(rows.getString(3)).toRealPath().equals(expected.toRealPath()),"ACTUAL_ORIGINAL_SQLITE_PATH_MISMATCH");}
    try(Statement statement=connection.createStatement();ResultSet rows=statement.executeQuery("SELECT COUNT(*) FROM SURVEY")){require(rows.next(),"ORIGINAL_SURVEY_COUNT_REQUIRED");result.setProperty("originalSurveyRows",Integer.toString(rows.getInt(1)));}
    require(System.getSecurityManager() instanceof OriginalBigscreenProcessBoundary,"OWN_BIGSCREEN_BOUNDARY_REQUIRED");OriginalBigscreenProcessBoundary guard=(OriginalBigscreenProcessBoundary)System.getSecurityManager();require(guard.allowedSqliteLoads()>0,"ACTUAL_VERIFIED_SQLITE_NATIVE_LOAD_REQUIRED");
    Object servlet=context.getClass().getMethod("getServletContext").invoke(context);String path=(String)Class.forName("javax.servlet.ServletContext").getMethod("getContextPath").invoke(servlet);result.setProperty("originalServletContextPath",path);
    result.setProperty("originalSQLiteFileAndConnectionMatched","true");result.setProperty("originalVideoBeanUsesOwnedUnavailableHostAndCredentials","true");result.setProperty("nativeSQLiteLoads",Integer.toString(guard.allowedSqliteLoads()));result.setProperty("sqliteDriverVersion",connection.getMetaData().getDriverVersion());result.setProperty("passed","true");
   }catch(Exception e){result.setProperty("passed","false");result.setProperty("failureClass",e.getClass().getName());try{StringWriter text=new StringWriter();e.printStackTrace(new PrintWriter(text));Files.write(root.resolve("observation-failure.private.log"),text.toString().getBytes("UTF-8"),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){}}
   try{try(OutputStream out=Files.newOutputStream(root.resolve("original-bigscreen-observation.properties"),StandardOpenOption.CREATE_NEW)){result.store(out,"Boolean and counts only; no original rows or credentials");}}catch(Exception e){throw new IllegalStateException("OWN_BIGSCREEN_OBSERVATION_WRITE_FAILED",e);}
  });
 }
}
