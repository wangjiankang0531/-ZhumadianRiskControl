package xnby.export;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.lang.reflect.Proxy;
import java.sql.*;
import org.yaml.snakeyaml.error.YAMLException;

/** Own fixtures only. Does not open a JDBC connection or inspect any real configuration. */
public final class ReadOnlyExportSelfTest {
    public static final class YamlTripwire {
        public YamlTripwire(){System.setProperty("xnby.export.yamlTripwire","true");}
    }
    static int passed;
    static void check(boolean condition,String name) { if(!condition)throw new AssertionError(name);passed++;System.out.println("PASS "+name); }
    static void rejects(Runnable action,String name) { boolean rejected=false;try{action.run();}catch(IllegalArgumentException|YAMLException error){rejected=true;}check(rejected,name); }
    static String config(String a,String b) {
        return "spring:\n  datasource:\n    dynamic:\n      datasource:\n        master:\n          url: jdbc:mysql://original:3306/tj_endanger?useSSL=true&autoReconnect=true&allowMultiQueries=true\n          username: own-fixture\n          password: "+a+"\n        tow:\n          url: jdbc:mysql://original:3306/jnpf\n          username: own-fixture\n          password: "+b+"\n";
    }

    static Connection connectionFixture(List<String> calls,boolean readOnly,String zone,boolean fullGrants) {
        return (Connection)Proxy.newProxyInstance(ReadOnlyExportSelfTest.class.getClassLoader(),new Class[]{Connection.class},(connection,method,args)->{
            if(method.getName().equals("setReadOnly")){calls.add("readOnly="+args[0]);return null;}
            if(method.getName().equals("setAutoCommit")){calls.add("autoCommit="+args[0]);return null;}
            if(method.getName().equals("createStatement"))return Proxy.newProxyInstance(ReadOnlyExportSelfTest.class.getClassLoader(),new Class[]{Statement.class},(statement,action,values)->{
                if(action.getName().equals("close"))return null;
                String sql=(String)values[0];calls.add(sql);
                if(action.getName().equals("execute"))return false;
                if(!action.getName().equals("executeQuery"))throw new AssertionError("unexpected statement operation");
                Map<String,String> row=new LinkedHashMap<>();
                if(sql.equals("SHOW GRANTS FOR CURRENT_USER()"))row.put("grant",fullGrants?"GRANT SELECT, SHOW VIEW, TRIGGER, EVENT ON *.* TO 'own'@'host'":"GRANT SELECT ON `jnpf`.* TO 'own'@'host'");
                else if(sql.startsWith("SELECT @@transaction_read_only")){row.put("readOnly",readOnly?"1":"0");row.put("isolationLevel","REPEATABLE-READ");row.put("version","own-fixture");row.put("timeZone",zone);}
                else throw new AssertionError("unexpected query");
                List<String> names=new ArrayList<>(row.keySet()), data=new ArrayList<>(row.values());int[] cursor={0};
                return Proxy.newProxyInstance(ReadOnlyExportSelfTest.class.getClassLoader(),new Class[]{ResultSet.class},(result,read,index)->{
                    return switch(read.getName()) {
                        case "next" -> cursor[0]++==0;
                        case "close" -> null;
                        case "getString" -> data.get((Integer)index[0]-1);
                        case "getMetaData" -> Proxy.newProxyInstance(ReadOnlyExportSelfTest.class.getClassLoader(),new Class[]{ResultSetMetaData.class},(metadata,get,column)->switch(get.getName()){case "getColumnCount"->names.size();case "getColumnLabel"->names.get((Integer)column[0]-1);default->throw new AssertionError("unexpected metadata operation");});
                        default -> throw new AssertionError("unexpected result operation");
                    };
                });
            });
            throw new AssertionError("unexpected connection operation");
        });
    }

