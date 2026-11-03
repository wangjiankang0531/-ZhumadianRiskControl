from pathlib import Path
import hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
template=(T/'cleanup_owned_unified_lifecycle_r295.ps1').read_text(encoding='utf-8')
rows=[]
for label in ['r36','r37']:
    s=template.replace('unified-update-lifecycle-r293','r39-actual-lifecycle-'+label+'-r346')
    s=s.replace('unified_update_owned_lifecycle_r292_20261103','native_plan_unified_candidate_r39_20261103\\lifecycle-'+label)
    s=s.replace('completed-code-fixture-cleanup-r295.json','completed-code-fixture-cleanup-r349.json')
    s=s.replace('verified-lifecycle-r294.json','verified-lifecycle-r346.json'if label=='r36'else'verified-lifecycle-r347.json')
    s=s.replace('baselineAdaptedR36SHA256','baselineAdapted'+label.upper()+'SHA256').replace('candidateAdaptedR38SHA256','candidateAdaptedR39SHA256')
    s=s.replace(' -ne 363',' -ne 364').replace('exactCodeLedger=363','exactCodeLedger=364')
    s=s.replace('owned-attempt-receipt-summary-r295.json','owned-attempt-receipt-summary-r349.json')
    s=s.replace("$command -match 'run_owned_unified_lifecycle_r294\\.py'", "$command -match 'plan_lifecycle_run_(r36_r346|r37_native_r347)\\.py'")
    s=s.replace('priorCleanupGuardRefusedFrontendAssetsBeforeAnyDeletion=$true;exactOwnPlanAndRootProtectedPathsNowCheckedSeparately=$true;', 'exactOwnPlanAndRootProtectedPathsCheckedSeparately=$true;')
    anchor='$rows=@()'
    if label=='r37':
        extra=r'''
$browserRoot=Join-Path $project 'work\event_delivery_consistency_20261030\full-controller-r163\r145'
$browserProof=Get-Content -LiteralPath (Join-Path $browserRoot 'plan-browser\result.json') -Raw | ConvertFrom-Json
$browserTerminal=Get-Content -LiteralPath (Join-Path $browserRoot 'plan-browser\browser-terminal.json') -Raw | ConvertFrom-Json
$browserOuter=Get-Content -LiteralPath (Join-Path $browserRoot 'browser-outer-terminal.json') -Raw | ConvertFrom-Json
if(-not $browserProof.passed -or @($browserProof.cases).Count -ne 21 -or @($browserProof.exceptions).Count -ne 0 -or $browserTerminal.chromeExitCode -ne 0 -or -not $browserTerminal.normalBrowserClose -or $browserOuter.exitCode -ne 0 -or -not $browserOuter.actualDescendantsZero){throw 'OWN_BROWSER_NOT_NORMAL_VERIFIED'}
foreach($process in $processes){if(([string]$process.CommandLine).Replace('/','\').IndexOf($browserRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'BROWSER_FIXTURE_STILL_LIVE'}}
$targets+=Join-Path $browserRoot 'plan-browser\chrome-profile'
'''
        assert s.count(anchor)==1;s=s.replace(anchor,extra+'\n'+anchor,1)
        a="$resolved.StartsWith($updates+'\\',[StringComparison]::OrdinalIgnoreCase)"
        assert s.count(a)==1;s=s.replace(a,a+" -or $resolved -ceq (Join-Path $browserRoot 'plan-browser\\chrome-profile')",1)
    file=V/('cleanup_plan_lifecycle_'+label+'_r349.ps1');assert not file.exists();file.write_text(s,encoding='utf-8')
    rows.append({'source':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'variant':label.upper()})
out=V/'plan-lifecycle-cleanup-prepared-r349.json';assert not out.exists();out.write_text(json.dumps({'preparedOnly':True,'sources':rows,'noDeletionPerformed':True,'requiresActualLifecycleNormalExitAndRestoredG':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'cleanupScripts':rows,'noDeletionPerformed':True}))
