package xnby.export;

import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.*;
import java.util.*;

/** Drives the actual producer using in-memory JDBC results, never DriverManager or a GUI. */
public final class ReadOnlyExportArtifactFixture {
    static final List<String> calls = new ArrayList<>();
    static boolean closed;
    static int rollbacks;

    static Map<String,Object> row(Object... pairs) {
        Map<String,Object> result = new LinkedHashMap<>();
        for (int i=0;i<pairs.length;i+=2) result.put((String)pairs[i],pairs[i+1]);
        return result;
    }

    static ResultSet result(List<Map<String,Object>> rows, List<String> emptyNames) {
        List<String> names = rows.isEmpty() ? emptyNames : new ArrayList<>(rows.get(0).keySet());
        int[] cursor = {-1};
        return (ResultSet)Proxy.newProxyInstance(ReadOnlyExportArtifactFixture.class.getClassLoader(),
            new Class[]{ResultSet.class},(proxy,method,args)->switch(method.getName()) {
                case "next" -> ++cursor[0] < rows.size();
                case "close" -> null;
                case "getString" -> {
                    Object value = rows.get(cursor[0]).get(names.get((Integer)args[0]-1));
                    yield value == null ? null : value.toString();
                }
                case "getBoolean" -> Boolean.TRUE.equals(rows.get(cursor[0]).get(names.get((Integer)args[0]-1)));
                case "getMetaData" -> Proxy.newProxyInstance(ReadOnlyExportArtifactFixture.class.getClassLoader(),
                    new Class[]{ResultSetMetaData.class},(metadata,get,column)->switch(get.getName()) {
                        case "getColumnCount" -> names.size();
                        case "getColumnLabel" -> names.get((Integer)column[0]-1);
                        default -> throw new AssertionError("Unexpected metadata access");
                    });
                default -> throw new AssertionError("Unexpected result access");
            });
    }

    static String hex(String value) { return HexFormat.of().withUpperCase().formatHex(value.getBytes(StandardCharsets.UTF_8)); }
    static Map<String,Object> column(String name,int ordinal,String type,String charset,String expression) {
        String columnType=switch(type) {
            case "decimal" -> "decimal(40,12)";
            case "varchar" -> "varchar(1000)";
            case "varbinary" -> "varbinary(64)";
            case "timestamp" -> "timestamp(6)";
            case "time" -> "time(6)";
            case "bit" -> "bit(16)";
            default -> type;
        };
        return row("COLUMN_NAME",name,"ORDINAL_POSITION",Integer.toString(ordinal),"DATA_TYPE",type,
            "COLUMN_TYPE",columnType,"CHARACTER_SET_NAME",charset,"COLLATION_NAME",charset==null?null:charset+"_bin",
            "EXTRA",expression.isEmpty()?"":"VIRTUAL GENERATED","GENERATION_EXPRESSION",expression);
    }

    static final String SPECIAL_TABLE = "原表\"\\\b";
    static final List<Map<String,Object>> TABLES = List.of(
        row("TABLE_SCHEMA","jnpf","TABLE_NAME",SPECIAL_TABLE,"TABLE_TYPE","BASE TABLE","ENGINE","InnoDB"),
        row("TABLE_SCHEMA","jnpf","TABLE_NAME","zero_rows","TABLE_TYPE","BASE TABLE","ENGINE","InnoDB"),
        row("TABLE_SCHEMA","tj_endanger","TABLE_NAME","types_fixture","TABLE_TYPE","BASE TABLE","ENGINE","InnoDB"),
        row("TABLE_SCHEMA","tj_endanger","TABLE_NAME","view_fixture","TABLE_TYPE","VIEW","ENGINE",null));

