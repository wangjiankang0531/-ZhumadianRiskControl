package xnby.replica;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Decode only explicit prepared properties into a private deployment template. */
public final class OriginalDeploymentProperties {
 static String quote(String value){StringBuilder out=new StringBuilder("\"");for(char c:value.toCharArray()){if(c=='\\'||c=='"')out.append('\\').append(c);else if(c<32)out.append(String.format("\\u%04x",(int)c));else out.append(c);}return out.append('"').toString();}
 public static void main(String[] args)throws Exception {
  if(args.length!=3)throw new IllegalArgumentException("TWO_PREPARED_INPUTS_AND_PRIVATE_OUTPUT_REQUIRED");
  Path output=Paths.get(args[2]);if(Files.exists(output))throw new IllegalArgumentException("FRESH_PRIVATE_OUTPUT_REQUIRED");
  StringBuilder json=new StringBuilder("{");
  for(int i=0;i<2;i++){
   Path source=Paths.get(args[i]);if(!Files.isRegularFile(source)||Files.size(source)>1024*1024)throw new IllegalArgumentException("BOUNDED_PREPARED_PROPERTIES_REQUIRED");
   Properties p=new Properties();try(java.io.Reader in=Files.newBufferedReader(source,StandardCharsets.UTF_8)){p.load(in);}
   if(i>0)json.append(',');json.append(quote(i==0?"platform":"business")).append(":{");boolean first=true;
   for(String key:new TreeSet<String>(p.stringPropertyNames())){if(!first)json.append(',');first=false;json.append(quote(key)).append(':').append(quote(p.getProperty(key)));}json.append('}');
  }
  json.append('}');Files.write(output,json.toString().getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
  System.out.println("PRIVATE_DEPLOYMENT_PROPERTIES_WRITTEN");
 }
}
