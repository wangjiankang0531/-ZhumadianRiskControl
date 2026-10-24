package xnby.platform;
import org.springframework.context.annotation.AnnotationBeanNameGenerator;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.beans.factory.support.BeanDefinitionRegistry;
import org.springframework.beans.factory.annotation.AnnotatedBeanDefinition;
import org.springframework.core.annotation.MergedAnnotation;
import java.nio.file.*;
import java.util.*;
import java.lang.reflect.*;

/** Delegate naming unchanged; record loader identities only when original naming throws. */
public final class ObservedPlatformBeanNameGenerator extends AnnotationBeanNameGenerator{
 public String generateBeanName(BeanDefinition definition,BeanDefinitionRegistry registry){
  try{return super.generateBeanName(definition,registry);}
  catch(RuntimeException original){
   Path output=Paths.get(System.getProperty("own.platform.root")).resolve("bean-name-failure-loaders.tsv");
   if(!Files.exists(output))try{
    List<String> rows=new ArrayList<>();rows.add("beanClass\t"+definition.getBeanClassName());rows.add("errorClass\t"+original.getClass().getName());
    loader(rows,"TCCL",Thread.currentThread().getContextClassLoader());loader(rows,"system",ClassLoader.getSystemClassLoader());loader(rows,"observer",getClass().getClassLoader());
    if(definition instanceof AnnotatedBeanDefinition){AnnotatedBeanDefinition annotated=(AnnotatedBeanDefinition)definition;
     Object metadata=annotated.getMetadata();rows.add("metadataClass\t"+metadata.getClass().getName());
     annotated.getMetadata().getAnnotations().stream().forEach(annotation->{
      rows.add("annotation\t"+annotation.getType().getName());
      for(Class<?> type=annotation.getClass();type!=null;type=type.getSuperclass())for(Field field:type.getDeclaredFields())if(ClassLoader.class.isAssignableFrom(field.getType()))try{
       field.setAccessible(true);loader(rows,"annotation."+field.getName(),(ClassLoader)field.get(annotation));
      }catch(Exception ignored){rows.add("annotationLoaderAccess\t"+ignored.getClass().getName());}
     });
    }
    Files.write(output,rows,StandardOpenOption.CREATE_NEW);
   }catch(Exception observation){original.addSuppressed(observation);}
   throw original;
  }
 }
 static void loader(List<String> rows,String name,ClassLoader loader){
  String identity=loader==null?"bootstrap":loader.getClass().getName()+"@"+Integer.toHexString(System.identityHashCode(loader));rows.add(name+"\t"+identity);
  try{Class<?> type=Class.forName("jnpf.config.JnpfOauthConfig",false,loader);rows.add(name+".oauth\tPASS\t"+type.getClassLoader().getClass().getName());}
  catch(Throwable error){rows.add(name+".oauth\t"+error.getClass().getName());}
 }
}
