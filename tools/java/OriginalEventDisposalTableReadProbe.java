package xnby.replica;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
import com.fasterxml.jackson.databind.ObjectMapper;
@SuppressWarnings("removal")
public final class OriginalEventDisposalTableReadProbe {
 static void need(boolean v,String c){if(!v)throw new IllegalStateException(c);}
 static String hash(String s)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}
 public static void main(String[] args)throws Exception{
  need(args.length==4&&args[1].equals("f1f395d9-12de-4d13-a5eb-f055bc58ca2d"),"EXACT_LOCAL_READONLY_QA");int port=Integer.parseInt(args[0]);Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[3]).toAbsolutePath();need(data.equals(Path.of("D:/Zqa20261025/Application/UserData/OriginalServer/database/data").toRealPath())&&!Files.exists(out),"EXACT_QA_DATADIR_AND_FRESH_OUTPUT");
  byte[] raw=System.in.readNBytes(4097);need(raw.length>0&&raw.length<=4096,"STDIN_BOUND");Properties p=new Properties();p.setProperty("user","root");p.setProperty("password",new String(raw,StandardCharsets.UTF_8));Arrays.fill(raw,(byte)0);p.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));OriginalProcessBoundary guard=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(guard);Map<String,Object> tables=new LinkedHashMap<>();
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/tj_endanger",p)){
   c.setReadOnly(true);try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,@@event_scheduler,DATABASE()")){need(r.next()&&args[1].equals(r.getString(1))&&r.getInt(2)==port&&data.equals(Path.of(r.getString(3)).toRealPath())&&"OFF".equals(r.getString(4))&&"tj_endanger".equals(r.getString(5)),"EXACT_INSTANCE_IDENTITY");}
   for(String t:List.of("event_info","event_disposal_record")){
    String ddl;try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SHOW CREATE TABLE `"+t+"`")){need(r.next(),"EXPECTED_TABLE");ddl=r.getString(2);need(ddl.startsWith("CREATE TABLE")&&ddl.contains("ENGINE=InnoDB"),"ORIGINAL_PERSISTENT_SCHEMA");}}
    List<String> rows=new ArrayList<>();try(Statement s=c.createStatement()){s.setQueryTimeout(10);try(ResultSet r=s.executeQuery("SELECT * FROM `"+t+"`")){var md=r.getMetaData();while(r.next()){need(rows.size()<10000,"BOUNDED_ROWS");StringBuilder row=new StringBuilder();for(int i=1;i<=md.getColumnCount();i++){String v=r.getString(i);row.append(md.getColumnName(i)).append(':').append(v==null?"NULL":v.length()+":"+v).append('\n');}need(row.length()<1048576,"BOUNDED_ROW");rows.add(hash(row.toString()));}}}Collections.sort(rows);tables.put(t,Map.of("rows",rows.size(),"rowMultisetSHA256",hash(String.join("\n",rows)),"schemaSHA256",hash(ddl)));
   }
  }finally{p.remove("password");}
  Files.writeString(out,new ObjectMapper().writeValueAsString(Map.of("permanentTwoTables",tables,"readOnlyConnection",true,"businessMethodsAuthenticationWritesOrHTTPInvoked",false,"rowValuesOutputOrCopied",false))+"\n",StandardOpenOption.CREATE_NEW);System.out.println("QA_EVENT_DISPOSAL_READONLY_TABLES=2");
 }
}
