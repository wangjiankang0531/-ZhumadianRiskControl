from pathlib import Path
import ast
V=Path(__file__).parent;s=(V/'verify_production_history_support_r199_r2.py').read_text(encoding='utf-8').replace('support-fixture-r2/Application','support-fixture-r3/Application')
s=s.replace("'configuration':configured['configuration'],'arguments'","'configuration':configured['configuration']['platform'],'arguments'")
s=s.replace("bad['configuration']['platform']['context.initializer.classes']='xnby.platform.OriginalAsyncRequestSnapshotRegistration'","bad['configuration']['context.initializer.classes']='xnby.platform.OriginalAsyncRequestSnapshotRegistration'")
ast.parse(s);p=V/'verify_production_history_support_r199_r3.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('FIXTURE_FOLLOWS_ACTUAL_MATERIALIZE_FLAT_PLATFORM_CONFIGURATION')
