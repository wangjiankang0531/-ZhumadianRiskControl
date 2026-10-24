package xnby.replica;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

/** Prepare an unapplied owned overlay: exact original business codes and explicit local API base. */
public final class OriginalBusinessSemantics {
 static final String[] KEEP={"safety.hiddenDangerFormCode","safety.checkLedgerFormCode","safety.roleId","safety.auditRoleId","safety.flow-category","safety.env-role-id","safety.safety-report-days","safety.hidden-danger-days","flow.workCode","flow.inspectionHandle","flow.workReservation","flow.workProgramme","flow.eventInfoHandle","flow.eventTaskHandle","spring.servlet.multipart.max-file-size","spring.servlet.multipart.max-request-size","spring.cache.type","spring.cache.redis.key-prefix","mybatis-plus.tenant-enable","mybatis-plus.global-config.db-config.column-format"};
 static String localBase(String value)throws Exception {
  URI uri=new URI(value);
  if(!"http".equals(uri.getScheme())||!"127.0.0.1".equals(uri.getHost())||uri.getPort()<1024||uri.getPort()>65535||uri.getRawUserInfo()!=null||uri.getRawQuery()!=null||uri.getRawFragment()!=null||!(uri.getRawPath()==null||uri.getRawPath().isEmpty()))throw new IllegalArgumentException("OWN_PLATFORM_BASE_REQUIRED");
  return value;
 }
 static String remap(String original,String local)throws Exception {
  if(original==null)throw new IllegalArgumentException("ORIGINAL_INTERNAL_API_REQUIRED");
  URI uri=new URI(original);String path=uri.getRawPath();
  if(!Arrays.asList("http","https").contains(uri.getScheme())||uri.getHost()==null||uri.getRawUserInfo()!=null||uri.getRawQuery()!=null||uri.getRawFragment()!=null||path!=null&&!path.matches("(?:/[A-Za-z0-9_-]+)*/?"))throw new IllegalArgumentException("ORIGINAL_INTERNAL_API_SHAPE");
  return local+(path==null?"":path);
 }
 static String timezoneUrl(String own,String original,String schema)throws Exception {
  if(own==null||!own.matches("jdbc:mysql://127\\.0\\.0\\.1:[0-9]{4,5}/"+schema+"\\?.*"))throw new IllegalArgumentException("OWN_JDBC_IDENTITY_REQUIRED");
  Matcher matcher=Pattern.compile("(?:[?&])serverTimezone=([^&#]+)",Pattern.CASE_INSENSITIVE).matcher(original==null?"":original);
  if(!matcher.find())throw new IllegalArgumentException("ORIGINAL_TIMEZONE_REQUIRED");String zone=URLDecoder.decode(matcher.group(1),"UTF-8");
  if(!Arrays.asList("GMT+8","GMT+08:00","Asia/Shanghai","UTC").contains(zone))throw new IllegalArgumentException("ORIGINAL_TIMEZONE_NOT_RECOGNIZED");
  Matcher target=Pattern.compile("([?&])serverTimezone=[^&#]*",Pattern.CASE_INSENSITIVE).matcher(own);if(!target.find())throw new IllegalArgumentException("OWN_TIMEZONE_PARAMETER_REQUIRED");String replaced=target.replaceFirst("$1serverTimezone="+URLEncoder.encode(zone,"UTF-8"));if(target.find())throw new IllegalArgumentException("DUPLICATE_OWN_TIMEZONE");return replaced;
 }
 static Properties prepare(Map<String,String> source,Properties own,String local)throws Exception {
  local=localBase(local);Properties result=new Properties();result.putAll(own);
  for(String key:KEEP){if(!source.containsKey(key)||OriginalBusinessConfigInventory.sensitive(key))throw new IllegalArgumentException("ORIGINAL_BUSINESS_KEY_REQUIRED");result.setProperty(key,source.get(key));}
  for(String key:new String[]{"safety.jnpfUrl","flow.url"})result.setProperty(key,remap(source.get(key),local));
  for(String side:new String[]{"master","tow"}){
   String key="spring.datasource.dynamic.datasource."+side+".url";result.setProperty(key,timezoneUrl(own.getProperty(key),source.get(key),"master".equals(side)?"tj_endanger":"jnpf"));
  }
  return result;
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=5||!args[1].matches("[0-9a-f]{64}"))throw new IllegalArgumentException("SOURCE_PIN_OWN_BASE_OUTPUT_REQUIRED");
  Path source=Paths.get(args[0]),candidate=Paths.get(args[2]),output=Paths.get(args[4]);if(Files.size(source)>65536||Files.exists(output))throw new IllegalArgumentException("SOURCE_SIZE_OR_OUTPUT_EXISTS");
  byte[] raw=Files.readAllBytes(source);if(!OriginalBusinessConfigInventory.sha(raw).equals(args[1]))throw new IllegalArgumentException("SOURCE_CONFIG_PIN_MISMATCH");
  Properties own=new Properties();try(Reader reader=Files.newBufferedReader(candidate,StandardCharsets.UTF_8)){own.load(reader);}
  Properties result=prepare(OriginalBusinessConfigInventory.parse(new String(raw,StandardCharsets.UTF_8)),own,args[3]);
  if(!OriginalBusinessConfigInventory.sha(Files.readAllBytes(source)).equals(args[1]))throw new IllegalArgumentException("SOURCE_CONFIG_CHANGED");
  try(OutputStream stream=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){result.store(stream,"UNAPPLIED owned overlay: exact original business codes, local internal API and original JDBC timezone");}
  Properties summary=new Properties();summary.setProperty("originalSemanticKeysCopied",String.valueOf(KEEP.length));summary.setProperty("internalApiBasesRemapped","2");summary.setProperty("jdbcTimezonesRestored","2");summary.setProperty("originalCredentialsCopied","false");summary.setProperty("applicationStarted","false");summary.setProperty("appliedToRunningCandidate","false");summary.setProperty("remainingIntegrationsVerified","false");summary.setProperty("fullCloneReady","false");
  try(OutputStream stream=Files.newOutputStream(output.resolveSibling("semantics-summary.properties"),StandardOpenOption.CREATE_NEW)){summary.store(stream,"No original values");}
  System.out.println("ORIGINAL_BUSINESS_SEMANTICS_PREPARED_NOT_APPLIED");
 }
}
