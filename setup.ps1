# Undertale Hebrew: build the Hebrew data.win from YOUR OWN copy of UNDERTALE (Steam v1.08), then install it.
#   powershell -ExecutionPolicy Bypass -File setup.ps1                  # build + install
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -NoInstall       # build only (result: build\data.win)
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -GameDir "D:\SteamLibrary\steamapps\common\Undertale"
# Needs: Windows, Python 3 (python on PATH) with Pillow, internet once (downloads UndertaleModTool CLI 0.9.2.0
# from its official GitHub release). No game files come with this repo: everything is made from your copy.
param(
    [string]$GameDir = "",
    [switch]$NoInstall
)
$ErrorActionPreference = "Stop"
$W = $PSScriptRoot
$OrigHash = "B718F8223A5BB31979FFEED10BE6140C857B882FC0D0462B89D6287AE38C81C7"  # Steam v1.08 data.win
$UtmtUrl = "https://github.com/UnderminersTeam/UndertaleModTool/releases/download/0.9.2.0/UTMT_CLI_v0.9.2.0-Windows.zip"
$UtmtHash = "E7573E45D107BE34F81F955C6E4AFC3C7C8F2628E5A6F307A871E3825B3DFB40"
function Hash($p) { (Get-FileHash -Algorithm SHA256 $p).Hash }
function Step($t) { Write-Output ""; Write-Output "== $t" }

# --- find the game ---
function Find-Game {
    $cands = @()
    foreach ($k in @("HKCU:\Software\Valve\Steam", "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam")) {
        try { $p = (Get-ItemProperty $k -ErrorAction Stop); if ($p.SteamPath) { $cands += $p.SteamPath }; if ($p.InstallPath) { $cands += $p.InstallPath } } catch {}
    }
    $libs = @()
    foreach ($s in $cands) {
        $libs += $s
        $vdf = Join-Path $s "steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) { $libs += $m.Groups[1].Value -replace '\\\\', '\' }
        }
    }
    $libs += "C:\Program Files (x86)\Steam"
    foreach ($l in $libs) {
        $d = Join-Path $l "steamapps\common\Undertale"
        if (Test-Path (Join-Path $d "data.win")) { return $d }
    }
    return $null
}
if (-not $GameDir) { $GameDir = Find-Game }
if (-not $GameDir -or -not (Test-Path (Join-Path $GameDir "data.win"))) { throw "UNDERTALE not found. Run again with -GameDir `"<folder with data.win>`"." }
Write-Output "Game folder: $GameDir"

# --- python + Pillow ---
Step "Checking Python"
$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { throw "Python 3 is not on PATH. Install it from python.org (tick 'Add python.exe to PATH') and run again." }
# exit code only: with "Stop", PowerShell 5.1 turns redirected stderr of a native command into a fatal error
& cmd /c "python -c ""import PIL"" >nul 2>&1"
if ($LASTEXITCODE -ne 0) { Write-Output "Installing Pillow..."; & python -m pip install --user pillow; if ($LASTEXITCODE -ne 0) { throw "pip install pillow failed" } }
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONWARNINGS = "ignore"

# --- UndertaleModTool CLI ---
$Tools = Join-Path $W "tools"; $Utmt = Join-Path $Tools "utmt"; $Cli = Join-Path $Utmt "UndertaleModCli.exe"
if (-not (Test-Path $Cli)) {
    Step "Getting UndertaleModTool CLI 0.9.2.0"
    New-Item -ItemType Directory -Force $Tools | Out-Null
    $zip = Join-Path $Tools "UTMT_CLI_v0.9.2.0-Windows.zip"
    if (-not (Test-Path $zip)) {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $UtmtUrl -OutFile $zip -UseBasicParsing
    }
    if ((Hash $zip) -ne $UtmtHash) { Remove-Item $zip; throw "UndertaleModTool download has an unexpected checksum; try again." }
    Expand-Archive -Path $zip -DestinationPath $Utmt -Force
    if (-not (Test-Path $Cli)) { $f = Get-ChildItem $Utmt -Recurse -Filter UndertaleModCli.exe | Select-Object -First 1; if ($f) { $Cli = $f.FullName } else { throw "UndertaleModCli.exe not found in the download" } }
}
$Empty = Join-Path $Tools "empty.txt"; Set-Content -Path $Empty -Value "" -Encoding ascii
function Utmt([string[]]$a, [string]$log) {
    $p = Start-Process -FilePath $Cli -ArgumentList $a -WorkingDirectory (Split-Path $Cli) -NoNewWindow -Wait -PassThru `
        -RedirectStandardInput $Empty -RedirectStandardOutput $log -RedirectStandardError "$log.err"
    return $p.ExitCode
}
function Q($s) { '"' + $s + '"' }

