$ErrorActionPreference='Stop'
$projectRoot='D:\Project\Zhumadian'
$deployment=Join-Path $projectRoot 'Document\Deployment\public_test_home_supervision_r47_20261104'
if (Test-Path -LiteralPath (Join-Path $deployment 'cleanup-r934.json')) { throw 'Cleanup receipt already exists' }
$active=@(Get-CimInstance Win32_Process | Where-Object {
 $_.Name -match '^(pythonw?|java|node|nginx|mysqld|minio|redis-server|chrome)\.exe$' -and
 (($_.CommandLine -replace '\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or $_.CommandLine -like '*verify_unified_home_supervision_r929.py*' -or $_.CommandLine -like '*verify_unified_transport_r933.py*' -or $_.CommandLine -like '*supervision_full_r927*' -or $_.CommandLine -like '*supervision_exact_r931*')
})
if ($active.Count -ne 0) { throw 'Actual test process still live' }
$readJson={param($path) Get-Content -LiteralPath $path -Raw | ConvertFrom-Json}
$independent=& $readJson (Join-Path $deployment 'independent-restore-r934.json')
if (-not $independent.passed -or -not $independent.fourDurablePointersAllMatched) { throw 'Independent current preimage check missing' }
foreach ($browser in @(@('current-supervision-browser-r927','current-supervision-r927'),@('exact-supervision-browser-r931','exact-supervision-r931'))) {
 $terminal=& $readJson (Join-Path $projectRoot ('work\'+$browser[0]+'\browser-terminal.json'))
 $job=& $readJson (Join-Path $projectRoot ('work\original-manager-full-lifecycle-r609\'+$browser[1]+'\normal-restart\browser-job-terminal.json'))
 if (-not $terminal.normalBrowserClosed -or $terminal.exitCode -ne 0 -or $terminal.forceTerminationUsed -or -not $job.actualJobDescendantsZero -or $job.exitCode -ne 0 -or $job.budget.activeProcesses -ne 0) { throw 'Actual browser exit proof missing' }
}
$recovered=& $readJson (Join-Path $projectRoot 'Document\Deployment\supervision_current_full_r920_20261104\conditional-pointer-recovery-r923.json')
if (-not $recovered.passedAsScopedRecovery -or -not $recovered.durableOriginalPointerBeforeImageRestored) { throw 'R921 recovery missing' }
foreach ($entry in @(@('sv925','verified-current-supervision-r925.json'),@('sv927','verified-current-supervision-r927.json'),@('sv931','verified-exact-supervision-r931.json'))) {
 $proof=& $readJson (Join-Path $projectRoot ('work\'+$entry[0]+'\'+$entry[1]))
 if (-not $proof.codeRestored -or -not $proof.privateConfigurationUnchanged -or -not $proof.originalCurrentPointerRestored) { throw 'Before image restoration missing' }
 foreach ($terminal in $proof.terminals) {
  if ($terminal.controllerExitCode -ne 0 -or -not $terminal.actualJobDescendantsZero -or $terminal.forceTerminationUsed) { throw 'Actual terminal proof missing' }
  foreach ($exitCode in $terminal.exitCodes.PSObject.Properties.Value) { if ($exitCode -ne 0) { throw 'Nonzero component' } }
 }
}
$r929=& $readJson (Join-Path $projectRoot 'Document\Deployment\unified_home_supervision_r928_20261104\verified-files-r929.json')
if (-not $r929.passed -or -not $r929.originalSourceAndBaseHashesPreserved) { throw 'File fixture source/restore proof missing' }
$paths=@('work\sv921\code-transaction\before','work\sv925\code-transaction\before','work\sv927\code-transaction\before','work\sv931\code-transaction\before','work\sv929','work\current-supervision-browser-r927\chrome-profile','work\exact-supervision-browser-r931\chrome-profile')
$records=@()
foreach ($relative in $paths) {
 $candidate=Join-Path $projectRoot $relative
 if (-not(Test-Path -LiteralPath $candidate)) { throw ('Expected owned artifact absent: '+$relative) }
 $resolved=(Resolve-Path -LiteralPath $candidate).Path
 if ($resolved -ne $candidate -or -not $resolved.StartsWith(($projectRoot+'\work\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Target escaped intended work root' }
 $rootItem=Get-Item -LiteralPath $resolved -Force
 $entries=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
 if ((($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) -or @($entries | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -ne 0) { throw 'Reparse path refused' }
 if ($relative -eq 'work\sv929' -and (Get-Content -LiteralPath (Join-Path $resolved 'own-code-fixture.marker') -Raw).Trim() -ne 'r47-frozen-core-file-test-no-services') { throw 'Wrong code fixture owner' }
 $files=@($entries | Where-Object {-not $_.PSIsContainer})
 $records += [ordered]@{relative=$relative;files=$files.Count;logicalBytes=($files|Measure-Object -Property Length -Sum).Sum}
}
foreach ($record in $records) { Remove-Item -LiteralPath (Join-Path $projectRoot $record.relative) -Recurse -Force }
foreach ($record in $records) { if(Test-Path -LiteralPath (Join-Path $projectRoot $record.relative)) { throw 'Owned artifact removal incomplete' } }
$result=[ordered]@{schema='xnby.r47.owned-test-cleanup.v1';passed=$true;actualProcessReferences=0;targets=$records;logicalIncludesSharedHardlinks=$true;physicalBytesFreedClaimed=$false;sourceCandidatesManifestsJournalsLogsDatabaseUploadsAssetsAndThreeDimensionalDataRetained=$true;publicOrDesktopTouched=$false}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $deployment 'cleanup-r934.json') -Encoding utf8
$result|ConvertTo-Json -Depth 6 -Compress
