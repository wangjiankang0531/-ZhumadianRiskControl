$ErrorActionPreference='Stop'
$root='D:\Project\Zhumadian'
$source=[IO.Path]::GetFullPath('D:\Project\Zhumadian\work\r23gv-r1\Application')
$target=[IO.Path]::GetFullPath('D:\Project\Zhumadian\_b\Application')
foreach($path in @($source,$target)){
 if(-not $path.StartsWith($root+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'PATH_OUTSIDE_PROJECT'}
}
if(Test-Path -LiteralPath (Split-Path -Parent $target)){throw 'SHORT_FIXTURE_ALREADY_EXISTS'}
$proof=Get-Content -LiteralPath 'D:\Project\Zhumadian\work\r23gv-r1\controller-code-prepared.json' -Raw -Encoding UTF8|ConvertFrom-Json
if(-not $proof.readyForShortPathMove){throw 'CODE_NOT_VERIFIED'}
$items=@(Get-Item -LiteralPath $source -Force)+@(Get-ChildItem -LiteralPath $source -Recurse -Force)
if(@($items|Where-Object{$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'REPARSE_REFUSED'}
$active=@(Get-CimInstance Win32_Process|Where-Object{$_.CommandLine -and $_.CommandLine.IndexOf($source,[StringComparison]::OrdinalIgnoreCase) -ge 0})
if($active.Count){throw 'VIEW_IN_USE'}
New-Item -ItemType Directory -Path (Split-Path -Parent $target)|Out-Null
Move-Item -LiteralPath $source -Destination $target
if((Test-Path -LiteralPath $source)-or -not(Test-Path -LiteralPath $target)){throw 'MOVE_NOT_COMPLETE'}
@{schema='xnby.owned-controller-short-fixture.v1';ownedSyntheticFixtureOnly=$true;publicOrFormalInstalled=$false;source=$source;application=$target}|ConvertTo-Json|Set-Content -LiteralPath 'D:\Project\Zhumadian\_b\own-fixture.json' -Encoding UTF8
Write-Output 'OWNED_VERIFIED_PROGRAM_VIEW_MOVED_TO_SHORT_PROJECT_FIXTURE_NO_SERVICES_STARTED'
