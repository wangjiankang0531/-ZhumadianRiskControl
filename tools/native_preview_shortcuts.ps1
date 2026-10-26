param(
    [Parameter(Mandatory=$true)][string]$BundleRoot,
    [Parameter(Mandatory=$true)][string]$ResourceRoot,
    [Parameter(Mandatory=$true)][string]$ProjectPath,
    [Parameter(Mandatory=$true)][string]$StateRoot,
    [Parameter(Mandatory=$true)][string]$ReceiptPath
)
$ErrorActionPreference = 'Stop'
$previewBundle = (Resolve-Path -LiteralPath $BundleRoot).ProviderPath
$previewResources = (Resolve-Path -LiteralPath $ResourceRoot).ProviderPath
$previewProject = (Resolve-Path -LiteralPath $ProjectPath).ProviderPath
$previewState = (Resolve-Path -LiteralPath $StateRoot).ProviderPath
$previewEditor = Join-Path $previewBundle 'xnby_zmd_editor.exe'
$previewPython = Join-Path $previewResources 'runtime\python\python.exe'
$previewServer = Join-Path $previewBundle 'serve_native_preview.py'
foreach ($previewFile in @($previewEditor,$previewPython,$previewServer,$previewProject)) {
    if (-not (Test-Path -LiteralPath $previewFile -PathType Leaf)) { throw 'Required preview file is missing' }
}
function ConvertTo-PreviewArgument([string]$Value) {
    if ($Value.Length -gt 0 -and $Value -notmatch '[\s"]') { return $Value }
    $quoted = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $quoted = [regex]::Replace($quoted, '(\\+)$', '$1$1')
    return '"' + $quoted + '"'
}
$previewEditorArgs = @('--editor-static-preview','--zhumadian-view=close',('--layers='+$previewProject),('--stats='+(Join-Path $previewState 'editor-startup.json')))
$previewWebArgs = @('-I','-B',$previewServer,'--bundle',$previewBundle,'--resources',$previewResources,'--layers',$previewProject,'--state',(Join-Path $previewState 'web-service.json'))
$previewStopArgs = @('-I','-B',$previewServer,'--stop','--state',(Join-Path $previewState 'web-service.json'))
$previewDefinitions = @(
    @{Name='1_编辑图层（基础地景体验）.lnk';Target=$previewEditor;Arguments=$previewEditorArgs},
    @{Name='2_网页查看当前图层.lnk';Target=$previewPython;Arguments=$previewWebArgs},
    @{Name='3_停止网页查看.lnk';Target=$previewPython;Arguments=$previewStopArgs}
)
$previewShell = New-Object -ComObject WScript.Shell
$previewReceipts = @()
foreach ($definition in $previewDefinitions) {
    $previewLinkPath = Join-Path $previewBundle $definition.Name
    $previewArguments = ($definition.Arguments | ForEach-Object { ConvertTo-PreviewArgument $_ }) -join ' '
    $previewLink = $previewShell.CreateShortcut($previewLinkPath)
    $previewLink.TargetPath = $definition.Target
    $previewLink.Arguments = $previewArguments
    $previewLink.WorkingDirectory = $previewResources
    $previewLink.WindowStyle = 1
    $previewLink.IconLocation = $previewEditor+',0'
    $previewLink.Save()
    $previewRead = $previewShell.CreateShortcut($previewLinkPath)
    if ($previewRead.TargetPath -ne $definition.Target -or $previewRead.Arguments -ne $previewArguments -or $previewRead.WorkingDirectory -ne $previewResources) { throw 'Shortcut read-back mismatch' }
    $previewReceipts += [pscustomobject]@{Name=$definition.Name;TargetPath=$previewRead.TargetPath;Arguments=$previewRead.Arguments;WorkingDirectory=$previewRead.WorkingDirectory}
}
$previewReceipts | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReceiptPath -Encoding utf8
