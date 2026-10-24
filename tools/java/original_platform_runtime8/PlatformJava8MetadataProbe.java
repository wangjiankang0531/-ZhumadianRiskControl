package xnby.platform;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import javax.script.*;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.core.type.classreading.SimpleMetadataReaderFactory;
import org.springframework.beans.factory.annotation.AnnotatedGenericBeanDefinition;
import org.springframework.beans.factory.support.SimpleBeanDefinitionRegistry;
import org.springframework.context.annotation.AnnotationBeanNameGenerator;
import xnby.compat.Java8IO;

/** Original Spring scans and bean naming, plus the installed JDK's real script engine. */
public final class PlatformJava8MetadataProbe {
 public static void run(Path root)throws Exception{
  ClassLoader child=PlatformJava8MetadataProbe.class.getClassLoader(),previous=Thread.currentThread().getContextClassLoader();
  List<String> rows=new ArrayList<String>();Thread.currentThread().setContextClassLoader(child);
  try{
   PathMatchingResourcePatternResolver resolver=new PathMatchingResourcePatternResolver(child);
   String pattern=System.getProperty("own.platform.metadata.pattern","classpath*:jnpf/**/*.class");
   Resource[] resources=resolver.getResources(pattern);List<String> urls=new ArrayList<String>();
   for(Resource resource:resources)urls.add(resource.getURL().toExternalForm());Collections.sort(urls);
   Files.write(root.resolve("scan-resource-urls.txt"),urls,StandardOpenOption.CREATE_NEW);
   rows.add("scanPattern\t"+pattern);rows.add("fullComponentScanResources\t"+resources.length);
   rows.add("componentResourceUrlsSHA256\t"+Java8IO.hex(MessageDigest.getInstance("SHA-256").digest(String.join("\n",urls).getBytes(StandardCharsets.UTF_8))));
   for(String name:Arrays.asList("jnpf.config.ConfigValueUtil","org.springframework.boot.availability.ReadinessState","ch.qos.logback.classic.spi.LoggingEvent")){
    Class.forName(name,false,child);rows.add("coldClassAfterScan\t"+name+"\tPASS");
   }
   SimpleMetadataReaderFactory factory=new SimpleMetadataReaderFactory(child);
   for(String name:Arrays.asList("jnpf.config.RedisConfig","jnpf.config.AuthAutoConfigration","jnpf.config.JnpfOauthConfig")){
    String bean=new AnnotationBeanNameGenerator().generateBeanName(new AnnotatedGenericBeanDefinition(factory.getMetadataReader(name).getAnnotationMetadata()),new SimpleBeanDefinitionRegistry());
    rows.add("naming\t"+name+"\tPASS\t"+bean);
   }
   ScriptEngine engine=new ScriptEngineManager().getEngineByName("JavaScript");
   if(engine==null||!"jdk.nashorn.api.scripting.NashornScriptEngine".equals(engine.getClass().getName()))throw new IllegalStateException("ORIGINAL_JDK_NASHORN_MISSING");
   Object value=engine.eval("1 + 2");if(!(value instanceof Number)||((Number)value).intValue()!=3)throw new IllegalStateException("JDK_SCRIPT_EVALUATION_FAILED");
   rows.add("scriptEngine\t"+engine.getClass().getName()+"\tPASS");
   rows.add("javaVersion\t"+System.getProperty("java.version"));
  }finally{
   Thread.currentThread().setContextClassLoader(previous);Files.write(root.resolve("spring-metadata-only-results.tsv"),rows,StandardOpenOption.CREATE_NEW);
  }
 }
}
