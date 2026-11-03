from pathlib import Path
V=Path(__file__).resolve().parent
text=(V/'cleanup_exercise_department_r323.ps1').read_text(encoding='utf-8')
text=text.replace('native_exercise_department_filter_verified_r320_20261103','native_plan_runtime_candidate_r329_20261103')
text=text.replace('completed-fixture-cleanup-r323.json','completed-fixture-cleanup-r332.json')
text=text.replace('r137','r141').replace('r139','r143').replace('Count -ne 16','Count -ne 18')
anchor="  }\n}\nif((Get-FileHash -LiteralPath (Join-Path $app 'release-manifest.json')"
assert text.count(anchor)==1
text=text.replace(anchor,"  }\n  if($attempt -eq 'r143' -and -not(Get-Content -LiteralPath (Join-Path $base 'prepared-r143\\plan-runtime-restored.json') -Raw|ConvertFrom-Json).passed){throw 'PLAN_RUNTIME_RESTORE_NOT_PROVEN'}\n}\nif((Get-FileHash -LiteralPath (Join-Path $app 'release-manifest.json')",1)
anchor="  foreach($pair in $mapping){"
assert text.count(anchor)==1
text=text.replace(anchor,"  if($attempt -eq 'r143'){$targets+=Join-Path $prepared 'plan-runtime-before';$mapping+=,@('plan-runtime-scope.json','plan-runtime-before')}\n"+anchor,1)
target=V/'cleanup_plan_runtime_r332.ps1';assert not target.exists();target.write_text(text,encoding='utf-8')
print('OWN_PLAN_RUNTIME_CLEANUP_SOURCE_PREPARED_NOT_EXECUTED')
