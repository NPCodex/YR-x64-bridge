param([string]$VcVarsVer='14.29')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$deps=Get-Content -LiteralPath (Join-Path $root 'dependencies.json') -Raw | ConvertFrom-Json
$cache=Join-Path $root '.cache'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
$archive=Join-Path $cache 'dxvk-2.6.1.tar.gz'
if(!(Test-Path -LiteralPath $archive)){Invoke-WebRequest -Uri $deps.dxvk.url -OutFile $archive}
if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $deps.dxvk.sha256){throw 'DXVK checksum mismatch.'}
& tar -xzf $archive -C $cache
if($LASTEXITCODE -ne 0){throw 'DXVK extraction failed.'}
$vendor=Join-Path $root 'third_party/l4d2-bridge'
& (Join-Path $vendor 'scripts/build_bridge.ps1') -DxvkDll (Join-Path $cache 'dxvk-2.6.1/x64/d3d9.dll') -Dxvk32Dll (Join-Path $cache 'dxvk-2.6.1/x32/d3d9.dll') -VcVarsVer $VcVarsVer
if($LASTEXITCODE -ne 0){throw 'Bridge compilation failed.'}
& (Join-Path $PSScriptRoot 'package.ps1') -BridgeDirectory (Join-Path $vendor 'dist/l4d2-bridge')
