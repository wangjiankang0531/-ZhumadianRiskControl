package xnby.replica;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;

/** Read-only fingerprints for two owned acceptance samples across normal restart.
 * No authentication calls, writes, TEMP tables, service methods or external I/O. */
@SuppressWarnings("removal")
public final class OriginalAtomicUpdateReadProbe {
 static void need(boolean yes,String code){if(!yes)throw new IllegalStateException(code);}
 static String sha(byte[] b)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}
 static Map<String,Object> rows(Connection c,String sql,String parameter,int expected)throws Exception{
  List<String> hashes=new ArrayList<>();try(PreparedStatement p=c.prepareStatement(sql)){p.setQueryTimeout(5);p.setString(1,parameter);try(ResultSet r=p.executeQuery()){var m=r.getMetaData();while(r.next()){need(hashes.size()<8,"OWN_ROW_BOUND");StringBuilder b=new StringBuilder();for(int i=1;i<=m.getColumnCount();i++){String v=r.getString(i);b.append(m.getColumnName(i)).append(':').append(v==null?"NULL":v.length()+":"+v).append('\n');}need(b.length()<262144,"OWN_ROW_BYTE_BOUND");hashes.add(sha(b.toString().getBytes(StandardCharsets.UTF_8)));}}}Collections.sort(hashes);need(hashes.size()==expected,"EXPECTED_OWN_SAMPLE_ROW_COUNT");return Map.of("rows",hashes.size(),"completeSelectedRowsSHA256",sha(String.join("\n",hashes).getBytes(StandardCharsets.US_ASCII)));
 }
 public static void main(String[] args)throws Exception{
  need(args.length==4,"PORT_UUID_DATADIR_OUTPUT");int port=Integer.parseInt(args[0]);Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[3]).toAbsolutePath();need(!Files.exists(out)&&Files.isDirectory(out.getParent()),"FRESH_OUTPUT");
  byte[] secret=System.in.readNBytes(4097);need(secret.length>0&&secret.length<=4096,"STDIN_SECRET_BOUND");Properties props=new Properties();props.put("user","root");props.put("password",new String(secret,StandardCharsets.UTF_8));Arrays.fill(secret,(byte)0);props.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","10000"));
  var boundary=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(boundary);Map<String,Integer> before=boundary.deniedCounts();Map<String,Object> samples=new LinkedHashMap<>();
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/tj_endanger",props)){
   c.setReadOnly(true);c.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ);c.setAutoCommit(false);
   try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,@@event_scheduler,DATABASE()")){need(r.next()&&args[1].equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toRealPath())&&"OFF".equals(r.getString(4))&&"tj_endanger".equals(r.getString(5)),"EXACT_OWN_LOCAL_DATABASE");}}
   String reservation="5a8ecafdd5095f6421befe45e585636d";
   samples.put("reservation",rows(c,"SELECT * FROM work_reservation_base WHERE id=?",reservation,1));
   samples.put("typedWork",rows(c,"SELECT * FROM work_hot WHERE work_reservation_base_id=?",reservation,1));
   samples.put("reservationPersonnel",rows(c,"SELECT * FROM work_reservation_personnel WHERE work_reservation_base_id=?",reservation,2));
   samples.put("thirdParty",rows(c,"SELECT * FROM third_party_unit_info WHERE id=?","4591c2999e47a74c9c8019cf09ddc8eb",1));
   samples.put("thirdPartyCredential",rows(c,"SELECT * FROM third_party_unit_info_credential WHERE social_code=?","QATEST202610280001",0));
   c.rollback();
  }finally{props.remove("password");}
  need(before.equals(boundary.deniedCounts()),"NO_UNEXPECTED_BOUNDARY_ACTIVITY");Files.writeString(out,new ObjectMapper().writeValueAsString(Map.of("samples",samples,"readOnlyConnection",true,"businessMethodsAuthenticationOrWritesInvoked",false,"notAFullDatabaseSnapshot",true))+"\n",StandardOpenOption.CREATE_NEW);System.out.println("OWNED_ACCEPTANCE_SAMPLE_GROUPS=5");
 }
}
