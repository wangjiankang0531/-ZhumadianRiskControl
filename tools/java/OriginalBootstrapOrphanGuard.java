package xnby.platform;
import java.io.*;
import java.lang.reflect.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.function.Function;
import org.aopalliance.intercept.MethodInterceptor;
import org.springframework.aop.framework.ProxyFactory;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.context.*;

/** Experimental startup-only orphan isolation; never deletes data or filters ordinary calls. */
public final class OriginalBootstrapOrphanGuard implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static final String BOOT="jnpf.init.FlowableLoadUtil", SERVICE="jnpf.engine.service.impl.FlowRunAddNodeTemplateEntityServiceImpl", ENTITY="jnpf.engine.entity.FlowRunAddNodeTemplateEntity";
 static final ThreadLocal<Scope> ACTIVE=new ThreadLocal<>();
 public interface Lookup {
  boolean definitionExists(String id)throws Exception;
  long runtimeDefinitionReferences(String id)throws Exception;
  long historicalDefinitionReferences(String id)throws Exception;
  long runtimeInstanceReferences(String id)throws Exception;
  long historicalInstanceReferences(String id)throws Exception;
 }
 public static final class Scope {
  final Properties result=new Properties();final Map<String,Integer> orphanGroups=new TreeMap<>();
  int inputRows,keptRows,listCalls;String beforeSignature;
 }
 static String hex(byte[] raw){StringBuilder s=new StringBuilder();for(byte b:raw)s.append(String.format(Locale.ROOT,"%02x",b&255));return s.toString();}
 static String hash(String value)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8)));}
 public static <T> List<T> select(List<T> original,Function<T,String> definition,Function<T,String> instance,Lookup lookup,Scope scope)throws Exception {
  if(original==null||original.size()>10000)throw new IllegalStateException("OWN_BOOTSTRAP_LIST_SHAPE");
  List<T> kept=new ArrayList<>();Map<String,Boolean> existing=new HashMap<>();Set<String> checkedDefinitions=new HashSet<>(),checkedInstances=new HashSet<>();
  scope.listCalls++;scope.inputRows=original.size();scope.orphanGroups.clear();
  for(T row:original) {
   String id=definition.apply(row),inst=instance.apply(row);
   if(id==null||id.isEmpty()||id.length()>512)throw new IllegalStateException("OWN_BOOTSTRAP_DEFINITION_SHAPE");
   Boolean present=existing.get(id);if(present==null){present=lookup.definitionExists(id);existing.put(id,present);}
   if(present){kept.add(row);continue;}
   if(checkedDefinitions.add(id)&&(lookup.runtimeDefinitionReferences(id)!=0||lookup.historicalDefinitionReferences(id)!=0))throw new IllegalStateException("OWN_MISSING_DEFINITION_HAS_PROCESS_REFERENCES");
   if(inst!=null&&!inst.isEmpty()&&checkedInstances.add(inst)&&(lookup.runtimeInstanceReferences(inst)!=0||lookup.historicalInstanceReferences(inst)!=0))throw new IllegalStateException("OWN_ORPHAN_ROW_INSTANCE_STILL_EXISTS");
   String key=hash(id);scope.orphanGroups.put(key,scope.orphanGroups.getOrDefault(key,0)+1);
  }
  scope.keptRows=kept.size();return kept.size()==original.size()?original:kept;
 }
 static Object invoke(Object target,String name,Object...args)throws Exception {
  Class<?>[] types=new Class<?>[args.length];Arrays.fill(types,String.class);
  try{return target.getClass().getMethod(name,types).invoke(target,args);}catch(InvocationTargetException e){Throwable cause=e.getCause();if(cause instanceof Exception)throw(Exception)cause;if(cause instanceof Error)throw(Error)cause;throw e;}
 }
 static String getter(Object row,String method){try{Object value=invoke(row,method);return value==null?null:value.toString();}catch(Exception e){throw new IllegalStateException("OWN_ORIGINAL_ENTITY_GETTER_FAILED",e);}}
 static String signature(List<?> rows)throws Exception {
  List<String> hashes=new ArrayList<>();
  for(Object row:rows){MessageDigest h=MessageDigest.getInstance("SHA-256");for(String name:new String[]{"getId","getProcessDefinitionId","getProcessInstanceId","getModelContent"}){String value=getter(row,name);byte[] raw=value==null?null:value.getBytes(StandardCharsets.UTF_8);h.update(ByteBuffer.allocate(4).putInt(raw==null?-1:raw.length).array());if(raw!=null)h.update(raw);}hashes.add(hex(h.digest()));}
  Collections.sort(hashes);return hash(String.join("",hashes));
 }
 static void pin(Class<?> type,String expected)throws Exception {
  MessageDigest h=MessageDigest.getInstance("SHA-256");try(InputStream in=type.getResourceAsStream("/"+type.getName().replace('.','/')+".class")){if(in==null)throw new IllegalStateException("OWN_BOOTSTRAP_CLASS_RESOURCE");byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)h.update(b,0,n);}
  if(!expected.equals(hex(h.digest())))throw new IllegalStateException("OWN_BOOTSTRAP_CLASS_PIN_MISMATCH");
 }
 static Lookup lookup(ConfigurableApplicationContext context)throws Exception {
  Object engine=context.getBean(Class.forName("org.flowable.engine.ProcessEngine",false,context.getClassLoader()));
  final Object repo=invoke(engine,"getRepositoryService"),runtime=invoke(engine,"getRuntimeService"),history=invoke(engine,"getHistoryService");
  return new Lookup(){
   public boolean definitionExists(String id)throws Exception{return invoke(invoke(invoke(repo,"createProcessDefinitionQuery"),"processDefinitionId",id),"singleResult")!=null;}
   long count(Object service,String create,String filter,String id)throws Exception{return ((Number)invoke(invoke(invoke(service,create),filter,id),"count")).longValue();}
   public long runtimeDefinitionReferences(String id)throws Exception{return count(runtime,"createProcessInstanceQuery","processDefinitionId",id);}
   public long historicalDefinitionReferences(String id)throws Exception{return count(history,"createHistoricProcessInstanceQuery","processDefinitionId",id);}
   public long runtimeInstanceReferences(String id)throws Exception{return count(runtime,"createProcessInstanceQuery","processInstanceId",id);}
   public long historicalInstanceReferences(String id)throws Exception{return count(history,"createHistoricProcessInstanceQuery","processInstanceId",id);}
  };
 }
 static void write(Path root,Scope scope)throws Exception {
  Properties p=scope.result;p.setProperty("sourceRowsSeen",Integer.toString(scope.inputRows));p.setProperty("validRowsPassedToOriginalInit",Integer.toString(scope.keptRows));p.setProperty("orphanRowsRetained",Integer.toString(scope.inputRows-scope.keptRows));p.setProperty("orphanDefinitionGroups",Integer.toString(scope.orphanGroups.size()));p.setProperty("serviceListCallsWithinOriginalInit",Integer.toString(scope.listCalls));
  for(Map.Entry<String,Integer> entry:scope.orphanGroups.entrySet())p.setProperty("orphanSHA256."+entry.getKey(),entry.getValue().toString());
  p.setProperty("databaseRowsDeletedOrUpdatedByGuard","false");p.setProperty("ordinaryServiceListFiltered","false");p.setProperty("fullCloneReady","false");
  try(OutputStream out=Files.newOutputStream(root.resolve("bootstrap-rehydration-observation.properties"),StandardOpenOption.CREATE_NEW)){p.store(out,"Startup compatibility candidate; original orphan rows preserved, raw IDs omitted");}
 }
 public void initialize(final ConfigurableApplicationContext context) {
  if(!Boolean.getBoolean("own.platform.rehydrate-existing-definitions"))return;
  boolean servlet=false;for(Method m:context.getClass().getMethods())if(m.getName().equals("getServletContext")&&m.getParameterCount()==0)servlet=true;if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.platform.root"));
  context.addBeanFactoryPostProcessor(factory->factory.addBeanPostProcessor(new BeanPostProcessor(){
   public Object postProcessAfterInitialization(Object bean,String name) {
    if(!name.equals("flowableLoadUtil")&&!name.equals("flowRunAddNodeTemplateEntityServiceImpl"))return bean;
    try {
     Class<?> type=AopUtils.getTargetClass(bean);boolean bootstrap=type.getName().equals(BOOT);
     if(!bootstrap&&!type.getName().equals(SERVICE))throw new IllegalStateException("OWN_ORIGINAL_BOOTSTRAP_BEAN_TYPE");
     pin(type,bootstrap?"5ed39329fe2d7aad4c56f2d11b3c89376595abc7e018f063365c26c23b7e82d5":"7324cdb5c83a647abc2644b24b21250d2dbd0e36e5526754db391ceaa0d213c4");
     pin(Class.forName(ENTITY,false,context.getClassLoader()),"662365cd6941e77eb4b7cc39df53eb1bea66b1f7c32fef538d5b23fcbfa8ce28");
     ProxyFactory proxy=new ProxyFactory(bean);proxy.setProxyTargetClass(true);
     proxy.addAdvice((MethodInterceptor)call->{
      if(bootstrap&&call.getMethod().getName().equals("init")&&call.getArguments().length==0) {
       if(ACTIVE.get()!=null)throw new IllegalStateException("OWN_NESTED_BOOTSTRAP_SCOPE");
       Scope scope=new Scope();scope.result.setProperty("originalBootstrapMethodInvoked","true");ACTIVE.set(scope);
       try {
        Object result=call.proceed();scope.result.setProperty("originalBootstrapMethodCompleted","true");ACTIVE.remove();
        Object service=context.getBean("flowRunAddNodeTemplateEntityServiceImpl");List<?> outside=(List<?>)invoke(service,"list");
        scope.result.setProperty("outsideBootstrapRows",Integer.toString(outside.size()));boolean equal=scope.beforeSignature!=null&&scope.beforeSignature.equals(signature(outside));
        scope.result.setProperty("outsideBootstrapCriticalFieldsSignaturePreserved",Boolean.toString(equal));
        if(!equal||scope.listCalls!=1)throw new IllegalStateException("OWN_OUTSIDE_BOOTSTRAP_PARITY_FAILED");return result;
       }catch(Throwable error){scope.result.setProperty("failureClass",error.getClass().getName());throw error;}finally{ACTIVE.remove();write(root,scope);}
      }
      Scope scope=ACTIVE.get();
      if(!bootstrap&&scope!=null&&call.getMethod().getName().equals("list")&&call.getArguments().length==0) {
       Object original=call.proceed();if(!(original instanceof List))throw new IllegalStateException("OWN_ORIGINAL_LIST_REQUIRED");
       List<?> rows=(List<?>)original;scope.beforeSignature=signature(rows);
       return select(rows,row->getter(row,"getProcessDefinitionId"),row->getter(row,"getProcessInstanceId"),lookup(context),scope);
      }
      return call.proceed();
     });return proxy.getProxy(context.getClassLoader());
    }catch(Exception e){throw new IllegalStateException("OWN_BOOTSTRAP_GUARD_SETUP_FAILED",e);}
   }
  }));
 }
}
