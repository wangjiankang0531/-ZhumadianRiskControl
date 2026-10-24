package xnby.replica;
import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.springframework.boot.context.properties.bind.*;
import org.springframework.boot.context.properties.source.MapConfigurationPropertySource;

/** Use the real Spring Binder and two original plain configuration beans, without starting Spring. */
public final class OriginalBusinessBeanBindingFixture {
 static String sha(byte[] raw)throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))s.append(String.format("%02x",b&255));return s.toString();}
 public static void main(String[] args)throws Exception {
  if(args.length!=3||!args[1].matches("[0-9a-f]{64}"))throw new IllegalArgumentException("PINNED_PRIVATE_INPUT_REQUIRED");
  Path input=Paths.get(args[0]),output=Paths.get(args[2]);if(Files.size(input)>256*1024||Files.exists(output))throw new IllegalArgumentException("INPUT_SIZE_OR_OUTPUT_EXISTS");byte[] raw=Files.readAllBytes(input);if(!sha(raw).equals(args[1]))throw new IllegalArgumentException("PRIVATE_INPUT_PIN_MISMATCH");
  Properties expected=new Properties();expected.load(new ByteArrayInputStream(raw));Map<String,String> values=new HashMap<>();for(String key:expected.stringPropertyNames())values.put(key,expected.getProperty(key));Binder binder=new Binder(new MapConfigurationPropertySource(values));
  Map<String,Object> beans=new HashMap<>();beans.put("safety",binder.bind("safety",Bindable.of(Class.forName("com.iemp.endanger.base.entity.SystemParams"))).get());beans.put("flow",binder.bind("flow",Bindable.of(Class.forName("com.iemp.endanger.util.flow.FlowConfig"))).get());int checked=0;
  for(String[] row:OriginalInternalPlatformObservation.BINDINGS){Object bean=beans.get(row[0].startsWith("safety.")?"safety":"flow");Object actual=bean.getClass().getMethod(row[1]).invoke(bean);String want=expected.getProperty(row[0]);if(want==null||actual==null||!(actual instanceof Number?Long.parseLong(want)==((Number)actual).longValue():want.equals(String.valueOf(actual))))throw new IllegalStateException("ORIGINAL_BEAN_BINDING_MISMATCH");checked++;}
  for(String prefix:new String[]{"safety","flow"}){String key=prefix.equals("safety")?"safety.jnpfUrl":"flow.url";Object bean=beans.get(prefix),actual=bean.getClass().getMethod(prefix.equals("safety")?"getJnpfUrl":"getUrl").invoke(bean);if(!expected.getProperty(key).equals(actual))throw new IllegalStateException("ORIGINAL_BEAN_URL_BINDING_MISMATCH");checked++;}
  Properties result=new Properties();result.setProperty("realOriginalBeanPropertyBindingsMatched",Integer.toString(checked));result.setProperty("inputSHA256",args[1]);result.setProperty("springApplicationStarted","false");result.setProperty("httpOrDatabaseRequested","false");result.setProperty("authenticatedBusinessVerified","false");result.setProperty("fullCloneReady","false");
  OriginalInternalPlatformObservation.publish(output.getParent(),result);Properties published=new Properties();try(InputStream stream=Files.newInputStream(output.getParent().resolve("internal-platform-observation.properties"))){published.load(stream);}if(!"16".equals(published.getProperty("realOriginalBeanPropertyBindingsMatched"))||Files.exists(output.getParent().resolve("internal-platform-observation.pending")))throw new IllegalStateException("ATOMIC_RECEIPT_NOT_COMPLETE");
  try{OriginalInternalPlatformObservation.publish(output.getParent(),result);throw new IllegalStateException("DUPLICATE_RECEIPT_ACCEPTED");}catch(FileAlreadyExistsException expectedDuplicate){}
  result.setProperty("atomicReceiptPublicationVerified","true");result.setProperty("duplicateReceiptRejected","true");
  try(OutputStream stream=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){result.store(stream,"Real Spring Binder and original configuration POJOs; no values written");}
  System.out.println("REAL_ORIGINAL_BEAN_BINDINGS_MATCHED="+checked);
 }
}
