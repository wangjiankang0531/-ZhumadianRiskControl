import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.util.*;import java.security.MessageDigest;
public final class OwnDutySchemaSnapshot {
 static String phase="start";
 static void need(boolean value){if(!value)throw new IllegalStateException("OWN_SCHEMA_IDENTITY_OR_STRUCTURE_CHECK_FAILED");}
 public static void main(String[] args){try{run(args);}catch(Exception failure){String state=failure instanceof SQLException?((SQLException)failure).getSQLState():"";int code=failure instanceof SQLException?((SQLException)failure).getErrorCode():0;System.err.println("OWN_DUTY_SCHEMA_DIAGNOSTIC:{\"phase\":\""+phase+"\",\"type\":\""+failure.getClass().getSimpleName()+"\",\"SQLState\":\""+(state==null?"":state)+"\",\"vendorCode\":"+code+"}");System.exit(1);}}
 static String capacity(Connection c)throws Exception{
  Map<String,Long>v=new LinkedHashMap<>();try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@max_connections")){need(r.next());v.put("maxConnections",r.getLong(1));}
  try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected','Max_used_connections','Connection_errors_max_connections')")){while(r.next()){String k=r.getString(1);need(k.matches("[A-Za-z_]+"));v.put(k,r.getLong(2));}}
  StringJoiner j=new StringJoiner(",","{","}\n");for(var e:v.entrySet())j.add("\""+e.getKey()+"\":"+e.getValue());return j.toString();
 }
 static void run(String[] a)throws Exception {
  need(a.length==5);need(!Files.exists(Paths.get("D:/Project/Zhumadian/_g/user-manual-protected.json")));need(Paths.get(a[2]).toRealPath().equals(Paths.get("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data").toRealPath()));int port=Integer.parseInt(a[0]);Path data=Paths.get(a[2]).toRealPath();byte[] bytes=new byte[32];int used=0;
  while(used<32){int n=System.in.read(bytes,used,32-used);need(n>0);used+=n;}
  String secret=new String(bytes,StandardCharsets.US_ASCII);Arrays.fill(bytes,(byte)0);
  Properties p=new Properties();p.put("user","root");p.put("password",secret);p.put("useSSL","false");p.put("allowPublicKeyRetrieval","true");p.put("connectTimeout","5000");p.put("socketTimeout","15000");
  MessageDigest digest=MessageDigest.getInstance("SHA-256");int count=0;
  phase="connect";try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",p)){
   c.setReadOnly(true);c.setAutoCommit(false);
   phase="identity";try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&Paths.get(r.getString(3)).toRealPath().equals(data));}
   Files.write(Paths.get(a[4]+".ready.json"),capacity(c).getBytes(StandardCharsets.US_ASCII));phase="await-capture";
   int signal=System.in.read();need(signal=='C'||signal=='X');if(signal=='X'){c.rollback();return;}
   Files.write(Paths.get(a[4]+".capacity.json"),capacity(c).getBytes(StandardCharsets.US_ASCII));
   for(String line:Files.readAllLines(Paths.get(a[3]),StandardCharsets.US_ASCII)){
    need(line.matches("(?:jnpf|tj_endanger)\\.[a-z0-9_]+"));String[] name=line.split("\\.",2);
    phase="ddl-"+line;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SHOW CREATE TABLE `"+name[0]+"`.`"+name[1]+"`")){need(r.next());String ddl=r.getString(2).replaceAll("\\bAUTO_INCREMENT=\\d+\\s*","");digest.update((line+"\n"+ddl+"\n").getBytes(StandardCharsets.UTF_8));count++;}
   }
   c.rollback();
  }finally{secret=null;p.clear();}
  phase="exact-count";need(count==398);StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format(Locale.ROOT,"%02x",b&255));
  Files.write(Paths.get(a[4]),("{\"tables\":"+count+",\"sha256\":\""+hex+"\",\"readOnlyMetadataOnly\":true,\"businessRowsRead\":false}\n").getBytes(StandardCharsets.US_ASCII));
 }
}
