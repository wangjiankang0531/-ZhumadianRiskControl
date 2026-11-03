$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian'
$visual='D:\CodexData\home\visualizations\2026\10\28\01a1836e-e4ee-7fb0-be6f-b24f2e2672e4\tencent-feedback-20261031'
$docs=Join-Path $project 'Document\Deployment\public_test_unified_plan_r39_20261103'
$output=Join-Path $docs 'completed-final-verifier-cleanup-r365.json'
if(Test-Path -LiteralPath $output){throw 'ALREADY_CLEANED_DO_NOT_REPEAT'}
$proof=Get-Content -LiteralPath (Join-Path $docs 'verified-fixed-transport-r364.json') -Raw|ConvertFrom-Json
if(-not$proof.passed -or -not$proof.cleanTransportBuilderReproducedAll8FilesByteForByte){throw 'FINAL_TRANSPORT_VERIFICATION_REQUIRED'}
$manifest=Join-Path $docs 'delivery-manifest.json'
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.manifestSHA256){throw 'FIXED_DELIVERY_DRIFT'}
$completed=Join-Path $project 'work\v39'
$terminal=Get-Content -LiteralPath (Join-Path $completed 'terminal.json') -Raw|ConvertFrom-Json
if(-not$terminal.passed -or -not$terminal.noProcessStarted -or -not$terminal.safeToRemoveAfterVerification){throw 'TEST_NOT_TERMINAL'}
$targets=@($completed)
$processes=Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|chrome|java|mysqld|minio|nginx|redis-server)\.exe$'}
foreach($process in $processes){
  $command=([string]$process.CommandLine).Replace('/','\')
  if($command -match 'verify_unified_plan_delivery_r364\.py'){throw 'VERIFIER_STILL_ACTIVE'}
  foreach($target in $targets){if($command.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'TARGET_STILL_REFERENCED'}}
}
$rows=@();[long]$allBytes=0
foreach($target in $targets){
  $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
  if($resolved -cne $target -or -not($target -ceq (Join-Path $visual 'r39-fixed-transport-validation-r353') -or $resolved.StartsWith((Join-Path $project 'work')+'\',[StringComparison]::OrdinalIgnoreCase))){throw 'EXACT_ABSOLUTE_SCOPE_REQUIRED'}
  $ancestor=Get-Item -LiteralPath $target
  while($ancestor){if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE'};$ancestor=$ancestor.Parent}
  $fake=Join-Path $target 'Application\private\server-configuration.json'
  if(Test-Path -LiteralPath $fake){$cfg=Get-Content -LiteralPath $fake -Raw|ConvertFrom-Json;if(-not$cfg.syntheticPreflightFixtureOnly -or -not$cfg.servicesMustNotBeStartedFromThisFixture -or $cfg.containsRealCredentials){throw 'NON_SYNTHETIC_CONFIGURATION'}}
  $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);[long]$files=0;[long]$bytes=0
  while($queue.Count){foreach($entry in Get-ChildItem -LiteralPath ($queue.Dequeue()) -Force){
    if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE'}
    if($entry.PSIsContainer){$queue.Enqueue($entry.FullName)}else{$files++;$bytes+=$entry.Length}
  }}
  $allBytes+=$bytes;$rows+=[pscustomobject]@{path=$target;files=$files;logicalBytes=$bytes;exactAbsoluteScopeNoReferencesNoReparse=$true}
}
if($allBytes -gt 128MB){throw 'UNEXPECTED_TEMPORARY_VOLUME'}
$freeBefore=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'NOT_REMOVED'}}
$freeAfter=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$result=[pscustomobject]@{passed=$true;targets=$rows;removedFiles=($rows|Measure-Object files -Sum).Sum;logicalBytes=$allBytes;observedDFreeDelta=($freeAfter-$freeBefore);observedDeltaNotUniquelyAttributed=$true;fixed8FileDeliverySourceAndSmallEvidenceKept=$true;noProcessStopped=$true;publicFormalDatabaseAssetsOrDesktopChanged=$false}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
$result|Select-Object passed,removedFiles,logicalBytes,observedDFreeDelta,fixed8FileDeliverySourceAndSmallEvidenceKept|ConvertTo-Json
