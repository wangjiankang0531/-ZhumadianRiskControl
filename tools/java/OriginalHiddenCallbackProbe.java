package xnby.replica;

import java.io.*;
import java.lang.reflect.*;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Characterizes unchanged hidden-workflow callbacks with synthetic in-memory mappers. */
@SuppressWarnings("removal")
public final class OriginalHiddenCallbackProbe {
 static final String ROOT=OriginalBusinessMethodProbe.ROOT;
 static final class Memory implements InvocationHandler {
  Object work,danger,correction; int reads,writes,workWrites,dangerWrites; boolean missingWork,missingCorrection;
  public Object invoke(Object proxy,Method method,Object[] args)throws Throwable {
   String name=method.getName(),mapper=method.getDeclaringClass().getSimpleName();
   if(method.getDeclaringClass()==Object.class)return switch(name){case "toString"->"SyntheticCallbackMapper";case "hashCode"->System.identityHashCode(proxy);case "equals"->proxy==args[0];default->throw new AssertionError(name);};
   // Generic BaseMapper methods report their declaring interface, so inspect the proxy's fixed interface.
   mapper=proxy.getClass().getInterfaces()[0].getSimpleName();
   if(mapper.equals("CheckHiddenDangerWorkorderMapper")&&name.equals("selectOne")){reads++;return missingWork?null:work;}
   if(mapper.equals("CheckHiddenDangerMapper")&&name.equals("selectById")){if(!Objects.equals(args[0],"SYNTHETIC-HIDDEN"))throw new AssertionError("HIDDEN_ID");reads++;return danger;}
   if(mapper.equals("CheckCorrectSituationMapper")&&name.equals("selectByCheckHiddenDangerId")){if(!Objects.equals(args[0],"SYNTHETIC-WORK"))throw new AssertionError("WORK_ID");reads++;return missingCorrection?null:correction;}
   if(mapper.equals("CheckHiddenDangerWorkorderMapper")&&name.equals("updateById")){if(args[0]!=work)throw new AssertionError("WORK_IDENTITY");writes++;workWrites++;return 1;}
   if(mapper.equals("CheckHiddenDangerMapper")&&name.equals("updateById")){if(args[0]!=danger)throw new AssertionError("HIDDEN_IDENTITY");writes++;dangerWrites++;return 1;}
   throw new AssertionError("UNEXPECTED_CALLBACK_MAPPER:"+mapper+"."+name);
  }
 }
 static Object proxy(Class<?> type,Memory memory){return type.isInterface()&&type.getSimpleName().endsWith("Mapper")?java.lang.reflect.Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},memory):null;}
 static Map<String,Object> scenario(ClassLoader loader,String name,String status,boolean missingWork,boolean missingCorrection)throws Exception {
  Memory m=new Memory();m.missingWork=missingWork;m.missingCorrection=missingCorrection;
  m.work=OriginalBusinessMethodProbe.make(loader,"server.hidden.entity.CheckHiddenDangerWorkEntity");
  OriginalBusinessMethodProbe.call(m.work,"setId","SYNTHETIC-WORK");OriginalBusinessMethodProbe.call(m.work,"setHiddenDangerId","SYNTHETIC-HIDDEN");OriginalBusinessMethodProbe.call(m.work,"setProcInstId","SYNTHETIC-PROCESS");
  m.danger=OriginalBusinessMethodProbe.make(loader,"server.hidden.entity.CheckHiddenDangerEntity");OriginalBusinessMethodProbe.call(m.danger,"setId","SYNTHETIC-HIDDEN");OriginalBusinessMethodProbe.call(m.danger,"setHiddenDangerStatus","SYNTHETIC-BEFORE");
  m.correction=OriginalBusinessMethodProbe.make(loader,"server.hidden.entity.CheckCorrectSituationEntity");OriginalBusinessMethodProbe.call(m.correction,"setId","SYNTHETIC-CORRECTION");OriginalBusinessMethodProbe.call(m.correction,"setCorrectCost",new BigDecimal("12.50"));OriginalBusinessMethodProbe.call(m.correction,"setCorrectDescribe","Synthetic correction detail");
  Class<?> serviceType=Class.forName(ROOT+"server.hidden.service.impl.CheckHiddenDangerServiceImpl",true,loader);Constructor<?>[] constructors=serviceType.getDeclaredConstructors();if(constructors.length!=1)throw new AssertionError("ONE_CONSTRUCTOR_REQUIRED");Constructor<?> ctor=constructors[0];Class<?>[] types=ctor.getParameterTypes();Object[] injected=new Object[types.length];for(int i=0;i<types.length;i++){if(types[i].isPrimitive())throw new AssertionError("PRIMITIVE_DEPENDENCY");injected[i]=proxy(types[i],m);}Object service=ctor.newInstance(injected);
  Class<?> dangerMapper=Class.forName(ROOT+"server.hidden.mapper.CheckHiddenDangerMapper",true,loader);OriginalBusinessMethodProbe.field(service,"baseMapper",proxy(dangerMapper,m));
  Throwable failure=null;boolean returned=false;try{returned=Boolean.TRUE.equals(OriginalBusinessMethodProbe.call(service,"callback","SYNTHETIC-PROCESS",status));}catch(InvocationTargetException error){failure=error.getCause();}
  Object workStatus=OriginalBusinessMethodProbe.call(m.work,"getHiddenDangerStatus"),dangerStatus=OriginalBusinessMethodProbe.call(m.danger,"getHiddenDangerStatus");boolean expectedFailure=missingWork||missingCorrection;
  boolean correctionCopied=Objects.equals(OriginalBusinessMethodProbe.call(m.danger,"getPutInto"),"12.50")&&Objects.equals(OriginalBusinessMethodProbe.call(m.danger,"getCorrectiveMeasures"),"Synthetic correction detail");
  boolean matched=expectedFailure?failure instanceof NullPointerException&&!returned&&m.writes==0:failure==null&&returned&&m.workWrites==1&&m.dangerWrites==1&&Objects.equals(status,workStatus)&&Objects.equals(status,dangerStatus)&&(!status.equals("已整改")||correctionCopied);
  Map<String,Object> row=new LinkedHashMap<>();row.put("case",name);row.put("returnedTrue",returned);row.put("exceptionType",failure==null?null:failure.getClass().getSimpleName());row.put("mapperReads",m.reads);row.put("inMemoryWrites",m.writes);row.put("workWrites",m.workWrites);row.put("dangerWrites",m.dangerWrites);row.put("workStatus",workStatus);row.put("dangerStatus",dangerStatus);row.put("correctionDetailsCopied",correctionCopied);row.put("characterizedExpectationMatched",matched);return row;
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=3)throw new IllegalArgumentException("APP_DEPENDENCIES_FRESH_OUTPUT_REQUIRED");Path app=Path.of(args[0]).toRealPath(),list=Path.of(args[1]).toRealPath(),output=Path.of(args[2]).toAbsolutePath().normalize();if(Files.exists(output)||!Files.isDirectory(output.getParent()))throw new IllegalStateException("FRESH_OUTPUT_REQUIRED");
  List<Path> deps=new ArrayList<>();for(String line:Files.readAllLines(list,StandardCharsets.UTF_8))if(!line.isBlank())deps.add(Path.of(line).toRealPath());if(deps.size()>256)throw new IllegalArgumentException("DEPENDENCY_LIMIT");
  try(ZipFile zip=new ZipFile(app.toFile())){ZipEntry e=zip.getEntry("BOOT-INF/classes/com/iemp/endanger/server/hidden/service/impl/CheckHiddenDangerServiceImpl.class");if(e==null)e=zip.getEntry("com/iemp/endanger/server/hidden/service/impl/CheckHiddenDangerServiceImpl.class");if(e==null)throw new IllegalStateException("HIDDEN_SERVICE_REQUIRED");try(InputStream in=zip.getInputStream(e)){if(in.readNBytes(4).length!=4)throw new IllegalStateException("CLASS_HEADER_REQUIRED");}}
  OriginalBusinessMethodProbe.Guard guard=new OriginalBusinessMethodProbe.Guard(output.getParent());System.setSecurityManager(guard);if(System.getSecurityManager()!=guard)throw new AssertionError("GUARD_INSTALL");int tests=0;try{guard.checkConnect("synthetic.invalid",443);}catch(SecurityException e){tests++;}try{guard.checkExec("SYNTHETIC_DO_NOT_EXECUTE");}catch(SecurityException e){tests++;}Path forbidden=output.getParent().getParent().resolve("callback-forbidden-write.txt");if(Files.exists(forbidden))throw new IllegalStateException("FRESH_SELFTEST_TARGET");try{Files.writeString(forbidden,"must not be written");}catch(SecurityException e){tests++;}if(tests!=3||Files.exists(forbidden))throw new AssertionError("GUARD_TESTS");guard.reset();
  List<Map<String,Object>> cases=new ArrayList<>();try(var loader=new OriginalBusinessMethodProbe.OriginalLoader(app,deps)){Thread.currentThread().setContextClassLoader(loader);cases.add(scenario(loader,"awaiting-correction","待整改",false,false));cases.add(scenario(loader,"review-rejected","复查不合格",false,false));cases.add(scenario(loader,"corrected","已整改",false,false));cases.add(scenario(loader,"unrecognized-status-characterization","SYNTHETIC-UNRECOGNIZED",false,false));cases.add(scenario(loader,"missing-work-characterization","待整改",true,false));cases.add(scenario(loader,"missing-correction-characterization","已整改",false,true));}
  boolean completed=cases.size()==6&&cases.stream().allMatch(c->Boolean.TRUE.equals(c.get("characterizedExpectationMatched")))&&guard.network==0&&guard.process==0&&guard.writes==0&&guard.links==0;Map<String,Object> result=new LinkedHashMap<>();result.put("javaVersion",System.getProperty("java.version"));result.put("guardSelfTests",tests);result.put("cases",cases);result.put("callbackCharacterizationCompleted",completed);result.put("originalNetworkAttemptsDenied",guard.network);result.put("originalProcessAttemptsDenied",guard.process);result.put("originalOutsideWritesDenied",guard.writes);result.put("originalNativeLoadsDenied",guard.links);result.put("databaseConnected",false);result.put("springContextStarted",false);result.put("actualWorkflowSubmissionVerified",false);result.put("inspectionAttachmentBranchVerified",false);Files.writeString(output,OriginalBusinessMethodProbe.json(result)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);System.out.println("CALLBACK_CHARACTERIZATION completed="+completed);System.exit(completed?0:2);
 }
}
