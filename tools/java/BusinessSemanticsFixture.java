package xnby.replica;
import java.util.*;
public final class BusinessSemanticsFixture {
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("SEMANTICS_CHECK_FAILED");checks++;}
 interface Action {void run()throws Exception;}
 static void rejects(Action action)throws Exception{try{action.run();throw new AssertionError("SEMANTICS_INPUT_ACCEPTED");}catch(IllegalArgumentException expected){checks++;}}
 public static void main(String[] args)throws Exception {
  Map<String,String> source=new HashMap<>();for(String key:OriginalBusinessSemantics.KEEP)source.put(key,"fixture-original-value");source.put("safety.jnpfUrl","http://source.invalid");source.put("flow.url","http://source.invalid/");source.put("spring.datasource.dynamic.datasource.master.url","jdbc:mysql://source.invalid/a?serverTimezone=GMT%2B8");source.put("spring.datasource.dynamic.datasource.tow.url","jdbc:mysql://source.invalid/b?serverTimezone=Asia%2FShanghai");source.put("spring.datasource.dynamic.datasource.master.password","private-original-password");
  Properties own=new Properties();own.setProperty("spring.datasource.dynamic.datasource.master.url","jdbc:mysql://127.0.0.1:33333/tj_endanger?useSSL=false&serverTimezone=UTC&characterEncoding=UTF-8");own.setProperty("spring.datasource.dynamic.datasource.tow.url","jdbc:mysql://127.0.0.1:33333/jnpf?serverTimezone=UTC&useSSL=false");own.setProperty("spring.datasource.dynamic.datasource.master.password","private-owned-password");Properties result=OriginalBusinessSemantics.prepare(source,own,"http://127.0.0.1:39000");
  check(Arrays.stream(OriginalBusinessSemantics.KEEP).allMatch(k->source.get(k).equals(result.getProperty(k)))&&"http://127.0.0.1:39000".equals(result.getProperty("safety.jnpfUrl"))&&"http://127.0.0.1:39000/".equals(result.getProperty("flow.url")));
  check(result.getProperty("spring.datasource.dynamic.datasource.master.url").contains("serverTimezone=GMT%2B8")&&result.getProperty("spring.datasource.dynamic.datasource.master.url").contains("useSSL=false")&&"private-owned-password".equals(result.getProperty("spring.datasource.dynamic.datasource.master.password"))&&"fixture-original-value".equals(source.get(OriginalBusinessSemantics.KEEP[0])));
  rejects(()->OriginalBusinessSemantics.prepare(source,own,"http://other.invalid:39000"));
  rejects(()->OriginalBusinessSemantics.remap("https://source.invalid/?token=fixture","http://127.0.0.1:39000"));
  rejects(()->OriginalBusinessSemantics.timezoneUrl("jdbc:mysql://other.invalid:33333/tj_endanger?serverTimezone=UTC",source.get("spring.datasource.dynamic.datasource.master.url"),"tj_endanger"));
  rejects(()->{Map<String,String> missing=new HashMap<>(source);missing.remove(OriginalBusinessSemantics.KEEP[0]);OriginalBusinessSemantics.prepare(missing,own,"http://127.0.0.1:39000");});
  System.out.println("BUSINESS_SEMANTICS_FIXTURE_CHECKS="+checks);
 }
}
