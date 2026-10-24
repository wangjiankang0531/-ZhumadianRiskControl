package xnby.replica;
import java.io.*;import java.lang.reflect.*;import java.nio.file.*;import java.util.*;import java.util.zip.*;
import com.fasterxml.jackson.databind.*;

/** Observe synthetic DTO contracts only; does not start applications or invoke business services. */
public final class OriginalReferenceDTOContractProbe {
 static final class AppLoader extends ClassLoader implements AutoCloseable {
  final ZipFile zip;AppLoader(Path archive)throws Exception{super(OriginalReferenceDTOContractProbe.class.getClassLoader());zip=new ZipFile(archive.toFile());}
  @Override protected Class<?> loadClass(String name,boolean resolve)throws ClassNotFoundException{
   synchronized(getClassLoadingLock(name)){
    Class<?> found=findLoadedClass(name);
    if(found==null&&name.startsWith("com.iemp.endanger.")){
     String path=name.replace('.','/')+".class";ZipEntry e=zip.getEntry("BOOT-INF/classes/"+path);if(e==null)e=zip.getEntry(path);
     if(e!=null)try(InputStream in=zip.getInputStream(e)){byte[] raw=in.readAllBytes();if(raw.length>4*1024*1024)throw new IOException("CLASS_LIMIT");found=defineClass(name,raw,0,raw.length);}catch(IOException error){throw new ClassNotFoundException(name,error);}
    }
    if(found==null)found=super.loadClass(name,false);if(resolve)resolveClass(found);return found;
   }
  }
  public void close()throws IOException{zip.close();}
 }
 static SortedSet<String> properties(Class<?> type){
  SortedSet<String> names=new TreeSet<>();ObjectMapper mapper=new ObjectMapper();mapper.getSerializationConfig().introspect(mapper.constructType(type)).findProperties().forEach(p->names.add(p.getName()));return names;
 }
 public static void main(String[] args)throws Exception{
  if(args.length!=4)throw new IllegalArgumentException("REFERENCE_REBUILT_DEPLOYED_AND_FRESH_OUTPUT_REQUIRED");Path out=Path.of(args[3]);if(Files.exists(out))throw new IOException("FRESH_OUTPUT_REQUIRED");
  List<Map<String,Object>> results=new ArrayList<>();int checks=0;
  for(int n=0;n<3;n++)try(AppLoader loader=new AppLoader(Path.of(args[n]))){
   Map<String,Object> row=new LinkedHashMap<>();row.put("mode",List.of("reference","rebuilt","deployed").get(n));
   Class<?> type=loader.loadClass("com.iemp.endanger.server.work.entity.vo.OtherWorkFileDock");Class<?> fileType=type.getDeclaredField("files").getType();Object files=fileType==List.class?Collections.emptyList():"[]";
   Object dto=type.getConstructor(String.class,fileType).newInstance("owned-dto-fixture",files);ObjectMapper mapper=new ObjectMapper();JsonNode serialized=mapper.readTree(mapper.writeValueAsBytes(dto));
   boolean array=serialized.path("files").isArray();if(array!=(n<2))throw new AssertionError("EXPECTED_REFERENCE_DEPLOYED_FILES_SHAPE_DIFFERENCE");checks++;row.put("filesSerializedAsArray",array);
   Map<String,Object> names=new LinkedHashMap<>();
   for(String suffix:List.of("ThirdInfoDock1","ThirdInfoDock3","ThirdInfoDock4")){
    SortedSet<String> fields=properties(loader.loadClass("com.iemp.endanger.server.safetyBasic.entity.vo."+suffix));names.put(suffix,fields);
   }
   row.put("jsonPropertyNames",names);results.add(row);
  }
  if(!results.get(0).get("jsonPropertyNames").equals(results.get(1).get("jsonPropertyNames")))throw new AssertionError("REBUILT_REFERENCE_PROPERTY_CONTRACT_MISMATCH");checks++;
  if(results.get(0).get("jsonPropertyNames").equals(results.get(2).get("jsonPropertyNames")))throw new AssertionError("EXPECTED_DEPLOYED_PROPERTY_DIFFERENCE_NOT_OBSERVED");checks++;
  Map<String,Object> report=new LinkedHashMap<>();report.put("checks",checks);report.put("contracts",results);report.put("originalServiceMethodsInvoked",false);report.put("applicationStarted",false);report.put("databaseConnected",false);report.put("syntheticDTOOnly",true);new ObjectMapper().writerWithDefaultPrettyPrinter().writeValue(out.toFile(),report);
  System.out.println("DTO_CONTRACT_CHECKS="+checks+" REFERENCE_REBUILT_SHAPES_MATCH=true DEPLOYED_SHAPES_DIFFER=true");
 }
}
