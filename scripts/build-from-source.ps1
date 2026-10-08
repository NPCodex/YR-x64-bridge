param([string]$DxvkDll='', [string]$VcVarsVer='14.29',[string]$UpstreamCommit='418c3a12ef013c64687a01c092e0027b395f91a0')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$vendor=Join-Path $root 'third_party/l4d2-bridge'
Copy-Item -LiteralPath (Join-Path $root 'config/backend.json') -Destination (Join-Path $vendor 'config/backend.json') -Force
& (Join-Path $vendor 'scripts/build_bridge.ps1') -UpstreamCommit $UpstreamCommit -VcVarsVer $VcVarsVer -DxvkDll $DxvkDll
if($LASTEXITCODE -ne 0){throw 'Bridge compilation failed'}
& (Join-Path $vendor 'scripts/test_diagnostics.ps1')
if($LASTEXITCODE -ne 0){throw 'Bridge diagnostics failed'}
& (Join-Path $PSScriptRoot 'package.ps1') -BridgeDirectory (Join-Path $vendor 'dist/l4d2-bridge')
