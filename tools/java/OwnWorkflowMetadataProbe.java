package xnby.replica;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.util.*;
/** Fixed SELECT-only metadata check against a UUID/port/datadir pinned owned test database. */
public final class OwnWorkflowMetadataProbe {
 public static void main(String[] args)throws Exception {
  if(args.length!=4)throw new IllegalArgumentException("PORT_UUID_DATADIR_FRESH_OUTPUT_REQUIRED");int port=Integer.parseInt(args[0]);if(port<1024||port>65535)throw new IllegalArgumentException("PORT");Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[3]).toAbsolutePath().normalize();if(Files.exists(out)||!Files.isDirectory(out.getParent()))throw new IllegalStateException("FRESH_OUTPUT");byte[] input=System.in.readNBytes(4097);if(input.length>4096)throw new IllegalArgumentException("CREDENTIAL_BOUND");
  Properties properties=new Properties();properties.setProperty("user","root");properties.setProperty("password",new String(input,StandardCharsets.UTF_8));Arrays.fill(input,(byte)0);
  for(var entry:Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000").entrySet())properties.setProperty(entry.getKey(),entry.getValue());
  Map<String,Object> report=new LinkedHashMap<>();List<List<Object>> forms=new ArrayList<>();
  try(Connection connection=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/",properties)) {
   connection.setReadOnly(true);connection.setAutoCommit(false);
   try(Statement statement=connection.createStatement()) {
    statement.setQueryTimeout(10);
    try(ResultSet r=statement.executeQuery("SELECT @@server_uuid,@@port,@@datadir,@@event_scheduler")) {
     if(!r.next()||!args[1].equals(r.getString(1))||r.getInt(2)!=port||!data.equals(Path.of(r.getString(3)).toRealPath())||!"OFF".equals(r.getString(4)))throw new IllegalStateException("OWN_DATABASE_IDENTITY_MISMATCH");report.put("ownedUUIDPortDatadirVerified",true);report.put("eventSchedulerOFF",true);
    }
    try(ResultSet r=statement.executeQuery("SELECT JSON_ARRAY(SHA2(f_id,256),SHA2(COALESCE(f_en_code,''),256),CAST(f_form_type AS CHAR),SHA2(COALESCE(f_url_address,''),256),IF(f_delete_mark IS NULL OR f_delete_mark='0',0,1),IF(f_enabled_mark=1,1,0)) FROM jnpf.flow_form ORDER BY f_id")) {
     List<String> encoded=new ArrayList<>();while(r.next()){if(encoded.size()>=1000)throw new IllegalStateException("FORM_ROW_BOUND");encoded.add(r.getString(1));}report.put("formRowsAsJSON",encoded);
    }
    try(ResultSet r=statement.executeQuery("SELECT (SELECT COUNT(*) FROM jnpf.flow_form_relation),(SELECT COUNT(*) FROM jnpf.base_role)")) {if(!r.next())throw new IllegalStateException("COUNTS_REQUIRED");report.put("formRelations",r.getLong(1));report.put("roles",r.getLong(2));}
   } finally {connection.rollback();}
  } finally {properties.remove("password");}
  report.put("verificationIssuedBusinessWrites",false);report.put("sourceDatabaseConnected",false);Files.writeString(out,OriginalBusinessMethodProbe.json(report)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);System.out.println("OWN_WORKFLOW_METADATA_COMPLETE");
 }
}
