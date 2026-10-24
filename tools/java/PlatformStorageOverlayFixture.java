package xnby.replica;
import java.nio.file.*;
import java.util.*;
public final class PlatformStorageOverlayFixture {
 static int checks;
 interface Checked {void run()throws Exception;}
 static void require(boolean v){if(!v)throw new IllegalStateException("PLATFORM_STORAGE_OVERLAY_FIXTURE_FAILED");checks++;}
 static void rejected(Checked call)throws Exception{try{call.run();}catch(IllegalArgumentException e){checks++;return;}throw new IllegalStateException("INVALID_PLATFORM_STORAGE_OVERLAY_ACCEPTED");}
 static Properties props(Properties p){Properties copy=new Properties();copy.putAll(p);return copy;}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath();String p="config.file-storage.",l=p+"local-plus[0].",m=p+"minio[0].";
  Map<String,String> original=new HashMap<>();original.put(p+"default-platform","fixture-local");original.put(l+"platform","fixture-local");original.put(l+"enable-storage","true");original.put(l+"enable-access","true");original.put(l+"domain","");original.put(l+"path-patterns","/fixture/**");original.put(l+"base-path","C:/original-private/");
  original.put(m+"platform","fixture-s3");original.put(m+"enable-storage","true");original.put(m+"bucket-name","original-fixture-bucket");original.put(m+"base-path","");original.put(m+"domain","");original.put(m+"access-key","source-access-do-not-copy");original.put(m+"secret-key","source-secret-do-not-copy");
  for(int i=0;i<13;i++)original.put("config.Fixture"+i+"Path","fixture"+i+"/");
  Properties base=new Properties();base.setProperty("unrelated.original","same");for(String kind:new String[]{"aliyun-oss","qiniu-kodo","tencent-cos"})base.setProperty(p+kind+"[0].enable-storage","false");
  Properties own=new Properties();own.setProperty("endpoint","http://127.0.0.1:52345");own.setProperty("accessKey","own-0123456789abcdef");own.setProperty("secretKey",String.join("",Collections.nCopies(48,"a")));
  Properties result=OriginalPlatformStorageOverlay.overlay(original,base,own,root);
  require(result.getProperty(p+"default-platform").equals("fixture-local"));require(result.getProperty(l+"enable-storage").equals("true"));require(result.getProperty(m+"enable-storage").equals("true"));require(result.getProperty(l+"base-path").equals(root.toString().replace('\\','/')+"/"));require(result.getProperty(l+"storage-path").equals(""));require(result.getProperty(m+"secret-key").equals(own.getProperty("secretKey")));require(result.getProperty("config.Fixture0Path").equals("fixture0/"));require(result.getProperty("unrelated.original").equals("same"));require(!result.toString().contains("source-secret-do-not-copy")&&!result.toString().contains("C:/original-private/"));require(!base.containsKey(l+"enable-storage"));
  for(String endpoint:new String[]{"http://192.168.0.107:52345","https://127.0.0.1:52345","http://user@127.0.0.1:52345","http://127.0.0.1:52345/other","http://127.0.0.1:52345?x=1"}){Properties bad=props(own);bad.setProperty("endpoint",endpoint);rejected(()->OriginalPlatformStorageOverlay.overlay(original,base,bad,root));}
  Properties secret=props(own);secret.setProperty("secretKey","old-private-secret");rejected(()->OriginalPlatformStorageOverlay.overlay(original,base,secret,root));
  for(String path:new String[]{"../outside/","C:/original/","/outside/","${config.other}"}){Map<String,String> bad=new HashMap<>(original);bad.put("config.Fixture0Path",path);rejected(()->OriginalPlatformStorageOverlay.overlay(bad,base,own,root));}
  Map<String,String> topology=new HashMap<>(original);topology.put(p+"default-platform","fixture-s3");rejected(()->OriginalPlatformStorageOverlay.overlay(topology,base,own,root));
  Map<String,String> domain=new HashMap<>(original);domain.put(l+"domain","https://old.invalid/");rejected(()->OriginalPlatformStorageOverlay.overlay(domain,base,own,root));
  Properties unrelated=props(base);unrelated.setProperty(p+"aliyun-oss[0].enable-storage","true");rejected(()->OriginalPlatformStorageOverlay.overlay(original,unrelated,own,root));
  System.out.println("PLATFORM_STORAGE_OVERLAY_CHECKS="+checks);
 }
}
