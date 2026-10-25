package xnby.replica;

import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.Permission;
import java.time.LocalDateTime;
import java.util.*;
import java.util.zip.*;

/** Calls selected unchanged business methods with in-memory mapper proxies, never Spring. */
@SuppressWarnings({"removal","unchecked"})
public final class OriginalBusinessMethodProbe {
 static final String ROOT="com.iemp.endanger.";
 static final Map<String,String> WORKS=new LinkedHashMap<>();
 static {WORKS.put("盲板抽堵作业","WorkBlind");WORKS.put("受限空间作业","WorkFiniteSpace");WORKS.put("动土作业","WorkGroundbreaking");WORKS.put("动火作业","WorkHot");WORKS.put("高处作业","WorkHigh");WORKS.put("吊装作业","WorkHoisting");WORKS.put("断路作业","WorkOpenCircuit");WORKS.put("临时用电作业","WorkTemporaryElectricity");}
 static final class Guard extends SecurityManager {
  final Path allowed; int network,process,writes,links;
  Guard(Path allowed){this.allowed=allowed.toAbsolutePath().normalize();}
  void reset(){network=process=writes=links=0;}
  public void checkPermission(Permission p){if(p instanceof java.nio.file.LinkPermission){writes++;throw new SecurityException("PROBE_LINK_CREATION_DENIED");}if(p instanceof RuntimePermission&&p.getName().equals("setSecurityManager"))throw new SecurityException("PROBE_GUARD_CANNOT_BE_REPLACED");}
  public void checkPermission(Permission p,Object c){checkPermission(p);}
  public void checkConnect(String h,int p){network++;throw new SecurityException("PROBE_NETWORK_DENIED");}
  public void checkConnect(String h,int p,Object c){checkConnect(h,p);}
  public void checkListen(int p){network++;throw new SecurityException("PROBE_LISTEN_DENIED");}
  public void checkAccept(String h,int p){network++;throw new SecurityException("PROBE_ACCEPT_DENIED");}
  public void checkExec(String c){process++;throw new SecurityException("PROBE_PROCESS_DENIED");}
  public void checkLink(String c){links++;throw new SecurityException("PROBE_NATIVE_LIBRARY_DENIED");}
  public void checkWrite(String f){Path p;try{p=Path.of(f).toFile().getCanonicalFile().toPath();}catch(IOException e){throw new SecurityException("PROBE_CANONICAL_WRITE_REQUIRED");}if(!p.startsWith(allowed)){writes++;throw new SecurityException("PROBE_OUTSIDE_WRITE_DENIED");}}
  public void checkDelete(String f){checkWrite(f);}
  public void checkWrite(FileDescriptor f){if(f!=FileDescriptor.out&&f!=FileDescriptor.err){writes++;throw new SecurityException("PROBE_UNKNOWN_DESCRIPTOR_WRITE_DENIED");}}
 }
 static final class OriginalLoader extends URLClassLoader {
  final ZipFile archive; final String prefix;
  OriginalLoader(Path app,List<Path> deps)throws Exception {super(deps.stream().map(p->{try{return p.toUri().toURL();}catch(Exception e){throw new IllegalArgumentException(e);}}).toArray(URL[]::new),OriginalBusinessMethodProbe.class.getClassLoader());archive=new ZipFile(app.toFile());prefix=archive.getEntry("BOOT-INF/classes/com/iemp/endanger/server/work/service/impl/WorkServiceImpl.class")!=null?"BOOT-INF/classes/":"";}
  protected Class<?> findClass(String name)throws ClassNotFoundException {
   if(!name.startsWith(ROOT))return super.findClass(name);
   ZipEntry entry=archive.getEntry(prefix+name.replace('.','/')+".class");
   if(entry==null)return super.findClass(name);if(entry.getSize()<0||entry.getSize()>4*1024*1024)throw new ClassNotFoundException(name);
   try(InputStream in=archive.getInputStream(entry)){byte[] b=in.readAllBytes();if(b.length!=entry.getSize())throw new IOException("CLASS_CHANGED");return defineClass(name,b,0,b.length);}catch(IOException e){throw new ClassNotFoundException(name,e);}
  }
  public void close()throws IOException {try{super.close();}finally{archive.close();}}
 }
 static Object call(Object target,String name,Object...args)throws Exception {
  for(Method m:target.getClass().getMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){try{return m.invoke(target,args);}catch(IllegalArgumentException e){continue;}}
  throw new NoSuchMethodException(target.getClass().getName()+"."+name);
 }
 static Object make(ClassLoader loader,String name)throws Exception {return Class.forName(ROOT+name,true,loader).getConstructor().newInstance();}
 static void field(Object target,String name,Object value)throws Exception {for(Class<?> c=target.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(target,value);return;}catch(NoSuchFieldException e){}throw new NoSuchFieldException(name);}
 static final class Memory implements InvocationHandler {
  final String mapper; final State state;
  Memory(String mapper,State state){this.mapper=mapper;this.state=state;}
  public Object invoke(Object proxy,Method m,Object[] args)throws Throwable {
   String n=m.getName();if(m.getDeclaringClass()==Object.class)return switch(n){case "toString"->"SyntheticMapper:"+mapper;case "hashCode"->System.identityHashCode(proxy);case "equals"->proxy==args[0];default->throw new AssertionError(n);};
   if(n.equals("selectCount")){
    state.reads++;
    if(mapper.equals("WorkMeasuresRelevanceMapper"))return Long.valueOf(state.measures);
    if(mapper.equals("WorkSignMapper")){if(state.signIndex>=state.signs.length)throw new AssertionError("UNEXPECTED_SIGN_QUERY");return Long.valueOf(state.signs[state.signIndex++]);}
   }
   if(n.equals("selectById")&&mapper.equals(state.workMapper)){state.reads++;return state.work;}
   if(n.equals("updateById")&&(mapper.equals(state.workMapper)||mapper.equals("CheckHiddenDangerMapper"))){state.writes++;state.updated=args[0];return 1;}
   if(n.equals("insert")&&mapper.equals("CheckReviewSituationMapper")){state.writes++;state.review=args[0];return 1;}
   if(n.equals("update")&&mapper.equals("WorkReservationBaseMapper")&&args.length==1){state.writes++;state.reservation=args[0];return 1;}
   throw new AssertionError("UNEXPECTED_MAPPER_CALL:"+mapper+"."+n);
  }
 }
 static final class State {long measures;long[] signs;int signIndex,reads,writes;Object work,updated,reservation,review;String workMapper;}
 static Object proxy(Class<?> type,State s){if(!type.isInterface()||!type.getSimpleName().endsWith("Mapper"))return null;return java.lang.reflect.Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},new Memory(type.getSimpleName(),s));}
 static Object service(ClassLoader loader,String name,State state)throws Exception {
  Class<?> type=Class.forName(ROOT+name,true,loader);Constructor<?>[] constructors=type.getDeclaredConstructors();if(constructors.length!=1)throw new AssertionError("ONE_CONSTRUCTOR_REQUIRED");
  Constructor<?> ctor=constructors[0];Object[] args=new Object[ctor.getParameterCount()];Class<?>[] types=ctor.getParameterTypes();for(int i=0;i<args.length;i++){if(types[i].isPrimitive())throw new AssertionError("UNEXPECTED_PRIMITIVE_DEPENDENCY");args[i]=proxy(types[i],state);}ctor.setAccessible(true);return ctor.newInstance(args);
 }
 static Map<String,Object> workCase(ClassLoader loader,String name,String kind,long measures,long[] signs,boolean expected,String message)throws Exception {
  State state=new State();state.measures=measures;state.signs=signs;
  if(WORKS.containsKey(kind)){String entity=WORKS.get(kind);state.workMapper=entity+"Mapper";state.work=make(loader,"server.work.entity."+entity);call(state.work,"setId","SYNTHETIC-WORK");call(state.work,"setWorkReservationBaseId","SYNTHETIC-RESERVATION");}
  Object service=service(loader,"server.work.service.impl.WorkServiceImpl",state);boolean success=false;Throwable failure=null;
  try{success=Boolean.TRUE.equals(call(service,"startWork","SYNTHETIC-WORK",kind));}catch(InvocationTargetException e){failure=e.getCause();}
  boolean denied=failure!=null&&failure.getClass().getName().endsWith(".ServiceException")&&(message==null||Objects.equals(message,failure.getMessage()));
  boolean workState=false,baseState=false,timeSame=false;
  if(success){workState=Objects.equals(call(state.work,"getProcessName"),"作业中");Object time=call(state.work,"getStartTime");Object sql=call(state.reservation,"getSqlSet");Map<?,?> params=(Map<?,?>)call(state.reservation,"getParamNameValuePairs");baseState=sql.toString().contains("process_name")&&sql.toString().contains("real_start_time")&&params.containsValue("作业中");timeSame=time instanceof LocalDateTime&&params.containsValue(time);}
  boolean passed=expected?success&&failure==null&&state.writes==2&&workState&&baseState&&timeSame:!success&&denied&&state.writes==0;
  Map<String,Object> row=new LinkedHashMap<>();row.put("case",name);row.put("expectedSuccess",expected);row.put("returnedSuccess",success);row.put("passed",passed);row.put("exceptionType",failure==null?null:failure.getClass().getSimpleName());row.put("reads",state.reads);row.put("inMemoryWrites",state.writes);row.put("workStateCorrect",workState);row.put("reservationStateCorrect",baseState);row.put("sameStartTime",timeSame);return row;
 }
 static Map<String,Object> reviewCase(ClassLoader loader,String name,String input)throws Exception {
  State state=new State();state.measures=0;state.signs=new long[0];Object service=service(loader,"server.hidden.service.impl.CheckHiddenDangerServiceImpl",state);
  Class<?> mapper=Class.forName(ROOT+"server.hidden.mapper.CheckHiddenDangerMapper",true,loader);field(service,"baseMapper",proxy(mapper,state));
  Object entity=make(loader,"server.hidden.entity.CheckHiddenDangerEntity");call(entity,"setId","SYNTHETIC-HIDDEN");call(entity,"setIsPass",input);call(entity,"setReviewDescribe","Synthetic method-only characterization");
  boolean returned=Boolean.TRUE.equals(call(service,"reviewHidden",entity));Object result=call(entity,"getHiddenDangerStatus");Object constant=Class.forName(ROOT+"common.Constants",true,loader).getField("YHXX_YHZT_YHZGWYH").get(null);
  Map<String,Object> row=new LinkedHashMap<>();row.put("case",name);row.put("returnedTrue",returned);row.put("reviewRecordCaptured",state.review!=null);row.put("sourceEntityCaptured",state.updated==entity);row.put("inMemoryWrites",state.writes);row.put("finalState",result);row.put("matchesReferenceClosedConstant",Objects.equals(result,constant));row.put("characterizationCompleted",returned&&state.review!=null&&state.updated==entity&&state.writes==2);return row;
 }
 static String json(Object value){
  if(value==null)return "null";if(value instanceof Boolean||value instanceof Number)return value.toString();if(value instanceof Map<?,?> m){List<String> parts=new ArrayList<>();for(var e:m.entrySet())parts.add(json(e.getKey().toString())+":"+json(e.getValue()));return "{"+String.join(",",parts)+"}";}if(value instanceof Collection<?> c)return "["+String.join(",",c.stream().map(OriginalBusinessMethodProbe::json).toList())+"]";
  StringBuilder b=new StringBuilder("\"");for(char ch:value.toString().toCharArray())switch(ch){case '\\'->b.append("\\\\");case '"'->b.append("\\\"");case '\n'->b.append("\\n");case '\r'->b.append("\\r");case '\t'->b.append("\\t");default->{if(ch<32)b.append(String.format(Locale.ROOT,"\\u%04x",(int)ch));else b.append(ch);}}return b.append('"').toString();
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=3)throw new IllegalArgumentException("APP_JAR_DEPENDENCY_LIST_FRESH_OUTPUT_REQUIRED");Path app=Path.of(args[0]).toRealPath(),list=Path.of(args[1]).toRealPath(),output=Path.of(args[2]).toAbsolutePath().normalize();if(Files.exists(output)||!Files.isDirectory(output.getParent()))throw new IllegalStateException("FRESH_OUTPUT_REQUIRED");
  List<Path> deps=new ArrayList<>();for(String line:Files.readAllLines(list,StandardCharsets.UTF_8))if(!line.isBlank())deps.add(Path.of(line).toRealPath());if(deps.size()>256)throw new IllegalStateException("DEPENDENCY_LIMIT");
  try(ZipFile warm=new ZipFile(app.toFile())){ZipEntry e=warm.getEntry("BOOT-INF/classes/com/iemp/endanger/server/work/service/impl/WorkServiceImpl.class");if(e==null)e=warm.getEntry("com/iemp/endanger/server/work/service/impl/WorkServiceImpl.class");if(e==null)throw new IllegalStateException("BUSINESS_CLASS_REQUIRED");try(InputStream in=warm.getInputStream(e)){if(in.readNBytes(4).length!=4)throw new IllegalStateException("CLASS_HEADER_REQUIRED");}}
  Guard guard=new Guard(output.getParent());System.setSecurityManager(guard);if(System.getSecurityManager()!=guard)throw new AssertionError("GUARD_NOT_INSTALLED");
  int selfTests=0;try{guard.checkConnect("synthetic.invalid",443);}catch(SecurityException e){selfTests++;}try{guard.checkExec("SYNTHETIC_DO_NOT_EXECUTE");}catch(SecurityException e){selfTests++;}
  Path forbidden=output.getParent().getParent().resolve("forbidden-probe-write.txt");if(Files.exists(forbidden))throw new IllegalStateException("FRESH_SELFTEST_TARGET_REQUIRED");try{Files.writeString(forbidden,"must not be written");}catch(SecurityException e){selfTests++;}if(Files.exists(forbidden)||selfTests!=3)throw new AssertionError("GUARD_SELFTEST_FAILED");guard.reset();
  List<Map<String,Object>> works=new ArrayList<>(),reviews=new ArrayList<>();
  try(OriginalLoader loader=new OriginalLoader(app,deps)){
   Thread.currentThread().setContextClassLoader(loader);
   works.add(workCase(loader,"missing-measures","动火作业",0,new long[]{},false,"开始作业必须先完成安全措施"));
   works.add(workCase(loader,"missing-briefing","动火作业",1,new long[]{0},false,"开始作业必须先完成安全交底"));
   works.add(workCase(loader,"missing-foreman-check","动火作业",1,new long[]{1,0},false,"开始作业必须当班班长验票"));
   works.add(workCase(loader,"missing-approval","动火作业",1,new long[]{1,1,0},false,"审批后才可以开始作业"));
   works.add(workCase(loader,"unsupported-work-type","SYNTHETIC-UNKNOWN",1,new long[]{1,1},false,"错误的作业类型"));
   for(String kind:WORKS.keySet())works.add(workCase(loader,"accepted-"+WORKS.get(kind),kind,1,kind.equals("动火作业")?new long[]{1,1,1}:new long[]{1,1},true,null));
   String same=(String)Class.forName(ROOT+"common.Constants",true,loader).getField("YHXX_YHZT_WPF").get(null);
   reviews.add(reviewCase(loader,"same-reference-input",same));reviews.add(reviewCase(loader,"equal-text-new-string",new String(same)));reviews.add(reviewCase(loader,"different-input","SYNTHETIC-NOT-PASS"));reviews.add(reviewCase(loader,"empty-input",""));
  }
  Map<String,Object> result=new LinkedHashMap<>();result.put("javaVersion",System.getProperty("java.version"));result.put("guardSelfTests",selfTests);result.put("workCases",works);result.put("reviewCharacterizations",reviews);result.put("originalNetworkAttemptsDenied",guard.network);result.put("originalProcessAttemptsDenied",guard.process);result.put("originalOutsideWritesDenied",guard.writes);result.put("originalNativeLoadsDenied",guard.links);result.put("databaseConnected",false);result.put("springContextStarted",false);result.put("fullBusinessFlowVerified",false);
  boolean passed=works.size()==13&&works.stream().allMatch(r->Boolean.TRUE.equals(r.get("passed")))&&reviews.size()==4&&reviews.stream().allMatch(r->Boolean.TRUE.equals(r.get("characterizationCompleted")))&&guard.network==0&&guard.process==0&&guard.writes==0&&guard.links==0;result.put("methodProbeCompleted",passed);
  Files.writeString(output,json(result)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);System.out.println("METHOD_PROBE work="+works.size()+" review="+reviews.size()+" completed="+passed);System.exit(passed?0:2);
 }
}
