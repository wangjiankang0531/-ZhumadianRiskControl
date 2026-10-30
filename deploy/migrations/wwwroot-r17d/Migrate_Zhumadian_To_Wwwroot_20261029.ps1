param(
 [ValidateSet('PrepareRetry','CheckOnly','Apply','Recover','Verify','CleanOldRoot')][string]$Mode='CheckOnly',
 [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ManifestSHA256
)
$ErrorActionPreference='Stop'
$stage='C:\FTP_Root\Zhumadian\Zhumadian_Directory_Migration_20261030_R17D'
$oldApplication='C:\Zdm\Application'
$newApplication='C:\inetpub\wwwroot\Zhumadian\Application'
$oldRoot='C:\Zdm'
$helper=Join-Path $stage 'migrate_zdm_directory_20261029.py'
$manifest=Join-Path $stage 'migration-manifest.json'
if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ManifestSHA256) {throw 'EXACT_MIGRATION_MANIFEST_REQUIRED'}
$plan=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
foreach($property in $plan.stageFiles.PSObject.Properties){
 $path=Join-Path $stage $property.Name
 $resolved=[IO.Path]::GetFullPath($path)
 if(-not $resolved.StartsWith($stage+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'OWN_STAGE_FILE_REQUIRED'}
 if((Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value.SHA256){throw 'STAGE_SOURCE_HASH_REQUIRED'}
}
function Assert-RegularPath([string]$Path){
 $full=[IO.Path]::GetFullPath($Path)
 for($entry=Get-Item -LiteralPath $full -Force -ErrorAction SilentlyContinue;$null -ne $entry;$entry=$entry.Parent){
  if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'DIRECTORY_REDIRECTION_REFUSED'}
 }
 return $full
}
function Invoke-Step([string]$Application,[string]$Step){
 & (Join-Path $Application 'runtime\python\python.exe') -I -B $helper $Step --manifest-sha256 $ManifestSHA256
 if($LASTEXITCODE -ne 0){throw ('MIGRATION_STEP_FAILED_'+$Step)}
}
function Restore-OldRoot {
 if(Test-Path -LiteralPath $newApplication){
  Invoke-Step $newApplication 'rollback-stop'
  if(Test-Path -LiteralPath $oldApplication){throw 'DO_NOT_OVERWRITE_OLD_APPLICATION'}
  if(-not(Test-Path -LiteralPath $oldRoot)){[void](New-Item -ItemType Directory -Path $oldRoot)}
  [void](Assert-RegularPath $newApplication);[void](Assert-RegularPath $oldRoot)
  Move-Item -LiteralPath $newApplication -Destination $oldApplication
 }
 Invoke-Step $oldApplication 'restart-old'
}
[void](Assert-RegularPath $stage);[void](Assert-RegularPath $oldRoot);[void](Assert-RegularPath $newApplication)
Set-Location -LiteralPath $stage
if($Mode -eq 'PrepareRetry'){Invoke-Step $oldApplication 'prepare-retry';exit 0}
if($Mode -eq 'CheckOnly'){Invoke-Step $oldApplication 'preflight';exit 0}
if($Mode -eq 'Recover'){Restore-OldRoot;exit 0}
if($Mode -eq 'Verify'){Invoke-Step $newApplication 'verify-new';exit 0}
if($Mode -eq 'CleanOldRoot'){
 Invoke-Step $newApplication 'verify-new'
 $resolved=Assert-RegularPath $oldRoot
 if($resolved -ine 'C:\Zdm' -or (Test-Path -LiteralPath $oldApplication)){throw 'EXACT_EMPTY_OLD_ROOT_REQUIRED'}
 if(Test-Path -LiteralPath $oldRoot){
  if(@(Get-ChildItem -LiteralPath $oldRoot -Force).Count -ne 0){throw 'UNKNOWN_OLD_CONTENT_PRESERVED'}
  # Delete only the proven empty old directory; never recursively delete runtime or user data.
  [IO.Directory]::Delete($oldRoot,$false)
 }
 Invoke-Step $newApplication 'confirm-clean'
 exit 0
}
$stopped=$false;$moved=$false
try{
 Invoke-Step $oldApplication 'stop-old';$stopped=$true
 if(Test-Path -LiteralPath $newApplication){
  if(@(Get-ChildItem -LiteralPath $newApplication -Force).Count -ne 0){throw 'TARGET_CHANGED_NO_OVERWRITE'}
  [IO.Directory]::Delete($newApplication,$false)
 }
 if([IO.Path]::GetPathRoot($oldApplication) -ine [IO.Path]::GetPathRoot($newApplication)){throw 'SAME_VOLUME_MOVE_REQUIRED'}
 [void](Assert-RegularPath $oldApplication);[void](Assert-RegularPath (Split-Path -Parent $newApplication))
 if(-not(Test-Path -LiteralPath (Split-Path -Parent $newApplication))){[void](New-Item -ItemType Directory -Path (Split-Path -Parent $newApplication))}
 Move-Item -LiteralPath $oldApplication -Destination $newApplication;$moved=$true
 Invoke-Step $newApplication 'activate-new'
 Write-Host 'NEW_DIRECTORY_READY; EXTERNAL_VERIFICATION_REQUIRED_BEFORE_EMPTY_ZDM_REMOVAL'
}catch{
 Write-Host ('MIGRATION_COORDINATOR_STOPPED_'+$_.Exception.GetType().Name)
 if($stopped){
  if($moved){Restore-OldRoot}else{Invoke-Step $oldApplication 'restart-old'}
 }
 throw
}
