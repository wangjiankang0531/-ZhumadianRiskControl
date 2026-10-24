package xnby.replica;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Storage topology only: never emit original endpoint, bucket, credential or path values. */
public final class OriginalPlatformStorageInventory {
 static Properties inspect(Map<String,String> source, Properties candidate) {
  Properties out=new Properties();String prefix="config.file-storage.";
  String selected=source.get(prefix+"default-platform");
  int enabled=0,selectedEnabled=0,candidateEnabled=0;
  for(String kind:Arrays.asList("local-plus","minio","aliyun-oss","qiniu-kodo","tencent-cos")) {
   String base=prefix+kind+"[0].";
   boolean active="true".equalsIgnoreCase(source.get(base+"enable-storage"));
   boolean match=selected!=null && selected.equals(source.get(base+"platform"));
   boolean own="true".equalsIgnoreCase(candidate.getProperty(base+"enable-storage"));
   enabled+=active?1:0; selectedEnabled+=active&&match?1:0;candidateEnabled+=own?1:0;
   out.setProperty(kind+".originalEnabled",String.valueOf(active));
   out.setProperty(kind+".originalDefaultMatches",String.valueOf(match));
   out.setProperty(kind+".candidateEnabled",String.valueOf(own));
   out.setProperty(kind+".candidateDefaultMatches",String.valueOf(candidate.getProperty(prefix+"default-platform","").equals(candidate.getProperty(base+"platform"))));
   out.setProperty(kind+".originalBasePathEmpty",String.valueOf("".equals(source.get(base+"base-path"))));
   out.setProperty(kind+".originalDomainEmpty",String.valueOf("".equals(source.get(base+"domain"))));
  }
  out.setProperty("originalEnabledProviders",String.valueOf(enabled));
  out.setProperty("originalEnabledDefaultProviders",String.valueOf(selectedEnabled));
  out.setProperty("candidateEnabledProviders",String.valueOf(candidateEnabled));
  out.setProperty("defaultPlatformPreserved",String.valueOf(selected!=null&&selected.equals(candidate.getProperty(prefix+"default-platform"))));
  int paths=0,changed=0,logical=0,relative=0,placeholders=0,unsafe=0;
  for(Map.Entry<String,String> e:source.entrySet())if(e.getKey().startsWith("config.")&&e.getKey().endsWith("Path")) {
   paths++;changed+=e.getValue().equals(candidate.getProperty(e.getKey()))?0:1;
   String value=e.getValue();if(value.startsWith("/")&&!value.startsWith("//")&&!value.contains("\\")&&!value.contains(":")&&!Arrays.asList(value.split("/",-1)).contains(".."))logical++;
   if(!value.startsWith("/")&&!value.contains("\\")&&!value.contains(":")&&!value.contains("${")&&!Arrays.asList(value.split("/",-1)).contains(".."))relative++;
   if(value.contains("${"))placeholders++;
   if(value.contains("\\")||value.contains(":")||Arrays.asList(value.split("/",-1)).contains(".."))unsafe++;
  }
  out.setProperty("originalPathSettings",String.valueOf(paths));out.setProperty("candidateRemappedPathSettings",String.valueOf(changed));
  out.setProperty("originalRootRelativeLogicalPaths",String.valueOf(logical));
  out.setProperty("originalPlainRelativePaths",String.valueOf(relative));out.setProperty("originalPlaceholderPaths",String.valueOf(placeholders));out.setProperty("originalUnsafePathShapes",String.valueOf(unsafe));
  String localBase=source.getOrDefault(prefix+"local-plus[0].base-path","");
  out.setProperty("local-plus.originalBaseHasPlaceholder",String.valueOf(localBase.contains("${")));
  out.setProperty("local-plus.originalBaseWindowsAbsolute",String.valueOf(localBase.matches("^[A-Za-z]:.*")));
  out.setProperty("local-plus.originalBaseStartsSlash",String.valueOf(localBase.startsWith("/")));
  out.setProperty("originalValuesWrittenToTopologyReport","false");out.setProperty("applicationStarted","false");out.setProperty("fullCloneReady","false");return out;
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=3)throw new IllegalArgumentException("ARCHIVE_CANDIDATE_NEW_OUTPUT_REQUIRED");
  Map<String,String> original=new TreeMap<>();String profile;
  try(ZipFile zip=new ZipFile(args[0])) {
   original.putAll(read(zip,"BOOT-INF/classes/application.yml"));
   profile=original.get("spring.profiles.active");
   if(!Arrays.asList("pro","test").contains(profile))throw new IllegalArgumentException("KNOWN_PROFILE_REQUIRED");
   original.putAll(read(zip,"BOOT-INF/classes/application-"+profile+".yml"));
  }
  Properties candidate=new Properties();try(InputStream in=Files.newInputStream(Paths.get(args[1]))){candidate.load(in);}
  Properties out=inspect(original,candidate);out.setProperty("archiveSelectedProfile",profile);
  try(OutputStream stream=Files.newOutputStream(Paths.get(args[2]),StandardOpenOption.CREATE_NEW)){out.store(stream,"Storage topology only; original values excluded");}
  System.out.println("ORIGINAL_PLATFORM_STORAGE_TOPOLOGY_AUDITED");
 }
 static Map<String,String> read(ZipFile zip,String path)throws Exception {
  ZipEntry e=zip.getEntry(path);if(e==null||e.getSize()<0||e.getSize()>65536)throw new IllegalArgumentException("BOUNDED_CONFIG_REQUIRED");
  byte[] raw;try(InputStream in=zip.getInputStream(e)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int n;while((n=in.read(buffer))!=-1){if(out.size()+n>65536)throw new IllegalArgumentException("CONFIG_SIZE_MISMATCH");out.write(buffer,0,n);}raw=out.toByteArray();}
  if(raw.length!=e.getSize())throw new IllegalArgumentException("CONFIG_SIZE_MISMATCH");
  return OriginalBusinessConfigInventory.parse(new String(raw,StandardCharsets.UTF_8));
 }
}
