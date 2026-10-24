package xnby.replica;

import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.jar.*;
import com.fasterxml.jackson.databind.*;

/** Synthetic DTO and class-source checks; never starts Spring or business services. */
public final class PortableReferenceRuntimeProbe {
  private static void check(boolean value,String code) { if(!value) throw new AssertionError(code); }
  private static String sha(byte[] raw) throws Exception {
    StringBuilder result=new StringBuilder();
    for(byte b:MessageDigest.getInstance("SHA-256").digest(raw)) result.append(String.format("%02x",b&255));
    return result.toString();
  }
  private static SortedSet<String> properties(Class<?> type,ObjectMapper mapper) {
    SortedSet<String> names=new TreeSet<>();
    mapper.getSerializationConfig().introspect(mapper.constructType(type)).findProperties().forEach(p->names.add(p.getName()));
    return names;
  }
  public static void main(String[] args) throws Exception {
    check(args.length==3,"PAYLOAD_FRESH_REPORT_AND_RESOURCE_PIN_REQUIRED");
    Path root=Paths.get(args[0]).toRealPath(),out=Paths.get(args[1]);
    check(!Files.exists(out)&&args[2].matches("[0-9a-f]{64}"),"FRESH_REPORT_AND_PIN_REQUIRED");
    ObjectMapper mapper=new ObjectMapper();ClassLoader loader=PortableReferenceRuntimeProbe.class.getClassLoader();
    Class<?> files=Class.forName("com.iemp.endanger.server.work.entity.vo.OtherWorkFileDock",true,loader);
    check(files.getDeclaredField("files").getType()==List.class,"REFERENCE_FILES_LIST_REQUIRED");
    Object dto=files.getConstructor(String.class,List.class).newInstance("portable-dto-fixture",Collections.emptyList());
    check(mapper.readTree(mapper.writeValueAsBytes(dto)).path("files").isArray(),"REFERENCE_FILES_JSON_ARRAY_REQUIRED");
    List<Class<?>> sources=new ArrayList<>();sources.add(files);int contracts=1;
    for(String suffix:Arrays.asList("ThirdInfoDock1","ThirdInfoDock3","ThirdInfoDock4")) {
      Class<?> type=Class.forName("com.iemp.endanger.server.safetyBasic.entity.vo."+suffix,false,loader);
      SortedSet<String> names=properties(type,mapper);sources.add(type);
      check(suffix.equals("ThirdInfoDock1")?names.contains("companyName"):(names.contains("username")&&!names.contains("userName")),"REFERENCE_PROPERTY_NAMES_REQUIRED");contracts++;
    }
    for(String name:Arrays.asList("com.fasterxml.jackson.databind.ObjectMapper","com.fasterxml.jackson.databind.JsonNode",
        "org.springframework.boot.SpringApplication","org.springframework.core.SpringVersion"))sources.add(Class.forName(name,false,loader));
    String main;
    try(JarFile jar=new JarFile(root.resolve("application.jar").toFile())) {
      check(jar.getManifest().getMainAttributes().getValue("Main-Class")==null,"CONTROLLED_LAUNCH_ONLY_REQUIRED");
      main=jar.getManifest().getMainAttributes().getValue("Original-Main-Class");
    }
    sources.add(Class.forName(main,false,loader));
    for(Class<?> type:sources) {
      URL location=type.getProtectionDomain().getCodeSource().getLocation();
      check(location.getProtocol().equals("file")&&Paths.get(location.toURI()).toRealPath().startsWith(root),"CLASS_SOURCE_OUTSIDE_PORTABLE_PAYLOAD");
    }
    URL resource=loader.getResource("bootstrap.yml");check(resource!=null&&resource.getProtocol().equals("jar"),"PORTABLE_RESOURCE_JAR_REQUIRED");
    JarURLConnection connection=(JarURLConnection)resource.openConnection();
    check(Paths.get(connection.getJarFileURL().toURI()).toRealPath().equals(root.resolve("application.jar")),"RESOURCE_SOURCE_OUTSIDE_PAYLOAD");
    try(InputStream input=resource.openStream()) {check(sha(input.readAllBytes()).equals(args[2]),"RESOURCE_BYTES_CHANGED");}
    Properties result=new Properties();result.setProperty("dtoContracts",Integer.toString(contracts));
    result.setProperty("applicationAndDependencyCodeSourcesInsidePayload",Integer.toString(sources.size()));
    result.setProperty("originalBootstrapResourceSHA256Exact","true");result.setProperty("onlySyntheticDTOConstructorsInvoked","true");
    result.setProperty("springApplicationStarted","false");result.setProperty("businessServiceInvoked","false");
    result.setProperty("databaseConnected","false");result.setProperty("passed","true");
    try(OutputStream output=Files.newOutputStream(out,StandardOpenOption.CREATE_NEW)) {result.store(output,"No business records, original credentials or resource contents");}
    System.out.println("PORTABLE_REFERENCE_DTO_CONTRACTS="+contracts+" CODE_SOURCES_INSIDE_PAYLOAD="+sources.size());
  }
}
