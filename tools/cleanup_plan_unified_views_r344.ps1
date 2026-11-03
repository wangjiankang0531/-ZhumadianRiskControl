$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian'
$docs=Join-Path $project 'Document\Deployment\native_plan_unified_candidate_r39_20261103'
$bundleRoot=Join-Path $project 'work\r39-plan-runtime-unified-r1'
$receiptPath=Join-Path $docs 'completed-file-fixture-cleanup-r344.json'
if(Test-Path -LiteralPath $receiptPath){throw 'ALREADY_CLEANED'}
$full=Get-Content -LiteralPath (Join-Path $docs 'full-program-verification-r343.json') -Raw|ConvertFrom-Json
if(-not$full.passed -or $full.variants.Count -ne 2){throw 'BOTH_PROGRAM_VIEWS_NOT_PASSED'}
$driverNames=@('run_plan_unified_full_views_r339.py','verify_plan_unified_full_r36_r339.py','verify_plan_unified_full_r37_r339.py','prepare_r37_full_view_dependency_r341.py','verify_plan_unified_full_r37_r341.py','verify_r37_full_view_resume_r343.py','run_plan_unified_transactions_r342.py','verify_plan_unified_transactions_r36_r342.py','verify_plan_unified_transactions_r37_r342.py')
foreach($process in Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|java|mysqld|redis-server|minio|nginx|chrome)\.exe$'}){
    foreach($driver in $driverNames){if(([string]$process.CommandLine).IndexOf($driver,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'OWN_VALIDATION_PROCESS_STILL_ACTIVE'}}
}
foreach($variant in @('r36','r37')){
    $p=Get-Content -LiteralPath (Join-Path $docs ($variant+'\full-program-preflight.json')) -Raw|ConvertFrom-Json
    $t=Get-Content -LiteralPath (Join-Path $docs ($variant+'\verified-transactions-r342.json')) -Raw|ConvertFrom-Json
    $r=Get-Content -LiteralPath (Join-Path $docs ($variant+'\plan-readiness-boundaries-r340.json')) -Raw|ConvertFrom-Json
    if(-not$p.allPassed -or -not$p.sourceProgramsUnchanged -or -not$t.passed -or $t.actualFileScenarios -ne 16 -or $t.compositionNegativeCases -ne 57 -or -not$r.passed -or $r.cases.Count -ne 8){throw 'SOURCE_OR_RECOVERY_PROOF_INCOMPLETE'}
}
$roots=@(
    (Join-Path $project 'work\r39-full-preflight-r36-r339\Application'),
    (Join-Path $project 'work\r39-full-preflight-r36-r339\bundle'),
    (Join-Path $project 'work\r39-full-preflight-r37-r341\Application'),
    (Join-Path $project 'work\r39-full-preflight-r37-r341\bundle')
)
foreach($variant in @('r36','r37')){
    foreach($folder in @('contract-Application','transactions','plan-readiness')){$roots+=Join-Path (Join-Path $bundleRoot $variant) $folder}
}
if($roots.Count -ne 10){throw 'EXACT_TEN_TEST_ROOTS_REQUIRED'}
$rows=@()
foreach($target in $roots){
    $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
    if($resolved -cne $target -or -not$resolved.StartsWith((Join-Path $project 'work')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'ABSOLUTE_OWN_TEST_SCOPE_REQUIRED'}
    if(Test-Path -LiteralPath (Join-Path $target 'user-manual-protected.json')){throw 'USER_MANUAL_ROOT_PROTECTED'}
    foreach($process in Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|java|mysqld|redis-server|minio|nginx|chrome)\.exe$'}){
        if(([string]$process.CommandLine).Replace('/','\').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'OWN_TARGET_REFERENCE_STILL_ACTIVE'}
    }
    $ancestor=Get-Item -LiteralPath $target
    while($ancestor -and $ancestor.FullName.StartsWith($project,[StringComparison]::OrdinalIgnoreCase)){
        if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE'}
        $ancestor=$ancestor.Parent
    }
    $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);[long]$files=0;[long]$bytes=0
    while($queue.Count){foreach($entry in Get-ChildItem -LiteralPath ($queue.Dequeue()) -Force){
        if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE'}
        if($entry.PSIsContainer){$queue.Enqueue($entry.FullName)}else{$files++;$bytes+=$entry.Length}
    }}
    $rows+=[PSCustomObject]@{path=$target;files=$files;logicalBytes=$bytes;exactAbsoluteNoReferencesNoReparse=$true}
}
$retained=@(
    (Join-Path $bundleRoot 'shared\payload\release-manifest.json'),
    (Join-Path $bundleRoot 'r36\bundle\update-manifest.json'),
    (Join-Path $bundleRoot 'r37\bundle\update-manifest.json'),
    (Join-Path $bundleRoot 'original-r37-contract\payload\release-manifest.json'),
    (Join-Path $project 'work\r39-full-preflight-r36-r339\resolution.json'),
    (Join-Path $project 'work\r39-full-preflight-r37-r341\resolution.json'),
    (Join-Path $project '_g\Application\release-manifest.json')
)
$pins=@{};foreach($file in $retained){$pins[$file]=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash}
if($pins[(Join-Path $project '_g\Application\release-manifest.json')].ToLowerInvariant() -ne 'e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'){throw 'ORIGINAL_OWN_G_RELEASE_DRIFT'}
$freeBefore=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'TARGET_NOT_REMOVED'}}
$freeAfter=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($file in $retained){if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $pins[$file]){throw 'RETAINED_SOURCE_OR_MANIFEST_CHANGED'}}
$report=[ordered]@{passed=$true;at=(Get-Date).ToString('o');targets=$rows;removedFileEntries=($rows|Measure-Object files -Sum).Sum;logicalBytes=($rows|Measure-Object logicalBytes -Sum).Sum;observedDFreeBefore=$freeBefore;observedDFreeAfter=$freeAfter;observedDFreeDelta=($freeAfter-$freeBefore);logicalHardlinkSizeNotClaimedAsPhysicalReclaim=$true;observedFreeDeltaNotUniquelyAttributed=$true;candidateBundlesSourceResultsResolutionMapsOriginalGDataAssetsAndUploadsRetained=$true;noProcessesTerminated=$true;publicFormal18891Scene8767AndDesktopUntouched=$true}
$report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $receiptPath -Encoding utf8
[ordered]@{passed=$true;removedFileEntries=$report.removedFileEntries;logicalBytes=$report.logicalBytes;observedDFreeDelta=$report.observedDFreeDelta;candidateBundlesAndSourcesRetained=$true}|ConvertTo-Json -Compress
