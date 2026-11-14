# Builds the Tirgumim launcher pack for Undertale Hebrew.
# The pack holds NO game file: only a binary patch (bsdiff) from the original Steam v1.08 data.win to the Hebrew
# build, plus the font licence. The launcher checks the player's data.win hash, backs it up and applies the patch.
#   powershell -ExecutionPolicy Bypass -File scripts\make_launcher_pack.ps1 -Version 0.1.0 [-GameDir "<Undertale folder>"] [-LauncherDir "D:\AIStuff\Hebrew Launcher"]
# Needs: everything setup.ps1 needs (your own v1.08 copy, Python + Pillow), and the launcher repo with
# make-pack patch support (manifest "patches", format bsdiff40). Result: build\undertale-he-<Version>.zip
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$GameDir = "",
    [string]$LauncherDir = "D:\AIStuff\Hebrew Launcher",
    [switch]$SkipBuild
)
$ErrorActionPreference = "Stop"
$W = Split-Path $PSScriptRoot
$OrigHash = "B718F8223A5BB31979FFEED10BE6140C857B882FC0D0462B89D6287AE38C81C7"  # Steam v1.08 data.win
$Orig = Join-Path $W "backup\data.win.orig"
$Heb = Join-Path $W "build\data.win"
function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash }

if (-not $SkipBuild) {
    $a = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $W "setup.ps1"), "-NoInstall")
    if ($GameDir) { $a += @("-GameDir", $GameDir) }
    & powershell @a
    if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed" }
}
if (-not (Test-Path $Orig) -or (Hash $Orig) -ne $OrigHash) { throw "backup\data.win.orig is missing or isn't the original v1.08 file" }
if (-not (Test-Path $Heb)) { throw "build\data.win not found" }
if ((Hash $Heb) -eq $OrigHash) { throw "build\data.win is the original file; the build didn't change anything" }

# Stage the pack folder under build\ (git-ignored).
$Stage = Join-Path $W "build\pack"
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
$Lic = Join-Path $Stage "files\undertale-hebrew"
New-Item -ItemType Directory -Force $Lic | Out-Null
Copy-Item (Join-Path $W "fonts\src_fontstruct\license.txt") (Join-Path $Lic "font-OFL-license.txt")
Copy-Item (Join-Path $W "fonts\src_fontstruct\readme.txt") (Join-Path $Lic "font-readme.txt")

$cfg = [ordered]@{
    packId                   = "undertale-he"
    gameId                   = "undertale"
    version                  = $Version
    title                    = "תרגום עברי ל-UNDERTALE"
    authors                  = @("Tirgumim")
    engine                   = "gamemaker"
    minLauncherVersion       = "0.3.0"
    requiresAccount          = $false
    gameVersions             = @(@{ name = "1.08 (Steam)"; checks = @(@{ path = "data.win"; sha256 = $OrigHash.ToLower() }) })
    allowUnknownGameVersion  = $false
    filesDir                 = "files"
    patches                  = @(@{ path = "data.win"; from = $Orig; to = $Heb })
}
$CfgPath = Join-Path $Stage "pack.config.json"
[IO.File]::WriteAllText($CfgPath, ($cfg | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding $false))

$Out = Join-Path $W "build\undertale-he-$Version.zip"
Push-Location $LauncherDir
try {
    & npm run make-pack -- $CfgPath --out $Out
    if ($LASTEXITCODE -ne 0) { throw "make-pack failed (does this launcher version support patches?)" }
} finally { Pop-Location }

Write-Output ""
Write-Output "Pack: $Out"
Write-Output "SHA-256: $(Hash $Out)"
Write-Output "Release: tag undertale-v$Version on NamiSwan222/undertale-hebrew, asset undertale-he-$Version.zip"
