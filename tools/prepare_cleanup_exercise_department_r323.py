from pathlib import Path
V=Path(__file__).resolve().parent
source=(V/'cleanup_native_plan_delete_r308.ps1').read_text(encoding='utf-8')
source=source.replace('native_plan_delete_roundtrip_r304_20261103','native_exercise_department_filter_verified_r320_20261103')
source=source.replace('completed-fixture-cleanup-r308.json','completed-fixture-cleanup-r323.json')
source=source.replace('r135','r139').replace('Count -ne 14','Count -ne 16')
start=source.index('$early=Get-Content ')
end=source.index("foreach($attempt in @('r134','r139')){")
assert start<end
source=source[:start]+source[end:]
source=source.replace("@('r134','r139')","@('r137','r139')").replace("@('r133','r134','r139')","@('r137','r139')")
anchor="$targets+=Join-Path $base 'r139\\plan-browser\\chrome-profile'"
assert source.count(anchor)==1
source=source.replace(anchor,"$targets+=Join-Path $base 'r137\\plan-browser\\chrome-profile'\n"+anchor)
assert not any(s in source for s in ['r133','r134','r135','prestart-refusal-and-restore'])
target=V/'cleanup_exercise_department_r323.ps1';assert not target.exists();target.write_text(source,encoding='utf-8')
print('OWN_EXERCISE_FILTER_CLEANUP_SOURCE_PREPARED_NOT_EXECUTED')