# --- original data.win ---
Step "Backing up your original data.win"
$Orig = Join-Path $W "backup\data.win.orig"
New-Item -ItemType Directory -Force (Join-Path $W "backup") | Out-Null
if (-not (Test-Path $Orig) -or (Hash $Orig) -ne $OrigHash) {
    $t = Join-Path $GameDir "data.win"
    if ((Hash $t) -ne $OrigHash) { throw "Your data.win isn't the original Steam v1.08 file (maybe a mod is installed). In Steam: UNDERTALE > Properties > Installed Files > Verify integrity, then run again." }
    Copy-Item $t $Orig -Force
}
Write-Output "OK (v1.08)"

# --- extract what the build needs from your copy ---
$X = Join-Path $W "extract"
foreach ($d in @("", "fonts", "sprites", "allspr", "allbg")) { New-Item -ItemType Directory -Force (Join-Path $X $d) | Out-Null }
if (-not (Test-Path (Join-Path $X "CodeEntries\gml_Script_textdata_en.gml"))) {
    Step "Decompiling the game code (a few minutes)"
    Utmt @("dump", (Q $Orig), "-o", (Q $X), "-c", "UMT_DUMP_ALL") (Join-Path $X "dump.log") | Out-Null
    if (-not (Test-Path (Join-Path $X "CodeEntries\gml_Script_textdata_en.gml"))) { throw "Code dump failed, see extract\dump.log" }
}
Step "Exporting fonts and images"
$env:UTHE_OUT = Join-Path $X "fonts"
Utmt @("load", (Q $Orig), "-s", (Q (Join-Path $W "scripts\export_fonts.csx"))) (Join-Path $X "fonts.log") | Out-Null
$env:UTHE_OUT = Join-Path $X "sprites"; $env:UTHE_SPRITES = "bt,gameover,spr_undertaletitle"
Utmt @("load", (Q $Orig), "-s", (Q (Join-Path $W "scripts\export_sprites.csx"))) (Join-Path $X "sprites.log") | Out-Null
if (-not (Test-Path (Join-Path $X "allbg\bg_grillbyout.png"))) {
    $env:UTHE_SPR = Join-Path $X "allspr"; $env:UTHE_BG = Join-Path $X "allbg"
    Utmt @("load", (Q $Orig), "-s", (Q (Join-Path $W "scripts\export_all_images.csx"))) (Join-Path $X "images.log") | Out-Null
}
if (-not (Test-Path (Join-Path $X "fonts\fnt_maintext.png"))) { throw "Font export failed, see extract\fonts.log" }

# --- build ---
function Py([string]$script) { & python (Join-Path $W $script); if ($LASTEXITCODE -ne 0) { throw "$script failed" } }
Step "Reading the text table"
Py "scripts\extract_strings.py"
Step "Redrawing images in Hebrew"
New-Item -ItemType Directory -Force (Join-Path $W "fonts\sprites"), (Join-Path $W "fonts\backgrounds") | Out-Null
Py "scripts\build_buttons.py"
Py "scripts\sprites\redraw_a.py"
Py "scripts\sprites\redraw_b.py"
Py "scripts\sprites\redraw_c.py"
Step "Building fonts and code"
Py "scripts\build_fonts.py"
Py "scripts\pack_sprites.py"
Py "scripts\make_gml.py"
Step "Writing the Hebrew data.win (a few minutes)"
New-Item -ItemType Directory -Force (Join-Path $W "build") | Out-Null
$env:UTHE_ROOT = $W
$log = Join-Path $W "build\build.log"
Utmt @("load", (Q $Orig), "-s", (Q (Join-Path $W "scripts\build_hebrew.csx")), "-o", (Q (Join-Path $W "build\data.win")), "-f") $log | Out-Null
if (-not (Select-String -Path $log -Pattern "HEBREW BUILD OK" -Quiet)) { throw "Build failed, see build\build.log" }
Write-Output "Built: $(Join-Path $W 'build\data.win')"

if (-not $NoInstall) {
    Step "Installing"
    & powershell -ExecutionPolicy Bypass -File (Join-Path $W "install.ps1") -GameDir $GameDir
}
Write-Output ""
Write-Output "Done. To go back to English: powershell -ExecutionPolicy Bypass -File install.ps1 -Restore"
