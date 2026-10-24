package xnby.replica;
import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.*;
import org.springframework.asm.*;

/** Read-only diagnostic fingerprints; normalized bytes are never saved, loaded, or executed. */
public final class OriginalBusinessClassFingerprint {
 static String hash(byte[] raw)throws Exception {byte[] h=MessageDigest.getInstance("SHA-256").digest(raw);StringBuilder b=new StringBuilder();for(byte v:h)b.append(String.format(Locale.ROOT,"%02x",v&255));return b.toString();}
 static void part(ByteArrayOutputStream out,String value)throws Exception {byte[] bytes=value==null?null:value.getBytes(StandardCharsets.UTF_8);out.write(ByteBuffer.allocate(4).putInt(bytes==null?-1:bytes.length).array());if(bytes!=null)out.write(bytes);}
 static final List<String> DETAILS=new ArrayList<>();
 static final class Header {int version,access;String name,signature,parent;String[] interfaces;ClassWriter writer(){ClassWriter w=new ClassWriter(0);w.visit(version,access,name,signature,parent,interfaces);return w;}}
 static String[] memberFingerprints(ClassReader reader)throws Exception {
  final Header header=new Header();final SortedMap<String,String> fields=new TreeMap<>(),methods=new TreeMap<>();final ClassWriter metadata=new ClassWriter(0);
  reader.accept(new ClassVisitor(Opcodes.ASM9,metadata){
   @Override public void visit(int version,int access,String name,String signature,String parent,String[] interfaces){header.version=version;header.access=access;header.name=name;header.signature=signature;header.parent=parent;header.interfaces=interfaces;super.visit(version,access,name,signature,parent,interfaces);}
   @Override public FieldVisitor visitField(int access,String name,String descriptor,String signature,Object value){final ClassWriter w=header.writer();return new FieldVisitor(Opcodes.ASM9,w.visitField(access,name,descriptor,signature,value)){@Override public void visitEnd(){super.visitEnd();w.visitEnd();try{fields.put(name+":"+descriptor,hash(w.toByteArray()));}catch(Exception e){throw new IllegalStateException(e);}}};}
   @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String signature,String[] exceptions){final ClassWriter w=header.writer();return new MethodVisitor(Opcodes.ASM9,w.visitMethod(access,name,descriptor,signature,exceptions)){@Override public void visitEnd(){super.visitEnd();w.visitEnd();try{methods.put(name+descriptor,hash(w.toByteArray()));}catch(Exception e){throw new IllegalStateException(e);}}};}
  },ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
  ByteArrayOutputStream fieldSet=new ByteArrayOutputStream(),methodSet=new ByteArrayOutputStream();
  for(Map.Entry<String,String> e:fields.entrySet()){part(fieldSet,e.getKey());part(fieldSet,e.getValue());DETAILS.add(header.name+".class\tfield\t"+e.getKey()+"\t"+e.getValue());}
  for(Map.Entry<String,String> e:methods.entrySet()){part(methodSet,e.getKey());part(methodSet,e.getValue());DETAILS.add(header.name+".class\tmethod\t"+e.getKey()+"\t"+e.getValue());}
  String classHash=hash(metadata.toByteArray()),fieldHash=hash(fieldSet.toByteArray()),methodHash=hash(methodSet.toByteArray());ByteArrayOutputStream all=new ByteArrayOutputStream();part(all,classHash);part(all,fieldHash);part(all,methodHash);return new String[]{hash(all.toByteArray()),classHash,fieldHash,methodHash};
 }
 static String describe(String name,byte[] raw)throws Exception {
  ClassReader reader=new ClassReader(raw);if(!name.equals(reader.getClassName()+".class"))throw new IllegalStateException("CLASS_ENTRY_NAME_MISMATCH");final SortedMap<String,List<String>> parameters=new TreeMap<>();
  reader.accept(new ClassVisitor(Opcodes.ASM9){@Override public MethodVisitor visitMethod(int access,String method,String descriptor,String signature,String[] exceptions){final List<String> values=new ArrayList<>();parameters.put(method+descriptor,values);return new MethodVisitor(Opcodes.ASM9){@Override public void visitParameter(String value,int flags){values.add(value==null?"<null>":value);values.add(Integer.toString(flags));}};}},ClassReader.SKIP_CODE|ClassReader.SKIP_FRAMES);
  ByteArrayOutputStream metadata=new ByteArrayOutputStream();int parameterCount=0;for(Map.Entry<String,List<String>> method:parameters.entrySet()){part(metadata,method.getKey());for(String value:method.getValue())part(metadata,value);parameterCount+=method.getValue().size()/2;}
  ClassWriter normalized=new ClassWriter(0);reader.accept(normalized,ClassReader.SKIP_DEBUG|ClassReader.SKIP_FRAMES);
  String[] members=memberFingerprints(reader);return name+"\t"+hash(raw)+"\t"+hash(normalized.toByteArray())+"\t"+hash(metadata.toByteArray())+"\t"+reader.readUnsignedShort(6)+"\t"+parameterCount+"\t"+String.join("\t",members);
 }
 public static void main(String[] args)throws Exception {
  if(args.length==3&&args[0].equals("--class")){Path input=Paths.get(args[1]).toRealPath(),output=Paths.get(args[2]);if(Files.exists(output)||Files.size(input)>4*1024*1024)throw new IllegalStateException("FRESH_BOUNDED_CLASS_FIXTURE_REQUIRED");byte[] raw=Files.readAllBytes(input);Files.write(output,Collections.singletonList(describe(new ClassReader(raw).getClassName()+".class",raw)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);return;}
  if(args.length!=2)throw new IllegalArgumentException("EXPLICIT_ARCHIVE_AND_FRESH_OUTPUT_REQUIRED");Path input=Paths.get(args[0]).toRealPath(),output=Paths.get(args[1]);if(Files.exists(output))throw new IllegalStateException("FRESH_FINGERPRINT_OUTPUT_REQUIRED");List<String> rows=new ArrayList<>();int classes=0;
  try(ZipFile zip=new ZipFile(input.toFile())) {
   List<? extends ZipEntry> entries=Collections.list(zip.entries());entries.sort(Comparator.comparing(ZipEntry::getName));
   for(ZipEntry entry:entries) {
    String name=entry.getName();if(!name.endsWith(".class")||name.startsWith("org/springframework/boot/loader/"))continue;
    if(name.startsWith("BOOT-INF/classes/"))name=name.substring("BOOT-INF/classes/".length());else if(!name.startsWith("com/iemp/endanger/"))continue;
    if(!name.startsWith("com/iemp/endanger/")||name.contains("..")||entry.getSize()<0||entry.getSize()>4*1024*1024)throw new IllegalStateException("BOUNDED_ORIGINAL_APPLICATION_CLASSES_REQUIRED");
    byte[] raw;try(InputStream in=zip.getInputStream(entry)){raw=in.readAllBytes();}if(raw.length!=entry.getSize())throw new IllegalStateException("CLASS_SIZE_CHANGED");rows.add(describe(name,raw));classes++;
   }
  }
  if(classes!=768)throw new IllegalStateException("ALL_768_ORIGINAL_APPLICATION_CLASSES_REQUIRED");Files.write(output,rows,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);Files.write(Paths.get(output.toString()+".members.tsv"),DETAILS,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);System.out.println("ORIGINAL_BUSINESS_CLASS_FINGERPRINTS="+classes);
 }
}
