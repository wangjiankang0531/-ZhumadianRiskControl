$ErrorActionPreference='Stop'
$projectRoot='D:\Project\Zhumadian'
$workRoot=Join-Path $projectRoot 'work'
$programRoot=Join-Path $workRoot 'r34gv-r1'
$recoveryRoot=Join-Path $workRoot 'r34tx-r1'
$candidateRoot=Join-Path $workRoot 'user_feedback_20261031\r34-pending-visibility-candidate-r1'
$documentRoot=Join-Path $projectRoot 'Document\Deployment\public_test_pending_visibility_r34_20261102'
$full=Get-Content -LiteralPath (Join-Path $programRoot 'full-preflight-result.json') -Raw|ConvertFrom-Json
$tx=Get-Content -LiteralPath (Join-Path $candidateRoot 'result.json') -Raw|ConvertFrom-Json
$order=Get-Content -LiteralPath (Join-Path $documentRoot 'transport-order-verification.json') -Raw|ConvertFrom-Json
if(!$full.allPassed -or $full.servicesOrDatabasesStarted -or !$tx.allCompositionContractsPassed -or !$tx.foreignDriftRefusedBeforeAnyRestore -or !$order.allPassed -or !$order.fixtureConfigurationBytesRestored){throw 'OWN_R34_FINISHED_PROOFS_REQUIRED'}
$active=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='node.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='minio.exe'" | Where-Object {
 $t=($_.CommandLine -replace '\\','/').ToLowerInvariant()
 $t.Contains('d:/project/zhumadian/work/r34gv-r1/') -or $t.Contains('d:/project/zhumadian/work/r34tx-r1/') -or $t.Contains('d:/project/zhumadian/work/user_feedback_20261031/r34-pending-visibility-candidate-r1/contract-application')
})
if($active.Count){throw 'OWN_R34_SCOPE_HAS_ACTIVE_REFERENCES'}
$allowed=@('normal','first-path','fourth-path','emergency-asset-removal','updater-write','payload-manifest-write','release-pointer-write','foreign-drift')
$targets=@((Join-Path $programRoot 'Application'),(Join-Path $programRoot 'bundle'),(Join-Path $candidateRoot 'contract-Application'))
foreach($case in @(Get-ChildItem -LiteralPath $recoveryRoot -Directory)){
 if($case.Name -notin $allowed){throw 'OWN_R34_RECOVERY_CASE_NOT_ALLOWLISTED'}
 $targets+=Join-Path $case.FullName 'Application'
 $targets+=Join-Path $case.FullName 'backup'
}
$inspected=@()
foreach($target in $targets){
 if(!(Test-Path -LiteralPath $target)){continue}
 $absolute=[IO.Path]::GetFullPath($target)
 $parent=[IO.Path]::GetDirectoryName($absolute)
 $isProgram=$parent -eq $programRoot -and [IO.Path]::GetFileName($absolute) -in @('Application','bundle')
 $isContract=$absolute -eq (Join-Path $candidateRoot 'contract-Application')
 $isRecovery=[IO.Path]::GetDirectoryName($parent) -eq $recoveryRoot -and [IO.Path]::GetFileName($parent) -in $allowed -and [IO.Path]::GetFileName($absolute) -in @('Application','backup')
 if(!$absolute.StartsWith($workRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or !($isProgram -or $isContract -or $isRecovery)){throw 'OWN_R34_ABSOLUTE_TARGET_SCOPE_REJECTED'}
 $node=Get-Item -LiteralPath $absolute
 while($node){
  if($node.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'OWN_R34_ANCESTOR_REPARSE_REFUSED'}
  if($node.FullName -eq $projectRoot){break}
  $node=$node.Parent
 }
 if(!$node){throw 'OWN_R34_TARGET_OUTSIDE_PROJECT'}
 $items=@(Get-ChildItem -LiteralPath $absolute -Recurse -Force)
 foreach($item in $items){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'OWN_R34_REPARSE_REFUSED'}}
 $files=@($items|Where-Object {!$_.PSIsContainer})
 $inspected+=@{path=$absolute;files=$files.Count;logicalBytes=[long](($files|Measure-Object Length -Sum).Sum)}
}
$before=(Get-PSDrive -Name D).Free
foreach($row in $inspected){Remove-Item -LiteralPath $row.path -Recurse -Force}
$after=(Get-PSDrive -Name D).Free
$result=@{at=(Get-Date).ToString('o');finishedOwnPreflightAndRecoveryViewsOnly=$true;directories=$inspected.Count;files=($inspected|Measure-Object files -Sum).Sum;logicalBytes=($inspected|Measure-Object logicalBytes -Sum).Sum;logicalBytesIncludeHardlinksNotPhysicalSavings=$true;observedDiskFreeDelta=$after-$before;diskDeltaNotExclusivelyAttributable=$true;sourceProgramsDeliveryBundleAssetsAndAllDatabasesKept=$true;servicesWereStarted=$false;desktopInputSent=$false;targets=$inspected}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $documentRoot 'own-preflight-views-cleanup.json') -Encoding UTF8
$result.Remove('targets')
$result|ConvertTo-Json -Depth 4
