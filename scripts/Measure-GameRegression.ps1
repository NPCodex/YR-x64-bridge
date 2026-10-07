param([Parameter(Mandatory=$true)][string]$Label,[Parameter(Mandatory=$true)][string]$Map,[int]$Rounds=3,[string]$OutputDirectory='regression-results')
$ErrorActionPreference='Stop'
if($Rounds -lt 1){throw 'Rounds must be positive'}
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$session=Get-Date -Format 'yyyyMMdd-HHmmss'
$csvPath=Join-Path (Resolve-Path $OutputDirectory).Path "$session-results.csv"
$samplePath=Join-Path (Resolve-Path $OutputDirectory).Path "$session-memory.csv"
$folder=(Resolve-Path $OutputDirectory).Path
Write-Host 'Use the same map, factions, resolution and Steam overlay setting for all versions.'
Write-Host 'Times include your manual confirmation delay. Run without performance logging for timing comparisons.'
foreach($round in 1..$Rounds){
  foreach($scenario in @('load-map','save-and-load','change-map')){
    Read-Host "Prepare $scenario round $round. Press Enter immediately BEFORE starting the action" | Out-Null
    $job=Start-Job -ArgumentList $samplePath,$round,$scenario -ScriptBlock {
      param($path,$round,$scenario)
      while($true){
        $rows=Get-Process gamemd,YRBridge64 -ErrorAction SilentlyContinue | ForEach-Object {
          [pscustomobject]@{time=(Get-Date -Format o);round=$round;scenario=$scenario;name=$_.ProcessName;pid=$_.Id;working_set=$_.WorkingSet64;private_bytes=$_.PrivateMemorySize64;cpu_seconds=$_.CPU;responding=$_.Responding}
        }
        if($rows){$rows | Export-Csv -LiteralPath $path -Append -NoTypeInformation -Encoding utf8}
        Start-Sleep -Seconds 1
      }
    }
    $timer=[Diagnostics.Stopwatch]::StartNew()
    try{
      $result=Read-Host 'When playable, press Enter. If failed, enter fail'
      $timer.Stop()
      [pscustomobject]@{session=$session;label=$Label;map=$Map;round=$round;scenario=$scenario;seconds=$timer.Elapsed.TotalSeconds;result=$(if($result -eq 'fail'){'fail'}else{'pass'})} | Export-Csv -LiteralPath $csvPath -Append -NoTypeInformation -Encoding utf8
    }finally{Stop-Job $job;Receive-Job $job -ErrorAction SilentlyContinue | Out-Null;Remove-Job $job}
  }
}
Write-Host "Saved $csvPath and $samplePath"
Write-Host 'Record cold/warm cache and test settings beside these results. Copy yr-bridge-performance-*.log into the result folder for diagnostic runs.'
