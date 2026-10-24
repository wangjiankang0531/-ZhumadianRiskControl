package xnby.export;

import java.awt.BorderLayout;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.*;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;
import java.util.zip.GZIPOutputStream;
import javax.swing.*;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/** One-shot, bounded, read-only logical export. No Spring, OS commands, or source DDL/DML. */
public final class ReadOnlyDatabaseExport {
    static final String FORMAT="tj-original-jdbc-hex-v2";
    static final Map<String,String> ROW_PROJECTION=Map.of(
        "float","hex(cast(cast(column as double) as binary))",
        "default","hex(cast(column as binary))","sqlNull","json-null","generatedColumns","excluded");
    static final List<String> SCHEMAS = List.of("jnpf", "tj_endanger");
    static final long MAX_BYTES = 512L * 1024 * 1024;
    static final long MAX_MILLIS = 20L * 60 * 1000;
    static final long MAX_ROW_BYTES = 4L * 1024 * 1024;
    static final String SNAPSHOT_SQL = "START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY";
    static final String TABLES_SQL = "SELECT TABLE_SCHEMA,TABLE_NAME,TABLE_TYPE,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA IN ('jnpf','tj_endanger') ORDER BY TABLE_SCHEMA,TABLE_NAME";

    static String identifier(String value) {
        if (value == null || value.isEmpty() || value.indexOf('\0') >= 0) throw new IllegalArgumentException("IDENTIFIER_INVALID");
        return "`" + value.replace("`", "``") + "`";
    }

