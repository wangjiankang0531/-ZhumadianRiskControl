$ErrorActionPreference='Stop'
$projectRoot='D:\Project\Zhumadian'
$visualRoot='D:\CodexData\home\visualizations\2026\10\28\01a1836e-e4ee-7fb0-be6f-b24f2e2672e4\tencent-feedback-20261031'
$deployment=Join-Path $projectRoot 'Document\Deployment\ledger_original_ui_r940_20261104'
$receipt=Join-Path $deployment 'cleanup-r963.json'
if(Test-Path -LiteralPath $receipt){throw 'CLEANUP_RECEIPT_ALREADY_EXISTS'}
$readJson={param($p) Get-Content -LiteralPath $p -Raw | ConvertFrom-Json}
$independent=& $readJson (Join-Path $deployment 'independent-restore-r962.json')
if(-not $independent.passed -or $independent.currentCodePathsIndependentlyMatchedBefore -ne 1427 -or $independent.durablePointerBeforeImagesMatched -ne 6){throw 'INDEPENDENT_RESTORE_PROOF_REQUIRED'}
$active=@(Get-CimInstance Win32_Process | Where-Object {
 $_.Name -match '^(pythonw?|java|node|nginx|mysqld|minio|redis-server|chrome)\.exe$' -and
 (($_.CommandLine -replace '\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') -or
  ($_.CommandLine -replace '\\','/') -match '/(ledger_full_r941|ledger_resume_r946|ledger_root_r948|ledger_download_r950|ledger_stable_r952|ledger_native_r960|ledger-browser-r(941|946|948|950|952|960)|stable-download-test-r(954|955)|dl(956|957|958))/' )
})
if($active.Count -ne 0){throw 'ACTUAL_OWN_TEST_PROCESS_STILL_LIVE'}
$targets=@()
foreach($n in @(941,946,948,950,952,960)){
 $proof=& $readJson (Join-Path $projectRoot "work\ledgerfull-r$n\verified-ledger-ui-r$n.json")
 if(-not $proof.codeRestored -or -not $proof.privateConfigurationUnchanged -or -not $proof.originalCurrentPointerRestored){throw 'ATTEMPT_RESTORE_REQUIRED'}
 foreach($t in $proof.terminals){if($t.controllerExitCode -ne 0 -or -not $t.actualJobDescendantsZero -or -not $t.normalOwnedShutdown -or $t.forceTerminationUsed){throw 'NORMAL_OWN_CONTROLLER_EXIT_REQUIRED'};foreach($x in $t.exitCodes.PSObject.Properties.Value){if($x -ne 0){throw 'NONZERO_COMPONENT_EXIT'}}}
 $targets+=Join-Path $projectRoot "work\ledgerfull-r$n\code-transaction\before"
 $labels=if($n -eq 960){@('first-start','normal-restart')}else{@('first-start')}
 foreach($label in $labels){
  $base=Join-Path $projectRoot "work\ledger-browser-r$n\$label";$terminal=& $readJson (Join-Path $base 'browser-terminal.json')
  if(-not $terminal.normalBrowserClosed -or $terminal.exitCode -ne 0 -or $terminal.forceTerminationUsed){throw 'NORMAL_LEDGER_BROWSER_EXIT_REQUIRED'}
  $stage=if($n -eq 941){"work\original-manager-full-lifecycle-r609\ledger-ui-r941\$label"}else{"work\original-manager-full-lifecycle-r609\ledger-ui-r941\resume-r$n\$label"}
  $child=@(& $readJson (Join-Path $projectRoot "$stage\probe-terminals.json") | Where-Object {$_.phase -eq 'original-ledger-browser'})
  if($child.Count -ne 1 -or -not $child[0].actualJobDescendantsZero -or $child[0].budget.activeProcesses -ne 0){throw 'ACTUAL_BROWSER_JOB_EXIT_REQUIRED'}
  $targets+=Join-Path $base 'chrome-profile'
 }
}
foreach($n in @(954,955,956,957,958)){
 $terminal=& $readJson (Join-Path $visualRoot "stable-download-terminal-r$n.json")
 if(-not $terminal.actualJobDescendantsZero -or $terminal.budget.activeProcesses -ne 0 -or $terminal.forceTerminationUsed){throw 'MECHANISM_BROWSER_JOB_EXIT_REQUIRED'}
 if($n -le 955){$profile=Join-Path $visualRoot "stable-download-test-r$n\chrome-profile"}else{$profile=Join-Path $projectRoot "work\dl$n\chrome-profile"}
 $targets+=$profile
}
$records=@();$freeBefore=(Get-PSDrive -Name D).Free
foreach($target in $targets){
 if(-not(Test-Path -LiteralPath $target -PathType Container)){throw ('EXPECTED_OWN_ARTIFACT_MISSING: '+$target)}
 $resolved=(Resolve-Path -LiteralPath $target).Path
 if($resolved -ne $target -or -not($resolved.StartsWith($projectRoot+'\work\',[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($visualRoot+'\stable-download-test-r',[StringComparison]::OrdinalIgnoreCase))){throw 'EXACT_ABSOLUTE_TARGET_SCOPE_REQUIRED'}
 $root=Get-Item -LiteralPath $resolved -Force;$entries=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force)
 if(($root.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or @($entries | Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count -ne 0){throw 'REPARSE_TARGET_REFUSED'}
 $files=@($entries | Where-Object {-not $_.PSIsContainer});$records+=[ordered]@{path=$resolved;files=$files.Count;logicalBytes=($files|Measure-Object Length -Sum).Sum}
}
foreach($row in $records){Remove-Item -LiteralPath $row.path -Recurse -Force}
foreach($row in $records){if(Test-Path -LiteralPath $row.path){throw 'OWN_ARTIFACT_REMOVAL_INCOMPLETE'}}
$freeAfter=(Get-PSDrive -Name D).Free
$result=[ordered]@{passed=$true;actualProcessReferences=0;targets=$records;logicalCountsMayIncludeHardlinks=$true;physicalFreeSpaceBefore=$freeBefore;physicalFreeSpaceAfter=$freeAfter;observedFreeSpaceDeltaOnly=($freeAfter-$freeBefore);exactPhysicalFreedAttributedToCleanup=$false;allBusinessRecordsPDFUploadsMetadataSourcesJournalsLogsAndFailuresRetained=$true;abnormal954BrowserExitNotReclassifiedAsNormal=$true;publicOrDesktopTouched=$false}
$result|ConvertTo-Json -Depth 7|Set-Content -LiteralPath $receipt -Encoding utf8
[ordered]@{passed=$true;removedOwnedDirectories=$records.Count;logicalBytes=($records|Measure-Object logicalBytes -Sum).Sum;observedFreeSpaceDeltaOnly=($freeAfter-$freeBefore)}|ConvertTo-Json -Compress
