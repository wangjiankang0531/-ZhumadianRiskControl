$ErrorActionPreference = 'Stop'
$project = 'D:\Project\Zhumadian'
$proofDir = Join-Path $project 'Document\Deployment\public_test_unified_mappers_r38_20261103'
$gate = Get-Content -LiteralPath (Join-Path $proofDir 'mapper-input-gate-cases.json') -Raw | ConvertFrom-Json
if (-not $gate.passed -or -not $gate.originalSyntheticConfigRestored -or $gate.checks -ne 13) { throw 'FINAL_GATE_NOT_COMPLETE' }
$wrapper = Join-Path $proofDir 'delivery\deploy_unified_mappers_r38.py'
if ((Get-FileHash -LiteralPath $wrapper -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.wrapperSHA256) { throw 'FINAL_GATE_WRAPPER_DRIFT' }
$targets = @(
  'D:\Project\Zhumadian\work\r38-unified-full-preflight-r275\Application',
  'D:\Project\Zhumadian\work\r38-unified-full-preflight-r275\bundle',
  'D:\Project\Zhumadian\work\user_feedback_20261031\r38-unified-original-mappers-r1\contract-Application',
  'D:\Project\Zhumadian\work\user_feedback_20261031\r38-unified-original-mappers-r1\transactions'
)
$reportPath = Join-Path $proofDir 'completed-fixture-cleanup-r283.json'
if (Test-Path -LiteralPath $reportPath) { throw 'ALREADY_HAS_CLEANUP_RECEIPT_DO_NOT_REPEAT' }
$programs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(pythonw?|java|chrome|node|mysqld|minio|redis-server|nginx|transport)\.exe$' }
foreach ($process in $programs) {
  $command = [string]$process.CommandLine
  if ($command -match 'verify_mapper_input_gate_r282\.py') { throw 'FINAL_GATE_PROCESS_STILL_LIVE' }
  foreach ($target in $targets) {
    if ($command.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0 -or $command.Replace('/','\').IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0) { throw 'TARGET_HAS_ACTIVE_PROCESS_REFERENCE' }
  }
}
$rows = @()
foreach ($target in $targets) {
  $resolved = (Resolve-Path -LiteralPath $target).ProviderPath
  if ($resolved -cne $target -or -not $resolved.StartsWith($project + '\work\',[StringComparison]::OrdinalIgnoreCase)) { throw 'EXACT_ABSOLUTE_TARGET_REQUIRED' }
  $ancestor = Get-Item -LiteralPath $target
  while ($ancestor -and $ancestor.FullName.StartsWith($project,[StringComparison]::OrdinalIgnoreCase)) {
    if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'ANCESTOR_REPARSE_POINT' }
    $ancestor = $ancestor.Parent
  }
  $queue = [Collections.Generic.Queue[string]]::new()
  $queue.Enqueue($target)
  [long]$files=0; [long]$logical=0; [long]$directories=0
  while ($queue.Count) {
    $directory = $queue.Dequeue(); $directories++
    foreach ($entry in Get-ChildItem -LiteralPath $directory -Force) {
      if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'CHILD_REPARSE_POINT' }
      if ($entry.PSIsContainer) { $queue.Enqueue($entry.FullName) } else { $files++; $logical += $entry.Length }
    }
  }
  $rows += [PSCustomObject]@{path=$target;fileEntries=$files;logicalBytes=$logical;directories=$directories;absoluteScopeVerified=$true;noActiveProcessReferences=$true;noReparsePoints=$true}
}
$freeBefore = [IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach ($row in $rows) {
  if ((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path) { throw 'TARGET_CHANGED_BEFORE_DELETE' }
  Remove-Item -LiteralPath $row.path -Recurse -Force
  if (Test-Path -LiteralPath $row.path) { throw 'TARGET_NOT_REMOVED' }
}
$freeAfter = [IO.DriveInfo]::new('D:\').AvailableFreeSpace
$report = [PSCustomObject]@{
  passed=$true;at=(Get-Date).ToString('o');targets=$rows;
  removedFileEntries=($rows | Measure-Object fileEntries -Sum).Sum;
  logicalBytes=($rows | Measure-Object logicalBytes -Sum).Sum;
  observedDFreeBefore=$freeBefore;observedDFreeAfter=$freeAfter;observedDFreeDelta=($freeAfter-$freeBefore);
  logicalHardlinkSizesAreNotPhysicalReclaimedBytes=$true;observedFreeDeltaNotUniquelyAttributed=$true;
  sourceFixedBundleAndDeliveryAndProofsRetained=$true;databaseAssetsUploadsAndUserBrowserUntouched=$true;
  publicFormal18891AndScene8767Untouched=$true;noProcessesTerminated=$true
}
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding utf8
$report | ConvertTo-Json -Depth 6
