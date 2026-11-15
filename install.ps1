# Undertale Hebrew: install, play or remove. Your data.win is never changed: the Hebrew game is a separate file
# (data_he.win) next to it, so starting UNDERTALE from Steam stays English and only -Play starts Hebrew.
#   powershell -ExecutionPolicy Bypass -File install.ps1            # put data_he.win in the game folder
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Play      # start UNDERTALE in Hebrew
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Restore   # remove the Hebrew file (and undo an old in-place install)
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Status
# Saves are shared between English and Hebrew.
param(
    [switch]$Restore,
    [switch]$Status,
    [switch]$Play,
    [string]$GameDir = "C:\Program Files (x86)\Steam\steamapps\common\Undertale"
)
$ErrorActionPreference = "Stop"
$W = $PSScriptRoot
$Orig = Join-Path $W "backup\data.win.orig"
$Heb = Join-Path $W "build\data.win"
$DataWin = Join-Path $GameDir "data.win"
$HebName = "data_he.win"
$Target = Join-Path $GameDir $HebName
$OrigHash = "B718F8223A5BB31979FFEED10BE6140C857B882FC0D0462B89D6287AE38C81C7"  # Steam v1.08 data.win

function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash }

if (-not (Test-Path $DataWin)) { throw "data.win not found in $GameDir" }
$dataOk = (Hash $DataWin) -eq $OrigHash
$hebIn = Test-Path $Target
Write-Output ("data.win: " + $(if ($dataOk) { "original English" } else { "not the original v1.08 file" }))
Write-Output ("Hebrew:   " + $(if ($hebIn) { "installed ($HebName)" } else { "not installed" }))
if ($Status) { exit 0 }

if ($Play) {
    if (-not $hebIn) { throw "Hebrew isn't installed yet. Run install.ps1 first." }
    # Through Steam (it passes the arguments on, but drops quotes, so use the bare file name; Steam starts the game in its folder); started directly, the Steam build restarts itself through Steam.
    $steam = $null
    try { $steam = (Get-ItemProperty "HKCU:\Software\Valve\Steam" -ErrorAction Stop).SteamExe } catch {}
    if ($steam -and (Test-Path $steam)) {
        Start-Process -FilePath $steam -ArgumentList "-applaunch 391540 -game $HebName"
    } else {
        Start-Process -FilePath (Join-Path $GameDir "UNDERTALE.exe") -ArgumentList "-game `"$Target`"" -WorkingDirectory $GameDir
    }
    exit 0
}

if (Get-Process -Name "UNDERTALE" -ErrorAction SilentlyContinue) { throw "Close UNDERTALE first." }

# Undo an install from v0.1.0, which replaced data.win itself.
if (-not $dataOk -and (Test-Path $Orig) -and (Hash $Orig) -eq $OrigHash) {
    $keep = Join-Path $W ("backup\data.win.replaced-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
    Copy-Item $DataWin $keep
    Copy-Item $Orig $DataWin -Force
    Write-Output "Put the original English data.win back (the replaced file is saved as $keep)."
    $dataOk = $true
}

if ($Restore) {
    if ($hebIn) { Remove-Item $Target -Force; Write-Output "Removed $HebName." }
    Write-Output "UNDERTALE is English only now."
    exit 0
}

if (-not $dataOk) { throw "Your data.win isn't the original Steam v1.08 file. In Steam: UNDERTALE > Properties > Installed Files > Verify integrity, then run again." }
if (-not (Test-Path $Heb)) { throw "build\data.win not found. Run setup.ps1 first." }
Copy-Item $Heb $Target -Force
Write-Output "Installed $Target."
Write-Output "Start Hebrew with: powershell -ExecutionPolicy Bypass -File install.ps1 -Play   (Steam still starts English)"