    static List<Map<String,Object>> columns(String schema,String name) {
        if (name.equals("types_fixture")) {
            var unsignedId=column("id",1,"bigint",null,"");unsignedId.put("COLUMN_TYPE","bigint unsigned");
            return List.of(
            unsignedId,column("decimal_value",2,"decimal",null,""),
            column("unicode_value",3,"varchar","utf8mb4",""),column("json_value",4,"json",null,""),
            column("binary_value",5,"varbinary",null,""),column("utc_time",6,"timestamp",null,""),
            column("negative_time",7,"time",null,""),column("legacy_date",8,"date",null,""),
            column("latin1_value",9,"varchar","latin1",""),column("bit_value",10,"bit",null,""),
            column("nullable_value",11,"varchar","utf8mb4",""),column("empty_value",12,"varchar","utf8mb4",""),
            column("computed",13,"decimal",null,"`id`+1"));
        }
        return List.of(column("id",1,"bigint",null,""),column("value",2,"varchar","utf8mb4",""),
                       column("computed",3,"int",null,"`id`+1"));
    }

    static List<Map<String,Object>> data(String name) {
        if (name.equals("zero_rows")) return List.of();
        if (name.equals(SPECIAL_TABLE)) return List.of(row("ok",true,"id",hex("9223372036854775807"),"value",null),
                                                    row("ok",true,"id",hex("0"),"value",""));
        if (name.equals("types_fixture")) return List.of(row("ok",true,"id",hex("18446744073709551615"),
            "decimal_value",hex("9007199254740993.123456789012"),"unicode_value",hex("中文😀\n\"\\"),
            "json_value",hex("{\"键\":\"值\"}"),"binary_value","00017FFF5C0A","utc_time",hex("2025-01-02 03:04:05.123456"),
            "negative_time",hex("-123:45:56.123456"),"legacy_date",hex("0000-00-00"),"latin1_value","E9",
            "bit_value","8001","nullable_value",null,"empty_value",""));
        throw new AssertionError("Unexpected fixture table");
    }

    static ResultSet query(String sql) {
        calls.add(sql);
        if (sql.startsWith("SELECT @@transaction_read_only")) return result(List.of(row("readOnly","1",
            "isolationLevel","REPEATABLE-READ","version","8.0.fixture-not-a-server","sourceTime","2025-01-02 03:04:05.123456",
            "timeZone","+00:00","sqlMode","STRICT_TRANS_TABLES","lowerCaseTableNames","0",
            "connectionCharset","utf8mb4","connectionCollation","utf8mb4_bin")),List.of());
        if (sql.equals("SHOW GRANTS FOR CURRENT_USER()"))
            return result(List.of(row("grant","GRANT SELECT, SHOW VIEW, TRIGGER, EVENT ON *.* TO 'fixture'@'host'")),List.of());
        if (sql.equals(ReadOnlyDatabaseExport.TABLES_SQL)) return result(TABLES,List.of());
        for (String schema:ReadOnlyDatabaseExport.SCHEMAS) {
            if (sql.equals("SHOW CREATE DATABASE "+ReadOnlyDatabaseExport.identifier(schema)))
                return result(List.of(row("Database",schema,"Create Database","CREATE DATABASE `"+schema+"`")),List.of());
        }
        for (var table:TABLES) {
            String schema=(String)table.get("TABLE_SCHEMA"),name=(String)table.get("TABLE_NAME");
            if (sql.equals("SHOW CREATE TABLE "+ReadOnlyDatabaseExport.identifier(schema)+"."+ReadOnlyDatabaseExport.identifier(name)))
                return result(List.of(row(table.get("TABLE_TYPE").equals("VIEW")?"View":"Table",name,table.get("TABLE_TYPE").equals("VIEW")?"Create View":"Create Table",
                    "Own fixture SQL text; never executed")),List.of());
            if (table.get("TABLE_TYPE").equals("BASE TABLE")) {
                var writable=columns(schema,name).stream().filter(c->c.get("GENERATION_EXPRESSION").equals("")).toList();
                if (sql.equals(ReadOnlyDatabaseExport.tableSql(schema,name,writable))) return result(data(name),List.of("ok"));
            }
        }
        if (sql.startsWith("SELECT TRIGGER_SCHEMA") || sql.startsWith("SELECT EVENT_SCHEMA") || sql.startsWith("SELECT ROUTINE_SCHEMA"))
            return result(List.of(row("dbName","tj_endanger","objectName","aux_fixture")),List.of());
        for (var kind:Map.of("TRIGGER","SQL Original Statement","EVENT","Create Event",
                             "PROCEDURE","Create Procedure","FUNCTION","Create Function").entrySet())
            if (sql.startsWith("SHOW CREATE "+kind.getKey()+" "))
                return result(List.of(row(kind.getValue(),"UNTRUSTED SQL; CALL side_effect();")),List.of());
        throw new AssertionError("Unexpected fixture query");
    }

