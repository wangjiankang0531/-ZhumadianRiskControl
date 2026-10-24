package xnby.replica;

import org.springframework.context.ApplicationContextInitializer;
import org.springframework.context.ConfigurableApplicationContext;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Observe original beans against one owned Redis, with a non-auth synthetic key. */
public final class OriginalJointRedisObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
    private static final String[] FIELDS={"UserId","DeptId","Name","UserName","Mobile","AvatarPath"};
    private static final String[] VALUES={"joint-synthetic-user","joint-synthetic-dept","联合缓存检查","joint-synthetic-name","00000000000","/synthetic/avatar.png"};
    public void initialize(final ConfigurableApplicationContext context){
        if(Arrays.stream(context.getClass().getMethods()).noneMatch(method->method.getName().equals("getServletContext")&&method.getParameterCount()==0))return;
        context.addApplicationListener(event->{
            if(!event.getClass().getName().equals("org.springframework.boot.context.event.ApplicationReadyEvent"))return;
            try{if(event.getClass().getMethod("getApplicationContext").invoke(event)!=context)return;}
            catch(Exception failure){throw new IllegalStateException("JOINT_EVENT_CONTEXT_FAILED",failure);}
            final Path root=Paths.get(System.getProperty("own.joint.root"));
            Thread worker=new Thread(()->observe(context,root),"own-joint-redis-observer");worker.setDaemon(true);worker.start();
        });
    }
    private static Object call(Object value,String name,Class<?>[] types,Object... args)throws Exception{
        try{return value.getClass().getMethod(name,types).invoke(value,args);}
        catch(InvocationTargetException error){throw new IllegalStateException("ORIGINAL_JOINT_CALL_FAILED_"+name,error.getCause());}
    }
    private static void require(boolean condition,String reason){if(!condition)throw new IllegalStateException(reason);}
    private static void observe(ConfigurableApplicationContext context,Path root){
        Properties result=new Properties();Object connection=null;
        try{
            Properties expected=new Properties();try(java.io.InputStream input=Files.newInputStream(root.resolve("joint-redis-expected.private.properties"))){expected.load(input);}
            String side=expected.getProperty("side"),prefix=side.equals("platform")?"spring.redis":"spring.data.redis";
            require(side.equals("platform")||side.equals("business"),"INVALID_OWN_SIDE");
            String key=expected.getProperty("probeKey");require(key.matches("__xnby_joint_wire_[a-f0-9-]{36}"),"INVALID_NONAUTH_PROBE_KEY");
            result.setProperty("side",side);
            for(String field:new String[]{"host","port","database","password"}){
                boolean equal=Objects.equals(expected.getProperty(field),context.getEnvironment().getProperty(prefix+"."+field));
                result.setProperty("effective"+field+"MatchesExpected",Boolean.toString(equal));require(equal,"OWN_REDIS_PROPERTY_MISMATCH_"+field);
            }
            ClassLoader loader=context.getClassLoader();Class<?> templateClass=Class.forName("org.springframework.data.redis.core.RedisTemplate",true,loader);
            Object template=context.getBean("redisTemplate");Object factory=templateClass.getMethod("getConnectionFactory").invoke(template);
            Class<?> factoryClass=Class.forName("org.springframework.data.redis.connection.RedisConnectionFactory",true,loader);
            connection=factoryClass.getMethod("getConnection").invoke(factory);
            Class<?> connectionClass=Class.forName("org.springframework.data.redis.connection.RedisConnection",true,loader);
            Object ping=connectionClass.getMethod("ping").invoke(connection);require("PONG".equals(ping),"OWN_REDIS_PING_FAILED");
            Properties info=(Properties)connectionClass.getMethod("info",String.class).invoke(connection,"server");
            require(expected.getProperty("processId").equals(info.getProperty("process_id")),"OWN_REDIS_PROCESS_ID_MISMATCH");
            result.setProperty("actualRedisProcessId",info.getProperty("process_id"));result.setProperty("ping","PONG");
            connectionClass.getMethod("close").invoke(connection);connection=null;
            if(side.equals("platform")){
                Class<?> model=Class.forName("jnpf.model.LoginUser",true,loader);Object user=model.getConstructor().newInstance();
                for(int i=0;i<FIELDS.length;i++)call(user,"set"+FIELDS[i],new Class<?>[]{String.class},VALUES[i]);
                Class<?> utilClass=Class.forName("jnpf.util.RedisUtil",true,loader);Object util=context.getBean(utilClass);
                utilClass.getMethod("insert",String.class,Object.class).invoke(util,key,user);
                result.setProperty("originalPlatformInsertCompleted","true");
            }else{
                long deadline=System.nanoTime()+90L*1000000000L;
                while(!Boolean.TRUE.equals(templateClass.getMethod("hasKey",Object.class).invoke(template,key))){
                    require(System.nanoTime()<deadline,"OWN_SHARED_KEY_WAIT_TIMEOUT");Thread.sleep(250);
                }
                Class<?> managerClass=Class.forName("com.cqweh.cloud.security.core.SessionManager",true,loader);
                Object manager=context.getBean(managerClass);
                String json=(String)managerClass.getMethod("getUser",String.class).invoke(manager,key);
                Class<?> jsons=Class.forName("com.cqweh.cloud.common.utils.Jsons",true,loader),model=Class.forName("com.cqweh.cloud.security.model.LoginUser",true,loader);
                Object user=jsons.getMethod("readObject",String.class,Class.class).invoke(null,json,model);
                for(int i=0;i<FIELDS.length;i++)require(Objects.equals(VALUES[i],call(user,"get"+FIELDS[i],new Class<?>[0])),"JOINT_FIELD_MISMATCH_"+FIELDS[i]);
                require(Boolean.TRUE.equals(templateClass.getMethod("delete",Object.class).invoke(template,key)),"OWN_SYNTHETIC_KEY_DELETE_FAILED");
                require(Boolean.FALSE.equals(templateClass.getMethod("hasKey",Object.class).invoke(template,key)),"OWN_SYNTHETIC_KEY_STILL_EXISTS");
                result.setProperty("originalBusinessReadFieldsMatched","6");result.setProperty("syntheticKeyDeleted","true");
            }
            result.setProperty("passed","true");
        }catch(Throwable failure){
            result.setProperty("passed","false");
            while(failure instanceof InvocationTargetException&&failure.getCause()!=null)failure=failure.getCause();
            result.setProperty("failureClass",failure.getClass().getName());
            try{java.io.StringWriter text=new java.io.StringWriter();failure.printStackTrace(new java.io.PrintWriter(text));Files.write(root.resolve("joint-redis-failure.private.log"),text.toString().getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){}
        }finally{
            if(connection!=null)try{Class.forName("org.springframework.data.redis.connection.RedisConnection",true,context.getClassLoader()).getMethod("close").invoke(connection);}catch(Exception ignored){}
            result.setProperty("loginOrJwtAttempted","false");result.setProperty("businessHttpAuthenticationVerified","false");
            try(java.io.OutputStream output=Files.newOutputStream(root.resolve("joint-redis-observation.properties"),StandardOpenOption.CREATE_NEW)){
                result.store(output,"Owned shared Redis original-bean observation; no credentials or user data");
            }catch(Exception error){throw new IllegalStateException("JOINT_OBSERVATION_WRITE_FAILED",error);}
        }
    }
}
