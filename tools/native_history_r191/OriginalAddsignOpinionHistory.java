package xnby.platform.history;

import com.baomidou.dynamic.datasource.tx.TransactionContext;
import org.springframework.transaction.support.TransactionSynchronization;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Transaction-local history snapshot; callers must supply the original mapper connection. */
public final class OriginalAddsignOpinionHistory {
  private static final ThreadLocal<State> CURRENT = new ThreadLocal<>();
  private static final class State {
    final String transaction;
    final Map<String, String> records = new HashMap<>();
    State(String transaction) { this.transaction = transaction; }
  }
  private static String id(String value) {
    if (value == null || value.trim().isEmpty() || value.length() > 50)
      throw new IllegalArgumentException("EXACT_NATIVE_HISTORY_ID_REQUIRED");
    return value;
  }
  public static String appendBeforeSignature(Connection connection, String sourceRecord,
      String process, String actor) throws SQLException {
    sourceRecord = id(sourceRecord); process = id(process); actor = id(actor);
    String transaction = TransactionContext.getXID();
    if (transaction == null || transaction.trim().isEmpty() || connection.getAutoCommit()
        || !"jnpf".equalsIgnoreCase(connection.getCatalog()))
      throw new IllegalStateException("ORIGINAL_DYNAMIC_TRANSACTION_AND_JNPF_CONNECTION_REQUIRED");
    State state = CURRENT.get();
    if (state == null || !state.transaction.equals(transaction)) {
      state = new State(transaction);
      CURRENT.set(state);
      final State bound = state;
      TransactionContext.registerSynchronization(new TransactionSynchronization() {
        @Override public void afterCompletion(int status) {
          if (CURRENT.get() == bound) CURRENT.remove();
        }
      });
    }
    String key = sourceRecord + "\u0000" + process + "\u0000" + actor;
    if (state.records.containsKey(key)) return state.records.get(key);
    if (state.records.size() >= 64) throw new IllegalStateException("NATIVE_HISTORY_TRANSACTION_BOUND");
    String historyId = UUID.randomUUID().toString().replace("-", "");
    // Empty node/operator references detach the history entry from every active task lookup.
    // Preserve the original service Date after its own JDBC conversion; never mix in SQL session time.
    String sql = "INSERT INTO jnpf.flow_task_operator_record "
        + "(f_id,f_node_code,f_node_name,f_handle_status,f_handle_id,f_handle_time,"
        + "f_handle_opinion,f_task_operator_id,f_task_node_id,f_task_id,f_sign_img,"
        + "f_status,f_operator_id,f_file_list,f_approver_type,f_sort_code,"
        + "f_creator_time,f_creator_user_id,f_delete_mark,f_tenant_id) "
        + "SELECT ?,f_node_code,f_node_name,10,f_handle_id,f_handle_time,"
        + "f_handle_opinion,'','',f_task_id,f_sign_img,f_status,f_operator_id,f_file_list,"
        + "f_approver_type,f_sort_code,f_creator_time,f_creator_user_id,"
        + "COALESCE(f_delete_mark,0),f_tenant_id FROM jnpf.flow_task_operator_record "
        + "WHERE f_id=? AND f_task_id=? AND f_handle_id=? AND f_handle_status=10 "
        + "AND COALESCE(f_delete_mark,0)=0 AND f_handle_time IS NOT NULL";
    try (PreparedStatement statement = connection.prepareStatement(sql)) {
      statement.setString(1, historyId); statement.setString(2, sourceRecord);
      statement.setString(3, process); statement.setString(4, actor);
      if (statement.executeUpdate() != 1)
        throw new SQLException("EXACT_NATIVE_BEFORE_ADDSIGN_RECORD_NOT_UPDATED");
    }
    state.records.put(key, historyId);
    return historyId;
  }
  public static boolean transactionStateCleared() { return CURRENT.get() == null; }
  private OriginalAddsignOpinionHistory() {}
}
