from pathlib import Path
import hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r133/mapper-scan-proof-r1';assert not C.exists();assert not(A.parent/'user-manual-protected.json').exists();C.mkdir()
source=T/'java/team_full_controller_r133/OwnTeamDefaultMapperScan.java';assert not source.exists()
source.write_text('''import java.nio.file.*;import java.security.*;import java.util.*;
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
  Files.writeString(Path.of(args[0]),"{\\"passed\\":true,\\"actualInstalledMybatisPlusDefaultScanUsed\\":true,\\"exactOriginalJarResourceMatches\\":1,\\"exactDefaultScanTargetMatches\\":1,\\"originalSQLBytesPreserved\\":true,\\"springContainerOrSQLOrNetworkStarted\\":false,\\"protectedOrPublicChanged\\":false}");
  System.out.println("OWN_TEAM_DEFAULT_SCAN_BYTE_EXACT_ORIGINAL_RESOURCE_CONFIRMED");
 }
}
''',encoding='utf-8',newline='\n')
classes=C/'classes';classes.mkdir();cp=';'.join(map(str,[A/'payload/business/run-template/classes',A/'payload/business/application.jar',*sorted((A/'payload/business/lib').glob('*.jar'))]));env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
for name,cmd in [('compile',[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(classes),str(source)]),('scan',[str(A/'runtime/jdk17/bin/java.exe'),'-Xmx96m','-cp',str(classes)+';'+cp,'OwnTeamDefaultMapperScan',str(C/'result.json')])]:
    p=subprocess.run(cmd,env=env,capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW);(C/(name+'.private.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,name+'_FAILED'
proof=json.loads((C/'result.json').read_bytes());proof['sourceSHA256']=hashlib.sha256(source.read_bytes()).hexdigest();(C/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
