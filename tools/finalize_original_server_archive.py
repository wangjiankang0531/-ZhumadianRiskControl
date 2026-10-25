from pathlib import Path
import argparse,datetime,hashlib,json,os,zipfile
parser=argparse.ArgumentParser(description='Seal the 20261025 original-system payload after two actual isolated normal starts/stops.')
parser.add_argument('--application',type=Path,required=True);parser.add_argument('--qa-application',type=Path,required=True);parser.add_argument('--preparation',type=Path,required=True);parser.add_argument('--source-tools',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args();app=args.application.resolve(strict=True);work=args.source_tools.resolve(strict=True);prep=args.preparation.resolve(strict=True);qa=args.qa_application.resolve(strict=True)
for name in ['j1','j2']:
 r=json.loads((qa/'UserData/OriginalServer/runs'/name/'receipt.json').read_bytes());assert r['normalOwnedShutdown'] and r['allOwnedChildrenExited'] and not r['forcedJobClosureComponents'] and r['platformContextClosed'] and r['businessContextClosed']
old=json.loads((qa/'release-manifest.json').read_bytes());files={}
source_map={rel:qa/rel for rel in old['controllerFiles']}
source_map.update({'tools/install_original_server_ingress.py':work/'install_original_server_ingress.py','tools/original_iis_cutover.py':work/'original_iis_cutover.py'})
for rel,p in source_map.items():files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(files[rel]==h for rel,h in old['controllerFiles'].items())
manifest=dict(old,controllerFiles=files,isolatedStartupAndRestartVerified=True,authenticatedBusinessOperationsVerified=False,fullCloneReady=False)
manifest.pop('originalBackendQAComplete',None)
data=json.dumps(manifest,indent=2).encode('utf-8');manifest_sha=hashlib.sha256(data).hexdigest()
folder=prep/'ZhumadianOriginal_Private_20261025';assert not folder.exists();folder.mkdir()
archive=prep/'original-server-payload.pending.zip';target=folder/'ZhumadianOriginal_20261025.zip';assert not target.exists()
with zipfile.ZipFile(archive,'a',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 names=set(z.namelist())
 for rel,p in source_map.items():assert 'Application/'+rel not in names;z.writestr('Application/'+rel,p.read_bytes())
 assert 'Application/release-manifest.json' not in names;z.writestr('Application/release-manifest.json',data)
 for name,tool,extra in [('Start_Original_Server.cmd','serve_original_server_release.py',''),('Deploy_Original_Server.cmd','install_original_server_ingress.py',''),('Rollback_Original_Server.cmd','install_original_server_ingress.py',' --rollback')]:
  text='@echo off\r\n"%~dp0runtime\\python\\python.exe" -I -B "%~dp0tools\\'+tool+'" --application "%~dp0." --release-manifest-sha256 '+manifest_sha+extra+'\r\nif errorlevel 1 pause\r\n'
  z.writestr('Application/'+name,text.encode('ascii'))
 osize=sum(i.file_size for i in z.infolist());assert osize<3*1024**3
os.replace(archive,target)
with target.open('rb') as f:archive_sha=hashlib.file_digest(f,'sha256').hexdigest()
bootstrap=r'''$ErrorActionPreference = 'Stop'
$archiveName = 'ZhumadianOriginal_20261025.zip'
$archiveSha = '__ARCHIVE_SHA__'
$manifestSha = '__MANIFEST_SHA__'
$root = 'C:\Zdm'
$application = Join-Path $root 'Application'
$oldIis = 'C:\FTP_Root\Zhumadian\ZhumadianBusiness_0.8.7_public_1\iis\web.config'
if (-not (Test-Path -LiteralPath $oldIis -PathType Leaf)) { throw 'Expected existing server IIS application is missing. No changes made.' }
if ((Get-PSDrive -Name C).Free -lt 12GB) { throw 'At least 12 GiB free on C is required.' }
$net = (Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full' -Name Release).Release
if ($net -lt 378389) { throw 'Existing .NET 4.5 or later is required. No IIS files changed.' }
$iisHostFile = Join-Path $env:SystemRoot 'System32\inetsrv\config\applicationHost.config'
$iisHost = New-Object System.Xml.XmlDocument
$iisHost.Load($iisHostFile)
if (-not (Test-Path -LiteralPath (Join-Path $env:SystemRoot 'System32\inetsrv\iiswsock.dll')) -or -not $iisHost.SelectSingleNode('/configuration/system.webServer/globalModules/add[@name="WebSocketModule"]')) { throw 'Existing IIS WebSocket feature is required. No roles or IIS files changed.' }
if (Test-Path -LiteralPath $root) {
  if ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Installation root must not redirect.' }
} else { New-Item -ItemType Directory -Path $root | Out-Null }
if (-not (Test-Path -LiteralPath $application)) {
  $archive = Join-Path $PSScriptRoot $archiveName
  if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ine $archiveSha) { throw 'Archive SHA256 mismatch. No IIS files changed.' }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $stage = Join-Path $root ('.pending-' + [Guid]::NewGuid().ToString())
  New-Item -ItemType Directory -Path $stage | Out-Null
  $zip = [IO.Compression.ZipFile]::OpenRead($archive)
  try {
    $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    [long]$expanded = 0
    foreach ($entry in $zip.Entries) {
      $entryName = $entry.FullName
      if (-not $entryName.StartsWith('Application/') -or $entryName.Contains('\') -or $entryName.Contains(':') -or ($entryName.Split('/') -contains '..') -or -not $seen.Add($entryName)) { throw 'Unsafe or duplicate archive member.' }
      $expanded += $entry.Length
      if ($expanded -gt 3GB) { throw 'Expanded archive bound exceeded.' }
      $destination = [IO.Path]::GetFullPath((Join-Path $stage $entryName))
      if (-not $destination.StartsWith($stage + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive target outside owned stage.' }
    }
  } finally { $zip.Dispose() }
  [IO.Compression.ZipFile]::ExtractToDirectory($archive, $stage)
  $stagedApplication = [IO.Path]::GetFullPath((Join-Path $stage 'Application'))
  if (-not $stagedApplication.StartsWith($root + '\.pending-', [StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFullPath($application) -ine 'C:\Zdm\Application' -or (Test-Path -LiteralPath $application)) { throw 'Unexpected installation move target.' }
  if ((Get-FileHash -LiteralPath (Join-Path $stagedApplication 'release-manifest.json') -Algorithm SHA256).Hash -ine $manifestSha) { throw 'Extracted release manifest mismatch.' }
  Move-Item -LiteralPath $stagedApplication -Destination $application
  [IO.Directory]::Delete($stage)
}
if ((Get-Item -LiteralPath $application -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Application path must not redirect.' }
if ((Get-FileHash -LiteralPath (Join-Path $application 'release-manifest.json') -Algorithm SHA256).Hash -ine $manifestSha) { throw 'Existing application belongs to a different release.' }
& (Join-Path $application 'runtime\python\python.exe') -I -B (Join-Path $application 'tools\install_original_server_ingress.py') --application $application --release-manifest-sha256 $manifestSha
if ($LASTEXITCODE -ne 0) { throw 'Original server deployment failed. Inspect C:\Zdm\Application\UserData\OriginalDeployment. Existing IIS is retained or restored.' }
Write-Host 'Server deployment finished. External PC/H5 and original user login checks remain required.'
'''.replace('__ARCHIVE_SHA__',archive_sha).replace('__MANIFEST_SHA__',manifest_sha)
(folder/'Deploy_Original_20261025.ps1').write_text(bootstrap,encoding='ascii',newline='\r\n')
(folder/'Deploy_Original_20261025.cmd').write_bytes(b'@echo off\r\n"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -NonInteractive -File "%~dp0Deploy_Original_20261025.ps1"\r\nif errorlevel 1 pause\r\n')
# Clear all HTTP handlers and disallow every extension in this owned transfer folder.
(folder/'web.config').write_text('<?xml version="1.0"?><configuration><system.webServer><handlers><clear /></handlers><security><requestFiltering><fileExtensions allowUnlisted="false"><clear /></fileExtensions></requestFiltering></security></system.webServer></configuration>',encoding='ascii')
receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'releaseId':manifest['releaseId'],'archive':str(target),'archiveBytes':target.stat().st_size,'archiveSHA256':archive_sha,'releaseManifestSHA256':manifest_sha,'controllerFiles':len(files),'allBackendControllerFilesMatchTwoActualQARuns':True,'isolatedStartupAndRestartVerified':True,'installerSixFileTransactionTestsVerified':True,'iisRuntimeVerified':False,'authenticatedBusinessOperationsVerified':False,'publicDeployed':False,'transferFolderMustDenyHTTPBeforePrivateUpload':True}
(prep/'final-release.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt),flush=True)
