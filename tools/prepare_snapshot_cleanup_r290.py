from pathlib import Path
V=Path(__file__).resolve().parent
s=(V/'cleanup_unified_fixtures_r283.ps1').read_text(encoding='utf-8')
a=s.index('$gate = ');b=s.index('$targets = ')
replacement='''$verified = Get-Content -LiteralPath (Join-Path $proofDir 'independent-fixed-delivery-verification.json') -Raw | ConvertFrom-Json
$gate = Get-Content -LiteralPath 'D:\\Project\\Zhumadian\\Document\\Deployment\\original_mapper_install_preflight_r285_20261103\\verified-cases-r287.json' -Raw | ConvertFrom-Json
if (-not $verified.passed -or -not $gate.passed -or $gate.checks -ne 20) { throw 'FINAL_GATE_NOT_COMPLETE' }
$runtime = Join-Path $proofDir 'delivery\\r38_update_runtime.py'
if ((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.candidateSourceSHA256) { throw 'FINAL_GATE_SOURCE_DRIFT' }
'''
s=s[:a]+replacement+s[b:]
s=s.replace('public_test_unified_mappers_r38_20261103','public_test_unified_mappers_r38_20261103_r2').replace('r38-unified-full-preflight-r275','r38-unified-full-preflight-r288').replace('r38-unified-original-mappers-r1','r38-unified-original-mappers-r2').replace('completed-fixture-cleanup-r283.json','completed-fixture-cleanup-r290.json')
s=s.replace("'verify_mapper_input_gate_r282\\.py'","'(verify_unified_(full_program|composition_recovery)_r288|verify_unified_snapshot_delivery_r289)\\.py'")
p=V/'cleanup_unified_snapshot_fixtures_r290.ps1';assert not p.exists();p.write_text(s,encoding='utf-8')
print('SECOND_CANDIDATE_COMPLETED_FIXTURE_CLEANUP_PREPARED')
