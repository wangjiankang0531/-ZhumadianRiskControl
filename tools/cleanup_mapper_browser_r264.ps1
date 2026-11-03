$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\Project\Zhumadian\work\event_delivery_consistency_20261030\full-controller-r163'
$taskDocument = 'D:\Project\Zhumadian\Document\Deployment\original_mapper_registration_verified_r264_20261103'
$taskProfiles = New-Object System.Collections.Generic.List[string]
foreach ($taskAttempt in @('r130')) {
    $taskProof = Get-Content -LiteralPath (Join-Path $taskRoot ($taskAttempt + '-outer-terminal.json')) -Raw | ConvertFrom-Json
    if ($taskProof.exitCode -ne 0 -or -not $taskProof.actualDescendantsZeroBeforeClose -or $taskProof.forceTerminationUsed) { throw 'TERMINAL_ZERO_PROOF_REQUIRED' }
    $taskPrep = Join-Path $taskRoot ('prepared-' + $taskAttempt)
    foreach ($taskRestoreName in @('frontend-restored.json','history-runtime-restored.json')) {
        $taskRestore = Get-Content -LiteralPath (Join-Path $taskPrep $taskRestoreName) -Raw | ConvertFrom-Json
        if (-not $taskRestore.passed) { throw 'EXACT_RESTORE_PROOF_REQUIRED' }
    }
    $taskBrowserNames = if ($taskAttempt -eq 'r122') { @('workflow-browser-operator','workflow-browser-operator-disposal','workflow-browser-reviewer-preview','workflow-browser-operator-added','workflow-browser-operator-waiting-parallel-b','workflow-browser-reviewer-after-added','workflow-browser-reviewer-final','workflow-browser-reviewer-handled-readback','workflow-browser-operator-completed-readback') } else { @('plan-browser') }
    foreach ($taskBrowserName in $taskBrowserNames) {
        $taskBrowserRoot = Join-Path (Join-Path $taskRoot $taskAttempt) $taskBrowserName
        $taskBrowserProof = Get-Content -LiteralPath (Join-Path $taskBrowserRoot 'browser-terminal.json') -Raw | ConvertFrom-Json
        $taskNormalBrowserClose = if ($taskAttempt -eq 'r122') { $taskBrowserProof.normalBrowserClosed } else { $taskBrowserProof.normalBrowserClose }
        if (-not $taskNormalBrowserClose -or $taskBrowserProof.chromeExitCode -ne 0 -or $taskBrowserProof.forceTerminationUsed) { throw 'BROWSER_ZERO_REQUIRED' }
        $taskProfiles.Add((Join-Path $taskBrowserRoot 'chrome-profile'))
    }
}
$taskEntries = New-Object System.Collections.Generic.List[object]
foreach ($taskProfile in $taskProfiles) {
    $taskAbsolute = [IO.Path]::GetFullPath($taskProfile)
    if (-not $taskAbsolute.StartsWith($taskRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($taskAbsolute) -ne 'chrome-profile') { throw 'ABSOLUTE_SCOPE_REJECTED' }
    if (-not (Test-Path -LiteralPath $taskAbsolute -PathType Container)) { throw 'PROFILE_MISSING_INSPECT_FIRST' }
    $taskResolved = (Resolve-Path -LiteralPath $taskAbsolute).ProviderPath
    if (-not $taskResolved.Equals($taskAbsolute,[StringComparison]::OrdinalIgnoreCase)) { throw 'PROFILE_RESOLVED_OUTSIDE_EXACT_SCOPE' }
    $taskParent = Get-Item -LiteralPath $taskAbsolute -Force
    while ($null -ne $taskParent -and $taskParent.FullName.StartsWith($taskRoot,[StringComparison]::OrdinalIgnoreCase)) {
        if ($taskParent.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_PARENT_REFUSED' }
        $taskParent = $taskParent.Parent
    }
    $taskQueue = New-Object System.Collections.Generic.Queue[string]
    $taskQueue.Enqueue($taskAbsolute)
    [long]$taskBytes = 0; [long]$taskFiles = 0
    while ($taskQueue.Count -gt 0) {
        foreach ($taskChild in Get-ChildItem -LiteralPath $taskQueue.Dequeue() -Force) {
            if ($taskChild.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_CHILD_REFUSED' }
            if ($taskChild.PSIsContainer) { $taskQueue.Enqueue($taskChild.FullName) } else { $taskFiles++; $taskBytes += $taskChild.Length }
        }
    }
    $taskEntries.Add([pscustomobject]@{ path=$taskAbsolute; fileEntries=$taskFiles; logicalBytes=$taskBytes })
}
$taskLive = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe' OR Name='node.exe' OR Name='java.exe' OR Name='python.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe'" | Where-Object {
    $taskCommand = ($_.CommandLine -replace '\\','/').ToLowerInvariant()
    $taskCommand.Contains('d:/project/zhumadian/_g/application') -or $taskCommand.Contains('full-controller-r163/r130/') -or $taskCommand.Contains('full-controller-r163/r130/') -or $taskCommand.Contains('full-controller-r163/r130/')
})
if ($taskLive.Count -ne 0) { throw 'LIVE_COMPONENT_OR_PROFILE_REFERENCE_REFUSED' }
$taskOriginalRelease = 'e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
if ((Get-FileHash -LiteralPath 'D:\Project\Zhumadian\_g\Application\release-manifest.json' -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskOriginalRelease) { throw 'ORIGINAL_FIXTURE_NOT_RESTORED' }
$taskBefore = (Get-PSDrive -Name D).Free
$taskScope = @{schema='xnby.r264.completed-own-browser-cleanup.v1'; terminalAttempts=@('r130'); profiles=$taskEntries; liveReferences=0; noReparse=$true; dataAssetsSourcesResultsOrUserProfilesIncluded=$false}
$taskScope | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $taskDocument 'own-browser-cleanup-scope.json') -Encoding UTF8
foreach ($taskProfile in $taskProfiles) { Remove-Item -LiteralPath $taskProfile -Recurse -Force }
foreach ($taskProfile in $taskProfiles) { if (Test-Path -LiteralPath $taskProfile) { throw 'OWN_PROFILE_DELETE_NOT_COMPLETE' } }
$taskAfter = (Get-PSDrive -Name D).Free
$taskResult = @{ passed=$true; profilesRemoved=$taskProfiles.Count; fileEntriesRemoved=($taskEntries | Measure-Object -Property fileEntries -Sum).Sum; logicalBytesRemoved=($taskEntries | Measure-Object -Property logicalBytes -Sum).Sum; observedDriveFreeDeltaBytes=($taskAfter-$taskBefore); driveDeltaExclusivelyAttributed=$false; sourceResultsDatabaseAssetsAndUserBrowserKept=$true; processesTerminated=$false }
$taskResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $taskDocument 'own-browser-cleanup-result.json') -Encoding UTF8
$taskResult | ConvertTo-Json -Compress
