from pathlib import Path
import json,subprocess,os,hashlib,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent
W=V/'mapper-offline-registration-r251-r2';assert not W.exists();W.mkdir()
source=W/'OwnOriginalMapperRegistrationR251.java'
source.write_text('''import java.io.*;import java.nio.file.*;import java.util.*;import java.util.jar.*;
import com.baomidou.mybatisplus.autoconfigure.MybatisPlusProperties;
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import org.apache.ibatis.builder.xml.XMLMapperBuilder;
public final class OwnOriginalMapperRegistrationR251 {
 public static void main(String[] a)throws Exception {
  if(a.length!=2||!a[0].equals("D:/Project/Zhumadian/_g/Application/payload/business/application.jar"))throw new Exception("OWN_SCOPE");
  MybatisPlusProperties p=new MybatisPlusProperties();List<String> defaults=new ArrayList<>();for(var r:p.resolveMapperLocations())defaults.add(r.getFilename());
  MybatisConfiguration c=new MybatisConfiguration();int loaded=0;List<String> errors=new ArrayList<>();
  try(JarFile j=new JarFile(a[0])){List<String> names=j.stream().map(e->e.getName()).filter(n->n.startsWith("xml/")&&n.endsWith(".xml")).sorted().toList();
   for(String n:names){try(InputStream in=j.getInputStream(j.getJarEntry(n))){new XMLMapperBuilder(in,c,n,c.getSqlFragments()).parse();loaded++;}catch(Throwable e){errors.add(n+":"+e.getClass().getSimpleName());}}
  }
  String pendingError="";int statements=-1;try{statements=(int)c.getMappedStatementNames().stream().filter(n->n.contains(".")).count();}catch(Throwable e){pendingError=e.getClass().getSimpleName();}
  StringBuilder b=new StringBuilder("{\\"onlyOfflineRegistrationNoSpringSQLNetworkOrDatasource\\":true,\\"defaultMapperResources\\":[");for(int i=0;i<defaults.size();i++){if(i>0)b.append(',');b.append('"').append(defaults.get(i)).append('"');}b.append("],\\"originalXMLParsed\\":").append(loaded).append(",\\"fullyQualifiedMappedStatements\\":").append(statements).append(",\\"pendingResolutionErrorType\\":\\"").append(pendingError).append("\\",\\"parseErrorTypes\\":[");
  for(int i=0;i<errors.size();i++){if(i>0)b.append(',');b.append('"').append(errors.get(i)).append('"');}b.append("]}");Files.writeString(Path.of(a[1]),b.toString());System.out.println("OWN_OFFLINE_MAPPER_SCAN_FINISHED");
 }
}''',encoding='utf-8')
cp=';'.join(map(str,[A/'payload/business/run-template/classes',A/'payload/business/application.jar',*sorted((A/'payload/business/lib').glob('*.jar'))]))
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
for name,args in [('compile',[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(W),str(source)]),('parse',[str(A/'runtime/jdk17/bin/java.exe'),'-Xmx160m','-cp',str(W)+';'+cp,'OwnOriginalMapperRegistrationR251',(A/'payload/business/application.jar').as_posix(),str(W/'result.json')])]:
 p=subprocess.run(args,capture_output=True,env=env,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
 (W/(name+'.private.log')).write_bytes(p.stdout+p.stderr)
 if p.returncode:print(json.dumps({'stage':name,'exitCode':p.returncode,'diagnosticLines':p.stderr.decode('utf-8',errors='replace').splitlines()[-8:]}));raise RuntimeError('OFFLINE_MAPPER_INSPECTION_FAILED')
proof=json.loads((W/'result.json').read_bytes());proof['sourceSHA256']=hashlib.sha256(source.read_bytes()).hexdigest();print(json.dumps(proof))
