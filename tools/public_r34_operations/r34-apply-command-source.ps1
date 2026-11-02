$ErrorActionPreference='Stop'
$root='C:\FTP_Root\Zhumadian\Zhumadian_Pending_Visibility_20261102_R34'
$manifest=Join-Path $root 'delivery-manifest.json'
if((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'd6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af'){throw 'R34_TRANSPORT_MANIFEST_DRIFT'}
$m=Get-Content -LiteralPath $manifest -Raw|ConvertFrom-Json
if(@(Get-ChildItem -LiteralPath $root -File -Force).Count -ne 8){throw 'R34_EXACT_EIGHT_FILES_REQUIRED'}
foreach($item in $m.files.PSObject.Properties){$p=Join-Path $root $item.Name;if((Get-Item -LiteralPath $p).Length -ne $item.Value.bytes -or (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Value.sha256){throw 'R34_TRANSPORT_PAYLOAD_DRIFT'}}
Write-Host 'R34_TRANSPORT_EIGHT_FILES_SHA256_MATCHED'
$app='C:\inetpub\wwwroot\Zhumadian\Application'
$identity=Get-Content -LiteralPath (Join-Path $app 'UserData\OriginalServer\installation.json') -Raw|ConvertFrom-Json
$current=Get-Content -LiteralPath (Join-Path $app 'UserData\OriginalServer\current-run.json') -Raw|ConvertFrom-Json
if($identity.databaseUUID -cne $current.databaseUUID -or $identity.releaseId -cne $current.releaseId){throw 'R34_INSTALLED_RUNNING_DATABASE_IDENTITY_MISMATCH'}
$identity=$null;$current=$null
Write-Host 'R34_INSTALLED_RUNNING_DATABASE_IDENTITY_MATCHED_NO_VALUES_RETURNED'
$python=Join-Path $app 'runtime\python\python.exe'
& $python -I -B (Join-Path $root 'deploy_pending_visibility_r34.py')
$code=$LASTEXITCODE
$poolReady=$null
if($code -eq 0){
 $poolText= & $python -I -B -c "import sys,json;from pathlib import Path;app=Path('C:/inetpub/wwwroot/Zhumadian/Application');sys.path.insert(0,str(app/'tools'));import original_public_test_update as m;row=m.owned_ready(app,'5f214688ed3038ecdc75f7cf03fb209f94b28f2233c219c26a9fc46e1dd65b5f');print(json.dumps(m.runtime_pool_ready(app,row)))"
 if($LASTEXITCODE -ne 0){throw 'R34_ADDITIONAL_POOL_READINESS_FAILED'}
 $poolReady=$poolText|ConvertFrom-Json
 if(-not $poolReady.poolPolicyAndExactRuntimeSourcesMatched){throw 'R34_POOL_SOURCES_NOT_MATCHED'}
}
$result=[pscustomobject]@{schema='xnby.public.r34.stage.v1';stage='deployment';exitCode=$code;transportEightSHA256Matched=$true;fixedManifestSHA256='d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af';candidateVersion='R34';poolReadiness=$poolReady;passed=($code -eq 0);actualPublicHTTPSAndLoggedInUIPending=$true;rawManifestAccountsSessionsBusinessCredentialsOrLogsIncluded=$false}
$json=$result|ConvertTo-Json -Compress
$folder=Join-Path $root 'verification'
if(-not(Test-Path -LiteralPath $folder)){New-Item -ItemType Directory -Path $folder|Out-Null}
$json|Set-Content -LiteralPath (Join-Path $folder 'r34-deployment-summary.json') -Encoding UTF8
Set-Clipboard -Value $json
Write-Output $json
