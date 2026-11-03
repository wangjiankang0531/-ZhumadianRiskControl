import java.io.*;import java.nio.file.*;import java.util.*;import java.util.jar.*;
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
  StringBuilder b=new StringBuilder("{\"onlyOfflineRegistrationNoSpringSQLNetworkOrDatasource\":true,\"defaultMapperResources\":[");for(int i=0;i<defaults.size();i++){if(i>0)b.append(',');b.append('"').append(defaults.get(i)).append('"');}b.append("],\"originalXMLParsed\":").append(loaded).append(",\"fullyQualifiedMappedStatements\":").append(statements).append(",\"pendingResolutionErrorType\":\"").append(pendingError).append("\",\"parseErrorTypes\":[");
  for(int i=0;i<errors.size();i++){if(i>0)b.append(',');b.append('"').append(errors.get(i)).append('"');}b.append("]}");Files.writeString(Path.of(a[1]),b.toString());System.out.println("OWN_OFFLINE_MAPPER_SCAN_FINISHED");
 }
}