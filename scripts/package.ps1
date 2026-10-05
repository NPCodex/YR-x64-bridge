param([string]$BridgeDirectory='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$version=(Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
$deps=Get-Content -LiteralPath (Join-Path $root 'dependencies.json') -Raw | ConvertFrom-Json
$cache=Join-Path $root '.cache'
New-Item -ItemType Directory -Path $cache -Force | Out-Null
if(!$BridgeDirectory){
    $archive=Join-Path $cache 'bridge-v1.1.zip'
    if(!(Test-Path -LiteralPath $archive)){Invoke-WebRequest -Uri $deps.bridge.url -OutFile $archive}
    if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $deps.bridge.sha256){throw 'Upstream ZIP checksum mismatch. Preserve and inspect the archive.'}
    $BridgeDirectory=Join-Path $cache 'bridge-v1.1'
    if(!(Test-Path -LiteralPath $BridgeDirectory)){Expand-Archive -LiteralPath $archive -DestinationPath $BridgeDirectory}
}
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
$bridgeHostPath=Join-Path $BridgeDirectory 'bin/.l4d2bridge/L4D2Bridge64.exe'
$backend=Join-Path $BridgeDirectory 'bin/.l4d2bridge/d3d9vk_x64.dll'
Assert-PE $client 0x14c
Assert-PE $bridgeHostPath 0x8664
Assert-PE $backend 0x8664
$name="YR-MO-DXVK64-Bridge-v$version"
$output=Join-Path $root "dist/$name"
$zip=Join-Path $root "dist/$name.zip"
if((Test-Path -LiteralPath $output) -or (Test-Path -LiteralPath $zip)){throw 'Release output already exists; preserve it before repackaging.'}
New-Item -ItemType Directory -Path (Join-Path $output '.l4d2bridge') -Force | Out-Null
Copy-Item -LiteralPath $client -Destination (Join-Path $output 'd3d9.dll')
Copy-Item -LiteralPath $bridgeHostPath -Destination (Join-Path $output '.l4d2bridge/L4D2Bridge64.exe')
Copy-Item -LiteralPath $backend -Destination (Join-Path $output '.l4d2bridge/d3d9vk_x64.dll')
foreach($relative in @('bridge.conf','.l4d2bridge/bridge.conf')){Copy-Item -LiteralPath (Join-Path $root 'config/bridge.conf') -Destination (Join-Path $output $relative)}
foreach($file in @('README.md','LICENSE','THIRD_PARTY.md','VERSION','dependencies.json')){Copy-Item -LiteralPath (Join-Path $root $file) -Destination $output}
Copy-Item -LiteralPath (Join-Path $root 'licenses') -Destination $output -Recurse
Copy-Item -LiteralPath (Join-Path $root 'docs') -Destination $output -Recurse
$hashes=[ordered]@{}
Get-ChildItem -LiteralPath $output -Recurse -Force -File | ForEach-Object {$hashes[$_.FullName.Substring($output.Length+1).Replace('\','/')]=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
$hashes | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $output 'SHA256.json') -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
# ZipFile includes .l4d2bridge, independent of hidden-file attributes.
[IO.Compression.ZipFile]::CreateFromDirectory($output,$zip,[IO.Compression.CompressionLevel]::Optimal,$false)
$check=[IO.Compression.ZipFile]::OpenRead($zip)
try{
    foreach($entry in @('d3d9.dll','.l4d2bridge/L4D2Bridge64.exe','.l4d2bridge/d3d9vk_x64.dll','bridge.conf','SHA256.json')){if(!$check.GetEntry($entry)){throw "Missing release entry: $entry"}}
}finally{$check.Dispose()}
$digest=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText(($zip+'.sha256'),"$digest  $name.zip`n")
Write-Output "Validated release: $zip"
