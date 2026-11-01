import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.util.*;import java.security.MessageDigest;
public final class OwnControllerSchemaSnapshot {
 static void need(boolean value){if(!value)throw new IllegalStateException("OWN_SCHEMA_IDENTITY_OR_STRUCTURE_CHECK_FAILED");}
 public static void main(String[] args){try{run(args);}catch(Exception failure){System.err.println("OWN_SCHEMA_CHECK_FAILED:"+failure.getClass().getSimpleName());System.exit(1);}}
 static void run(String[] a)throws Exception {
  need(a.length==5);int port=Integer.parseInt(a[0]);Path data=Paths.get(a[2]).toRealPath();byte[] bytes=new byte[32];int used=0;
  while(used<32){int n=System.in.read(bytes,used,32-used);need(n>0);used+=n;}
  String secret=new String(bytes,StandardCharsets.US_ASCII);Arrays.fill(bytes,(byte)0);
  Properties p=new Properties();p.put("user","root");p.put("password",secret);p.put("useSSL","false");p.put("allowPublicKeyRetrieval","true");p.put("connectTimeout","5000");p.put("socketTimeout","15000");
  MessageDigest digest=MessageDigest.getInstance("SHA-256");int count=0;
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",p)){
   c.setReadOnly(true);c.setAutoCommit(false);
   try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&Paths.get(r.getString(3)).toRealPath().equals(data));}
   for(String line:Files.readAllLines(Paths.get(a[3]),StandardCharsets.US_ASCII)){
    need(line.matches("(?:jnpf|tj_endanger)\\.[a-z0-9_]+"));String[] name=line.split("\\.",2);
    try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SHOW CREATE TABLE `"+name[0]+"`.`"+name[1]+"`")){need(r.next());String ddl=r.getString(2).replaceAll("\\bAUTO_INCREMENT=\\d+\\s*","");digest.update((line+"\n"+ddl+"\n").getBytes(StandardCharsets.UTF_8));count++;}
   }
   c.rollback();
  }finally{secret=null;p.clear();}
  need(count==398);StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format(Locale.ROOT,"%02x",b&255));
  Files.write(Paths.get(a[4]),("{\"tables\":"+count+",\"sha256\":\""+hex+"\",\"readOnlyMetadataOnly\":true,\"businessRowsRead\":false}\n").getBytes(StandardCharsets.US_ASCII));
 }
}
