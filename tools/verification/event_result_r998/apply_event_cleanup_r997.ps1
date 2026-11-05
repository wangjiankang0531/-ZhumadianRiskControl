$ErrorActionPreference='Stop'
$planPath='D:\Project\Zhumadian\Document\Deployment\event_crud_native_r990_20261104\cleanup-plan-r997.json'
$resultPath='D:\Project\Zhumadian\Document\Deployment\event_crud_native_r990_20261104\cleanup-result-r997.json'
if(Test-Path -LiteralPath $resultPath){throw 'CLEANUP_ALREADY_HAS_RESULT_INSPECT_NOT_REPLAY'}
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if($plan.schema -ne 'xnby.own-event-test-cleanup.v1' -or -not $plan.allCodeConfigAndPointersIndependentlyRestored){throw 'EXACT_CLEANUP_PLAN_REQUIRED'}
$refs=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'" | Where-Object {($_.CommandLine -replace '\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')})
if($refs.Count -ne 0){throw 'ACTUAL_OWN_G_REFERENCES_PREVENT_CLEANUP'}
$validated=@()
foreach($target in $plan.targets){
 $resolved=(Resolve-Path -LiteralPath $target.path).ProviderPath
 $allowed=@('D:\Project\Zhumadian\work\ev979','D:\Project\Zhumadian\work\ev982','D:\Project\Zhumadian\work\ev985','D:\Project\Zhumadian\work\ev990')
 $inside=$false
 foreach($root in $allowed){if($resolved.StartsWith($root+'\',[System.StringComparison]::OrdinalIgnoreCase)){$inside=$true}}
 if(-not $inside -or $resolved -ne [IO.Path]::GetFullPath($target.path)){throw 'RESOLVED_CLEANUP_SCOPE_MISMATCH'}
 if($resolved -notmatch '\\(code-transaction\\before|browser\\(first-start|normal-restart)\\chrome-profile)$'){throw 'ONLY_CODE_PREIMAGES_OR_OWN_PROFILE_ALLOWED'}
 $items=@(Get-Item -LiteralPath $resolved -Force)+@(Get-ChildItem -LiteralPath $resolved -Force -Recurse)
 if(@($items | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'REPARSE_POINT_REFUSED'}
 $validated+=,$resolved
}
$freeBefore=(Get-PSDrive -Name D).Free
$done=@()
foreach($path in $validated){
 Remove-Item -LiteralPath $path -Recurse -Force
 if(Test-Path -LiteralPath $path){throw 'CLEANUP_PATH_STILL_PRESENT'}
 $done+=,$path
 [ordered]@{phase='deleting';removed=$done;allTerminalProofsChecked=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
}
$logical=($plan.targets | Measure-Object -Property logicalBytes -Sum).Sum
[ordered]@{phase='completed';removed=$done;directories=$done.Count;logicalBytes=$logical;observedDriveFreeDelta=((Get-PSDrive -Name D).Free-$freeBefore);physicalAttributionClaimed=$false;businessDataPreserved=$true} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding UTF8
[ordered]@{phase='completed';directories=$done.Count;logicalBytes=$logical} | ConvertTo-Json -Compress
