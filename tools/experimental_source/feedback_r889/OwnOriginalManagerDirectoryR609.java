import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.*;
import java.sql.*;
import java.util.*;

/** Future owned full-lifecycle data fixture: two existing normal users, one manager field.
 * No user creation, password/session reads, roles, permanent schema or public host.
 */
public final class OwnOriginalManagerDirectoryR609 {
    static final Path DATA=Path.of("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data");
    static final Path RUN=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/feedback-r880/runtime-resume-r887");
    static final String A="a5310000000000000000000000000064",B="a5310000000000000000000000000065";
    static final Set<String> KEYS=Set.of("schema","databaseUUID","dataDirectory","actor","manager","oldNull","oldValue","managerOldNull","managerOldValue","phase");
    static void need(boolean ok,String reason){if(!ok)throw new IllegalStateException(reason);}
    static void plain(Path p)throws Exception{
        need(p.toAbsolutePath().normalize().equals(p),"ABSOLUTE_NORMAL_PATH_REQUIRED");
        for(Path q=p;q!=null;q=q.getParent())if(Files.exists(q)){
            need(!Files.isSymbolicLink(q)&&q.toRealPath().equals(q),"NO_LINKED_RUNTIME_PATH");
        }
    }
    record User(String id,String account,String manager){}
    static User user(Connection c,String id,String account)throws Exception{
        need(id.equals(A)||id.equals(B),"ONLY_TWO_SYNTHETIC_USERS");
        try(PreparedStatement p=c.prepareStatement("SELECT f_id,f_account,f_manager_id,f_enabled_mark,f_delete_mark,f_is_administrator FROM base_user WHERE f_id=? FOR UPDATE")){
            p.setQueryTimeout(10);p.setString(1,id);
            try(ResultSet r=p.executeQuery()){
                need(r.next()&&id.equals(r.getString(1))&&account.equals(r.getString(2)),"EXACT_EXISTING_OWN_ACCOUNT_REQUIRED");
                need(r.getInt(4)==1&&!r.wasNull(),"OWN_USER_ENABLED_REQUIRED");
                int deleted=r.getInt(5);need(r.wasNull()||deleted==0,"OWN_USER_NOT_DELETED_REQUIRED");
                need(r.getInt(6)==0&&!r.wasNull(),"OWN_USER_MUST_NOT_BE_ADMINISTRATOR");
                User u=new User(id,account,r.getString(3));need(!r.next(),"ONE_OWN_USER_REQUIRED");return u;
            }
        }
    }
    static boolean empty(String x){return x==null||x.isEmpty();}
    static void identity(Connection c,int port,String uuid)throws Exception{
        try(Statement s=c.createStatement()){
            s.setQueryTimeout(10);
            try(ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir,@@port,DATABASE()")){
                need(r.next()&&uuid.equals(r.getString(1))&&Path.of(r.getString(2)).toRealPath().equals(DATA)&&r.getInt(3)==port&&"jnpf".equals(r.getString(4)),"EXACT_OWN_DATABASE_IDENTITY_REQUIRED");
            }
        }
    }
    static String prior(Properties p,String prefix){return p.getProperty(prefix+"Null").equals("true")?null:p.getProperty(prefix+"Value");}
    static void setPrior(Properties p,String prefix,String value){p.setProperty(prefix+"Null",String.valueOf(value==null));p.setProperty(prefix+"Value",value==null?"":value);}
    static byte[] writeJournal(Path path,Properties p,byte[] expected)throws Exception{
        plain(path);Path tmp=path.resolveSibling(path.getFileName()+".writing");need(!Files.exists(tmp),"EXISTING_JOURNAL_WRITE_REFUSE");
        if(expected==null)need(!Files.exists(path),"EXISTING_PREIMAGE_REFUSE_DUPLICATE_APPLY");
        else need(Files.exists(path)&&Arrays.equals(Files.readAllBytes(path),expected),"FOREIGN_JOURNAL_DRIFT_REFUSE");
        ByteArrayOutputStream out=new ByteArrayOutputStream();p.store(out,"Owned synthetic manager-field preimage only");byte[] next=out.toByteArray();
        need(next.length<8192,"BOUNDED_PREIMAGE_REQUIRED");
        // Persist a new preimage before any SQL mutation. CREATE_NEW also refuses
        // a competing attempt; an interrupted initial write precedes the update.
        if(expected==null){
            try(FileChannel outFile=FileChannel.open(path,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
                ByteBuffer data=ByteBuffer.wrap(next);while(data.hasRemaining())outFile.write(data);outFile.force(true);
            }
            return next;
        }
        try(FileChannel outFile=FileChannel.open(tmp,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)){
            ByteBuffer data=ByteBuffer.wrap(next);while(data.hasRemaining())outFile.write(data);outFile.force(true);
        }
        need(Files.exists(path)&&Arrays.equals(Files.readAllBytes(path),expected),"FOREIGN_JOURNAL_DRIFT_BEFORE_PHASE_WRITE");
        try{Files.move(tmp,path,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
        catch(Exception e){Files.deleteIfExists(tmp);throw e;}
        return next;
    }
    static void update(Connection c,String next,String previous)throws Exception{
        try(PreparedStatement p=c.prepareStatement("UPDATE base_user SET f_manager_id=? WHERE f_id=? AND f_account=? AND f_manager_id <=> ?")){
            p.setQueryTimeout(10);p.setString(1,next);p.setString(2,A);p.setString(3,"own_operator_a");p.setString(4,previous);
            need(p.executeUpdate()==1,"OWN_MANAGER_COMPARE_AND_SET_REQUIRED");
        }
    }
    public static void main(String[] args)throws Exception{
        need(args.length==5&&Set.of("inspect","apply","restore").contains(args[0]),"FIXTURE_MODE_REQUIRED");
        String mode=args[0];int port=Integer.parseInt(args[1]);String uuid=args[2];
        need(port>1024&&port<65536&&!Set.of(8767,18891,18892).contains(port)&&uuid.matches("[0-9a-f-]{36}"),"OWN_LOOPBACK_IDENTITY_REQUIRED");
        need(Path.of(args[3]).equals(DATA),"ONLY_EXISTING_OWN_G_DATABASE");plain(DATA);plain(RUN);
        need(Files.isDirectory(RUN)&&Files.isRegularFile(RUN.resolve("own-normal-manager-test.marker")),"FULL_LIFECYCLE_OWNER_MARKER_REQUIRED");
        need(Files.readString(RUN.resolve("own-normal-manager-test.marker"),StandardCharsets.US_ASCII).equals("own-original-manager-full-lifecycle-r609\n"),"EXACT_TEST_MARKER_REQUIRED");
        need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")),"USER_PROTECTED_FIXTURE_REFUSE");
        Path journal=Path.of(args[4]);need(journal.equals(RUN.resolve("manager-directory.private.properties")),"EXACT_PRIVATE_PREIMAGE_PATH_REQUIRED");plain(journal);
        String password=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"),"ONLY_OWN_STDIN_CREDENTIAL");
        String url="jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=10000&allowMultiQueries=false";
        try(Connection c=DriverManager.getConnection(url,"root",password)){
            password=null;identity(c,port,uuid);c.setAutoCommit(false);
            try{
                User a=user(c,A,"own_operator_a"),b=user(c,B,"own_reviewer_b");
                need(empty(b.manager)&& (empty(a.manager)||B.equals(a.manager)),"ONLY_EMPTY_OR_EXACT_PRIOR_OWN_HIERARCHY");
                if(mode.equals("inspect")){
                    c.rollback();System.out.println("OWN_EXISTING_NORMAL_MANAGER_PAIR_INSPECTED_NO_WRITE");return;
                }
                if(mode.equals("apply")){
                    Properties p=new Properties();p.setProperty("schema","xnby.owned-manager-preimage.r609.v1");p.setProperty("databaseUUID",uuid);p.setProperty("dataDirectory",DATA.toString());p.setProperty("actor",A);p.setProperty("manager",B);
                    setPrior(p,"old",a.manager);setPrior(p,"managerOld",b.manager);p.setProperty("phase","prepared");byte[] raw=writeJournal(journal,p,null);
                    if(!B.equals(a.manager))update(c,B,a.manager);
                    need(B.equals(user(c,A,"own_operator_a").manager),"OWN_ORIGINAL_MANAGER_FIELD_READBACK_REQUIRED");
                    c.commit();p.setProperty("phase","applied");writeJournal(journal,p,raw);
                    System.out.println("OWN_NORMAL_MANAGER_FIELD_READY_PREIMAGE_RETAINED");
                }else{
                    need(Files.isRegularFile(journal)&&Files.size(journal)<8192,"OWN_PREIMAGE_REQUIRED");byte[] raw=Files.readAllBytes(journal);Properties p=new Properties();p.load(new ByteArrayInputStream(raw));
                    need(p.stringPropertyNames().equals(KEYS)&&p.getProperty("schema").equals("xnby.owned-manager-preimage.r609.v1")&&p.getProperty("databaseUUID").equals(uuid)&&p.getProperty("dataDirectory").equals(DATA.toString())&&p.getProperty("actor").equals(A)&&p.getProperty("manager").equals(B),"EXACT_OWN_PREIMAGE_IDENTITY_REQUIRED");
                    need(Set.of("prepared","applied","restored").contains(p.getProperty("phase")),"KNOWN_PREIMAGE_PHASE_REQUIRED");
                    need(Set.of("true","false").contains(p.getProperty("oldNull"))&&Set.of("true","false").contains(p.getProperty("managerOldNull")),"EXACT_NULL_MARKERS_REQUIRED");
                    String before=prior(p,"old"),managerBefore=prior(p,"managerOld");need((empty(before)||B.equals(before))&&empty(managerBefore)&&Objects.equals(b.manager,managerBefore),"PRIOR_PAIR_AND_MANAGER_MUST_MATCH");
                    need(Objects.equals(a.manager,before)||B.equals(a.manager),"FOREIGN_MANAGER_DRIFT_REFUSE_RESTORE");
                    if(!Objects.equals(a.manager,before))update(c,before,a.manager);
                    need(Objects.equals(user(c,A,"own_operator_a").manager,before),"EXACT_MANAGER_PREIMAGE_RESTORED");
                    c.commit();p.setProperty("phase","restored");writeJournal(journal,p,raw);
                    System.out.println("OWN_NORMAL_MANAGER_PREIMAGE_RESTORED");
                }
            }catch(Exception e){c.rollback();throw e;}
        }
    }
}