    static String json(Object value) {
        if (value == null) return "null";
        if (value instanceof Boolean || value instanceof Number) return value.toString();
        if (value instanceof Map<?, ?> map) {
            List<String> pairs = new ArrayList<>();
            for (var entry : map.entrySet()) pairs.add(json(String.valueOf(entry.getKey())) + ":" + json(entry.getValue()));
            return "{" + String.join(",", pairs) + "}";
        }
        if (value instanceof Iterable<?> list) {
            List<String> items = new ArrayList<>();
            for (Object item : list) items.add(json(item));
            return "[" + String.join(",", items) + "]";
        }
        if (!(value instanceof String)) throw new IllegalArgumentException("JSON_VALUE_UNSUPPORTED");
        StringBuilder out = new StringBuilder("\"");
        for (char c : ((String)value).toCharArray()) {
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> { if (c < 32) out.append(String.format("\\u%04x", (int)c)); else out.append(c); }
            }
        }
        return out.append('"').toString();
    }

    @SuppressWarnings("unchecked")
    static Map<String,Object> map(Object value) {
        if (!(value instanceof Map<?,?>)) throw new IllegalArgumentException("CONFIG_MAP_REQUIRED");
        return (Map<String,Object>)value;
    }

    static Map<String,Object> child(Map<String,Object> value, String... path) {
        for (String key : path) value = map(value.get(key));
        return value;
    }

    record Config(String host, int port, String user, String password, Properties properties) {
        static Config parse(String text, String host) {
            if (text.length() > 65536 || !host.matches("(?:[0-9]{1,3}\\.){3}[0-9]{1,3}")) throw new IllegalArgumentException("CONFIG_SCOPE_INVALID");
            String[] parts = host.split("\\.");
            int[] ip = Arrays.stream(parts).mapToInt(Integer::parseInt).toArray();
            if (Arrays.stream(ip).anyMatch(i -> i > 255) || !(ip[0] == 10 || ip[0] == 192 && ip[1] == 168 || ip[0] == 172 && ip[1] >= 16 && ip[1] <= 31)) throw new IllegalArgumentException("PRIVATE_SOURCE_HOST_REQUIRED");
            LoaderOptions options = new LoaderOptions();
            options.setMaxAliasesForCollections(0);
            options.setCodePointLimit(65536);
            options.setAllowDuplicateKeys(false);
            Map<String,Object> all = map(new Yaml(new SafeConstructor(options)).load(text));
            Map<String,Object> sources = child(all,"spring","datasource","dynamic","datasource");
            Map<String,Object> master = child(sources,"master"), other = child(sources,"tow");
            Object user = master.get("username"), password = master.get("password");
            if (!(user instanceof String) || !(password instanceof String || password instanceof Number || password instanceof Boolean) || !Objects.equals(user,other.get("username")) || !Objects.equals(password,other.get("password"))) throw new IllegalArgumentException("SOURCE_IDENTITIES_DIFFER_OR_INVALID");
            String a = Objects.toString(master.get("url"),""), b = Objects.toString(other.get("url"),"");
            if (!a.startsWith("jdbc:mysql://") || !b.startsWith("jdbc:mysql://")) throw new IllegalArgumentException("MYSQL_SOURCE_REQUIRED");
            URI first = URI.create(a.substring(5)), second = URI.create(b.substring(5));
            int port = first.getPort() == -1 ? 3306 : first.getPort();
            if (!"/tj_endanger".equals(first.getPath()) || !"/jnpf".equals(second.getPath()) || !Objects.equals(first.getHost(),second.getHost()) || first.getUserInfo() != null || second.getUserInfo() != null || port != (second.getPort() == -1 ? 3306 : second.getPort()) || port != 3306) throw new IllegalArgumentException("SOURCE_DATABASE_SCOPE_INVALID");
            Properties props = new Properties();
            Set<String> allowed = Set.of("useSSL","requireSSL","verifyServerCertificate","allowPublicKeyRetrieval","serverTimezone","characterEncoding","useUnicode");
            for (String part : Objects.toString(first.getRawQuery(),"").split("&")) {
                String[] pair = part.split("=",2);
                String key = URLDecoder.decode(pair[0],StandardCharsets.UTF_8);
                if (pair.length == 2 && allowed.contains(key)) props.setProperty(key,URLDecoder.decode(pair[1],StandardCharsets.UTF_8));
            }
            props.setProperty("user",(String)user);
            props.setProperty("password",String.valueOf(password));
            props.setProperty("autoReconnect","false");
            props.setProperty("connectTimeout","5000");
            props.setProperty("socketTimeout","15000");
            props.setProperty("allowMultiQueries","false");
            props.setProperty("netTimeoutForStreamingResults","0");
            props.setProperty("useInformationSchema","true");
            return new Config(host,port,(String)user,String.valueOf(password),props);
        }
        String url() { return "jdbc:mysql://" + host + ":" + port + "/tj_endanger"; }
        @Override public String toString() { return "Original source configuration (credentials hidden)"; }
    }

    static final class Control {
        final AtomicBoolean cancelled = new AtomicBoolean();
        volatile Connection connection;
        final long deadline;
        final long byteLimit;
        long bytes;
        Control(long millis,long byteLimit) { deadline = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(millis); this.byteLimit = byteLimit; }
        void check() throws IOException {
            if (cancelled.get()) throw new IOException("CANCELLED");
            if (System.nanoTime() > deadline) throw new IOException("TIME_LIMIT");
        }
        void add(long amount) throws IOException {
            check();
            if (amount < 0 || amount > byteLimit - bytes) throw new IOException("OUTPUT_SIZE_LIMIT");
            bytes += amount;
        }
        void cancel() {
            cancelled.set(true);
            Connection current = connection;
            if (current != null) {
                Thread closer = new Thread(() -> { try { current.close(); } catch(SQLException ignored) {} },"own-export-connection-close");
                closer.setDaemon(true); closer.start();
            }
        }
    }

    static final class BudgetStream extends FilterOutputStream {
        final Control control;
        BudgetStream(OutputStream stream,Control control) { super(stream); this.control=control; }
        @Override public void write(int value) throws IOException { control.add(1);out.write(value); }
        @Override public void write(byte[] bytes,int offset,int length) throws IOException { control.add(length);out.write(bytes,offset,length); }
    }

    static List<Map<String,Object>> query(Connection connection,String sql) throws SQLException {
        List<Map<String,Object>> rows = new ArrayList<>();
        try (Statement statement=connection.createStatement(); ResultSet result=statement.executeQuery(sql)) {
            ResultSetMetaData metadata=result.getMetaData();
            while(result.next()) {
                Map<String,Object> row=new LinkedHashMap<>();
                for(int n=1;n<=metadata.getColumnCount();n++) row.put(metadata.getColumnLabel(n),result.getString(n));
                rows.add(row);
            }
        }
        return rows;
    }

    static Map<String,Object> one(Connection connection,String sql) throws SQLException {
        List<Map<String,Object>> rows=query(connection,sql);
        if(rows.size()!=1) throw new SQLException("EXPECTED_ONE_METADATA_ROW","HY000");
        return rows.get(0);
    }

    static boolean fullMetadataPrivileges(List<Map<String,Object>> grants) {
        Set<String> privileges=new HashSet<>();
        for(var row:grants)for(Object value:row.values()) {
            String line=Objects.toString(value,"").toUpperCase(Locale.ROOT);
            int end=line.indexOf(" ON *.* TO ");
            if(!line.startsWith("GRANT ") || end<0)continue;
            privileges.addAll(Arrays.asList(line.substring(6,end).split(",\\s*")));
        }
        return privileges.contains("ALL PRIVILEGES") || privileges.containsAll(Set.of("SELECT","SHOW VIEW","TRIGGER","EVENT"));
    }

    static String sha(Path path) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        try(InputStream stream=Files.newInputStream(path)) { byte[] block=new byte[65536];int n;while((n=stream.read(block))!=-1)digest.update(block,0,n); }
        return HexFormat.of().formatHex(digest.digest());
    }

    static void writeJson(Path path,Object value,Control control) throws IOException {
        try(OutputStream out=new BudgetStream(Files.newOutputStream(path,StandardOpenOption.CREATE_NEW),control)) { out.write((json(value)+"\n").getBytes(StandardCharsets.UTF_8)); }
    }

    static void claimAttempt(Path root) throws IOException {
        Files.writeString(root.resolve("attempt_started.json"),json(Map.of("startedAt",Instant.now().toString(),"automaticRetry",false))+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }

    static String binaryExpression(Map<String,Object> column) {
        String name=identifier((String)column.get("COLUMN_NAME"));
        Object type=column.get("DATA_TYPE");
        if(!(type instanceof String text) || !text.matches("[a-zA-Z]+"))throw new IllegalArgumentException("COLUMN_DATA_TYPE_REQUIRED");
        return text.equalsIgnoreCase("float")?"CAST(CAST("+name+" AS DOUBLE) AS BINARY)":"CAST("+name+" AS BINARY)";
    }
    static boolean floatProjectionSupported(String version) {
        var match=java.util.regex.Pattern.compile("^(\\d+)\\.(\\d+)\\.(\\d+)(?:[^0-9].*)?$").matcher(version);
        if(!match.matches() || version.toLowerCase(Locale.ROOT).contains("mariadb"))return false;
        try {
            int major=Integer.parseInt(match.group(1)),minor=Integer.parseInt(match.group(2)),patch=Integer.parseInt(match.group(3));
            return major>8 || major==8 && (minor>0 || patch>=17);
        }catch(NumberFormatException ignored){return false;}
    }
    static String tableSql(String database,String table,List<Map<String,Object>> columns) {
        if(!SCHEMAS.contains(database) || columns.isEmpty()) throw new IllegalArgumentException("TABLE_SCOPE_INVALID");
        List<String> fields=new ArrayList<>(), lengths=new ArrayList<>();
        for(var column:columns) lengths.add("COALESCE(OCTET_LENGTH("+binaryExpression(column)+"),0)");
        String sizeOk="("+String.join("+",lengths)+"<="+MAX_ROW_BYTES+")";
        fields.add(sizeOk);
        for(var column:columns) fields.add("CASE WHEN "+sizeOk+" THEN HEX("+binaryExpression(column)+") ELSE NULL END");
        return "SELECT "+String.join(",",fields)+" FROM "+identifier(database)+"."+identifier(table);
    }

    static Map<String,Object> beginSnapshot(Connection connection) throws SQLException {
        connection.setReadOnly(true);
        connection.setAutoCommit(false);
        try(Statement statement=connection.createStatement()) {
            statement.execute("SET SESSION time_zone='+00:00'");
            statement.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ");
            statement.execute(SNAPSHOT_SQL);
        }
        Map<String,Object> state=one(connection,"SELECT @@transaction_read_only AS readOnly, @@transaction_isolation AS isolationLevel, @@version AS version, NOW(6) AS sourceTime, @@session.time_zone AS timeZone, @@session.sql_mode AS sqlMode, @@lower_case_table_names AS lowerCaseTableNames, @@character_set_connection AS connectionCharset, @@collation_connection AS connectionCollation");
        if(!"1".equals(state.get("readOnly")) || !"REPEATABLE-READ".equals(state.get("isolationLevel"))) throw new SQLException("READ_ONLY_SNAPSHOT_NOT_VERIFIED","HY000");
        if(!"+00:00".equals(state.get("timeZone")))throw new SQLException("UTC_SESSION_NOT_VERIFIED","HY000");
        if(!fullMetadataPrivileges(query(connection,"SHOW GRANTS FOR CURRENT_USER()")))throw new SQLException("FULL_SOURCE_METADATA_PRIVILEGES_NOT_PROVEN","HY000");
        return state;
    }

    static Map<String,Object> definitionForComparison(Map<String,Object> row) {
        Map<String,Object> normalized=new LinkedHashMap<>(row);
        for(var entry:row.entrySet())if(entry.getKey().equals("Create Table") && entry.getValue() instanceof String value)
            normalized.put(entry.getKey(),value.replaceFirst("(?m)^(\\) ENGINE=\\S+ )AUTO_INCREMENT=\\d+ ","$1"));
        return normalized;
    }

    static Map<String,Object> export(Connection connection,Path output,Control control,Consumer<String> log) throws Exception {
        control.connection=connection;
        control.check();
        Map<String,Object> state=beginSnapshot(connection);
        List<Map<String,Object>> tables=query(connection,TABLES_SQL);
        if(tables.isEmpty() || !tables.stream().map(row->row.get("TABLE_SCHEMA")).collect(java.util.stream.Collectors.toSet()).containsAll(SCHEMAS)) throw new SQLException("SOURCE_SCHEMAS_MISSING","HY000");
        for(var table:tables) if("BASE TABLE".equals(table.get("TABLE_TYPE")) && !"InnoDB".equals(table.get("ENGINE"))) throw new SQLException("NON_TRANSACTIONAL_SOURCE_TABLE","HY000");
        Map<String,Object> catalog=new LinkedHashMap<>();
        catalog.put("format",FORMAT);catalog.put("rowProjection",ROW_PROJECTION);
        catalog.put("sourceState",state);
        List<Map<String,Object>> databases=new ArrayList<>();
        for(String schema:SCHEMAS) databases.add(one(connection,"SHOW CREATE DATABASE "+identifier(schema)));
        catalog.put("databases",databases);
        List<Map<String,Object>> objects=new ArrayList<>();
        Map<String,List<Map<String,Object>>> writableColumns=new HashMap<>();
        for(var table:tables) {
            control.check();
            String database=(String)table.get("TABLE_SCHEMA"), name=(String)table.get("TABLE_NAME");
            if(!SCHEMAS.contains(database)) throw new SQLException("SOURCE_SCHEMA_OUT_OF_SCOPE","HY000");
            Map<String,Object> object=new LinkedHashMap<>(table);
            object.put("create",one(connection,"SHOW CREATE TABLE "+identifier(database)+"."+identifier(name)));
            List<Map<String,Object>> columns;
            try(PreparedStatement statement=connection.prepareStatement("SELECT COLUMN_NAME,ORDINAL_POSITION,DATA_TYPE,COLUMN_TYPE,CHARACTER_SET_NAME,COLLATION_NAME,EXTRA,GENERATION_EXPRESSION FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION")) {
                statement.setString(1,database);statement.setString(2,name);
                columns=new ArrayList<>();
                try(ResultSet result=statement.executeQuery()) {
                    ResultSetMetaData metadata=result.getMetaData();
                    while(result.next()) {
                        Map<String,Object> column=new LinkedHashMap<>();
                        for(int n=1;n<=metadata.getColumnCount();n++)column.put(metadata.getColumnLabel(n),result.getString(n));
                        columns.add(column);
                    }
                }
            }
            object.put("columns",columns);
            writableColumns.put(database+"."+name,columns.stream().filter(column->Objects.toString(column.get("GENERATION_EXPRESSION"),"").isEmpty()).toList());
            objects.add(object);
        }
        catalog.put("tablesAndViews",objects);
        boolean hasFloat=writableColumns.values().stream().flatMap(List::stream).anyMatch(c->"float".equalsIgnoreCase(Objects.toString(c.get("DATA_TYPE"),"")));
        if(hasFloat && !floatProjectionSupported(Objects.toString(state.get("version"),"")))throw new SQLException("FLOAT_PROJECTION_SERVER_VERSION_UNSUPPORTED","HY000");
        for(String kind:List.of("TRIGGER","EVENT","PROCEDURE","FUNCTION")) {
            control.check();
            String sql=switch(kind) {
                case "TRIGGER" -> "SELECT TRIGGER_SCHEMA AS dbName,TRIGGER_NAME AS objectName FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA IN ('jnpf','tj_endanger') ORDER BY TRIGGER_SCHEMA,TRIGGER_NAME";
                case "EVENT" -> "SELECT EVENT_SCHEMA AS dbName,EVENT_NAME AS objectName FROM information_schema.EVENTS WHERE EVENT_SCHEMA IN ('jnpf','tj_endanger') ORDER BY EVENT_SCHEMA,EVENT_NAME";
                default -> "SELECT ROUTINE_SCHEMA AS dbName,ROUTINE_NAME AS objectName FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA IN ('jnpf','tj_endanger') AND ROUTINE_TYPE='"+kind+"' ORDER BY ROUTINE_SCHEMA,ROUTINE_NAME";
            };
            List<Map<String,Object>> definitions=new ArrayList<>();
            for(var object:query(connection,sql)) {
                String database=(String)object.get("dbName"), name=(String)object.get("objectName");
                if(!SCHEMAS.contains(database)) throw new SQLException("SOURCE_SCHEMA_OUT_OF_SCOPE","HY000");
                Map<String,Object> row=new LinkedHashMap<>(object);
                row.put("definition",one(connection,"SHOW CREATE "+kind+" "+identifier(database)+"."+identifier(name)));
                definitions.add(row);
            }
            catalog.put(kind.toLowerCase(Locale.ROOT)+"s",definitions);
        }
        writeJson(output.resolve("catalog.json"),catalog,control);
        List<Map<String,Object>> counts=new ArrayList<>();
        for(String database:SCHEMAS) {
            Path path=output.resolve(database+".rows.jsonl.gz");
            try(OutputStream target=new BudgetStream(Files.newOutputStream(path,StandardOpenOption.CREATE_NEW),control);
                GZIPOutputStream gzip=new GZIPOutputStream(target,65536);
                BufferedWriter writer=new BufferedWriter(new OutputStreamWriter(gzip,StandardCharsets.UTF_8),65536)) {
                for(var table:tables) {
                    if(!database.equals(table.get("TABLE_SCHEMA")) || !"BASE TABLE".equals(table.get("TABLE_TYPE"))) continue;
                    String name=(String)table.get("TABLE_NAME");
                    control.check();
                    List<Map<String,Object>> columns=writableColumns.get(database+"."+name);
                    long rows=0;
                    MessageDigest dataSHA=MessageDigest.getInstance("SHA-256");
                    try(Statement statement=connection.createStatement(ResultSet.TYPE_FORWARD_ONLY,ResultSet.CONCUR_READ_ONLY)) {
                        statement.setFetchSize(Integer.MIN_VALUE);
                        try(ResultSet result=statement.executeQuery(tableSql(database,name,columns))) {
                            while(result.next()) {
                                control.check();
                                if(!result.getBoolean(1))throw new IOException("ROW_SIZE_LIMIT");
                                List<String> values=new ArrayList<>();
                                for(int n=1;n<=columns.size();n++) {
                                    String hex=result.getString(n+1);
                                    if(hex!=null && (hex.length()%2!=0 || !hex.matches("[0-9A-F]*")))throw new SQLException("HEX_ENCODING_INVALID","HY000");
                                    values.add(hex);
                                }
                                String line=json(Arrays.asList(name,values))+"\n";
                                dataSHA.update(line.getBytes(StandardCharsets.UTF_8));
                                writer.write(line);rows++;
                                if(rows%10000==0)log.accept(database+"."+name+": "+rows+" rows");
                            }
                        }
                    }
                    writer.flush();
                    counts.add(Map.of("schema",database,"table",name,"rows",rows,"rowStreamSHA256",HexFormat.of().formatHex(dataSHA.digest())));
                    log.accept(database+"."+name+": "+rows+" rows completed");
                }
            }
        }
        // Concurrent source DDL invalidates the export; normal DML may advance AUTO_INCREMENT.
        if(!tables.equals(query(connection,TABLES_SQL)))throw new SQLException("SOURCE_DDL_CHANGED","HY000");
        for(var object:objects) {
            control.check();
            String database=(String)object.get("TABLE_SCHEMA"), name=(String)object.get("TABLE_NAME");
            if(!definitionForComparison(map(object.get("create"))).equals(definitionForComparison(one(connection,"SHOW CREATE TABLE "+identifier(database)+"."+identifier(name))))) throw new SQLException("SOURCE_DDL_CHANGED","HY000");
        }
        List<Map<String,Object>> files=new ArrayList<>();
        for(String name:List.of("catalog.json","jnpf.rows.jsonl.gz","tj_endanger.rows.jsonl.gz")) {
            Path path=output.resolve(name);
            files.add(Map.of("name",name,"bytes",Files.size(path),"sha256",sha(path)));
        }
        connection.rollback();
        Map<String,Object> receipt=new LinkedHashMap<>();
        receipt.put("format",FORMAT);receipt.put("rowProjection",ROW_PROJECTION);receipt.put("completed",true);
        receipt.put("readOnlySnapshotVerified",true);receipt.put("sourceState",state);
        receipt.put("fullMetadataPrivilegesVerified",true);
        receipt.put("schemas",SCHEMAS);receipt.put("tableCounts",counts);receipt.put("files",files);
        receipt.put("completedAt",Instant.now().toString());receipt.put("sourceBusinessDmlOrDdlExecuted",false);
        receipt.put("directPhysicalDatadirAccess",false);receipt.put("generatedColumnsExcludedFromRows",true);
        receipt.put("rowEncoding","FLOAT promoted to DOUBLE before BINARY; all values HEX encoded; SQL NULL retained as JSON null");
        receipt.put("restoreVerified",false);receipt.put("fullCloneReady",false);
        return receipt;
    }

    static String safeFailure(Throwable error) {
        if(error instanceof SQLException sql) {
            Set<String> ownCodes=Set.of("EXPECTED_ONE_METADATA_ROW","READ_ONLY_SNAPSHOT_NOT_VERIFIED","UTC_SESSION_NOT_VERIFIED","FULL_SOURCE_METADATA_PRIVILEGES_NOT_PROVEN","SOURCE_SCHEMAS_MISSING","NON_TRANSACTIONAL_SOURCE_TABLE","SOURCE_SCHEMA_OUT_OF_SCOPE","HEX_ENCODING_INVALID","SOURCE_DDL_CHANGED");
            return (sql.getErrorCode()==0 && ownCodes.contains(sql.getMessage())?sql.getMessage()+"; ":"")+"SQLState="+sql.getSQLState()+", vendorCode="+sql.getErrorCode();
        }
        if(error instanceof IOException && Set.of("CANCELLED","TIME_LIMIT","OUTPUT_SIZE_LIMIT","ROW_SIZE_LIMIT").contains(error.getMessage()))return error.getMessage();
        return error.getClass().getSimpleName();
    }

    static void launch(String[] args) throws Exception {
        if(args.length!=4) throw new IllegalArgumentException("Expected source-config, private-source-host, output-root, config-SHA256");
        Path configPath=Paths.get(args[0]).toRealPath(), outputRoot=Paths.get(args[2]).toAbsolutePath().normalize();
        if(Files.size(configPath)>65536 || !Files.isDirectory(outputRoot))throw new IllegalArgumentException("INPUT_SCOPE_INVALID");
        if(!sha(configPath).equals(args[3]))throw new IllegalArgumentException("SOURCE_CONFIGURATION_HASH_CHANGED");
        Config config=Config.parse(Files.readString(configPath,StandardCharsets.UTF_8),args[1]);
        JFrame frame=new JFrame("天津原数据只读导出器（候选，未验收恢复）");
        JTextArea log=new JTextArea(18,90);log.setEditable(false);log.setLineWrap(true);
        log.setText("范围：jnpf、tj_endanger；源主机："+config.host()+":"+config.port()+"\n单次读取，最多20分钟、压缩输出合计512MiB；不重试登录。\n不复制物理库，不执行原应用、DDL、业务写入、触发器或事件。\n结果保存在当前252机器的私有输出目录；密码不会显示或写入日志。\n尚未验证真实数据库导出及恢复；请在获准后点击一次。\n");
        JButton start=new JButton("开始本次只读导出"),cancel=new JButton("停止本次读取");cancel.setEnabled(false);
        JPanel buttons=new JPanel();buttons.add(start);buttons.add(cancel);
        frame.add(new JScrollPane(log),BorderLayout.CENTER);frame.add(buttons,BorderLayout.SOUTH);
        // Deadline begins when the operation is started, not while awaiting approval.
        final Control[] active={null};
        Consumer<String> logger=text->SwingUtilities.invokeLater(()->log.append(text+"\n"));
        start.addActionListener(event->{
            start.setEnabled(false);cancel.setEnabled(true);
            Control job=new Control(MAX_MILLIS,MAX_BYTES);active[0]=job;
            Thread worker=new Thread(()->{
                Path output=null;
                ScheduledExecutorService timer=Executors.newSingleThreadScheduledExecutor(r->{Thread thread=new Thread(r,"own-export-deadline");thread.setDaemon(true);return thread;});
                timer.schedule(job::cancel,MAX_MILLIS,TimeUnit.MILLISECONDS);
                try {
                    if(!sha(configPath).equals(args[3]))throw new IllegalArgumentException("SOURCE_CONFIGURATION_HASH_CHANGED");
                    claimAttempt(outputRoot);
                    output=Files.createDirectory(outputRoot.resolve("export_"+DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss").format(LocalDateTime.now())+"_"+UUID.randomUUID().toString().substring(0,8)));
                    logger.accept("连接一次原数据库，校验只读一致性快照……");
                    Class.forName("com.mysql.cj.jdbc.Driver");
                    Map<String,Object> receipt;
                    try(Connection connection=DriverManager.getConnection(config.url(),config.properties())) {
                        receipt=export(connection,output,job,logger);
                    }
                    writeJson(output.resolve("manifest.json"),receipt,job);
                    logger.accept("导出完成；文件SHA和表行数已写入manifest.json。恢复及业务对照仍未验收。");
                    logger.accept("输出目录："+output);
                } catch(Throwable error) {
                    logger.accept("本次停止或失败："+safeFailure(error)+"。未自动重试；部分文件不得当作完整备份。");
                    if(output!=null)try {Files.writeString(output.resolve("FAILED.json"),json(Map.of("completed",false,"error",safeFailure(error),"recordedAt",Instant.now().toString()))+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);}catch(IOException ignored){}
                } finally { timer.shutdownNow();job.connection=null;SwingUtilities.invokeLater(()->cancel.setEnabled(false)); }
            },"own-read-only-export");
            worker.setDaemon(true);worker.start();
        });
        cancel.addActionListener(event->{if(active[0]!=null)active[0].cancel();cancel.setEnabled(false);});
        frame.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        frame.addWindowListener(new WindowAdapter(){@Override public void windowClosing(WindowEvent event){if(active[0]!=null)active[0].cancel();}});
        frame.pack();frame.setLocationByPlatform(true);frame.setVisible(true);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(()->{try { launch(args); }catch(Throwable error){JOptionPane.showMessageDialog(null,"启动准备失败："+safeFailure(error)+"。未连接数据库。","只读导出器",JOptionPane.ERROR_MESSAGE);}});
    }
}
