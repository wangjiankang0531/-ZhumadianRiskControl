package xnby.replica;
import java.util.*;
public final class ObjectStoreOverlayFixture {
 interface Action{void run()throws Exception;}
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("OBJECT_STORE_OVERLAY_CHECK_FAILED");checks++;}
 static void reject(Action action)throws Exception{try{action.run();throw new AssertionError("INVALID_STORE_OVERLAY_ACCEPTED");}catch(IllegalArgumentException expected){checks++;}}
 public static void main(String[] args)throws Exception{
  Map<String,String> source=new HashMap<String,String>();source.put("minio.bucketName","original-fixture-bucket");source.put("minio.accessKey","source-not-for-copy");source.put("minio.secretKey","source-not-for-copy");
  Properties base=new Properties();base.setProperty("unrelated.business.key","keep");base.setProperty("minio.port","9");Properties own=new Properties();own.setProperty("endpoint","http://127.0.0.1:12000");own.setProperty("accessKey","own-0123456789abcdef");own.setProperty("secretKey","0123456789abcdef0123456789abcdef0123456789abcdef");
  Properties result=OriginalBusinessObjectStoreOverlay.overlay(source,base,own);check(result.getProperty("minio.bucketName").equals("original-fixture-bucket"));check(result.getProperty("minio.accessKey").equals(own.getProperty("accessKey")));check(result.getProperty("minio.secretKey").equals(own.getProperty("secretKey")));check(result.getProperty("unrelated.business.key").equals("keep"));check(result.getProperty("minio.url").equals("127.0.0.1")&&result.getProperty("minio.port").equals("12000")&&result.getProperty("minio.secure").equals("false"));check(base.getProperty("minio.port").equals("9")&&!base.containsKey("minio.bucketName"));
  for(String endpoint:new String[]{"http://192.0.2.1:12000","https://127.0.0.1:12000","http://127.0.0.1:12000/path","http://127.0.0.1:12000?q=1","http://user@127.0.0.1:12000","http://127.0.0.1:12000#fragment","http://127.0.0.1:9"}){Properties invalid=new Properties();invalid.putAll(own);invalid.setProperty("endpoint",endpoint);reject(()->OriginalBusinessObjectStoreOverlay.overlay(source,base,invalid));}
  for(String bucket:new String[]{"","../original","UPPER-bucket","x"}){Map<String,String> invalid=new HashMap<String,String>(source);invalid.put("minio.bucketName",bucket);reject(()->OriginalBusinessObjectStoreOverlay.overlay(invalid,base,own));}
  Properties invalid=new Properties();invalid.putAll(own);invalid.setProperty("accessKey","source-not-for-copy");reject(()->OriginalBusinessObjectStoreOverlay.overlay(source,base,invalid));
  System.out.println("OBJECT_STORE_OVERLAY_FIXTURE_CHECKS="+checks);
 }
}
