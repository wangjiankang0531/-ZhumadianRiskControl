package xnby.replica;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;
import org.springframework.asm.*;

/** Direct Spring mapping metadata only. Does not define or execute application classes. */
public final class OriginalBusinessEndpointInventory {
 static final String PREFIX="Lorg/springframework/web/bind/annotation/";
 static final Map<String,String> MAPPINGS=new HashMap<>();
 static {for(String name:Arrays.asList("Get","Post","Put","Delete","Patch"))MAPPINGS.put(PREFIX+name+"Mapping;",name.toUpperCase(Locale.ROOT));MAPPINGS.put(PREFIX+"RequestMapping;","");}
 static final class Mapping {List<String> paths=new ArrayList<>(),verbs=new ArrayList<>();boolean constraints;
  Mapping(String descriptor){String verb=MAPPINGS.get(descriptor);if(!verb.isEmpty())verbs.add(verb);}
  AnnotationVisitor visitor(){return new AnnotationVisitor(Opcodes.ASM9){
   void value(String name,Object value){if(name.equals("value")||name.equals("path")){if(value instanceof String)paths.add((String)value);}else if(Arrays.asList("params","headers","consumes","produces").contains(name))constraints=true;}
   public void visit(String name,Object value){value(name,value);}
   public AnnotationVisitor visitArray(final String name){return new AnnotationVisitor(Opcodes.ASM9){public void visit(String ignored,Object value){value(name,value);}public void visitEnum(String ignored,String descriptor,String value){if(name.equals("method"))verbs.add(value);}};}
   public void visitEnum(String name,String descriptor,String value){if(name.equals("method"))verbs.add(value);}
  };}
  List<String> paths(){return paths.isEmpty()?Collections.singletonList(""):paths;}
 }
 static final class Method {String name,descriptor;List<Mapping> mappings=new ArrayList<>();List<String> annotations=new ArrayList<>();}
 static final class Controller {String name,parent;boolean stereotype;List<Mapping> mappings=new ArrayList<>();List<Method> methods=new ArrayList<>();}
 static Map<String,Object> object(Object... entries){Map<String,Object> result=new LinkedHashMap<>();for(int i=0;i<entries.length;i+=2)result.put((String)entries[i],entries[i+1]);return result;}
 static String join(String root,String path){String result;if(root.isEmpty())result=path;else if(path.isEmpty())result=root;else if(root.endsWith("/")&&path.startsWith("/"))result=root+path.substring(1);else if(!root.endsWith("/")&&!path.startsWith("/"))result=root+"/"+path;else result=root+path;return result.startsWith("/")?result:"/"+result;}
 static List<Map<String,Object>> scan(byte[] bytes){
  final Controller c=new Controller();
  new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9){
   public void visit(int version,int access,String name,String signature,String parent,String[] interfaces){c.name=name;c.parent=parent;}
   public AnnotationVisitor visitAnnotation(String descriptor,boolean visible){
    if(descriptor.equals(PREFIX+"RestController;")||descriptor.equals("Lorg/springframework/stereotype/Controller;"))c.stereotype=true;
    if(MAPPINGS.containsKey(descriptor)){Mapping m=new Mapping(descriptor);c.mappings.add(m);return m.visitor();}return null;
   }
   public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){
    final Method method=new Method();method.name=name;method.descriptor=descriptor;c.methods.add(method);
    return new MethodVisitor(Opcodes.ASM9){public AnnotationVisitor visitAnnotation(String annotation,boolean visible){method.annotations.add(annotation);if(MAPPINGS.containsKey(annotation)){Mapping m=new Mapping(annotation);method.mappings.add(m);return m.visitor();}return null;}};
   }
  },ClassReader.SKIP_CODE|ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
  List<Map<String,Object>> result=new ArrayList<>();
  List<Mapping> roots=c.mappings.isEmpty()?Collections.singletonList(new Mapping(PREFIX+"RequestMapping;")):c.mappings;
  for(Method method:c.methods)for(Mapping mapping:method.mappings)for(Mapping root:roots)for(String base:root.paths())for(String path:mapping.paths()){
   List<String> verbs=new ArrayList<>(mapping.verbs.isEmpty()?root.verbs:mapping.verbs);
   boolean conflict=false;if(!root.verbs.isEmpty()&&!mapping.verbs.isEmpty()){verbs.retainAll(root.verbs);conflict=verbs.isEmpty();}
   if(verbs.isEmpty()&&!conflict)verbs.add("ANY");
   result.add(object("controller",c.name.replace('/','.'),"superClass",c.parent,"controllerStereotype",c.stereotype,"handler",method.name,"descriptor",method.descriptor,"path",join(base,path),"verbs",verbs,"methodConditionConflict",conflict,"additionalConditions",root.constraints||mapping.constraints,"scope","direct annotations only; inherited/composed mappings and runtime registration not resolved"));
  }
  return result;
 }
 static String hash(byte[] bytes)throws Exception{byte[] h=MessageDigest.getInstance("SHA-256").digest(bytes);StringBuilder s=new StringBuilder();for(byte x:h)s.append(String.format(Locale.ROOT,"%02x",x&255));return s.toString();}
 static String json(Object value){
  if(value==null)return "null";if(value instanceof Number||value instanceof Boolean)return value.toString();
  if(value instanceof Map){List<String> parts=new ArrayList<>();for(Object e:((Map<?,?>)value).entrySet()){Map.Entry<?,?> row=(Map.Entry<?,?>)e;parts.add(json(row.getKey().toString())+":"+json(row.getValue()));}return "{"+String.join(",",parts)+"}";}
  if(value instanceof Iterable){List<String> parts=new ArrayList<>();for(Object x:(Iterable<?>)value)parts.add(json(x));return "["+String.join(",",parts)+"]";}
  String s=value.toString();StringBuilder out=new StringBuilder("\"");for(int i=0;i<s.length();i++){char c=s.charAt(i);if(c=='"'||c=='\\')out.append('\\').append(c);else if(c<32)out.append(String.format(Locale.ROOT,"\\u%04x",(int)c));else out.append(c);}return out.append('"').toString();
 }
 public static void main(String[] args)throws Exception{
  if(args.length!=2)throw new IllegalArgumentException("EXPLICIT_LOCAL_APPLICATION_JAR_AND_FRESH_REPORT_REQUIRED");Path input=Paths.get(args[0]).toRealPath(),output=Paths.get(args[1]);if(Files.exists(output))throw new IOException("FRESH_REPORT_REQUIRED");
  List<Map<String,Object>> routes=new ArrayList<>();Map<String,String> pins=new TreeMap<>();int count=0;
  try(ZipFile zip=new ZipFile(input.toFile())){List<? extends ZipEntry> entries=Collections.list(zip.entries());entries.sort(Comparator.comparing(ZipEntry::getName));for(ZipEntry entry:entries){String name=entry.getName();if(!name.startsWith("com/iemp/endanger/")||!name.endsWith(".class"))continue;if(entry.getSize()<0||entry.getSize()>4*1024*1024)throw new IOException("BOUNDED_CLASS_REQUIRED");byte[] raw;try(InputStream in=zip.getInputStream(entry)){raw=in.readAllBytes();}if(raw.length!=entry.getSize())throw new IOException("CLASS_SIZE_CHANGED");count++;pins.put(name,hash(raw));routes.addAll(scan(raw));}}
  if(count!=768)throw new IOException("EXPECTED_768_APPLICATION_CLASSES_REQUIRED");
  Files.write(output,json(object("classesRead",count,"directMappings",routes,"classSHA256",pins,"originalClassesLoadedOrExecuted",false,"applicationStarted",false,"databaseConnected",false,"fullCloneReady",false)).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
  System.out.println("BUSINESS_CLASSES_READ="+count+" DIRECT_MAPPINGS="+routes.size()+" ORIGINAL_CLASSES_EXECUTED=false");
 }
}
