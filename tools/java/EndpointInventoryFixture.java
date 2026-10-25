package xnby.replica;
import java.util.*;
import org.springframework.asm.*;

/** Synthetic annotation bytes, never defined as an application class. */
public final class EndpointInventoryFixture {
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("ENDPOINT_FIXTURE_"+checks);checks++;}
 static byte[] fixture(String[] bases,String[] classVerbs,String mapping,String[] paths,String[] methodVerbs,boolean conditions){
  ClassWriter w=new ClassWriter(0);w.visit(Opcodes.V1_8,Opcodes.ACC_PUBLIC|Opcodes.ACC_ABSTRACT,"own/Fixture",null,"java/lang/Object",null);
  w.visitAnnotation(OriginalBusinessEndpointInventory.PREFIX+"RestController;",true).visitEnd();
  if(bases!=null){AnnotationVisitor c=w.visitAnnotation(OriginalBusinessEndpointInventory.PREFIX+"RequestMapping;",true);AnnotationVisitor p=c.visitArray("path");for(String s:bases)p.visit(null,s);p.visitEnd();AnnotationVisitor verbs=c.visitArray("method");for(String s:classVerbs)verbs.visitEnum(null,"Lorg/springframework/web/bind/annotation/RequestMethod;",s);verbs.visitEnd();c.visitEnd();}
  MethodVisitor m=w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_ABSTRACT,"ownHandler","()V",null,null);AnnotationVisitor a=m.visitAnnotation(OriginalBusinessEndpointInventory.PREFIX+mapping+";",true);
  if(paths!=null){AnnotationVisitor p=a.visitArray("value");for(String s:paths)p.visit(null,s);p.visitEnd();}
  if(methodVerbs!=null){AnnotationVisitor p=a.visitArray("method");for(String s:methodVerbs)p.visitEnum(null,"Lorg/springframework/web/bind/annotation/RequestMethod;",s);p.visitEnd();}
  if(conditions){AnnotationVisitor p=a.visitArray("headers");p.visit(null,"OWN_PRIVATE_FIXTURE_SHOULD_NOT_BE_EMITTED");p.visitEnd();}
  a.visitEnd();m.visitEnd();w.visitMethod(Opcodes.ACC_PUBLIC|Opcodes.ACC_ABSTRACT,"unmapped","()V",null,null).visitEnd();w.visitEnd();return w.toByteArray();
 }
 public static void main(String[] args){
  List<Map<String,Object>> rows=OriginalBusinessEndpointInventory.scan(fixture(new String[]{"/own/","/other"},new String[]{"GET","POST"},"GetMapping",new String[]{"/list","/detail"},null,true));
  check(rows.size()==4);check(rows.stream().allMatch(r->r.get("verbs").equals(Collections.singletonList("GET"))));check(rows.get(0).get("path").equals("/own/list"));
  check(rows.stream().allMatch(r->r.get("handler").equals("ownHandler")&&r.get("descriptor").equals("()V")&&r.get("controllerStereotype").equals(true)));check(rows.stream().allMatch(r->r.get("additionalConditions").equals(true)));
  check(!OriginalBusinessEndpointInventory.json(rows).contains("OWN_PRIVATE_FIXTURE_SHOULD_NOT_BE_EMITTED"));
  rows=OriginalBusinessEndpointInventory.scan(fixture(new String[]{"/own"},new String[]{"GET"},"PostMapping",new String[]{"/conflict"},null,false));check(rows.size()==1&&rows.get(0).get("methodConditionConflict").equals(true)&&((List<?>)rows.get(0).get("verbs")).isEmpty());
  rows=OriginalBusinessEndpointInventory.scan(fixture(null,new String[0],"RequestMapping",null,null,false));check(rows.get(0).get("path").equals("/")&&rows.get(0).get("verbs").equals(Collections.singletonList("ANY")));
  rows=OriginalBusinessEndpointInventory.scan(fixture(new String[]{"/own"},new String[]{"GET","POST"},"RequestMapping",new String[]{""},new String[]{"POST"},false));check(rows.get(0).get("path").equals("/own")&&rows.get(0).get("verbs").equals(Collections.singletonList("POST")));
  check(OriginalBusinessEndpointInventory.json("quote\"\n\\").equals("\"quote\\\"\\u000a\\\\\""));
  System.out.println("ENDPOINT_ANNOTATION_FIXTURE_CHECKS="+checks);
 }
}
