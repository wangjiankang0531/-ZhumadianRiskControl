$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian';$docs=Join-Path $project 'Document\Deployment\native_plan_six_relations_r372_20261103'
$output=Join-Path $docs 'completed-fixture-cleanup-r382.json'
if(Test-Path -LiteralPath $output){throw 'ALREADY_CLEANED_DO_NOT_REPEAT'}
$proof=Get-Content -LiteralPath (Join-Path $docs 'verified-component-and-build-r381.json') -Raw|ConvertFrom-Json
if(-not$proof.passedComponentAndFullBuildStage -or -not$proof.full29CaseNormalRoleAcceptancePending){throw 'EXPECTED_COMPONENT_ONLY_STAGE_REQUIRED'}
$component=Join-Path $project 'work\plan-resource-cancel-r375'
$full=Join-Path $project 'work\user_feedback_20261031\plan-resource-cancel-r378'
foreach($variant in @('baseline','candidate')){
  $outer=Get-Content -LiteralPath (Join-Path $component ($variant+'-outer-terminal.json')) -Raw|ConvertFrom-Json
  $terminal=Get-Content -LiteralPath (Join-Path $component ($variant+'\terminal.json')) -Raw|ConvertFrom-Json
  if($outer.nodeExitCode -ne 0 -or -not$outer.actualDescendantsZero -or $terminal.chromeExitCode -ne 0 -or -not$terminal.serverNormallyClosed){throw 'OWN_COMPONENT_NOT_NORMAL_ZERO'}
}
$build=Get-Content -LiteralPath (Join-Path $full 'retry-r2\build-terminal.json') -Raw|ConvertFrom-Json
$restored=Get-Content -LiteralPath (Join-Path $full 'retry-r2\source-restored.json') -Raw|ConvertFrom-Json
if($build.nodeExitCode -ne 0 -or -not$build.actualDescendantsZeroBeforeClose -or -not$restored.allSevenOverrideLayersRestored){throw 'BUILD_OR_SOURCE_RESTORE_NOT_COMPLETE'}
if(Test-Path -LiteralPath (Join-Path $full 'source\node_modules')){throw 'DEPENDENCY_JUNCTION_MUST_ALREADY_BE_REMOVED'}
if((Get-FileHash -LiteralPath (Join-Path $project '_g\Application\release-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'){throw 'OWN_G_NOT_ORIGINAL'}
$targets=@()
foreach($variant in @('baseline','candidate')){foreach($folder in @('site','profile')){$targets+=Join-Path $component ($variant+'\'+$folder)}}
$targets+=Join-Path $project 'work\plan-resource-cancel-r377\source'
$targets+=Join-Path $full 'source'
foreach($folder in @('cache','dist','retry-r2\cache')){$p=Join-Path $full $folder;if(Test-Path -LiteralPath $p){$targets+=$p}}
$processes=Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|chrome|java|mysqld|esbuild|nginx|minio|redis-server)\.exe$'}
foreach($process in $processes){
  $command=([string]$process.CommandLine).Replace('/','\')
  foreach($root in @($component,$full,(Join-Path $project '_g\Application'))){if($command.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'OWN_TEST_OR_G_REFERENCE_STILL_ACTIVE'}}
}
$origin=Join-Path $project 'work\user_feedback_20261031\emergency-workflow-source-r17\source'
$rows=@();[long]$allBytes=0
foreach($target in $targets){
  $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
  if($resolved -cne $target -or -not$resolved.StartsWith((Join-Path $project 'work')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'EXACT_ABSOLUTE_WORK_SCOPE_REQUIRED'}
  $ancestor=Get-Item -LiteralPath $target
  while($ancestor){if($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE'};$ancestor=$ancestor.Parent}
  $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);[long]$files=0;[long]$bytes=0
  $isRestoredSource=$target.EndsWith('\source',[StringComparison]::OrdinalIgnoreCase)
  while($queue.Count){foreach($entry in Get-ChildItem -LiteralPath ($queue.Dequeue()) -Force){
    if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE'}
    if($entry.PSIsContainer){$queue.Enqueue($entry.FullName)}else{
      $files++;$bytes+=$entry.Length
      if($isRestoredSource){$rel=$entry.FullName.Substring($target.Length+1);$old=Join-Path $origin $rel;if(-not(Test-Path -LiteralPath $old) -or (Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash){throw 'RESTORED_SOURCE_DRIFT'}}
    }
  }}
  $allBytes+=$bytes;$rows+=[pscustomobject]@{path=$target;files=$files;logicalBytes=$bytes;exactAbsoluteNoReferencesNoReparse=$true;restoredSourcePinsCompared=$isRestoredSource}
}
if($allBytes -gt 256MB){throw 'UNEXPECTED_TEMPORARY_VOLUME'}
$freeBefore=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'TARGET_NOT_REMOVED'}}
$freeAfter=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$result=[pscustomobject]@{passed=$true;targets=$rows;removedFiles=($rows|Measure-Object files -Sum).Sum;logicalBytes=$allBytes;observedDFreeDelta=($freeAfter-$freeBefore);observedChangeNotUniquelyAttributed=$true;componentSourcesFullCompiledCandidateAndSmallResultsRetained=$true;referenceDependenciesAssetsDatabaseAndUploadsRetained=$true;noProcessesTerminated=$true;publicFormalSceneOrDesktopChanged=$false}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
$result|Select-Object passed,removedFiles,logicalBytes,observedDFreeDelta,componentSourcesFullCompiledCandidateAndSmallResultsRetained|ConvertTo-Json
