$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian';$app=Join-Path $project '_g\Application'
$base=Join-Path $project 'work\event_delivery_consistency_20261030\full-controller-r163'
$docs=Join-Path $project 'Document\Deployment\native_plan_delete_roundtrip_r304_20261103'
$reportPath=Join-Path $docs 'completed-fixture-cleanup-r308.json'
if(Test-Path -LiteralPath $reportPath){throw 'ALREADY_CLEANED_DO_NOT_REPEAT'}
$result=Get-Content -LiteralPath (Join-Path $base 'r135\result.json') -Raw|ConvertFrom-Json
$browser=Get-Content -LiteralPath (Join-Path $base 'r135\plan-browser\result.json') -Raw|ConvertFrom-Json
$browserTerminal=Get-Content -LiteralPath (Join-Path $base 'r135\plan-browser\browser-terminal.json') -Raw|ConvertFrom-Json
if(-not$result.allPassed -or -not$browser.passed -or @($browser.cases).Count -ne 14 -or $browserTerminal.chromeExitCode -ne 0 -or -not$browserTerminal.normalBrowserClose){throw 'FINAL_BUSINESS_OR_BROWSER_NOT_PASSED'}
$early=Get-Content -LiteralPath (Join-Path $project 'Document\Deployment\native_plan_delete_roundtrip_r297_20261103\prestart-refusal-and-restore-r300.json') -Raw|ConvertFrom-Json
if(-not$early.passed -or -not$early.refusalBeforeTestRootOrControllerAllocation -or $early.normalSixComponentReceiptsFabricated){throw 'PRESTART_RESTORE_NOT_PROVEN'}
foreach($attempt in @('r134','r135')){
  $outer=Get-Content -LiteralPath (Join-Path $base ($attempt+'-outer-terminal.json')) -Raw|ConvertFrom-Json
  $terminal=Get-Content -LiteralPath (Join-Path $base ($attempt+'\controller-terminal.json')) -Raw|ConvertFrom-Json
  $receipt=Get-Content -LiteralPath (Join-Path $base ($attempt+'\scoped-controller-receipt.json')) -Raw|ConvertFrom-Json
  if(-not$outer.actualDescendantsZeroBeforeClose -or -not$terminal.actualDescendantJobCountZeroBeforeClose -or $terminal.exitCode -ne 0 -or -not$receipt.normalOwnedShutdown -or -not$receipt.allOwnedChildrenExited){throw 'CONTROLLER_NOT_NORMAL_TERMINAL'}
  foreach($component in $receipt.exitCodesBeforeJobClose.PSObject.Properties){if($component.Value -ne 0){throw 'CHILD_EXIT_NOT_ZERO'}}
  foreach($name in @('frontend-restored.json','mapper-observer-restored.json','mapper-product-restored.json','history-runtime-restored.json')){
    if(-not(Get-Content -LiteralPath (Join-Path $base ('prepared-'+$attempt+'\'+$name)) -Raw|ConvertFrom-Json).passed){throw 'PREIMAGE_RESTORE_NOT_PASSED'}
  }
}
if((Get-FileHash -LiteralPath (Join-Path $app 'release-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'){throw 'ORIGINAL_G_RELEASE_DRIFT'}
$processes=Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|chrome|java|mysqld|minio|nginx|redis-server)\.exe$'}
foreach($process in $processes){
  $command=([string]$process.CommandLine).Replace('/','\')
  if($command.IndexOf($app,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'OWN_G_PROCESS_STILL_ACTIVE'}
  foreach($attempt in @('r133','r134','r135')){
    if($command.IndexOf((Join-Path $base $attempt),[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $command.IndexOf((Join-Path $base ('prepared-'+$attempt)),[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'TEST_FIXTURE_PROCESS_STILL_ACTIVE'}
  }
}
$targets=@()
foreach($attempt in @('r133','r134','r135')){
  $prepared=Join-Path $base ('prepared-'+$attempt)
  foreach($folder in @('frontend-before','mapper-observer-before','mapper-product-before','history-before','before')){$targets+=Join-Path $prepared $folder}
  $mapping=@(@('frontend-scope.json','frontend-before'),@('mapper-observer-scope.json','mapper-observer-before'),@('mapper-product-scope.json','mapper-product-before'),@('history-runtime-scope.json','history-before'))
  foreach($pair in $mapping){
    $scope=Get-Content -LiteralPath (Join-Path $prepared $pair[0]) -Raw|ConvertFrom-Json
    foreach($row in $scope.oldFiles.PSObject.Properties){
      if($null -eq $row.Value){continue}
      if($row.Name.Contains('..')){throw 'BACKUP_RELATIVE_PATH_REQUIRED'}
      $file=Join-Path (Join-Path $prepared $pair[1]) $row.Name
      if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.Value.sha256){throw 'BACKUP_SHA_DRIFT'}
    }
  }
  $stock=Get-Content -LiteralPath (Join-Path $prepared 'temporary-synthetic-config-scope.json') -Raw|ConvertFrom-Json
  foreach($row in $stock.files.PSObject.Properties){
    $file=Join-Path (Join-Path $prepared 'before') $row.Name
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.Value.beforeSHA256){throw 'ORIGINAL_SYNTHETIC_CONFIG_BACKUP_DRIFT'}
    if($row.Name -eq 'private/server-configuration.json' -and (Get-FileHash -LiteralPath (Join-Path $app $row.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.Value.beforeSHA256){throw 'CURRENT_SYNTHETIC_CONFIG_NOT_RESTORED'}
  }
}
$targets+=Join-Path $base 'r135\plan-browser\chrome-profile'
$rows=@()
foreach($target in $targets){
  $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
  if($resolved -cne $target -or -not $resolved.StartsWith($base+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'EXACT_ABSOLUTE_SCOPE_REQUIRED'}
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
  $rows+=[PSCustomObject]@{path=$target;files=$files;logicalBytes=$bytes;exactAbsoluteScopeNoReferencesNoReparse=$true}
}
$freeBefore=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'NOT_REMOVED'}}
$freeAfter=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$report=[PSCustomObject]@{passed=$true;at=(Get-Date).ToString('o');targets=$rows;removedFileEntries=($rows|Measure-Object files -Sum).Sum;logicalBytes=($rows|Measure-Object logicalBytes -Sum).Sum;observedDFreeBefore=$freeBefore;observedDFreeAfter=$freeAfter;observedDFreeDelta=($freeAfter-$freeBefore);observedFreeChangeNotUniquelyAttributed=$true;sourceResultsSmallReceiptsOriginalDatabaseAndUploadedObjectRetained=$true;publicFormal18891Scene8767UserBrowserAndOther3DThreadUntouched=$true;noProcessesTerminated=$true}
$report|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $reportPath -Encoding utf8
$report|Select-Object passed,removedFileEntries,logicalBytes,observedDFreeDelta,sourceResultsSmallReceiptsOriginalDatabaseAndUploadedObjectRetained|ConvertTo-Json
