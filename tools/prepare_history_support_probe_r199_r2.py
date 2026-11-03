from pathlib import Path
import ast
V=Path(__file__).parent;s=(V/'verify_production_history_support_r199.py').read_text(encoding='utf-8')
s=s.replace("W/'support-fixture/Application'","W/'support-fixture-r2/Application'")
s=s.replace("G/'payload/platform/run-template/own-platform-observation.jar'","G/'payload/callback-overlay/20261026-password-identity/own-platform-observation.jar'")
ast.parse(s);p=V/'verify_production_history_support_r199_r2.py';assert not p.exists();p.write_text(s,encoding='utf-8')
print('FIXTURE_USES_ACTUAL_PINNED_CALLBACK_AUTH_ARCHIVE_NO_PRODUCT_CHANGE')
