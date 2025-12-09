# MAGATFAIRY - Simple Reliable Monitor
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "MAGATFAIRY Monitor"

$rootDir = "D:\rawdata\GMR61@GMR61"
$outputDir = "D:\magatfairy\exports"  
$logFile = "D:\magatfairy\live.log"

# Clean
Remove-Item $logFile -Force -ErrorAction SilentlyContinue
Remove-Item "$outputDir\*.h5" -Force -ErrorAction SilentlyContinue
Remove-Item "$outputDir\.progress.json" -Force -ErrorAction SilentlyContinue

$totalExp = (Get-ChildItem "$rootDir\*\matfiles\*.mat").Count

Write-Host "MAGATFAIRY CONVERSION" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Experiments: $totalExp"
Write-Host "Starting..."
Write-Host ""

# Start Python with output going to log file
$cmd = "cd D:\magatfairy; python -u -m cli.magatfairy convert batch --root-dir `"$rootDir`" --output-dir `"$outputDir`" 2>&1 | Tee-Object -FilePath `"$logFile`""
Start-Process powershell -ArgumentList "-Command", $cmd -WindowStyle Hidden

Start-Sleep 2
$start = Get-Date

# Monitor loop
while ($true) {
    $elapsed = (Get-Date) - $start
    $h5Count = (Get-ChildItem "$outputDir\*.h5" -ErrorAction SilentlyContinue).Count
    
    # Get log content
    $lines = @()
    if (Test-Path $logFile) {
        $lines = Get-Content $logFile -Tail 50 -ErrorAction SilentlyContinue
    }
    
    # Parse state
    $currentExp = ""
    $currentTrack = ""
    $trackTotal = 0
    foreach ($l in $lines) {
        if ($l -match "Exporting:\s*(\S+)") { $currentExp = $Matches[1] }
        if ($l -match "Track\s*(\d+)/(\d+)") { $currentTrack = $Matches[1]; $trackTotal = $Matches[2] }
        if ($l -match "\[SUCCESS\]") { $currentExp = ""; $currentTrack = "" }
    }
    
    # Display
    Clear-Host
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " MAGATFAIRY LIVE MONITOR                          Elapsed: $("{0:hh\:mm\:ss}" -f $elapsed)" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Collection progress
    $pct = [math]::Round(($h5Count / $totalExp) * 100)
    $bar = ("#" * [math]::Floor(50 * $h5Count / $totalExp)) + ("." * (50 - [math]::Floor(50 * $h5Count / $totalExp)))
    Write-Host " COLLECTION: [$bar] $h5Count/$totalExp ($pct%)" -ForegroundColor $(if($h5Count -gt 0){"Green"}else{"Yellow"})
    Write-Host ""
    
    # Current experiment
    if ($currentExp) {
        Write-Host " CURRENT: $currentExp" -ForegroundColor Magenta
        if ($currentTrack -and $trackTotal -gt 0) {
            $tpct = [math]::Round(([int]$currentTrack / [int]$trackTotal) * 100)
            $tbar = ("#" * [math]::Floor(50 * [int]$currentTrack / [int]$trackTotal)) + ("." * (50 - [math]::Floor(50 * [int]$currentTrack / [int]$trackTotal)))
            Write-Host " TRACKS:  [$tbar] $currentTrack/$trackTotal ($tpct%)" -ForegroundColor Cyan
        }
    } else {
        Write-Host " CURRENT: (loading next...)" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Console output
    Write-Host " CONSOLE OUTPUT:" -ForegroundColor DarkGray
    Write-Host " ---------------" -ForegroundColor DarkGray
    $recent = $lines | Select-Object -Last 20
    foreach ($l in $recent) {
        $c = "Gray"
        if ($l -match "\[OK\]|\[SUCCESS\]") { $c = "Green" }
        elseif ($l -match "ERROR|FAIL|Exception") { $c = "Red" }
        elseif ($l -match "Track \d+") { $c = "Cyan" }
        elseif ($l -match "Exporting:") { $c = "Magenta" }
        elseif ($l -match "Loading|Loaded") { $c = "DarkCyan" }
        $disp = if ($l.Length -gt 76) { $l.Substring(0,73) + "..." } else { $l }
        Write-Host " $disp" -ForegroundColor $c
    }
    
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    
    # Check if done
    if ($h5Count -eq $totalExp) {
        Write-Host ""
        Write-Host " COMPLETE! All $totalExp experiments converted." -ForegroundColor Green
        Write-Host " Total time: $("{0:hh\:mm\:ss}" -f $elapsed)" -ForegroundColor White
        break
    }
    
    # Check if process died
    $pyProc = Get-Process python* -ErrorAction SilentlyContinue
    if (-not $pyProc -and $h5Count -lt $totalExp) {
        Write-Host ""
        Write-Host " ERROR: Python process died! Check live.log for errors." -ForegroundColor Red
        break
    }
    
    Start-Sleep 1
}

Write-Host ""
Write-Host "Press any key..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
