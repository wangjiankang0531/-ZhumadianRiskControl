package xnby.platform.history;

import org.apache.ibatis.executor.Executor;
import org.apache.ibatis.mapping.MappedStatement;
import org.apache.ibatis.plugin.*;
import com.baomidou.dynamic.datasource.tx.TransactionContext;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.sql.Connection;
import java.util.Map;
import java.util.function.BooleanSupplier;

/** Capture only the original service's successful before-addsign record update. */
@Intercepts(@Signature(type=Executor.class,method="update",args={MappedStatement.class,Object.class}))
public final class OriginalBeforeAddsignHistoryInterceptor implements Interceptor {
  private static final String ENTITY="jnpf.engine.entity.FlowTaskOperatorRecordEntity";
  private static final String STATEMENT="jnpf.engine.mapper.FlowTaskOperatorRecordMapper.updateById";
  private final BooleanSupplier originalCall;
  public OriginalBeforeAddsignHistoryInterceptor() { this(OriginalBeforeAddsignHistoryInterceptor::originalServiceCall); }
  OriginalBeforeAddsignHistoryInterceptor(BooleanSupplier originalCall) {
    this.originalCall=originalCall;
    pin(ENTITY,"e476d426af5f71273de27ee75048d2bdbdbd493bdf7192dc5dbb3974439ef70c");
    pin("jnpf.engine.mapper.FlowTaskOperatorRecordMapper","8f1669734b88cc7dbdef1da0e40d6f8278f7ff1d38bb7e71e48b54cf00aa58fe");
  }
  private static void pin(String name,String expected) {
    try(InputStream input=OriginalBeforeAddsignHistoryInterceptor.class.getClassLoader().getResourceAsStream(name.replace('.','/')+".class")){
      if(input==null)throw new IllegalStateException("ORIGINAL_HISTORY_MODEL_RESOURCE_REQUIRED");
      ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;
      while((count=input.read(buffer))!=-1){if(bytes.size()+count>262144)throw new IllegalStateException("ORIGINAL_HISTORY_MODEL_SIZE_BOUND");bytes.write(buffer,0,count);}
      StringBuilder digest=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes.toByteArray()))digest.append(String.format(java.util.Locale.ROOT,"%02x",b&255));
      if(!digest.toString().equals(expected))
        throw new IllegalStateException("ORIGINAL_HISTORY_MODEL_PIN_MISMATCH");
    }catch(Exception error){throw new IllegalStateException("ORIGINAL_HISTORY_MODEL_PIN_REJECTED",error);}
  }
  private static boolean originalServiceCall() {
    for(StackTraceElement frame:Thread.currentThread().getStackTrace())
      if(frame.getClassName().equals("jnpf.engine.service.impl.FlowTaskNewServiceImpl")&&frame.getMethodName().equals("freeApprover"))return true;
    return false;
  }
  private static Object get(Object value,String method)throws Exception {
    Method getter=value.getClass().getMethod(method);return getter.invoke(value);
  }
  @Override public Object intercept(Invocation invocation)throws Throwable {
    MappedStatement mapped=(MappedStatement)invocation.getArgs()[0];
    if(!STATEMENT.equals(mapped.getId())||!originalCall.getAsBoolean())return invocation.proceed();
    Object value=invocation.getArgs()[1];
    if(value instanceof Map<?,?>)value=((Map<?,?>)value).get("et");
    if(value==null||!ENTITY.equals(value.getClass().getName())||!Integer.valueOf(10).equals(get(value,"getHandleStatus")))return invocation.proceed();
    Executor executor=(Executor)invocation.getTarget();Connection connection=executor.getTransaction().getConnection();
    if(TransactionContext.getXID()==null||connection.getAutoCommit()||!"jnpf".equalsIgnoreCase(connection.getCatalog()))
      throw new IllegalStateException("ORIGINAL_HISTORY_TRANSACTION_REQUIRED_BEFORE_UPDATE");
    String record=String.valueOf(get(value,"getId")),process=(String)get(value,"getTaskId"),actor=(String)get(value,"getHandleId");
    Object result=invocation.proceed();
    // The original batch executor queues updates. Flush within the existing transaction,
    // so the snapshot SELECT observes its new opinion/status and never commits on its own.
    executor.flushStatements();
    OriginalAddsignOpinionHistory.appendBeforeSignature(connection,record,process,actor);
    return result;
  }
}
