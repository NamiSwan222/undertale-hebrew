# Builds the Tirgumim launcher pack for Undertale Hebrew (free accounts only: requiresAccount false).
# The pack holds NO game file. It holds a BSDIFF40 patch from the original Steam v1.08 data.win to the Hebrew build,
# plus the font licence. The launcher (0.4.0+) checks the player's data.win hash and writes the Hebrew game to a NEW
# file, data_he.win, next to it (data.win is never changed). Hebrew runs only when the launcher starts the game
# ("activation": Steam -applaunch with -game data_he.win); started from Steam, UNDERTALE stays English.
#   powershell -ExecutionPolicy Bypass -File scripts\make_launcher_pack.ps1 -Version 0.1.0              # build + pack
#   powershell -ExecutionPolicy Bypass -File scripts\make_launcher_pack.ps1 -Version 0.1.0 -SkipBuild   # pack an existing build
# Options: -GameDir "<Undertale folder>" (passed to setup.ps1), -Original/-Hebrew (other input files).
# Needs: everything setup.ps1 needs (your own v1.08 copy, Python + Pillow), and Rust (cargo) for scripts\bsdiff.
# Result: build\undertale-he-<Version>.zip, its SHA-256, and the release tag/asset names.
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$GameDir = "",
    [string]$Original = "",
    [string]$Hebrew = "",
    [switch]$SkipBuild,
    [switch]$AnyOriginal  # tests only: accept an original that isn't the v1.08 file
)
$ErrorActionPreference = "Stop"
$W = Split-Path $PSScriptRoot
$OrigHash = "B718F8223A5BB31979FFEED10BE6140C857B882FC0D0462B89D6287AE38C81C7"  # Steam v1.08 data.win
if (-not $Original) { $Original = Join-Path $W "backup\data.win.orig" }
if (-not $Hebrew) { $Hebrew = Join-Path $W "build\data.win" }
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Version must look like 0.1.0" }
function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash.ToLower() }

# --- the Hebrew build ---
if (-not $SkipBuild) {
    $a = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $W "setup.ps1"), "-NoInstall")
    if ($GameDir) { $a += @("-GameDir", $GameDir) }
    & powershell @a
    if ($LASTEXITCODE -ne 0) { throw "setup.ps1 failed" }
}
if (-not (Test-Path $Original)) { throw "Original data.win not found: $Original" }
if (-not (Test-Path $Hebrew)) { throw "Hebrew data.win not found: $Hebrew" }
$from = Hash $Original; $to = Hash $Hebrew
if ($from -ne $OrigHash.ToLower() -and -not $AnyOriginal) { throw "$Original isn't the original Steam v1.08 data.win" }
if ($from -eq $to) { throw "The Hebrew data.win is the same as the original" }

# --- the patch tool (qbsdiff, the same crate the launcher applies patches with) ---
$Tool = Join-Path $PSScriptRoot "bsdiff\target\release\ut-bsdiff.exe"
if (-not (Test-Path $Tool)) {
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) { throw "Rust (cargo) is needed to build scripts\bsdiff: https://rustup.rs" }
    & cargo build --release --quiet --manifest-path (Join-Path $PSScriptRoot "bsdiff\Cargo.toml")
    if ($LASTEXITCODE -ne 0) { throw "building scripts\bsdiff failed" }
}

# --- stage the pack (build\ is git-ignored) ---
$Stage = Join-Path $W "build\pack"
if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Force (Join-Path $Stage "patches"), (Join-Path $Stage "files\undertale-hebrew") | Out-Null
Copy-Item (Join-Path $W "fonts\src_fontstruct\license.txt") (Join-Path $Stage "files\undertale-hebrew\font-OFL-license.txt")
Copy-Item (Join-Path $W "fonts\src_fontstruct\readme.txt") (Join-Path $Stage "files\undertale-hebrew\font-readme.txt")

Write-Output "Making the patch (a minute or two)..."
$PatchRel = "patches/data.win.bsdiff"
& $Tool diff $Original $Hebrew (Join-Path $Stage $PatchRel)
if ($LASTEXITCODE -ne 0) { throw "ut-bsdiff failed" }

$files = @()
foreach ($f in Get-ChildItem -Recurse -File (Join-Path $Stage "files") | Sort-Object FullName) {
    $rel = $f.FullName.Substring((Join-Path $Stage "files").Length + 1).Replace('\', '/')
    $files += [ordered]@{ path = $rel; sha256 = (Hash $f.FullName); size = $f.Length }
}
$manifest = [ordered]@{
    schema                  = 1
    packId                  = "undertale-he"
    gameId                  = "undertale"
    version                 = $Version
    title                   = "תרגום עברי ל-UNDERTALE"
    authors                 = @("Tirgumim")
    engine                  = "gamemaker"
    minLauncherVersion      = "0.4.0"
    requiresAccount         = $false
    gameVersions            = @([ordered]@{ name = "1.08 (Steam)"; checks = @([ordered]@{ path = "data.win"; sha256 = $from }) })
    allowUnknownGameVersion = $false
    files                   = $files
    patches                 = @([ordered]@{ path = "data.win"; output = "data_he.win"; fromSha256 = $from; toSha256 = $to; size = (Get-Item $Hebrew).Length; patch = $PatchRel })
    activation              = [ordered]@{ mode = "args"; exe = "UNDERTALE.exe"; args = @("-game", "{gameDir}/data_he.win"); workingDir = "{gameDir}"; via = "steam" }
}
$utf8 = New-Object Text.UTF8Encoding $false
[IO.File]::WriteAllText((Join-Path $Stage "tirgumim-pack.json"), ($manifest | ConvertTo-Json -Depth 8), $utf8)

# --- zip with forward-slash entry names (Compress-Archive on PowerShell 5.1 writes backslashes) ---
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$Out = Join-Path $W "build\undertale-he-$Version.zip"
if (Test-Path $Out) { Remove-Item $Out }
$zip = [IO.Compression.ZipFile]::Open($Out, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($f in Get-ChildItem -Recurse -File $Stage | Sort-Object FullName) {
        $rel = $f.FullName.Substring($Stage.Length + 1).Replace('\', '/')
        [void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $f.FullName, $rel, [IO.Compression.CompressionLevel]::Optimal)
    }
} finally { $zip.Dispose() }

Write-Output ""
Write-Output "Pack:    $Out ($([math]::Round((Get-Item $Out).Length / 1MB, 1)) MB)"
Write-Output "SHA-256: $(Hash $Out)"
Write-Output "data.win $from -> $to"
Write-Output "Release: tag undertale-v$Version on NamiSwan222/undertale-hebrew, asset undertale-he-$Version.zip"
