package xnby.replica;
import java.util.*;
/** Detect disabled defaults and distinguish logical paths without exposing their contents. */
public final class PlatformStorageInventoryFixture {
 static int checks;
 static void require(boolean value){if(!value)throw new IllegalStateException("PLATFORM_TOPOLOGY_FIXTURE_FAILED");checks++;}
 public static void main(String[] args) {
  String p="config.file-storage.";Map<String,String> original=new HashMap<>();
  original.put(p+"default-platform","fixture-local");original.put(p+"local-plus[0].platform","fixture-local");original.put(p+"local-plus[0].enable-storage","true");original.put(p+"local-plus[0].base-path","files/");original.put(p+"local-plus[0].domain","");
  original.put(p+"minio[0].platform","fixture-s3");original.put(p+"minio[0].enable-storage","true");original.put("config.DocumentFilePath","documents/");original.put("config.TemporaryFilePath","/temporary/");
  Properties candidate=new Properties();candidate.setProperty(p+"default-platform","fixture-local");candidate.setProperty(p+"local-plus[0].platform","fixture-local");candidate.setProperty(p+"local-plus[0].enable-storage","false");
  Properties out=OriginalPlatformStorageInventory.inspect(original,candidate);
  require(out.getProperty("originalEnabledProviders").equals("2"));require(out.getProperty("originalEnabledDefaultProviders").equals("1"));require(out.getProperty("candidateEnabledProviders").equals("0"));require(out.getProperty("defaultPlatformPreserved").equals("true"));require(out.getProperty("originalPathSettings").equals("2"));require(out.getProperty("originalPlainRelativePaths").equals("1"));require(out.getProperty("originalRootRelativeLogicalPaths").equals("1"));require(out.getProperty("candidateRemappedPathSettings").equals("2"));
  candidate.setProperty(p+"local-plus[0].enable-storage","true");out=OriginalPlatformStorageInventory.inspect(original,candidate);require(out.getProperty("candidateEnabledProviders").equals("1"));
  candidate.setProperty(p+"default-platform","fixture-other");out=OriginalPlatformStorageInventory.inspect(original,candidate);require(out.getProperty("defaultPlatformPreserved").equals("false"));
  original.put("config.DocumentFilePath","../outside/");out=OriginalPlatformStorageInventory.inspect(original,candidate);require(out.getProperty("originalUnsafePathShapes").equals("1"));
  require(!out.toString().contains("../outside/")&&!out.toString().contains("fixture-local"));
  System.out.println("PLATFORM_STORAGE_INVENTORY_CHECKS="+checks);
 }
}
