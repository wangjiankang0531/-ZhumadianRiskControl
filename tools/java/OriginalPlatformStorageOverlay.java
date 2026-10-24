package xnby.replica;
import java.io.*;
import java.net.URI;
import java.nio.file.*;
import java.util.*;
import java.util.zip.ZipFile;

/** Restore original provider selection and logical paths; replace physical location and credentials. */
public final class OriginalPlatformStorageOverlay {
 static void require(boolean v,String code){if(!v)throw new IllegalArgumentException(code);}
 static Properties overlay(Map<String,String> original,Properties candidate,Properties own,Path files)throws Exception {
  String p="config.file-storage.",local=p+"local-plus[0].",minio=p+"minio[0].";
  require("true".equals(original.get(local+"enable-storage"))&&"true".equals(original.get(minio+"enable-storage")),"ORIGINAL_TWO_PROVIDER_TOPOLOGY_REQUIRED");
  require(original.get(local+"platform")!=null&&original.get(local+"platform").equals(original.get(p+"default-platform")),"ORIGINAL_LOCAL_DEFAULT_REQUIRED");
  require("".equals(original.get(local+"domain"))&&"".equals(original.get(minio+"domain"))&&"".equals(original.get(minio+"base-path")),"ORIGINAL_EMPTY_DOMAINS_AND_OBJECT_PREFIX_REQUIRED");
  require(Arrays.asList("true","false").contains(original.get(local+"enable-access")),"ORIGINAL_ACCESS_FLAG_REQUIRED");
  require(original.get(minio+"platform")!=null&&!original.get(minio+"platform").equals(original.get(local+"platform")),"DISTINCT_ORIGINAL_PROVIDER_IDENTITIES_REQUIRED");
  String bucket=original.get(minio+"bucket-name");require(bucket!=null&&bucket.matches("[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]"),"ORIGINAL_PLATFORM_BUCKET_REQUIRED");
  URI endpoint=new URI(own.getProperty("endpoint",""));
  require("http".equals(endpoint.getScheme())&&"127.0.0.1".equals(endpoint.getHost())&&endpoint.getPort()>=1024&&endpoint.getPort()<=65535&&endpoint.getRawUserInfo()==null&&endpoint.getRawQuery()==null&&endpoint.getRawFragment()==null&&endpoint.getRawPath().isEmpty(),"OWN_LOOPBACK_STORE_REQUIRED");
  require(own.getProperty("accessKey","").matches("own-[a-f0-9]{16}")&&own.getProperty("secretKey","").matches("[a-f0-9]{48}"),"OWN_GENERATED_CREDENTIALS_REQUIRED");
  Path actual=files.toRealPath();require(Files.isDirectory(actual)&&!Files.isSymbolicLink(files),"EXISTING_OWN_STORAGE_DIRECTORY_REQUIRED");
  Properties out=new Properties();out.putAll(candidate);
  out.setProperty(p+"default-platform",original.get(p+"default-platform"));
  for(String key:new String[]{"platform","enable-storage","enable-access","domain","path-patterns"}) {
   String value=original.get(local+key);require(value!=null,"COMPLETE_ORIGINAL_LOCAL_CONFIGURATION_REQUIRED");out.setProperty(local+key,value);
  }
  out.setProperty(local+"base-path",actual.toString().replace('\\','/')+"/");out.setProperty(local+"storage-path","");
  for(String key:new String[]{"platform","enable-storage","bucket-name","base-path","domain"})out.setProperty(minio+key,original.get(minio+key));
  out.setProperty(minio+"end-point",endpoint.toString());out.setProperty(minio+"access-key",own.getProperty("accessKey"));out.setProperty(minio+"secret-key",own.getProperty("secretKey"));
  int paths=0;
  for(Map.Entry<String,String> e:original.entrySet())if(e.getKey().startsWith("config.")&&e.getKey().endsWith("Path")) {
   String value=e.getValue();require(value.matches("[A-Za-z0-9_./-]{1,256}")&&!value.startsWith("/")&&!Arrays.asList(value.split("/",-1)).contains(".."),"ORIGINAL_PLAIN_RELATIVE_LOGICAL_PATH_REQUIRED");out.setProperty(e.getKey(),value);paths++;
  }
  require(paths==13,"EXACT_ORIGINAL_THIRTEEN_LOGICAL_PATHS_REQUIRED");
  // Other providers remain disabled; this adapter does not authorize their external endpoints.
  for(String kind:new String[]{"aliyun-oss","qiniu-kodo","tencent-cos"})require("false".equals(out.getProperty(p+kind+"[0].enable-storage")),"UNRELATED_PROVIDER_MUST_REMAIN_DISABLED");
  return out;
 }
 static Map<String,String> original(Path archive)throws Exception {
  Map<String,String> out=new TreeMap<>();try(ZipFile zip=new ZipFile(archive.toFile())) {
   out.putAll(OriginalPlatformStorageInventory.read(zip,"BOOT-INF/classes/application.yml"));String profile=out.get("spring.profiles.active");require(Arrays.asList("test","pro").contains(profile),"KNOWN_ORIGINAL_PROFILE_REQUIRED");out.putAll(OriginalPlatformStorageInventory.read(zip,"BOOT-INF/classes/application-"+profile+".yml"));
  }return out;
 }
 public static void main(String[] args)throws Exception {
  require(args.length==5,"ARCHIVE_CANDIDATE_OWN_CONNECTION_STORAGE_OUTPUT_REQUIRED");
  Properties base=new Properties(),own=new Properties();try(InputStream in=Files.newInputStream(Paths.get(args[1]))){base.load(in);}try(InputStream in=Files.newInputStream(Paths.get(args[2]))){own.load(in);}
  Properties prepared=overlay(original(Paths.get(args[0])),base,own,Paths.get(args[3]));
  try(OutputStream stream=Files.newOutputStream(Paths.get(args[4]),StandardOpenOption.CREATE_NEW)){prepared.store(stream,"Original provider identities and logical paths; owned physical storage and credentials only");}
  System.out.println("ORIGINAL_PLATFORM_STORAGE_OVERLAY_PREPARED_NOT_STARTED");
 }
}
