param([string]$BridgeDirectory='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$version=(Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
$deps=Get-Content -LiteralPath (Join-Path $root 'dependencies.json') -Raw | ConvertFrom-Json
$cache=Join-Path $root '.cache'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
if(!$BridgeDirectory){throw 'v1.0 requires renamed client and Host. Run scripts/build-from-source.ps1 or pass -BridgeDirectory with a newly built YR runtime.'}
$BridgeDirectory=(Resolve-Path -LiteralPath $BridgeDirectory).Path
$manifest=Get-Content -LiteralPath (Join-Path $BridgeDirectory 'SHA256.json') -Raw | ConvertFrom-Json
foreach($entry in $manifest.PSObject.Properties){
    if((Get-FileHash -LiteralPath (Join-Path $BridgeDirectory $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value){throw "Upstream file checksum mismatch: $($entry.Name)"}
}
function Assert-PE([string]$Path,[int]$Machine){
    $data=[IO.File]::ReadAllBytes($Path)
    if($data.Length -lt 64 -or $data[0] -ne 77 -or $data[1] -ne 90){throw "Invalid PE: $Path"}
    $offset=[BitConverter]::ToInt32($data,60)
    if($offset -lt 0 -or $offset+6 -gt $data.Length -or [BitConverter]::ToUInt32($data,$offset) -ne 17744){throw "Invalid PE header: $Path"}
    if([BitConverter]::ToUInt16($data,$offset+4) -ne $Machine){throw "Wrong architecture: $Path"}
}
$client=Join-Path $BridgeDirectory 'bin/dxvk_d3d9.dll'
$bridgeHostPath=Join-Path $BridgeDirectory 'bin/.yrbridge/YRBridge64.exe'
$backend=Join-Path $BridgeDirectory 'bin/.yrbridge/d3d9vk_x64.dll'
Assert-PE $client 0x14c
Assert-PE $bridgeHostPath 0x8664
Assert-PE $backend 0x8664
$name="YR-MO-DXVK64-Bridge-v$version"
$output=Join-Path $root "dist/$name"
$zip=Join-Path $root "dist/$name.zip"
if((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $zip)){throw 'Release output already exists; preserve it before repackaging.'}
New-Item -ItemType Directory -Path (Join-Path $output '.yrbridge') -Force | Out-Null
Copy-Item -LiteralPath $client -Destination (Join-Path $output 'd3d9.dll')
Copy-Item -LiteralPath $bridgeHostPath -Destination (Join-Path $output '.yrbridge/YRBridge64.exe')
Copy-Item -LiteralPath $backend -Destination (Join-Path $output '.yrbridge/d3d9vk_x64.dll')
foreach($relative in @('bridge.conf','.yrbridge/bridge.conf')){Copy-Item -LiteralPath (Join-Path $root 'config/bridge.conf') -Destination (Join-Path $output $relative)}
foreach($file in @('README.md','LICENSE','THIRD_PARTY.md','VERSION','dependencies.json')){Copy-Item -LiteralPath (Join-Path $root $file) -Destination $output}
if(Test-Path -LiteralPath (Join-Path $BridgeDirectory 'BACKEND.json')){Copy-Item -LiteralPath (Join-Path $BridgeDirectory 'BACKEND.json') -Destination (Join-Path $output 'BACKEND.json')}
if($env:UPSTREAM_COMMIT){@{upstream_commit=$env:UPSTREAM_COMMIT;recipe_commit=$env:GITHUB_SHA;game_validation='Pending'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'UPSTREAM.json'); Copy-Item -LiteralPath (Join-Path $root 'config/backend.json') -Destination (Join-Path $output 'dependencies.json') -Force}
if(Test-Path -LiteralPath (Join-Path $root 'third_party/l4d2-bridge/.deps/gplall/source-backend.json')){Copy-Item -LiteralPath (Join-Path $root 'third_party/l4d2-bridge/.deps/gplall/source-backend.json') -Destination (Join-Path $output 'dependencies.json') -Force}
Copy-Item -LiteralPath (Join-Path $BridgeDirectory 'licenses') -Destination $output -Recurse
Copy-Item -LiteralPath (Join-Path $root 'docs') -Destination $output -Recurse
$hashes=[ordered]@{}
Get-ChildItem -LiteralPath $output -Recurse -Force -File | ForEach-Object {$hashes[$_.FullName.Substring($output.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
$hashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'SHA256.json') -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
# ZipFile includes .yrbridge, independent of hidden-file attributes.
[IO.Compression.ZipFile]::CreateFromDirectory($output,$zip,[IO.Compression.CompressionLevel]::Optimal,$false)
$check=[IO.Compression.ZipFile]::OpenRead($zip)
try{
    foreach($entry in @('d3d9.dll','.yrbridge/YRBridge64.exe','.yrbridge/d3d9vk_x64.dll','bridge.conf','SHA256.json')){if(!$check.GetEntry($entry)){throw "Missing release entry: $entry"}}
}finally{$check.Dispose()}
$digest=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(($zip+'.sha256'),"$digest  $name.zip`n")
Write-Output "Validated release: $zip"
