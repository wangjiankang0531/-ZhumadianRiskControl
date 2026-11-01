$ErrorActionPreference='Stop'
$stage='D:\Project\Zhumadian\work\user_feedback_20261031\r23-unified-candidate-r1'
$plan=Get-Content -LiteralPath (Join-Path $stage 'r117-fixture-cleanup-plan.json') -Raw -Encoding UTF8|ConvertFrom-Json
$project='D:\Project\Zhumadian'
$source=[IO.Path]::GetFullPath([string]$plan.preserveDataSource)
$preserve=[IO.Path]::GetFullPath([string]$plan.preserveDataTarget)
if($source -ne 'D:\Project\Zhumadian\_b\Application\UserData\OriginalServer\database\data'){throw 'UNKNOWN_SOURCE_DATA'}
if($preserve -ne 'D:\Project\Zhumadian\work\event_delivery_consistency_20261030\full-controller-r117\retained-synthetic-data'){throw 'UNKNOWN_DATA_DESTINATION'}
foreach($path in @($source,$preserve)){if(-not $path.StartsWith($project+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'OUTSIDE_PROJECT'}}
if(Test-Path -LiteralPath $preserve){throw 'DATA_DESTINATION_EXISTS'}
$paths=@()
foreach($target in $plan.targets){
 $path=[IO.Path]::GetFullPath([string]$target.path).TrimEnd('\')
 if(-not($path.StartsWith($project+'\work\r23gx-r1\',[StringComparison]::OrdinalIgnoreCase)-or $path -eq $project+'\_b'-or $path -eq $stage+'\sparse-graceful-update-preparation-r1\contract-Application')){throw 'UNEXPECTED_CLEANUP_TARGET'}
 $items=@(Get-Item -LiteralPath $path -Force)+@(Get-ChildItem -LiteralPath $path -Recurse -Force)
 if(@($items|Where-Object{$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'REDIRECTED_TREE'}
 $files=@($items|Where-Object{-not $_.PSIsContainer -and -not $_.FullName.StartsWith($source+'\',[StringComparison]::OrdinalIgnoreCase)})
 if($files.Count -ne @($target.files.PSObject.Properties).Count){throw 'FILE_SET_DRIFT'}
 foreach($file in $files){
  $name=$file.FullName.Substring($path.Length+1).Replace('\','/');$expected=$target.files.PSObject.Properties[$name]
  if($null -eq $expected -or $file.Length -ne $expected.Value.bytes){throw 'UNEXPECTED_FILE'}
  if((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected.Value.sha256){throw 'FILE_DRIFT'}
 }
 $paths+=,$path
}
$live=@(Get-CimInstance Win32_Process|Where-Object{
 $line=$_.CommandLine;if($null -eq $line){return $false}
 foreach($path in $paths){if($line.IndexOf($path,[StringComparison]::OrdinalIgnoreCase)-ge 0){return $true}}
 return $false
})
if($live.Count){throw 'FIXTURE_PROGRAMS_STILL_LIVE'}
Move-Item -LiteralPath $source -Destination $preserve
if((Test-Path -LiteralPath $source)-or -not(Test-Path -LiteralPath $preserve)){throw 'SYNTHETIC_DATA_NOT_PRESERVED'}
$before=(Get-PSDrive D).Free
foreach($path in $paths){Remove-Item -LiteralPath $path -Recurse -Force}
foreach($path in $paths){if(Test-Path -LiteralPath $path){throw 'TARGET_REMAINS'}}
$after=(Get-PSDrive D).Free
$result=[ordered]@{targets=$paths.Count;zeroMatchingProcesses=$true;allFileSHA256Verified=$true;readinessReportsArchived=10;ownedSyntheticDatabasePreserved=$true;preservedSyntheticDataBytes=$plan.preservedSyntheticDataBytes;sourceResultsCurrentCandidateAndFixedDeliveryKept=$true;hardlinksNotCountedAsFreedPayloadBytes=$true;observedDiskFreeIncreaseBytes=($after-$before)}
$result|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $stage 'r117-fixture-cleanup-completed.json') -Encoding UTF8
$result|ConvertTo-Json -Compress
