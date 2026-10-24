package xnby.platform;
import org.yaml.snakeyaml.*;
import org.yaml.snakeyaml.nodes.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Original YAML is parsed as nodes only; external integration values are replaced before writing. */
public final class OriginalPlatformConfigBuilder{
 static void flatten(Node node,String key,Map<String,String> out){
  if(node instanceof MappingNode m){
   for(NodeTuple tuple:m.getValue()){
    if(!(tuple.getKeyNode() instanceof ScalarNode k))throw new IllegalArgumentException("NON_SCALAR_KEY");
    flatten(tuple.getValueNode(),key.isEmpty()?k.getValue():key+"."+k.getValue(),out);
   }
  }else if(node instanceof SequenceNode s){int i=0;for(Node child:s.getValue())flatten(child,key+"["+(i++)+"]",out);}
  else if(node instanceof ScalarNode s)out.put(key,s.getTag().equals(Tag.NULL)?"":s.getValue());
 }
 static void yaml(ZipFile zip,String name,Map<String,String> out)throws Exception{
  ZipEntry entry=zip.getEntry(name);if(entry==null||entry.getSize()>1024*1024)throw new IllegalArgumentException("SOURCE_CONFIG_MISSING");
  byte[] raw;try(var stream=zip.getInputStream(entry)){raw=stream.readNBytes(1024*1024+1);}if(raw.length!=entry.getSize())throw new IllegalArgumentException("SOURCE_CONFIG_SIZE");
  LoaderOptions options=new LoaderOptions();options.setMaxAliasesForCollections(10);options.setCodePointLimit(1024*1024);
  for(Node node:new Yaml(options).composeAll(new java.io.StringReader(new String(raw,java.nio.charset.StandardCharsets.UTF_8))))flatten(node,"",out);
 }
 public static void main(String[] args)throws Exception{
  Path archive=Paths.get(args[0]),root=Paths.get(args[1]).toRealPath();Properties own=new Properties();
  try(var input=Files.newInputStream(root.resolve("own-integration.properties"))){own.load(input);}
  Map<String,String> source=new LinkedHashMap<>();String profile;
  try(ZipFile zip=new ZipFile(archive.toFile())){
   yaml(zip,"BOOT-INF/classes/application.yml",source);profile=source.get("spring.profiles.active");
   if(!Set.of("pro","test").contains(profile))throw new IllegalArgumentException("SOURCE_PROFILE_NOT_RECOGNIZED");
   yaml(zip,"BOOT-INF/classes/application-"+profile+".yml",source);
  }
  Map<String,String> config=new LinkedHashMap<>();Set<String> overridden=new TreeSet<>();
  String secret=own.getProperty("ownSecret");
  for(var entry:source.entrySet()){
   String key=entry.getKey(),lower=key.toLowerCase(Locale.ROOT),value=entry.getValue();
   if(lower.matches(".*(password|secret|token|access[-]?key|app[-]?key|securitykey|mastersecret).*")){value=secret;overridden.add(key);}
   if(value.startsWith("http://")||value.startsWith("https://")||value.startsWith("jdbc:")||lower.matches(".*[.]host$")){value="http://127.0.0.1:9/own-unavailable";overridden.add(key);}
   if((key.startsWith("config.")&&key.endsWith("Path"))||lower.matches(".*(base-path|storage-path|logpath|log[.]path)$")){
    value=root.resolve("files").resolve(key.replaceAll("[^A-Za-z0-9_-]","_")).toString()+"/";Files.createDirectories(Paths.get(value));overridden.add(key);
   }
   if(lower.endsWith(".enable-storage")||lower.endsWith(".enable-access")){value="false";overridden.add(key);}
   config.put(key,value);
  }
  Map<String,String> fixed=new LinkedHashMap<>();
  fixed.put("server.address","127.0.0.1");fixed.put("server.port","0");fixed.put("spring.profiles.active","own-platform-isolation");
  fixed.put("spring.datasource.host","127.0.0.1");fixed.put("spring.datasource.port",own.getProperty("mysqlPort"));fixed.put("spring.datasource.username","root");fixed.put("spring.datasource.password",own.getProperty("mysqlPassword"));
  Path publicKey=Paths.get(own.getProperty("mysqlPublicKeyPath"));
  byte[] publicBytes=Files.readAllBytes(publicKey);if(publicBytes.length>4096||!new String(publicBytes,java.nio.charset.StandardCharsets.US_ASCII).startsWith("-----BEGIN PUBLIC KEY-----"))throw new IllegalArgumentException("OWN_PUBLIC_KEY_SHAPE");
  Path copiedKey=root.resolve("own-mysql-public-key.pem");Files.write(copiedKey,publicBytes,StandardOpenOption.CREATE_NEW);
  String keyPath=java.net.URLEncoder.encode(copiedKey.toString(),java.nio.charset.StandardCharsets.UTF_8);
  String jdbc="jdbc:mysql://127.0.0.1:"+own.getProperty("mysqlPort")+"/jnpf?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia%2FShanghai&useSSL=false&allowPublicKeyRetrieval=false&serverRSAPublicKeyFile="+keyPath+"&connectTimeout=3000&socketTimeout=8000";
  fixed.put("spring.datasource.db-name","jnpf");fixed.put("spring.datasource.prepare-url",jdbc);
  fixed.put("spring.redis.host","127.0.0.1");fixed.put("spring.redis.port",own.getProperty("redisPort"));fixed.put("spring.redis.password",own.getProperty("redisPassword"));fixed.put("spring.redis.database","0");
  fixed.put("spring.cloud.bootstrap.enabled","false");fixed.put("spring.cloud.nacos.config.enabled","false");fixed.put("spring.cloud.nacos.discovery.enabled","false");fixed.put("spring.cloud.discovery.enabled","false");
  fixed.put("config.sharding-sphere-enabled","false");fixed.put("socials.socials-enabled","false");fixed.put("config.IgexinEnabled","false");fixed.put("config.ErrorReport","false");
  fixed.put("xxl.job.enabled","false");fixed.put("xxl.job.executor.port","0");fixed.put("xxl.job.admin.addresses","");
  fixed.put("flowable.async-executor-activate","false");fixed.put("flowable.async-history-executor-activate","false");fixed.put("flowable.database-schema-update","false");
  fixed.put("spring.jmx.enabled","false");fixed.put("spring.main.banner-mode","off");fixed.put("logging.config",root.resolve("own-logback.xml").toUri().toString());
  fixed.put("log.path",root.resolve("logs").toString());fixed.put("context.initializer.classes","xnby.platform.PlatformStartupObservation");
  fixed.put("spring.mail.host","127.0.0.1");fixed.put("spring.mail.port","9");fixed.put("spring.mail.username","own@example.invalid");
  fixed.put("spring.devtools.restart.enabled","false");
  config.putAll(fixed);overridden.addAll(fixed.keySet());
  Properties result=new Properties();config.forEach(result::setProperty);try(var output=Files.newOutputStream(root.resolve("application.properties"),StandardOpenOption.CREATE_NEW)){result.store(output,"Own isolated platform; source external services and credentials replaced");}
  Files.write(root.resolve("overridden-property-names.txt"),overridden,StandardOpenOption.CREATE_NEW);
  Files.writeString(root.resolve("configuration-structure-summary.txt"),"sourceProfile="+profile+"\nsourceProperties="+source.size()+"\nownedProperties="+config.size()+"\nsourceShardingTypeParsedOrExecuted=false\n",StandardOpenOption.CREATE_NEW);
 }
}
