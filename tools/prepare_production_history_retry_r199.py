from pathlib import Path
import ast
V=Path(__file__).parent;s=(V/'build_production_history_module_r199.py').read_text(encoding='utf-8')
s=s.replace("OUT=W/'production-module-r199'","OUT=W/'production-module-r199-r2'")
old="template/'persistent-launcher-classes',template/'wrapper-classes'])"
new="template/'persistent-launcher-classes',template/'wrapper-classes',A/'payload/callback-overlay/20261026-password-identity/persistent-launcher-classes'])"
assert s.count(old)==1;s=s.replace(old,new);ast.parse(s);p=V/'build_production_history_module_r199_r2.py';assert not p.exists();p.write_text(s,encoding='utf-8')
print('ORIGINAL_CALLBACK_SCOPE_COMPILE_DEPENDENCY_INCLUDED_NO_ORIGINAL_CLASS_CHANGED')
