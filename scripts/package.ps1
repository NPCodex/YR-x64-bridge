param([string]$BridgeDirectory='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$version=(Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
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
$backendMetadataPath=Join-Path $BridgeDirectory 'BACKEND.json'
$backendMetadata=Get-Content -LiteralPath $backendMetadataPath -Raw | ConvertFrom-Json
if($backendMetadata.sha256 -ne (Get-FileHash -LiteralPath $backend -Algorithm SHA256).Hash.ToLowerInvariant()){throw 'Backend metadata checksum mismatch'}
$upstreamMetadataPath=Join-Path $BridgeDirectory 'UPSTREAM.json'
$name="YR-MO-DXVK64-Bridge-v$version"
$output=Join-Path $root "dist/$name"
$zip=Join-Path $root "dist/$name.zip"
$checksum=$zip+'.sha256'
foreach($destination in @($output,$zip,$checksum)){if(Test-Path -LiteralPath $destination){throw 'Release output already exists; preserve it before repackaging.'}}
$dist=[IO.Path]::GetFullPath((Join-Path $root 'dist'))
New-Item -ItemType Directory -Path $dist -Force | Out-Null
$staging=Join-Path $dist ('.package-'+[Guid]::NewGuid().ToString('N'))
$stagedOutput=Join-Path $staging $name
$stagedZip=Join-Path $staging "$name.zip"
$stagedChecksum=$stagedZip+'.sha256'
$published=[Collections.Generic.List[string]]::new()
function Remove-OwnedReleasePath([string]$Path){
    $resolved=[IO.Path]::GetFullPath($Path)
    if(!$resolved.StartsWith($dist+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw "Cleanup path outside release directory: $resolved"}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
try{
    New-Item -ItemType Directory -Path (Join-Path $stagedOutput '.yrbridge') -Force | Out-Null
    Copy-Item -LiteralPath $client -Destination (Join-Path $stagedOutput 'd3d9.dll')
    Copy-Item -LiteralPath $bridgeHostPath -Destination (Join-Path $stagedOutput '.yrbridge/YRBridge64.exe')
    Copy-Item -LiteralPath $backend -Destination (Join-Path $stagedOutput '.yrbridge/d3d9vk_x64.dll')
    foreach($relative in @('bridge.conf','.yrbridge/bridge.conf')){Copy-Item -LiteralPath (Join-Path $root 'config/bridge.conf') -Destination (Join-Path $stagedOutput $relative)}
    foreach($file in @('README.md','LICENSE','THIRD_PARTY.md','VERSION')){Copy-Item -LiteralPath (Join-Path $root $file) -Destination $stagedOutput}
    # Provenance travels with the validated runtime, never with a global download cache.
    Copy-Item -LiteralPath $backendMetadataPath -Destination (Join-Path $stagedOutput 'BACKEND.json')
    Copy-Item -LiteralPath $backendMetadataPath -Destination (Join-Path $stagedOutput 'dependencies.json')
    if(Test-Path -LiteralPath $upstreamMetadataPath){Copy-Item -LiteralPath $upstreamMetadataPath -Destination (Join-Path $stagedOutput 'UPSTREAM.json')}
    Copy-Item -LiteralPath (Join-Path $BridgeDirectory 'licenses') -Destination $stagedOutput -Recurse
    Copy-Item -LiteralPath (Join-Path $root 'docs') -Destination $stagedOutput -Recurse
    $hashes=[ordered]@{}
    Get-ChildItem -LiteralPath $stagedOutput -Recurse -Force -File | ForEach-Object {$hashes[$_.FullName.Substring($stagedOutput.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
    if($hashes['.yrbridge/d3d9vk_x64.dll'] -ne $backendMetadata.sha256){throw 'Backend changed during packaging'}
    $hashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stagedOutput 'SHA256.json') -Encoding utf8
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    # ZipFile includes .yrbridge, independent of hidden-file attributes.
    [IO.Compression.ZipFile]::CreateFromDirectory($stagedOutput,$stagedZip,[IO.Compression.CompressionLevel]::Optimal,$false)
    $check=[IO.Compression.ZipFile]::OpenRead($stagedZip)
    try{
        foreach($entry in @('d3d9.dll','.yrbridge/YRBridge64.exe','.yrbridge/d3d9vk_x64.dll','bridge.conf','SHA256.json')){if(!$check.GetEntry($entry)){throw "Missing release entry: $entry"}}
    }finally{$check.Dispose()}
    $digest=(Get-FileHash -LiteralPath $stagedZip -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText($stagedChecksum,"$digest  $name.zip`n")
    # Move only complete, verified outputs into their final names. Moves refuse collisions.
    [IO.Directory]::Move($stagedOutput,$output)
    $published.Add($output)
    [IO.File]::Move($stagedZip,$zip)
    $published.Add($zip)
    [IO.File]::Move($stagedChecksum,$checksum)
    $published.Add($checksum)
}catch{
    foreach($destination in $published){Remove-OwnedReleasePath $destination}
    throw
}finally{
    Remove-OwnedReleasePath $staging
}
Write-Output "Validated release: $zip"
