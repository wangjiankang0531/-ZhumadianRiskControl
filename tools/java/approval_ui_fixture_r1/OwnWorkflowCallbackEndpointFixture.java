import java.io.*;import java.nio.file.*;import java.sql.*;
import com.fasterxml.jackson.databind.*;import com.fasterxml.jackson.databind.node.ObjectNode;
/** Bind the one prior synthetic callback interface to this owned runtime's business port. */
public final class OwnWorkflowCallbackEndpointFixture {
 static void need(boolean b)throws Exception{if(!b)throw new Exception("OWN_CALLBACK_FIXTURE_SCOPE_REJECTED");}
 public static void main(String[]a)throws Exception{
  need(a.length==4&&a[1].matches("[0-9a-f-]{36}")&&Path.of(a[2]).toAbsolutePath().normalize().toString().replace('\\','/').equals("D:/Project/Zhumadian/_e/Application/UserData/OriginalServer/database/data"));
  int port=Integer.parseInt(a[0]),business=Integer.parseInt(a[3]);need(port>=1024&&port<=65535&&business>=1024&&business<=65535&&port!=business);
  String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=10000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&Path.of(r.getString(2)).toAbsolutePath().normalize().equals(Path.of(a[2]).toAbsolutePath().normalize()));}
   String old;try(PreparedStatement p=c.prepareStatement("SELECT f_data_config_json,f_type,f_en_code FROM base_data_interface WHERE f_id=?")){p.setString(1,"a5320000000000000000000000000005");try(ResultSet r=p.executeQuery()){need(r.next()&&r.getInt(2)==3&&"OWN_NORMAL_WORKFLOW_CALLBACK".equals(r.getString(3)));old=r.getString(1);need(!r.next());}}
   ObjectMapper mapper=new ObjectMapper();JsonNode original=mapper.readTree(old);ObjectNode changed=(ObjectNode)original.deepCopy();JsonNode api=changed.path("apiData");String previous=api.path("url").asText();need(previous.matches("http://127\\.0\\.0\\.1:[0-9]{4,5}/(?:serv/)?eventTask/callback")&&api.path("method").asInt()==1&&api.path("query").size()==2);
   String next="http://127.0.0.1:"+business+"/eventTask/callback";((ObjectNode)api).put("url",next);ObjectNode reversed=changed.deepCopy();((ObjectNode)reversed.path("apiData")).put("url",previous);need(reversed.equals(original));
   try(PreparedStatement p=c.prepareStatement("UPDATE base_data_interface SET f_data_config_json=? WHERE f_id=? AND f_data_config_json=?")){p.setString(1,mapper.writeValueAsString(changed));p.setString(2,"a5320000000000000000000000000005");p.setString(3,old);need(p.executeUpdate()==1);}
   System.out.println("{\"onlyPriorOwnedSyntheticInterfaceUpdated\":true,\"onlyCallbackURLChanged\":true,\"actualOwnedBusinessPortAndOriginalCallbackPathMatched\":true,\"productSchemaOrRealFormOrRoleChanged\":false}");
  }
 }
}
