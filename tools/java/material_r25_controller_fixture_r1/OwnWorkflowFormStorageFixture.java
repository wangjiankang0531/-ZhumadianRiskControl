import java.io.*;import java.nio.file.*;import java.sql.*;
/** Restore only the exact prior synthetic form scratch table on _d. */
public final class OwnWorkflowFormStorageFixture{
 static void need(boolean b)throws Exception{if(!b)throw new Exception("OWN_FORM_STORAGE_SCOPE_REJECTED");}
 public static void main(String[]a)throws Exception{
  need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")));
  need(a.length==3&&a[1].matches("[0-9a-f-]{36}")&&Path.of(a[2]).toAbsolutePath().normalize().toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data"));
  String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+Integer.parseInt(a[0])+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=10000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&Path.of(r.getString(2)).toAbsolutePath().normalize().equals(Path.of(a[2]).toAbsolutePath().normalize()));}
   try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='jnpf' AND table_name='own_approval_form'")){need(r.next()&&r.getInt(1)==0);}
   try(Statement s=c.createStatement()){s.execute("CREATE TABLE jnpf.own_approval_form (f_id VARCHAR(128) NOT NULL PRIMARY KEY, f_flow_id VARCHAR(128), f_flow_task_id VARCHAR(128), f_version INT DEFAULT 0, approval_note VARCHAR(512)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");}
   System.out.println("{\"onlyOwnScratchFormCreated\":true}");
  }
 }
}
