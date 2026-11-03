from pathlib import Path
import subprocess,os,json
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent;W=V/'mapper-resource-pattern-r262';assert not W.exists();W.mkdir()
source=W/'OwnMapperResourcePatternR262.java'
source.write_text('''import java.nio.file.*;import java.io.*;import java.util.*;import java.util.jar.*;import java.security.*;import com.baomidou.mybatisplus.autoconfigure.MybatisPlusProperties;
public final class OwnMapperResourcePatternR262{
 static void need(boolean b)throws Exception{if(!b)throw new Exception("EXACT_ORIGINAL_MAPPER_RESOURCE_REQUIRED");}static String sha(byte[]b)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(b));}
 public static void main(String[]a)throws Exception{Map<String,String> original=new TreeMap<>();try(JarFile z=new JarFile("D:/Project/Zhumadian/_g/Application/payload/business/application.jar")){for(var e:z.stream().filter(x->x.getName().startsWith("xml/")&&x.getName().endsWith(".xml")).toList()){try(InputStream in=z.getInputStream(e)){need(original.put(Path.of(e.getName()).getFileName().toString(),sha(in.readAllBytes()))==null);}}}need(original.size()==96);
 MybatisPlusProperties p=new MybatisPlusProperties();var defaults=p.resolveMapperLocations();need(defaults.length==1&&defaults[0].getFilename().equals("FirstAidTeamMembersMapper.xml"));try(InputStream in=defaults[0].getInputStream()){need(sha(in.readAllBytes()).equals(original.get(defaults[0].getFilename())));}
 p.setMapperLocations(new String[]{"classpath*:/xml/**/*.xml"});var resources=p.resolveMapperLocations();Set<String> actual=new TreeSet<>();for(var r:resources){need(actual.add(r.getFilename()));try(InputStream in=r.getInputStream()){need(sha(in.readAllBytes()).equals(original.get(r.getFilename())));}}need(actual.equals(original.keySet()));Files.writeString(Path.of(a[0]),"{\\"passed\\":true,\\"defaultResources\\":1,\\"originalPatternResources\\":96,\\"allResolvedBytesExactlyOriginalJar\\":true,\\"duplicateFilenameOrResource\\":false,\\"retainedTeamXMLBytesEqualOriginalJar\\":true,\\"springContainerSQLOrNetworkStarted\\":false}");}}
''',encoding='utf-8')
cp=';'.join(map(str,[A/'payload/business/run-template/classes',A/'payload/business/application.jar',*sorted((A/'payload/business/lib').glob('*.jar'))]));env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
for label,cmd in [('compile',[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx96m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(W),str(source)]),('resolve',[str(A/'runtime/jdk17/bin/java.exe'),'-Xmx96m','-cp',str(W)+';'+cp,'OwnMapperResourcePatternR262',str(W/'result.json')])]:
 r=subprocess.run(cmd,env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=35);(W/(label+'.private.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,label+'_FAILED'
print((W/'result.json').read_text(encoding='utf-8'))
