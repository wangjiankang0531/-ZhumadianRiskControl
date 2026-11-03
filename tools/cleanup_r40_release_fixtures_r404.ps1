$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian';$work=Join-Path $project 'work';$docs=Join-Path $project 'Document\Deployment\public_test_plan_resources_r40_20261103'
$output=Join-Path $docs 'completed-fixture-cleanup-r404.json'
if(Test-Path -LiteralPath $output){throw 'ALREADY_CLEANED'}
$transport=Get-Content -LiteralPath (Join-Path $docs 'verified-fixed-transport-r403.json') -Raw|ConvertFrom-Json
if(-not$transport.passed -or -not$transport.cleanTransportBuilderReproducedAll8FilesByteForByte -or $transport.realServicesDatabasePublicOrDesktopTouched){throw 'VERIFICATION_NOT_COMPLETE'}
$temporary=Join-Path $work 'v40';$terminal=Get-Content -LiteralPath (Join-Path $temporary 'terminal.json') -Raw|ConvertFrom-Json
if(-not$terminal.passed -or -not$terminal.noProcessStarted -or -not$terminal.safeToRemoveAfterVerification -or $terminal.exactTemporaryRoot -cne $temporary){throw 'EXACT_TRANSPORT_TERMINAL_REQUIRED'}
$targets=@($temporary)
foreach($label in @('r36','r37')){
 $proofRoot=Join-Path $project ('Document\Deployment\native_plan_resource_cancel_r385_20261103\release-verification\'+$label)
 $full=Get-Content -LiteralPath (Join-Path $proofRoot 'full-program-preflight.json') -Raw|ConvertFrom-Json
 $recovery=Get-Content -LiteralPath (Join-Path $proofRoot 'composition-and-recovery.json') -Raw|ConvertFrom-Json
 if(-not$full.allPassed -or -not$full.sourceProgramsUnchanged -or $full.servicesStarted -or -not$recovery.passed -or $recovery.realProcessesSQLDatabaseOrPublicTouched -or $recovery.negativeCompositionCases -ne 63 -or @($recovery.normalAndFaultFileRecoveryCases).Count -ne 16){throw 'FULL_PROGRAM_OR_RECOVERY_NOT_VERIFIED'}
 $fullRoot=Join-Path $work ('r40-full-preflight-'+$label+'-r401')
 foreach($part in @('Application','bundle')){$targets+=Join-Path $fullRoot $part}
 $candidate=Join-Path $work ('r40-plan-resource-cancel-r385\'+$label)
 foreach($part in @('contract-Application','transactions','plan-readiness')){$targets+=Join-Path $candidate $part}
}
$processes=Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|java|chrome|mysqld|minio|nginx|redis-server)\.exe$'}
foreach($p in $processes){$cmd=([string]$p.CommandLine).Replace('/','\');foreach($target in $targets){if($cmd.IndexOf($target,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'TEMPORARY_REFERENCE_STILL_ACTIVE'}}
 if($cmd -match '(run_r40_release_checks_r401|verify_r40_(full|transactions)_(r36|r37)_r401|verify_plan_resources_delivery_r403)\.py'){throw 'VERIFIER_PROCESS_STILL_LIVE'}
}
$rows=@();[long]$all=0
foreach($target in $targets){
 $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
 if($resolved -cne $target -or -not$resolved.StartsWith($work+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'EXACT_ABSOLUTE_WORK_TARGET_REQUIRED'}
 $a=Get-Item -LiteralPath $target;while($a){if($a.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE'};$a=$a.Parent}
 $q=[Collections.Generic.Queue[string]]::new();$q.Enqueue($target);[long]$count=0;[long]$bytes=0
 while($q.Count){foreach($f in Get-ChildItem -LiteralPath ($q.Dequeue()) -Force){
  if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE'}
  if($f.PSIsContainer){$q.Enqueue($f.FullName)}else{$count++;$bytes+=$f.Length}
 }}
 $all+=$bytes;$rows+=[pscustomobject]@{path=$target;files=$count;logicalBytes=$bytes;absoluteNoReferencesNoReparse=$true}
}
if($all -gt 12GB){throw 'UNEXPECTED_LOGICAL_VOLUME'}
$before=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'DELETE_TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'TARGET_NOT_REMOVED'}}
$after=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$result=[pscustomobject]@{passed=$true;targets=$rows;removedFiles=($rows|Measure-Object files -Sum).Sum;logicalBytes=$all;observedDFreeDelta=($after-$before);hardlinkLogicalBytesNotPhysicalReclaimed=$true;observedFreeDeltaNotUniquelyAttributed=$true;candidateBundlesFixedTransportSourcesAndSmallEvidenceRetained=$true;assetsReferenceDatabaseUploadsAndFormalApplicationsUntouched=$true;noProcessesTerminated=$true}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
$result|Select-Object passed,removedFiles,logicalBytes,observedDFreeDelta|ConvertTo-Json
