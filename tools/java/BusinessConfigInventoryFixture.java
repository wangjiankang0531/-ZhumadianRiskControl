package xnby.replica;
import java.io.*;
import java.util.*;
public final class BusinessConfigInventoryFixture {
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("CONFIG_INVENTORY_CHECK_FAILED");checks++;}
 static void rejects(String yaml){try{OriginalBusinessConfigInventory.parse(yaml);throw new AssertionError("CONFIG_INPUT_ACCEPTED");}catch(IllegalArgumentException|org.yaml.snakeyaml.error.YAMLException expected){checks++;}}
 public static void main(String[] args)throws Exception {
  String source="safety:\n  jnpfUrl: http://private-host/fixture\n  hiddenDangerFormCode: fixture-original-id\n  app-secret: fixture-private-secret\nspring:\n  datasource:\n    dynamic:\n      datasource:\n        master:\n          url: jdbc:mysql://private-host/db?serverTimezone=Asia/Shanghai\n        tow:\n          url: jdbc:mysql://private-host/db?serverTimezone=UTC\nflag: true\n";
  Map<String,String> original=OriginalBusinessConfigInventory.parse(source);Properties candidate=new Properties();candidate.setProperty("flag","true");candidate.setProperty("safety.jnpfUrl","http://127.0.0.1:9");
  Properties result=OriginalBusinessConfigInventory.compare(original,candidate);
  check("missing".equals(result.getProperty("key.safety.hiddenDangerFormCode"))&&"different".equals(result.getProperty("key.safety.jnpfUrl"))&&"equal".equals(result.getProperty("key.flag")));
  StringWriter writer=new StringWriter();result.store(writer,"fixture");String text=writer.toString();check(!text.contains("private-host")&&!text.contains("fixture-original-id")&&!text.contains("fixture-private-secret")&&"redacted-missing".equals(result.getProperty("key.safety.app-secret"))&&OriginalBusinessConfigInventory.sensitive("dockToekn"));
  check("Asia-Shanghai".equals(result.getProperty("originalJdbcTimezone.master"))&&"UTC".equals(result.getProperty("originalJdbcTimezone.tow"))&&"GMT-plus-eight".equals(OriginalBusinessConfigInventory.timezone("jdbc:mysql://private-host/db?serverTimezone=GMT%2B8")));
  rejects("a: 1\na: 2\n");rejects("a: 1\n---\nb: 2\n");rejects("a: &cycle {next: *cycle}\n");rejects("a: !!java/object:java.lang.Runtime {}\n");
  System.out.println("CONFIG_INVENTORY_FIXTURE_CHECKS="+checks);
 }
}
