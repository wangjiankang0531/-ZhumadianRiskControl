package xnby.replica;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.time.*;import java.util.*;import com.fasterxml.jackson.databind.ObjectMapper;
/** Inserts only known synthetic risk rows in a freshly created owned schema. */
public final class OriginalRiskUnitDataFixture{
 public static void main(String[]a)throws Exception{
  if(a.length!=3)throw new IllegalArgumentException("OWN_RISK_SEED_ARGS");
  Path root=Path.of(a[0]).toRealPath();if(!root.getFileName().toString().matches("full-business-main-r[1-9][0-9]*"))throw new IllegalStateException("OWN_RISK_ROOT");
  int port=Integer.parseInt(a[1]);byte[] raw=System.in.readNBytes(4097);if(raw.length!=32)throw new IllegalStateException("SYNTHETIC_SECRET_BOUND");
  var props=new Properties();props.putAll(Map.of("user","xnby_whole_main","password",new String(raw,StandardCharsets.US_ASCII),"useSSL","false","allowPublicKeyRetrieval","true","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));Arrays.fill(raw,(byte)0);
  try(var c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/tj_endanger",props)){
   try(var s=c.createStatement();var r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){
    if(!r.next()||!a[2].equals(r.getString(1))||port!=r.getInt(2)||!root.resolve("data").toRealPath().equals(Path.of(r.getString(3)).toRealPath())||!"tj_endanger".equals(r.getString(4)))throw new IllegalStateException("EXACT_OWN_RISK_DATABASE");
   }
   try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM check_risk_level")){if(!r.next()||r.getInt(1)!=0)throw new IllegalStateException("EMPTY_RISK_TABLE_REQUIRED");}
   c.setAutoCommit(false);
   try(var p=c.prepareStatement("INSERT INTO check_risk_level(id,department,person,analysis_object,analysis_unit,risk_level,coordinate,create_time) VALUES(?,?,?,?,?,?,?,?)")){
    for(int i=1;i<=31;i++){p.setString(1,String.format(Locale.ROOT,"%019d",i));p.setString(2,i%2==0?"Own risk department B":"Own risk department A");p.setString(3,"Own risk person");p.setString(4,"Own risk object "+i);p.setString(5,"Own risk unit "+i);p.setString(6,"1");p.setString(7,"113.0,32.0");p.setTimestamp(8,Timestamp.valueOf(LocalDateTime.of(2000,1,1,0,0).plusSeconds(i/5)));if(p.executeUpdate()!=1)throw new IllegalStateException("OWN_RISK_INSERT_COUNT");}
    c.commit();
   }catch(Exception e){c.rollback();throw e;}
  }finally{props.remove("password");}
  new ObjectMapper().writeValue(root.resolve("risk-unit-seed-result.json").toFile(),Map.of("syntheticRows",31,"actualOriginalTable","check_risk_level","timestampsIncludeTies",true,"originalRowsOrAccountsIncluded",false));
  System.out.println("OWN_RISK_UNIT_SEED_PASSED");
 }
}