    static Connection connection() {
        return (Connection)Proxy.newProxyInstance(ReadOnlyExportArtifactFixture.class.getClassLoader(),
            new Class[]{Connection.class},(connection,method,args)->switch(method.getName()) {
                case "setReadOnly", "setAutoCommit" -> { calls.add(method.getName()+"="+args[0]); yield null; }
                case "rollback" -> { rollbacks++; yield null; }
                case "close" -> { closed=true; yield null; }
                case "createStatement" -> Proxy.newProxyInstance(ReadOnlyExportArtifactFixture.class.getClassLoader(),
                    new Class[]{Statement.class},(statement,action,values)->switch(action.getName()) {
                        case "close", "setFetchSize" -> null;
                        case "executeQuery" -> query((String)values[0]);
                        case "execute" -> {
                            String sql=(String)values[0];
                            if (!List.of("SET SESSION time_zone='+00:00'","SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ",
                                         ReadOnlyDatabaseExport.SNAPSHOT_SQL).contains(sql)) throw new AssertionError("Unexpected session SQL");
                            calls.add(sql);yield false;
                        }
                        default -> throw new AssertionError("Unexpected statement access");
                    });
                case "prepareStatement" -> {
                    if (!((String)args[0]).startsWith("SELECT COLUMN_NAME,ORDINAL_POSITION")) throw new AssertionError("Unexpected prepared SQL");
                    Map<Integer,String> parameters=new HashMap<>();
                    yield Proxy.newProxyInstance(ReadOnlyExportArtifactFixture.class.getClassLoader(),
                        new Class[]{PreparedStatement.class},(statement,action,values)->switch(action.getName()) {
                            case "setString" -> { parameters.put((Integer)values[0],(String)values[1]);yield null; }
                            case "close" -> null;
                            case "executeQuery" -> result(columns(parameters.get(1),parameters.get(2)),List.of());
                            default -> throw new AssertionError("Unexpected prepared statement access");
                        });
                }
                default -> throw new AssertionError("Unexpected connection access");
            });
    }

    public static void main(String[] args) throws Exception {
        if (args.length!=1) throw new IllegalArgumentException("Fresh fixture directory required");
        Path output=Files.createDirectory(Path.of(args[0]));
        var control=new ReadOnlyDatabaseExport.Control(60000,1024*1024);
        Map<String,Object> receipt;
        try (Connection connection=connection()) {
            receipt=ReadOnlyDatabaseExport.export(connection,output,control,ignored->{});
        }
        if (!closed || rollbacks!=1) throw new AssertionError("Fixture connection closure not verified");
        ReadOnlyDatabaseExport.writeJson(output.resolve("manifest.json"),receipt,control);
        System.out.println(ReadOnlyDatabaseExport.json(Map.of("actualProducerInvoked",true,"JDBCResultsAreOwnFixtures",true,
            "realDatabaseConnections",0,"GUIStarted",false,"rollbackCount",rollbacks,"connectionClosed",closed,
            "manifestSHA256",ReadOnlyDatabaseExport.sha(output.resolve("manifest.json")))));
    }
}