    public static void main(String[] args) throws Exception {
        check(ReadOnlyDatabaseExport.identifier("a`b; DROP TABLE x").equals("`a``b; DROP TABLE x`"),"identifiers quoted without executing their text");
        rejects(()->ReadOnlyDatabaseExport.identifier("bad\0name"),"NUL identifier rejected");
        check(ReadOnlyDatabaseExport.json(Arrays.asList(null,"汉字\n\"\\",true,12)).equals("[null,\"汉字\\n\\\"\\\\\",true,12]"),"JSON NULL Unicode and control characters preserved");
        var parsed=ReadOnlyDatabaseExport.Config.parse(config("'private-fixture'","'private-fixture'"),"192.168.12.34");
        check(parsed.url().equals("jdbc:mysql://192.168.12.34:3306/tj_endanger"),"only approved source host replaces container host");
        check("true".equals(parsed.properties().getProperty("useSSL")),"original TLS option retained");
        check("false".equals(parsed.properties().getProperty("autoReconnect")) && "false".equals(parsed.properties().getProperty("allowMultiQueries")),"reconnect and multiple SQL disabled");
        check(!parsed.toString().contains("private-fixture") && !parsed.toString().contains("own-fixture"),"configuration string hides credentials");
        check(ReadOnlyDatabaseExport.fullMetadataPrivileges(List.of(Map.of("grant","GRANT SELECT, SHOW VIEW, TRIGGER, EVENT ON *.* TO 'own'@'host'"))),"explicit global read metadata grants recognized");
        check(!ReadOnlyDatabaseExport.fullMetadataPrivileges(List.of(Map.of("grant","GRANT SELECT ON `jnpf`.* TO 'own'@'host'"))),"partial visibility cannot claim complete database export");
        List<String> calls=new ArrayList<>();
        ReadOnlyDatabaseExport.beginSnapshot(connectionFixture(calls,true,"+00:00",true));
        check(calls.get(0).equals("readOnly=true") && calls.get(1).equals("autoCommit=false") && calls.get(2).equals("SET SESSION time_zone='+00:00'") && calls.get(4).equals(ReadOnlyDatabaseExport.SNAPSHOT_SQL),"read-only manual transaction and UTC established before querying source");
        boolean wrongMode=false;try{ReadOnlyDatabaseExport.beginSnapshot(connectionFixture(new ArrayList<>(),false,"+00:00",true));}catch(SQLException error){wrongMode=true;}
        check(wrongMode,"unverified read-only transaction rejected");
        boolean wrongZone=false;try{ReadOnlyDatabaseExport.beginSnapshot(connectionFixture(new ArrayList<>(),true,"SYSTEM",true));}catch(SQLException error){wrongZone=true;}
        check(wrongZone,"unverified source timezone rejected");
        boolean partial=false;try{ReadOnlyDatabaseExport.beginSnapshot(connectionFixture(new ArrayList<>(),true,"+00:00",false));}catch(SQLException error){partial=true;}
        check(partial,"snapshot with incomplete metadata privileges rejected");
        var ddl=Map.<String,Object>of("Create Table","CREATE TABLE `own` (\n  `id` bigint\n) ENGINE=InnoDB AUTO_INCREMENT=123 DEFAULT CHARSET=utf8mb4");
        var advanced=Map.<String,Object>of("Create Table","CREATE TABLE `own` (\n  `id` bigint\n) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4");
        var changed=Map.<String,Object>of("Create Table","CREATE TABLE `own` (\n  `id` varchar(20)\n) ENGINE=InnoDB AUTO_INCREMENT=125 DEFAULT CHARSET=utf8mb4");
        check(ReadOnlyDatabaseExport.definitionForComparison(ddl).equals(ReadOnlyDatabaseExport.definitionForComparison(advanced)),"concurrent DML sequence movement does not invalidate snapshot rows");
        check(!ReadOnlyDatabaseExport.definitionForComparison(ddl).equals(ReadOnlyDatabaseExport.definitionForComparison(changed)),"source table definition changes are rejected");
        rejects(()->ReadOnlyDatabaseExport.Config.parse(config("'one'","'different'"),"192.168.12.34"),"different source credentials cannot claim one snapshot");
        rejects(()->ReadOnlyDatabaseExport.Config.parse(config("'same'","'same'").replace("/jnpf","/unrelated"),"192.168.12.34"),"unrelated database rejected");
        rejects(()->ReadOnlyDatabaseExport.Config.parse(config("'same'","'same'"),"8.8.8.8"),"public credential destination rejected");
        new YamlTripwire();check(Boolean.getBoolean("xnby.export.yamlTripwire"),"YAML constructor fixture positive control");System.clearProperty("xnby.export.yamlTripwire");
        rejects(()->ReadOnlyDatabaseExport.Config.parse("!!xnby.export.ReadOnlyExportSelfTest$YamlTripwire {}","192.168.12.34"),"YAML object construction rejected");
        check(!Boolean.getBoolean("xnby.export.yamlTripwire"),"untrusted YAML never constructs the fixture object");
        rejects(()->ReadOnlyDatabaseExport.Config.parse(config("'same'","'same'").replace("password: 'same'","password: 'same'\n          password: 'same'"),"192.168.12.34"),"duplicate keys in otherwise valid datasource rejected");
        var columns=List.<Map<String,Object>>of(Map.of("COLUMN_NAME","numeric`column"),Map.of("COLUMN_NAME","text"));
        String sql=ReadOnlyDatabaseExport.tableSql("jnpf","own`fixture",columns);
        check(sql.contains("HEX(CAST(`numeric``column` AS BINARY))") && sql.contains("OCTET_LENGTH") && sql.endsWith("FROM `jnpf`.`own``fixture`"),"numeric representation and row size use server binary casts");
        rejects(()->ReadOnlyDatabaseExport.tableSql("mysql","user",columns),"system database rows cannot be selected");
        var budget=new ReadOnlyDatabaseExport.Control(60000,3);
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();
        boolean limited=false;
        try(var stream=new ReadOnlyDatabaseExport.BudgetStream(bytes,budget)) {stream.write(new byte[]{1,2,3});try{stream.write(4);}catch(IOException error){limited=true;}}
        check(limited && bytes.size()==3,"compressed output stops before exceeding budget");
        var cancelled=new ReadOnlyDatabaseExport.Control(60000,100);cancelled.cancel();
        boolean stopped=false;try{cancelled.check();}catch(IOException error){stopped=true;}
        check(stopped,"cancellation prevents subsequent reads or output");
        Path root=Files.createTempDirectory("own-export-fixture-");
        Path result=root.resolve("evidence.json");Files.writeString(result,"preserved");
        boolean retained=false;try{ReadOnlyDatabaseExport.writeJson(result,Map.of("changed",true),new ReadOnlyDatabaseExport.Control(60000,100));}catch(FileAlreadyExistsException error){retained=true;}
        check(retained && Files.readString(result).equals("preserved"),"existing output cannot be overwritten");
        ReadOnlyDatabaseExport.claimAttempt(root);
        boolean oneAttempt=false;try{ReadOnlyDatabaseExport.claimAttempt(root);}catch(FileAlreadyExistsException error){oneAttempt=true;}
        check(oneAttempt,"a second GUI instance cannot start another source connection attempt");
        Files.delete(root.resolve("attempt_started.json"));
        Files.delete(result);Files.delete(root);
        System.out.println("SELF_TESTS_PASSED="+passed+" realDatabaseConnections=0 sourceWrites=0");
    }
}
