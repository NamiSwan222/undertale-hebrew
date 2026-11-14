# Undertale Hebrew: install or restore.
#   powershell -ExecutionPolicy Bypass -File install.ps1            # install the Hebrew data.win
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Restore   # put the original English data.win back
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Status    # show which version is installed
# Close the game first. Only data.win is changed; your save files are not touched
# (the Hebrew build uses the same save folder, so saves carry over in both directions).
param(
    [switch]$Restore,
    [switch]$Status,
    [string]$GameDir = "C:\Program Files (x86)\Steam\steamapps\common\Undertale"
)
$ErrorActionPreference = "Stop"
$W = $PSScriptRoot
$Orig = Join-Path $W "backup\data.win.orig"
$Heb = Join-Path $W "build\data.win"
$Target = Join-Path $GameDir "data.win"
$OrigHash = "B718F8223A5BB31979FFEED10BE6140C857B882FC0D0462B89D6287AE38C81C7"  # Steam v1.08 data.win

function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash }

if (-not (Test-Path $Target)) { throw "data.win not found in $GameDir" }
$cur = Hash $Target
$state = if ($cur -eq $OrigHash) { "original English" } elseif ((Test-Path $Heb) -and $cur -eq (Hash $Heb)) { "Hebrew (current build)" } else { "unknown / other version" }
Write-Output "Installed data.win: $state"
if ($Status) { exit 0 }

if (Get-Process -Name "UNDERTALE" -ErrorAction SilentlyContinue) { throw "Close UNDERTALE first." }

# make sure we always hold a copy of the original
if (-not (Test-Path $Orig)) {
    if ($cur -ne $OrigHash) { throw "No original backup and the installed data.win isn't the original. Verify the game files in Steam first." }
    New-Item -ItemType Directory -Force (Split-Path $Orig) | Out-Null
    Copy-Item $Target $Orig
}
if ((Hash $Orig) -ne $OrigHash) { throw "backup\data.win.orig doesn't match the original v1.08 hash" }
# never lose an unknown data.win (e.g. another mod)
if ($state -eq "unknown / other version") {
    $keep = Join-Path $W ("backup\data.win.replaced-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
    Copy-Item $Target $keep
    Write-Output "Saved the unknown data.win to $keep"
}

if ($Restore) {
    Copy-Item $Orig $Target -Force
    Write-Output "Restored the original English data.win."
} else {
    if (-not (Test-Path $Heb)) { throw "build\data.win not found. Run scripts\build.sh first." }
    Copy-Item $Heb $Target -Force
    Write-Output "Installed the Hebrew data.win. (Steam 'Verify integrity of game files' also restores English.)"
}
Write-Output ("Now: " + $(if ((Hash $Target) -eq $OrigHash) { "original English" } else { "Hebrew" }))
