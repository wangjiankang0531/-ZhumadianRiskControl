package xnby.replica;

import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Synthetic, in-memory Redis transport only. Never authenticates or starts Spring. */
public final class OriginalRedisWireProbe {
    private static ClassLoader loader;
    private static Path root;
    private static final String PREFIX="cqweh:opm:userInfo:";
    private static final String[] FIELDS={"UserId","DeptId","Name","UserName","Mobile","AvatarPath"};
    private static final List<String> results=new ArrayList<String>();
    private static final Map<String,byte[]> wire=new LinkedHashMap<String,byte[]>();
    private static int sets, gets, expirations, factoryConnections;
    private static final List<Long> expiryMillis=new ArrayList<Long>();

    private static Class<?> type(String name)throws Exception {return Class.forName(name,true,loader);}
    private static Object call(Object receiver,String method,Class<?>[] types,Object... values)throws Exception {
        try{return receiver.getClass().getMethod(method,types).invoke(receiver,values);}
        catch(InvocationTargetException failure){throw new IllegalStateException("ORIGINAL_CALL_FAILED_"+method,failure.getCause());}
    }
    private static void check(boolean ok,String name){if(!ok)throw new IllegalStateException(name);}
    private static String[] sample(int n){
        String[] values={"wire-user-"+n,"wire-dept-"+n,"合成用户"+n,"wire-name-"+n,"00000000000","/synthetic/avatar-"+n+".png"};
        if(n==1)values[2]="汉字与补充字符\uD83D\uDE80";
        if(n==2)values[2]="引号\"与反斜线\\及换行\n下一行";
        if(n==3){values[2]="";values[4]="";values[5]="";}
        if(n==4){values[1]=null;values[4]=null;values[5]=null;}
        if(n==5){char[] many=new char[8192];Arrays.fill(many,'测');values[2]=new String(many);}
        return values;
    }
    private static String b64(byte[] bytes){return Base64.getEncoder().encodeToString(bytes);}
    private static byte[] utf8(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static Object defaultObject(Object proxy,Method method,Object[] args){
        if(method.getName().equals("toString"))return "SYNTHETIC_REDIS_NO_NETWORK";
        if(method.getName().equals("hashCode"))return System.identityHashCode(proxy);
        if(method.getName().equals("equals"))return proxy==args[0];
        throw new IllegalStateException("UNEXPECTED_OBJECT_METHOD");
    }
    private static Object factory()throws Exception {
        final Class<?> connectionType=type("org.springframework.data.redis.connection.RedisConnection");
        final Object connection=Proxy.newProxyInstance(loader,new Class<?>[]{connectionType},new InvocationHandler(){
            public Object invoke(Object proxy,Method method,Object[] args)throws Throwable {
                String name=method.getName();
                if(method.getDeclaringClass()==Object.class)return defaultObject(proxy,method,args);
                if(name.equals("isPipelined")||name.equals("isQueueing")||name.equals("isClosed"))return false;
                if(name.equals("close"))return null;
                if(name.endsWith("Commands")&&method.getReturnType().isInstance(proxy))return proxy;
                if(name.equals("set")&&args.length==2&&args[0] instanceof byte[]&&args[1] instanceof byte[]){
                    String key=b64((byte[])args[0]);check(!wire.containsKey(key),"DUPLICATE_SYNTHETIC_SET");
                    wire.put(key,((byte[])args[1]).clone());sets++;return Boolean.TRUE;
                }
                if(name.equals("get")&&args.length==1&&args[0] instanceof byte[]){
                    byte[] result=wire.get(b64((byte[])args[0]));gets++;return result==null?null:result.clone();
                }
                if((name.equals("expire")||name.equals("pExpire"))&&args.length==2&&args[0] instanceof byte[]&&args[1] instanceof Number){
                    check(wire.containsKey(b64((byte[])args[0])),"EXPIRY_WITHOUT_SYNTHETIC_SET");
                    long duration=((Number)args[1]).longValue();check(duration>0,"NONPOSITIVE_ORIGINAL_EXPIRY");
                    expiryMillis.add(name.equals("expire")?Math.multiplyExact(duration,1000L):duration);expirations++;return Boolean.TRUE;
                }
                throw new IllegalStateException("UNEXPECTED_REDIS_COMMAND_"+name);
            }
        });
        return Proxy.newProxyInstance(loader,new Class<?>[]{type("org.springframework.data.redis.connection.RedisConnectionFactory")},new InvocationHandler(){
            public Object invoke(Object proxy,Method method,Object[] args){
                if(method.getDeclaringClass()==Object.class)return defaultObject(proxy,method,args);
                if(method.getName().equals("getConnection")){factoryConnections++;return connection;}
                if(method.getName().equals("getConvertPipelineAndTxResults"))return false;
                if(method.getName().equals("translateExceptionIfPossible"))return null;
                throw new IllegalStateException("UNEXPECTED_CONNECTION_FACTORY_"+method.getName());
            }
        });
    }
    private static void originalClass(String name)throws Exception {
        String resource=name.replace('.','/')+".class";
        java.io.InputStream stream=loader.getResourceAsStream(resource);check(stream!=null,"CLASS_RESOURCE_MISSING");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try{byte[] block=new byte[8192];int length;while((length=stream.read(block))!=-1)digest.update(block,0,length);}finally{stream.close();}
        StringBuilder hex=new StringBuilder();for(byte value:digest.digest())hex.append(String.format("%02x",value&255));
        results.add("CLASS\t"+name+"\t"+hex);
    }
    private static void write()throws Exception {
        Object config=type("jnpf.config.RedisConfig").getConstructor().newInstance();
        Field factoryField=config.getClass().getDeclaredField("factory");factoryField.setAccessible(true);factoryField.set(config,factory());
        Object template=call(config,"redisTemplate",new Class<?>[0]);
        Object util=type("jnpf.util.RedisUtil").getConstructor().newInstance();
        Field templateField=util.getClass().getDeclaredField("redisTemplate");templateField.setAccessible(true);templateField.set(util,template);
        Class<?> model=type("jnpf.model.LoginUser");
        for(int i=0;i<6;i++){
            Object user=model.getConstructor().newInstance();String[] values=sample(i);
            for(int f=0;f<FIELDS.length;f++)call(user,"set"+FIELDS[f],new Class<?>[]{String.class},values[f]);
            call(util,"insert",new Class<?>[]{String.class,Object.class},PREFIX+values[0],user);
            results.add("PASS\tplatform-original-insert-"+i+"\t6-synthetic-fields");
        }
        check(sets==6&&gets==0&&expirations==6,"UNEXPECTED_WRITE_COUNTS");
        check(new HashSet<Long>(expiryMillis).size()==1,"INCONSISTENT_ORIGINAL_EXPIRY");
        results.add("EXPIRATION_MILLISECONDS\t"+expiryMillis.get(0));
        List<String> rows=new ArrayList<String>();for(Map.Entry<String,byte[]> row:wire.entrySet())rows.add(row.getKey()+"\t"+b64(row.getValue()));
        Files.write(root.resolve("synthetic-redis-wire.tsv"),rows,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        Object serializer=call(template,"getValueSerializer",new Class<?>[0]);
        results.add("SERIALIZER\tplatform\t"+serializer.getClass().getName());
        for(String name:new String[]{"jnpf.config.RedisConfig","jnpf.util.RedisUtil","jnpf.model.LoginUser"})originalClass(name);
    }
    private static void read()throws Exception {
        for(String row:Files.readAllLines(root.resolve("synthetic-redis-wire.tsv"),StandardCharsets.UTF_8)){
            String[] columns=row.split("\\t",-1);check(columns.length==2,"WIRE_ROW_FORMAT");
            byte[] raw=Base64.getDecoder().decode(columns[1]);check(raw.length<=128*1024,"WIRE_SIZE_LIMIT");
            check(wire.put(columns[0],raw)==null,"DUPLICATE_WIRE_KEY");
        }
        check(wire.size()==6,"WIRE_CASE_COUNT");
        Object config=type("com.cqweh.cloud.redis.RedisAutoConfiguration").getConstructor().newInstance();
        Object template=call(config,"redisTemplate",new Class<?>[]{type("org.springframework.data.redis.connection.RedisConnectionFactory")},factory());
        call(template,"afterPropertiesSet",new Class<?>[0]);
        Class<?> manager=type("com.cqweh.cloud.cache.core.CacheManager");
        Object cacheManager=Proxy.newProxyInstance(loader,new Class<?>[]{manager},new InvocationHandler(){
            public Object invoke(Object proxy,Method method,Object[] args){
                if(method.getDeclaringClass()==Object.class)return defaultObject(proxy,method,args);
                if(method.getName().equals("getCache"))return null;
                throw new IllegalStateException("UNEXPECTED_CACHE_MANAGER_CALL");
            }
        });
        Class<?> properties=type("com.cqweh.cloud.security.config.SecurityProperties");
        Object session=type("com.cqweh.cloud.security.core.SessionManager").getConstructor(manager,type("org.springframework.data.redis.core.RedisTemplate"),properties)
            .newInstance(cacheManager,template,properties.getConstructor().newInstance());
        Class<?> model=type("com.cqweh.cloud.security.model.LoginUser");
        Method parse=type("com.cqweh.cloud.common.utils.Jsons").getMethod("readObject",String.class,Class.class);
        for(int i=0;i<6;i++){
            String[] expected=sample(i);String json=(String)call(session,"getUser",new Class<?>[]{String.class},PREFIX+expected[0]);
            Object actual=parse.invoke(null,json,model);
            for(int f=0;f<FIELDS.length;f++)check(Objects.equals(expected[f],call(actual,"get"+FIELDS[f],new Class<?>[0])),"FIELD_MISMATCH_"+i+"_"+FIELDS[f]);
            results.add("PASS\tbusiness-original-read-"+i+"\t6-synthetic-fields");
        }
        boolean missingRejected=false;
        try{call(session,"getUser",new Class<?>[]{String.class},PREFIX+"synthetic-missing");}
        catch(IllegalStateException expected){
            Throwable cause=expected;while(cause.getCause()!=null)cause=cause.getCause();
            missingRejected=cause instanceof NullPointerException;
        }
        check(missingRejected,"MISSING_ORIGINAL_SESSION_NOT_REJECTED");
        results.add("EXPECTED_REJECTION\tmissing-cache-entry\tjava.lang.NullPointerException");
        check(sets==0&&gets==7&&expirations==0,"UNEXPECTED_READ_COUNTS");
        Object serializer=call(template,"getValueSerializer",new Class<?>[0]);
        results.add("SERIALIZER\tbusiness\t"+serializer.getClass().getName());
        for(String name:new String[]{"com.cqweh.cloud.redis.RedisAutoConfiguration","com.cqweh.cloud.security.core.SessionManager","com.cqweh.cloud.security.model.LoginUser","com.cqweh.cloud.common.utils.Jsons"})originalClass(name);
    }
    public static void main(String[] args)throws Exception {
        check(args.length==2,"EXPLICIT_MODE_AND_ROOT_REQUIRED");loader=Thread.currentThread().getContextClassLoader();root=Paths.get(args[1]).toRealPath();
        if(args[0].equals("platform-write"))write();else if(args[0].equals("business-read"))read();else throw new IllegalArgumentException("UNKNOWN_MODE");
        results.add("COUNTS\tsets="+sets+"\tgets="+gets+"\texpirations="+expirations+"\tconnections="+factoryConnections);
        Files.write(root.resolve(args[0]+"-results.tsv"),results,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("SYNTHETIC_ORIGINAL_REDIS_WIRE_PASS "+args[0]);
    }
}
