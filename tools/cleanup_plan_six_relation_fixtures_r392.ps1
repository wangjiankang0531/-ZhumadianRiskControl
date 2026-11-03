$ErrorActionPreference='Stop'
$project='D:\Project\Zhumadian';$app=Join-Path $project '_g\Application'
$docs=Join-Path $project 'Document\Deployment\native_plan_resource_cancel_r385_20261103'
$output=Join-Path $docs 'completed-fixture-cleanup-r392.json'
if(Test-Path -LiteralPath $output){throw 'ALREADY_CLEANED'}
$old=Join-Path $project 'work\plan-six-relations-cancel-r386';$current=Join-Path $project 'work\plan-six-relations-typed-r390';$ui=Join-Path $project 'work\plan-six-relations-ui-r394';$uiPrevious=Join-Path $project 'work\plan-six-relations-ui-r396';$uiFinal=Join-Path $project 'work\plan-six-relations-ui-r398'
foreach($receipt in @((Join-Path $old 'terminal.json'),(Join-Path $old 'resume-terminal-r388.json'),(Join-Path $current 'terminal.json'),(Join-Path $ui 'terminal.json'),(Join-Path $uiPrevious 'terminal.json'),(Join-Path $uiFinal 'terminal.json'))){
 $r=Get-Content -LiteralPath $receipt -Raw|ConvertFrom-Json
 if(-not$r.allOwnedControllerHandlesTerminal){throw 'CONTROLLER_HANDLES_NOT_TERMINAL'}
 if($receipt -ne (Join-Path $old 'terminal.json') -and -not$r.originalGCodeAndPointersRestored){throw 'OWN_G_NOT_RESTORED'}
 foreach($c in $r.controllers){
  if($c.controllerExitCode -ne 0 -or -not$c.actualJobDescendantsZero -or -not$c.receipt.normalOwnedShutdown){throw 'NOT_NORMAL_ZERO'}
  if(@($c.receipt.exitCodesBeforeJobClose.PSObject.Properties).Count -ne 6){throw 'SIX_CHILDREN_REQUIRED'}
  foreach($v in $c.receipt.exitCodesBeforeJobClose.PSObject.Properties){if($v.Value -ne 0){throw 'CHILD_NOT_ZERO'}}
 }
}
if((Get-FileHash -LiteralPath (Join-Path $app 'release-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'){throw 'ORIGINAL_G_PIN_REQUIRED'}
$targets=@()
foreach($work in @($old,$current)){foreach($name in @('bundle','baseline','original-before')){$targets+=Join-Path $work $name}}
foreach($root in @($ui,$uiPrevious,$uiFinal)){foreach($name in @('bundle','candidate-code','original-before')){$targets+=Join-Path $root $name}}
$browserRoots=@()
foreach($label in @('r149','r151','r153','r155','r157')){
 $root=Join-Path $project ('work\event_delivery_consistency_20261030\full-controller-r163\'+$label)
 $inner=Get-Content -LiteralPath (Join-Path $root 'plan-browser\browser-terminal.json') -Raw|ConvertFrom-Json
 $outer=Get-Content -LiteralPath (Join-Path $root 'browser-outer-terminal.json') -Raw|ConvertFrom-Json
 if($inner.chromeExitCode -ne 0 -or -not$inner.normalBrowserClose -or -not$outer.actualDescendantsZero){throw 'BROWSER_NOT_TERMINAL'}
 $browserRoots+=$root;$targets+=Join-Path $root 'plan-browser\chrome-profile'
}
$processes=Get-CimInstance Win32_Process|Where-Object {$_.Name -match '^(pythonw?|node|chrome|java|mysqld|minio|nginx|redis-server)\.exe$'}
foreach($p in $processes){
 $cmd=([string]$p.CommandLine).Replace('/','\')
 foreach($root in @($app,$old,$current,$ui,$uiPrevious,$uiFinal)+$browserRoots){if($cmd.IndexOf($root,[StringComparison]::OrdinalIgnoreCase) -ge 0){throw 'OWN_PROCESS_OR_CODE_REFERENCE_ACTIVE'}}
}
$rows=@();[long]$total=0
foreach($target in $targets){
 $resolved=(Resolve-Path -LiteralPath $target).ProviderPath
 if($resolved -cne $target -or -not$resolved.StartsWith((Join-Path $project 'work')+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'EXACT_WORK_ABSOLUTE_SCOPE_REQUIRED'}
 $a=Get-Item -LiteralPath $target
 while($a){if($a.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'ANCESTOR_REPARSE'};$a=$a.Parent}
 $queue=[Collections.Generic.Queue[string]]::new();$queue.Enqueue($target);[long]$files=0;[long]$bytes=0
 while($queue.Count){foreach($e in Get-ChildItem -LiteralPath ($queue.Dequeue()) -Force){
  if($e.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'CHILD_REPARSE'}
  if($e.PSIsContainer){$queue.Enqueue($e.FullName)}else{$files++;$bytes+=$e.Length}
 }}
 $total+=$bytes;$rows+=[pscustomobject]@{path=$target;files=$files;logicalBytes=$bytes;exactAbsoluteNoReferencesNoReparse=$true}
}
if($total -gt 512MB){throw 'UNEXPECTED_TEMPORARY_SIZE'}
$before=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
foreach($row in $rows){if((Resolve-Path -LiteralPath $row.path).ProviderPath -cne $row.path){throw 'DELETE_TARGET_CHANGED'};Remove-Item -LiteralPath $row.path -Recurse -Force;if(Test-Path -LiteralPath $row.path){throw 'DELETE_NOT_COMPLETED'}}
$after=[IO.DriveInfo]::new('D:\').AvailableFreeSpace
$result=[pscustomobject]@{passed=$true;targets=$rows;removedFiles=($rows|Measure-Object files -Sum).Sum;logicalBytes=$total;observedDFreeDelta=($after-$before);observedChangeNotUniquelyAttributed=$true;candidateR40BundlesCompiledSourcesAndSmallResultsRetained=$true;databaseUploadsAssetsReferenceAndFormalApplicationsRetained=$true;noProcessesTerminated=$true}
$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $output -Encoding utf8
$result|Select-Object passed,removedFiles,logicalBytes,observedDFreeDelta|ConvertTo-Json
