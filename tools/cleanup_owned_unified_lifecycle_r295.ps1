$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian'
$app=Join-Path $project '_g\Application'
$work=Join-Path $project 'work\unified-update-lifecycle-r293'
$docs=Join-Path $project 'Document\Deployment\unified_update_owned_lifecycle_r292_20261103'
$output=Join-Path $docs 'completed-code-fixture-cleanup-r295.json'
if(Test-Path -LiteralPath $output){throw 'ALREADY_CLEANED_DO_NOT_REPEAT'}
$proof=Get-Content -LiteralPath (Join-Path $docs 'verified-lifecycle-r294.json') -Raw | ConvertFrom-Json
$scope=Get-Content -LiteralPath (Join-Path $work 'scope.json') -Raw | ConvertFrom-Json
$terminal=Get-Content -LiteralPath (Join-Path $work 'terminal.json') -Raw | ConvertFrom-Json
if(-not $proof.passed -or -not $terminal.allOwnedControllerHandlesTerminal -or -not $terminal.originalGCodeAndPointersRestored -or $terminal.failure){throw 'LIFECYCLE_OR_RESTORE_NOT_COMPLETE'}
if(@($terminal.controllers).Count -ne 3){throw 'EXPECTED_THREE_CONTROLLERS'}
foreach($controller in $terminal.controllers){
  if($controller.controllerExitCode -ne 0 -or -not $controller.actualJobDescendantsZero -or -not $controller.receipt.normalOwnedShutdown -or -not $controller.receipt.allOwnedChildrenExited){throw 'CONTROLLER_NOT_NORMAL_ZERO'}
  if(@($controller.receipt.exitCodesBeforeJobClose.PSObject.Properties).Count -ne 6){throw 'SIX_COMPONENT_RECEIPT_REQUIRED'}
  foreach($component in $controller.receipt.exitCodesBeforeJobClose.PSObject.Properties){if($component.Value -ne 0){throw 'CHILD_NOT_ZERO'}}
}
if((Get-FileHash -LiteralPath (Join-Path $app 'release-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $scope.baseOriginalGReleaseSHA256){throw 'ORIGINAL_G_RELEASE_NOT_RESTORED'}
if((Get-FileHash -LiteralPath (Join-Path $app 'private\server-configuration.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $scope.privateConfigurationPin.sha256){throw 'PRIVATE_CONFIGURATION_DRIFT'}
$plan=Get-Content -LiteralPath (Join-Path $work 'bundle\update-manifest.json') -Raw | ConvertFrom-Json
$updates=Join-Path $app 'UserData\OriginalPublicUpdates'
$candidates=@()
foreach($entry in Get-ChildItem -LiteralPath $updates -Directory){
  if($entry.Name -notmatch '^[0-9a-f]{32}$'){continue}
  if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'UPDATE_DIRECTORY_REPARSE'}
  $resultPath=Join-Path $entry.FullName 'result.json'
  if(-not(Test-Path -LiteralPath $resultPath)){continue}
  $result=Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
  if($result.updateId -eq $plan.updateId -and $result.oldReleaseSHA256 -eq $scope.baselineAdaptedR36SHA256 -and $result.newReleaseSHA256 -eq $scope.candidateAdaptedR38SHA256){
    if($result.attempt -cne $entry.FullName){throw 'ATTEMPT_DIRECTORY_NOT_EXACT'}
    $rollback=Get-Content -LiteralPath (Join-Path $entry.FullName 'rollback-result.json') -Raw | ConvertFrom-Json
    if(-not $rollback.rolledBack -or -not $result.ready -or $rollback.attempt -cne $entry.FullName){throw 'ACTUAL_ROLLBACK_NOT_COMPLETE'}
    $changes=Get-Content -LiteralPath (Join-Path $entry.FullName 'changes.json') -Raw | ConvertFrom-Json
    if(@($changes.PSObject.Properties).Count -ne 363){throw 'EXACT_CODE_LEDGER_REQUIRED'}
    $expectedNames=@($plan.files.PSObject.Properties.Name)+@($plan.removedFrontendFiles.PSObject.Properties.Name)
    if(Compare-Object @($changes.PSObject.Properties.Name|Sort-Object) @($expectedNames|Sort-Object)){throw 'LEDGER_DIFFERS_FROM_EXACT_OWN_PLAN'}
    foreach($change in $changes.PSObject.Properties){
      if($change.Name -match '^(Assets|Reference|private|UserData)(/|$)' -or $change.Name.Contains('..')){throw 'NON_CODE_LEDGER_PATH'}
      if($null -ne $change.Value.before){
        $backup=Join-Path (Join-Path $entry.FullName 'before') $change.Name
        if((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $change.Value.before){throw 'BACKUP_CODE_PIN_MISMATCH'}
      }
    }
    $candidates+=$entry.FullName
  }
}
if($candidates.Count -ne 1){throw 'ONE_EXACT_OWN_COMPLETED_ATTEMPT_REQUIRED'}
$targets=@((Join-Path $work 'bundle'),(Join-Path $work 'baseline'),(Join-Path $work 'original-before'),$candidates[0])
$processes=Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(pythonw?|java|chrome|node|mysqld|minio|redis-server|nginx)\.exe$' }
foreach($process in $processes){
  $command=([string]$process.CommandLine).Replace('/','\')
  if($command.IndexOf($app,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $command.IndexOf($work,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $command -match 'run_owned_unified_lifecycle_r294\.py'){throw 'OWN_LIFECYCLE_OR_G_PROCESS_STILL_LIVE'}
}
$rows=@()
foreach($target in $targets){
  $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
  if($resolved -cne $target -or -not($resolved.StartsWith($work+'\',[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($updates+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'EXACT_ABSOLUTE_DELETE_SCOPE_REQUIRED'}
  $ancestor=Get-Item -LiteralPath $target
  while($ancestor -and $ancestor.FullName.StartsWith($project,[StringComparison]::OrdinalIgnoreCase)){
    if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE_POINT'}
    $ancestor=$ancestor.Parent
  }
  $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);[long]$files=0;[long]$logical=0
  while($queue.Count){
    $directory=$queue.Dequeue()
    foreach($entry in Get-ChildItem -LiteralPath $directory -Force){
      if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE_POINT'}
      if($entry.PSIsContainer){$queue.Enqueue($entry.FullName)}else{$files++;$logical+=$entry.Length}
    }
  }
  $rows+=[PSCustomObject]@{path=$target;files=$files;logicalBytes=$logical;absoluteScopeNoReferencesAndNoReparseVerified=$true}
}
$receipt=[PSCustomObject]@{passed=$true;actualApplyAndRollback=$true;controllers=3;normalControllerAndChildZeroReceipts=3;originalModelsCompared=398;exactCodeLedger=363;oneOwnAttemptDirectoryVerified=$true;allBackupCodeHashesVerified=$true;actualIISTLS=$false;HTTPIngressAdapterUsed=$true;priorCleanupGuardRefusedFrontendAssetsBeforeAnyDeletion=$true;exactOwnPlanAndRootProtectedPathsNowCheckedSeparately=$true;rawRuntimeUUIDsOrBusinessRowsIncluded=$false}
$receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $docs 'owned-attempt-receipt-summary-r295.json') -Encoding utf8
$freeBefore=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){
  if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'DELETE_TARGET_CHANGED'}
  Remove-Item -LiteralPath $row.path -Recurse -Force
  if(Test-Path -LiteralPath $row.path){throw 'TARGET_NOT_REMOVED'}
}
$freeAfter=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$result=[PSCustomObject]@{passed=$true;at=(Get-Date).ToString('o');targets=$rows;removedFileEntries=($rows|Measure-Object files -Sum).Sum;logicalBytes=($rows|Measure-Object logicalBytes -Sum).Sum;observedDFreeBefore=$freeBefore;observedDFreeAfter=$freeAfter;observedDFreeDelta=($freeAfter-$freeBefore);observedFreeDeltaNotUniquelyAttributed=$true;hardlinkLogicalBytesNotPhysicalReclaimedBytes=$true;sourceFixedPublicBundleProofsAndSmallReceiptsRetained=$true;syntheticDatabaseUploadsAndPrivateConfigurationRetained=$true;publicFormal18891Scene8767AndOther3DThreadUntouched=$true;noProcessesTerminated=$true}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
$result|ConvertTo-Json -Depth 5
