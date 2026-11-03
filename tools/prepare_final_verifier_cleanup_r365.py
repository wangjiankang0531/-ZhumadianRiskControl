from pathlib import Path
V=Path(__file__).resolve().parent;s=(V/'cleanup_transport_verifiers_r358.ps1').read_text(encoding='utf-8')
s=s.replace('completed-verifier-cleanup-r358.json','completed-final-verifier-cleanup-r365.json').replace('verified-fixed-transport-r355.json','verified-fixed-transport-r364.json')
a="$targets=@((Join-Path $visual 'r39-fixed-transport-validation-r353'),(Join-Path $project 'work\\r39-transport-validation-r354'),$completed)"
assert s.count(a)==1;s=s.replace(a,'$targets=@($completed)',1).replace("verify_unified_plan_delivery_r35[345]\\.py","verify_unified_plan_delivery_r364\\.py")
out=V/'cleanup_final_verifier_r365.ps1';assert not out.exists();out.write_text(s,encoding='utf-8');print('final-cleanup-prepared')
