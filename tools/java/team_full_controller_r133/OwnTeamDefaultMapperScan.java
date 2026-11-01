import java.nio.file.*;import java.security.*;import java.util.*;
import com.baomidou.mybatisplus.autoconfigure.MybatisPlusProperties;
public final class OwnTeamDefaultMapperScan{
 static void need(boolean v)throws Exception{if(!v)throw new Exception("OWN_TEAM_DEFAULT_MAPPER_SCAN_REQUIRED");}
 static String sha(byte[] raw)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
 public static void main(String[] args)throws Exception{
  Path app=Path.of("D:/Project/Zhumadian/_g/Application").toRealPath();need(!Files.exists(app.getParent().resolve("user-manual-protected.json")));
  need(args.length==1&&Path.of(args[0]).toAbsolutePath().normalize().equals(Path.of("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r133/mapper-scan-proof-r1/result.json")));
  String pin="2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd";
  MybatisPlusProperties properties=new MybatisPlusProperties();need(Arrays.equals(properties.getMapperLocations(),new String[]{"classpath*:/mapper/**/*.xml"}));
  int matched=0;for(var resource:properties.resolveMapperLocations())if("FirstAidTeamMembersMapper.xml".equals(resource.getFilename())){
   need(resource.getFile().toPath().toRealPath().equals(app.resolve("payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml")));try(var in=resource.getInputStream()){need(sha(in.readAllBytes()).equals(pin));}matched++;
  }need(matched==1);int original=0;var sources=OwnTeamDefaultMapperScan.class.getClassLoader().getResources("xml/FirstAidTeamMembersMapper.xml");while(sources.hasMoreElements()){try(var in=sources.nextElement().openStream()){need(sha(in.readAllBytes()).equals(pin));}original++;}need(original==1);
  Files.writeString(Path.of(args[0]),"{\"passed\":true,\"actualInstalledMybatisPlusDefaultScanUsed\":true,\"exactOriginalJarResourceMatches\":1,\"exactDefaultScanTargetMatches\":1,\"originalSQLBytesPreserved\":true,\"springContainerOrSQLOrNetworkStarted\":false,\"protectedOrPublicChanged\":false}");
  System.out.println("OWN_TEAM_DEFAULT_SCAN_BYTE_EXACT_ORIGINAL_RESOURCE_CONFIRMED");
 }
}
