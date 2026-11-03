from pathlib import Path
V=Path(__file__).resolve().parent
source=(V/'cleanup_exercise_department_r323.ps1').read_text(encoding='utf-8')
source=source.replace('native_exercise_department_filter_verified_r320_20261103','native_parent_delete_with_exercises_r325_20261103')
source=source.replace('completed-fixture-cleanup-r323.json','completed-fixture-cleanup-r327.json')
source=source.replace("@('r137','r139')","@('r141')")
source=source.replace("$targets+=Join-Path $base 'r137\\plan-browser\\chrome-profile'\n",'')
source=source.replace('r139','r141').replace('Count -ne 16','Count -ne 18')
assert 'r137'not in source and 'r139'not in source
target=V/'cleanup_parent_delete_r327.ps1';assert not target.exists();target.write_text(source,encoding='utf-8')
print('OWN_PARENT_DELETE_CLEANUP_SOURCE_PREPARED_NOT_EXECUTED')
