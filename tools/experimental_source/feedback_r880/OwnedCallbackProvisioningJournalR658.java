import java.io.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.util.*;

/** Private, per-stage SQL intent/ack record. Does not prove runtime identity.
 * The actual parent must own the directory and validate live DB/controller first.
 */
public final class OwnedCallbackProvisioningJournalR658{
    public record Binding(String attemptId,String databaseUUID,String dataDirectory,String releaseSHA256,
                          long controllerPID,String planSHA256,String beforeRowsSHA256,String afterRowsSHA256,String stage){}
    final Path path;final Binding binding;final Properties base;
    static void need(boolean b,String message)throws IOException{if(!b)throw new IOException(message);}
    static boolean hash(String s){return s!=null&&s.matches("[0-9a-f]{64}");}
    static void plain(Path p)throws IOException{
        need(p.isAbsolute()&&p.toAbsolutePath().normalize().equals(p),"NORMAL_ABSOLUTE_CALLBACK_JOURNAL_REQUIRED");
        for(Path q=p;q!=null;q=q.getParent())if(Files.exists(q))need(!Files.isSymbolicLink(q)&&q.toRealPath().equals(q),"CALLBACK_JOURNAL_LINK_REFUSED");
    }
    public OwnedCallbackProvisioningJournalR658(Path p,Binding b)throws IOException{
        plain(p);binding=b;path=p;need(Files.isDirectory(p.getParent()),"PARENT_OWNED_ATTEMPT_DIRECTORY_REQUIRED");
        need(b!=null&&b.attemptId()!=null&&b.attemptId().matches("[0-9a-f]{32}")&&b.controllerPID()>0,"EXACT_CALLBACK_ATTEMPT_BINDING_REQUIRED");
        try{need(UUID.fromString(b.databaseUUID()).toString().equals(b.databaseUUID()),"CANONICAL_CALLBACK_DATABASE_UUID_REQUIRED");}catch(IllegalArgumentException e){throw new IOException("CANONICAL_CALLBACK_DATABASE_UUID_REQUIRED");}
        need(hash(b.releaseSHA256())&&hash(b.planSHA256())&&hash(b.afterRowsSHA256()),"EXACT_CALLBACK_PLAN_PINS_REQUIRED");
        need(Set.of("first-start","normal-restart").contains(b.stage())&&p.getFileName().toString().equals("callback-"+b.stage()+"-journal.private.properties"),"EXACT_CALLBACK_STAGE_JOURNAL_NAME_REQUIRED");
        need(b.stage().equals("first-start")?b.beforeRowsSHA256()==null:hash(b.beforeRowsSHA256()),"EXACT_CALLBACK_PREVIOUS_ROWS_PIN_REQUIRED");
        Path data=Path.of(b.dataDirectory());need(data.isAbsolute()&&data.normalize().equals(data),"ABSOLUTE_CALLBACK_DATABASE_DIRECTORY_REQUIRED");
        need(p.toString().length()+8<260,"CALLBACK_JOURNAL_TEMP_PATH_TOO_LONG");
        base=new Properties();base.setProperty("schema","xnby.owned-callback-provisioning.r658.v1");base.setProperty("attemptId",b.attemptId());
        base.setProperty("databaseUUID",b.databaseUUID());base.setProperty("dataDirectory",b.dataDirectory());base.setProperty("releaseSHA256",b.releaseSHA256());
        base.setProperty("controllerPID",Long.toString(b.controllerPID()));base.setProperty("planSHA256",b.planSHA256());
        base.setProperty("beforeRowsSHA256",b.beforeRowsSHA256()==null?"absent":b.beforeRowsSHA256());base.setProperty("afterRowsSHA256",b.afterRowsSHA256());base.setProperty("stage",b.stage());
        base.setProperty("journalPath",p.toString());
    }
    public Binding binding(){return binding;}
    public Path path(){return path;}
    static Properties parse(byte[] raw)throws IOException{
        need(raw.length>0&&raw.length<16384,"BOUNDED_CALLBACK_JOURNAL_REQUIRED");Properties p=new Properties();p.load(new ByteArrayInputStream(raw));return p;
    }
    public byte[] requireCurrent()throws IOException{
        plain(path);byte[] raw=Files.readAllBytes(path);Properties p=parse(raw);
        Set<String> keys=new HashSet<>(base.stringPropertyNames());keys.add("phase");need(p.stringPropertyNames().equals(keys),"EXACT_CALLBACK_JOURNAL_KEYS_REQUIRED");
        for(String k:base.stringPropertyNames())need(Objects.equals(p.getProperty(k),base.getProperty(k)),"CALLBACK_JOURNAL_BINDING_DRIFT_REFUSED");
        need(Set.of("issued-before-sql","commit-confirmed","readback-verified").contains(p.getProperty("phase")),"KNOWN_CALLBACK_JOURNAL_PHASE_REQUIRED");return raw;
    }
    public String phase()throws IOException{return parse(requireCurrent()).getProperty("phase");}
    public void requireUnused()throws IOException{
        plain(path);plain(path.resolveSibling(path.getFileName()+".writing"));
        need(!Files.exists(path)&&!Files.exists(path.resolveSibling(path.getFileName()+".writing")),"CALLBACK_ATTEMPT_ALREADY_ISSUED_NO_AUTO_RETRY");
    }
    static String digest(Path p)throws IOException {
        try {return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
        catch(java.security.NoSuchAlgorithmException e){throw new IOException(e);}
    }
    void previous()throws IOException{
        need(binding.stage().equals("normal-restart"),"ONLY_EXPLICIT_MANAGER_REBIND_STAGE_REQUIRED");
        Path root=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609");
        Path first=root.resolve("feedback-r880/first-start"),second=root.resolve("feedback-r880/normal-restart");
        need(path.getParent().equals(first)||path.getParent().equals(second),"EXACT_OWN_FEEDBACK_CALLBACK_CHAIN_REQUIRED");
        boolean transition=path.getParent().equals(first);
        Path previous=(transition?root.resolve("task-ui-r806/normal-restart"):first).resolve("callback-normal-restart-journal.private.properties");plain(previous);
        if(transition)need(digest(previous).equals("6d097be8b8ce094c0d8b0e41c7f1e67faa897fa23d3b821e1869d8ae62d25b98"),"PINNED_OLD_CALLBACK_JOURNAL_REQUIRED");
        Properties p=parse(Files.readAllBytes(previous));
        Set<String> keys=new HashSet<>(base.stringPropertyNames());keys.add("phase");need(p.stringPropertyNames().equals(keys),"EXACT_PREVIOUS_CALLBACK_JOURNAL_KEYS_REQUIRED");
        need(p.getProperty("phase").equals("readback-verified"),"VERIFIED_PREVIOUS_CALLBACK_STAGE_REQUIRED");
        for(String k:List.of("schema","attemptId","databaseUUID","dataDirectory"))need(base.getProperty(k).equals(p.getProperty(k)),"PREVIOUS_CALLBACK_STAGE_IDENTITY_DRIFT");
        need(base.getProperty("releaseSHA256").equals("eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93")&&p.getProperty("releaseSHA256").equals(transition?"e957cf851cb253d4ac020ef04711ebd6e9f066bfc1471002b10d53c88de71db2":"eb14761be88db0e21f037cd5ad8d3b648eeb8bbf561bf8c71b0f742f1cda6c93"),"EXACT_FIXED_CALLBACK_RELEASE_TRANSITION_REQUIRED");
        Path previousPlan=previous.resolveSibling("callback-normal-restart-plan.private.json");plain(previousPlan);
        need(p.getProperty("planSHA256").equals(digest(previousPlan)),"PREVIOUS_CALLBACK_PLAN_BINDING_REQUIRED");
        need(p.getProperty("stage").equals("normal-restart")&&p.getProperty("journalPath").equals(previous.toString())&&binding.beforeRowsSHA256().equals(p.getProperty("afterRowsSHA256")),"EXACT_PREVIOUS_CALLBACK_ROWS_REQUIRED");
    }
    public byte[] prepare()throws IOException{requireUnused();previous();return write("issued-before-sql",null);}
    static byte[] encoded(Properties p)throws IOException{ByteArrayOutputStream out=new ByteArrayOutputStream();p.store(out,"Private owned callback intent; no credentials or raw rows");return out.toByteArray();}
    static void forceWrite(Path p,byte[] raw)throws IOException{
        try(FileChannel c=FileChannel.open(p,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            ByteBuffer b=ByteBuffer.wrap(raw);while(b.hasRemaining())c.write(b);c.force(true);
        }
    }
    byte[] write(String phase,byte[] expected)throws IOException{
        plain(path);Properties p=new Properties();p.putAll(base);p.setProperty("phase",phase);byte[] raw=encoded(p);
        if(expected==null){requireUnused();forceWrite(path,raw);need(Arrays.equals(Files.readAllBytes(path),raw),"CALLBACK_INTENT_WRITE_READBACK_FAILED");return raw;}
        need(Arrays.equals(requireCurrent(),expected),"CALLBACK_JOURNAL_CHANGED_BEFORE_ACK");
        Path tmp=path.resolveSibling(path.getFileName()+".writing");plain(tmp);need(!Files.exists(tmp),"CALLBACK_ACK_TEMP_ALREADY_EXISTS");
        boolean created=false;
        try{
            forceWrite(tmp,raw);created=true;need(Arrays.equals(requireCurrent(),expected),"CALLBACK_JOURNAL_DRIFT_BEFORE_ACK_REPLACE");
            Files.move(tmp,path,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);created=false;
        }finally{if(created)Files.deleteIfExists(tmp);}
        need(Arrays.equals(Files.readAllBytes(path),raw),"CALLBACK_ACK_WRITE_READBACK_FAILED");return raw;
    }
    public byte[] commitConfirmed(byte[] issued)throws IOException{
        need(parse(issued).getProperty("phase").equals("issued-before-sql"),"CALLBACK_ISSUED_INTENT_REQUIRED");return write("commit-confirmed",issued);
    }
    public byte[] readbackVerified(byte[] observed)throws IOException{return write("readback-verified",observed);}
}
