package xnby.replica;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.yaml.snakeyaml.*;
import org.yaml.snakeyaml.nodes.*;

/** Parse original configuration as YAML nodes; emit key coverage, never original values. */
public final class OriginalBusinessConfigInventory {
 static void flatten(Node node,String key,Map<String,String> out) {
  walk(node,key,out,new IdentityHashMap<Node,Boolean>(),0);
 }
 static void walk(Node node,String key,Map<String,String> out,IdentityHashMap<Node,Boolean> stack,int depth) {
  if(depth>32||stack.put(node,Boolean.TRUE)!=null)throw new IllegalArgumentException("CONFIG_DEPTH_OR_CYCLE");
  if(!Arrays.asList(Tag.MAP,Tag.SEQ,Tag.STR,Tag.INT,Tag.FLOAT,Tag.BOOL,Tag.NULL,Tag.TIMESTAMP).contains(node.getTag()))throw new IllegalArgumentException("CONFIG_TAG_REJECTED");
  if(node instanceof MappingNode) {
   for(NodeTuple tuple:((MappingNode)node).getValue()) {
    if(!(tuple.getKeyNode() instanceof ScalarNode))throw new IllegalArgumentException("SCALAR_KEY_REQUIRED");
    String name=((ScalarNode)tuple.getKeyNode()).getValue();
    if(!name.matches("[A-Za-z0-9_.-]{1,128}"))throw new IllegalArgumentException("CONFIG_KEY_SHAPE");
    walk(tuple.getValueNode(),key.isEmpty()?name:key+"."+name,out,stack,depth+1);
   }
  } else if(node instanceof SequenceNode) {
   int i=0;for(Node child:((SequenceNode)node).getValue())walk(child,key+"["+(i++)+"]",out,stack,depth+1);
  } else if(node instanceof ScalarNode) {
   if(out.containsKey(key))throw new IllegalArgumentException("DUPLICATE_CONFIG_KEY");
   out.put(key,Tag.NULL.equals(node.getTag())?"":((ScalarNode)node).getValue());
  } else throw new IllegalArgumentException("CONFIG_NODE_SHAPE");
  stack.remove(node);
 }
 static Map<String,String> parse(String text) {
  if(text.length()>65536)throw new IllegalArgumentException("CONFIG_SIZE");
  LoaderOptions options=new LoaderOptions();options.setMaxAliasesForCollections(10);options.setCodePointLimit(65536);
  Map<String,String> out=new TreeMap<>();int documents=0;
  for(Node node:new Yaml(options).composeAll(new StringReader(text))){if(++documents>1)throw new IllegalArgumentException("ONE_CONFIG_DOCUMENT_REQUIRED");flatten(node,"",out);}
  return out;
 }
 static boolean sensitive(String key) {return key.toLowerCase(Locale.ROOT).matches(".*(password|secret|token|toekn|credential|authorization|access[-]?key|app[-]?key|username|user-name).*");}
 static String timezone(String url) {
  java.util.regex.Matcher m=java.util.regex.Pattern.compile("(?:[?&])serverTimezone=([^&#]*)",java.util.regex.Pattern.CASE_INSENSITIVE).matcher(url);
  if(!m.find())return "not-established";
  String value;try{value=java.net.URLDecoder.decode(m.group(1),"UTF-8");}catch(Exception e){return "explicit-other";}
  if(value.equalsIgnoreCase("Asia/Shanghai"))return "Asia-Shanghai";
  if(value.equalsIgnoreCase("UTC"))return "UTC";
  if(value.equalsIgnoreCase("GMT+8")||value.equalsIgnoreCase("GMT+08:00"))return "GMT-plus-eight";
  return "explicit-other";
 }
 static Properties compare(Map<String,String> original,Properties candidate) {
  Properties result=new Properties();int missing=0,equal=0,different=0,redacted=0;
  for(Map.Entry<String,String> item:original.entrySet()) {
   String key=item.getKey(),state;
   if(sensitive(key)){state=candidate.containsKey(key)?"redacted-present":"redacted-missing";redacted++;}
   else if(!candidate.containsKey(key)){state="missing";missing++;}
   else if(item.getValue().equals(candidate.getProperty(key))){state="equal";equal++;}
   else {state="different";different++;}
   result.setProperty("key."+key,state);
  }
  result.setProperty("sourceProperties",String.valueOf(original.size()));result.setProperty("nonSensitiveMissing",String.valueOf(missing));result.setProperty("nonSensitiveEqual",String.valueOf(equal));result.setProperty("nonSensitiveDifferent",String.valueOf(different));result.setProperty("sensitiveRedacted",String.valueOf(redacted));
  for(String side:new String[]{"master","tow"}) {
   String url=original.getOrDefault("spring.datasource.dynamic.datasource."+side+".url","");
   result.setProperty("originalJdbcTimezone."+side,timezone(url));
  }
  result.setProperty("originalValuesWritten","false");result.setProperty("applicationStarted","false");result.setProperty("fullCloneReady","false");return result;
 }
 static String sha(byte[] raw)throws Exception {StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))s.append(String.format("%02x",b&255));return s.toString();}
 public static void main(String[] args)throws Exception {
  if(args.length!=4||!args[1].matches("[0-9a-f]{64}"))throw new IllegalArgumentException("EXPLICIT_CONFIG_PIN_AND_OUTPUT_REQUIRED");
  Path source=Paths.get(args[0]),candidate=Paths.get(args[2]),output=Paths.get(args[3]);
  if(Files.size(source)>65536||Files.exists(output))throw new IllegalArgumentException("CONFIG_SIZE_OR_OUTPUT_EXISTS");
  byte[] raw=Files.readAllBytes(source);if(!sha(raw).equals(args[1]))throw new IllegalArgumentException("SOURCE_CONFIG_PIN_MISMATCH");
  Properties own=new Properties();try(Reader reader=Files.newBufferedReader(candidate,StandardCharsets.UTF_8)){own.load(reader);}
  Properties report=compare(parse(new String(raw,StandardCharsets.UTF_8)),own);report.setProperty("sourceSHA256",args[1]);report.setProperty("candidateSHA256",sha(Files.readAllBytes(candidate)));
  if(!sha(Files.readAllBytes(source)).equals(args[1]))throw new IllegalArgumentException("SOURCE_CHANGED");
  try(OutputStream stream=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){report.store(stream,"Key coverage only; source values and credentials excluded");}
  System.out.println("ORIGINAL_BUSINESS_CONFIG_KEYS_AUDITED");
 }
}
