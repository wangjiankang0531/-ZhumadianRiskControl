package xnby.bigscreen;
import java.nio.file.*;
import java.sql.*;
import java.net.*;
import java.util.*;

/** Real fixed SQLite JNI and owned reference-data copy; never an original/reference writable path. */
public final class BigscreenSqliteNativeFixture {
 static int checks;interface Checked{void run()throws Exception;}
 static void require(boolean v){if(!v)throw new IllegalStateException("BIGSCREEN_SQLITE_NATIVE_FIXTURE_FAILED");checks++;}
 static void denied(Checked call)throws Exception{try{call.run();}catch(SecurityException e){checks++;return;}throw new IllegalStateException("UNLISTED_BIGSCREEN_OPERATION_ACCEPTED");}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath(),outside=Paths.get(args[1]);Path bad=root.resolve("bad-native-root");Files.createDirectories(bad.resolve("native"));Files.write(bad.resolve("native/sqlitejdbc.dll"),new byte[]{0});
  boolean rejected=false;try{new OriginalBigscreenProcessBoundary(bad,Collections.<Integer>emptySet(),false);}catch(IllegalArgumentException e){rejected=true;}require(rejected);
  final OriginalBigscreenProcessBoundary guard=new OriginalBigscreenProcessBoundary(root,Collections.<Integer>emptySet(),false);System.setSecurityManager(guard);
  Class.forName("org.sqlite.JDBC");
  try(Connection connection=DriverManager.getConnection("jdbc:sqlite:"+root.resolve("data/working.db"))) {
   require(connection.getMetaData().getDriverVersion().equals("3.36.0.3"));
   try(Statement s=connection.createStatement();ResultSet r=s.executeQuery("PRAGMA database_list")){require(r.next()&&Paths.get(r.getString(3)).toRealPath().equals(root.resolve("data/working.db").toRealPath()));}
   try(Statement s=connection.createStatement();ResultSet r=s.executeQuery("SELECT COUNT(*) FROM SURVEY")){require(r.next()&&r.getInt(1)==4);}
   try(Statement s=connection.createStatement();ResultSet r=s.executeQuery("PRAGMA quick_check")){require(r.next()&&"ok".equals(r.getString(1)));}
  }
  require(guard.allowedSqliteLoads()>0);require(guard.deniedCounts().isEmpty());
  denied(()->System.load(root.resolve("native/not-allowed.dll").toString()));denied(()->System.loadLibrary("sqlitejdbc"));denied(()->Files.write(outside,new byte[]{1}));denied(()->{try(Socket socket=new Socket("127.0.0.1",59991)){};});denied(()->System.setSecurityManager(null));
  require(System.getSecurityManager()==guard);System.out.println("BIGSCREEN_SQLITE_NATIVE_CHECKS="+checks);System.out.println("ALLOWED_SQLITE_NATIVE_LOADS="+guard.allowedSqliteLoads());
 }
}
