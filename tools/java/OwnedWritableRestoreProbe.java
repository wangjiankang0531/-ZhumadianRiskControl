package xnby.export;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.util.*;
import java.security.MessageDigest;
import xnby.replica.OriginalProcessBoundary;

/** One durable lock-owner write and exact restoration in a cold-restored owned clone. */
@SuppressWarnings("removal")
public final class OwnedWritableRestoreProbe {
    static String value(Connection c,String id)throws SQLException {
        try(PreparedStatement s=c.prepareStatement("SELECT LOCK_OWNER_ FROM jnpf.ACT_RU_EXECUTION WHERE ID_=?")) {
            s.setString(1,id);try(ResultSet r=s.executeQuery()){if(!r.next())throw new SQLException("OWN_ROW_MISSING");String v=r.getString(1);if(r.next())throw new SQLException("OWN_ROW_NOT_UNIQUE");return v;}
        }
    }
    static void update(Connection c,String id,String owner)throws SQLException {
        try(PreparedStatement s=c.prepareStatement("UPDATE jnpf.ACT_RU_EXECUTION SET LOCK_OWNER_=? WHERE ID_=?")) {
            if(owner==null)s.setNull(1,Types.VARCHAR);else s.setString(1,owner);s.setString(2,id);
            if(s.executeUpdate()!=1)throw new SQLException("OWN_SINGLE_ROW_UPDATE_REQUIRED");
        }
    }
    public static void main(String[] args)throws Exception {
        Path root=Paths.get(args[0]).toRealPath();Properties config=new Properties();
        try(var in=Files.newInputStream(root.resolve("own-connection.properties"))){config.load(in);}
        int port=Integer.parseInt(config.getProperty("port"));
        OriginalProcessBoundary guard=new OriginalProcessBoundary(root,Set.of(port),true);System.setSecurityManager(guard);
        Properties props=new Properties();props.setProperty("user","root");props.setProperty("password",config.getProperty("password"));
        for(var e:Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","socketTimeout","60000").entrySet())props.setProperty(e.getKey(),e.getValue());
        try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/",props)) {
            VerifiedOriginalRows.identity(c,root);
            var state=VerifiedOriginalRows.one(c,"SELECT @@global.read_only AS serverReadOnly,@@global.super_read_only AS serverSuperReadOnly,@@transaction_read_only AS sessionReadOnly,@@event_scheduler AS eventScheduler");
            VerifiedOriginalRows.require("0".equals(state.get("serverReadOnly"))&&"0".equals(state.get("serverSuperReadOnly"))&&"0".equals(state.get("sessionReadOnly"))&&"OFF".equals(state.get("eventScheduler")),"OWN_WRITABLE_STATE_REQUIRED");
            String id,before;
            try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT ID_,LOCK_OWNER_ FROM jnpf.ACT_RU_EXECUTION ORDER BY ID_ LIMIT 1")) {
                VerifiedOriginalRows.require(r.next(),"OWN_EXECUTION_ROW_REQUIRED");id=r.getString(1);before=r.getString(2);
            }
            Map<String,Object> backup=new LinkedHashMap<>();backup.put("table","jnpf.ACT_RU_EXECUTION");backup.put("id",id);backup.put("lockOwnerBefore",before);
            Files.writeString(root.resolve("single-row-before.private.json"),ReadOnlyDatabaseExport.json(backup)+"\n",StandardOpenOption.CREATE_NEW);
            String marker="xnby-owned-"+UUID.randomUUID();boolean written=false,restored=false;
            try {
                c.setAutoCommit(false);update(c,id,marker);c.commit();written=true;
                VerifiedOriginalRows.require(marker.equals(value(c,id)),"OWN_COMMITTED_WRITE_NOT_OBSERVED");c.commit();
            } finally {
                // Restore even if a failed assertion interrupts the observation.
                if(written){c.rollback();update(c,id,before);c.commit();restored=Objects.equals(before,value(c,id));c.commit();}
            }
            VerifiedOriginalRows.require(written&&restored,"OWN_DURABLE_WRITE_RESTORE_FAILED");
            c.setAutoCommit(true);
            var catalog=VerifiedOriginalRows.jsonFile(root.resolve("baseline-catalog.json"),32*1024*1024);
            VerifiedOriginalRows.setString(c,"SET SESSION sql_mode=?",(String)VerifiedOriginalRows.map(catalog.get("sourceState")).get("sqlMode"));
            Path out=Files.createDirectory(root.resolve("verification-export"));var control=new ReadOnlyDatabaseExport.Control(300000,512L*1024*1024);
            var manifest=ReadOnlyDatabaseExport.export(c,out,control,ignored->{});ReadOnlyDatabaseExport.writeJson(out.resolve("manifest.json"),manifest,control);
            Map<String,Object> receipt=new LinkedHashMap<>();receipt.put("ownedUUIDDatadirPortAndPIDVerified",true);receipt.put("initialWritableState",state);
            receipt.put("originalTableSingleFieldCommitted",true);receipt.put("committedValueObserved",true);receipt.put("originalFieldValueRestoredAndCommitted",restored);
            receipt.put("recordIdSHA256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(id.getBytes(StandardCharsets.UTF_8))));
            receipt.put("targetManifestSHA256",ReadOnlyDatabaseExport.sha(out.resolve("manifest.json")));receipt.put("deniedOperations",guard.deniedCounts());
            receipt.put("sourceDatabaseConnected",false);receipt.put("fullCloneReady",false);
            Files.writeString(root.resolve("writable-probe-receipt.json"),ReadOnlyDatabaseExport.json(receipt)+"\n",StandardOpenOption.CREATE_NEW);
        }
    }
}
