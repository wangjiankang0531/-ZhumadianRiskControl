package xnby.replica;
import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Copy only the original bucket identity; credentials belong to our owned store. */
public final class OriginalBusinessObjectStoreOverlay {
 static Properties overlay(Map<String,String> original,Properties candidate,Properties own)throws Exception {
  String bucket=original.get("minio.bucketName");
  if(bucket==null||!bucket.matches("[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]"))throw new IllegalArgumentException("ORIGINAL_BUCKET_IDENTITY_REQUIRED");
  URI endpoint=new URI(own.getProperty("endpoint"));
  if(!"http".equals(endpoint.getScheme())||!"127.0.0.1".equals(endpoint.getHost())||endpoint.getPort()<1024||endpoint.getPort()>65535||endpoint.getRawUserInfo()!=null||endpoint.getRawQuery()!=null||endpoint.getRawFragment()!=null||!endpoint.getRawPath().isEmpty())throw new IllegalArgumentException("OWN_LOOPBACK_OBJECT_STORE_REQUIRED");
  if(!own.getProperty("accessKey","").matches("own-[a-f0-9]{16}")||!own.getProperty("secretKey","").matches("[a-f0-9]{48}"))throw new IllegalArgumentException("OWN_GENERATED_STORE_CREDENTIALS_REQUIRED");
  Properties result=new Properties();result.putAll(candidate);result.setProperty("minio.url","127.0.0.1");result.setProperty("minio.port",Integer.toString(endpoint.getPort()));result.setProperty("minio.secure","false");result.setProperty("minio.accessKey",own.getProperty("accessKey"));result.setProperty("minio.secretKey",own.getProperty("secretKey"));result.setProperty("minio.bucketName",bucket);return result;
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=5||!args[1].matches("[a-f0-9]{64}"))throw new IllegalArgumentException("EXPLICIT_SOURCE_PIN_AND_OWN_INPUTS_REQUIRED");
  Path source=Paths.get(args[0]),candidate=Paths.get(args[2]),connection=Paths.get(args[3]),output=Paths.get(args[4]);
  if(Files.size(source)>65536||Files.exists(output))throw new IllegalArgumentException("SOURCE_SIZE_OR_OUTPUT_EXISTS");
  byte[] raw=Files.readAllBytes(source);if(!OriginalBusinessConfigInventory.sha(raw).equals(args[1]))throw new IllegalArgumentException("SOURCE_PIN_MISMATCH");
  Properties base=new Properties(),own=new Properties();try(Reader reader=Files.newBufferedReader(candidate,StandardCharsets.UTF_8)){base.load(reader);}try(Reader reader=Files.newBufferedReader(connection,StandardCharsets.UTF_8)){own.load(reader);}
  Properties result=overlay(OriginalBusinessConfigInventory.parse(new String(raw,StandardCharsets.UTF_8)),base,own);
  if(!OriginalBusinessConfigInventory.sha(Files.readAllBytes(source)).equals(args[1]))throw new IllegalArgumentException("SOURCE_CONFIG_CHANGED");
  try(OutputStream stream=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){result.store(stream,"Owned object store only; original bucket identity, no source credentials copied");}
  System.out.println("ORIGINAL_BUCKET_AND_OWN_OBJECT_STORE_OVERLAY_PREPARED");
 }
}
