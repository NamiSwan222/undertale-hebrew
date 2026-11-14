# Lab run: start the lab build minimized (no focus), BelowNormal priority, small restore rect at right edge.
# Usage: powershell -File lab_run.ps1 -Script <lab script file> -Out <dir for screenshots> [-TimeoutSec 300]
param(
    [Parameter(Mandatory = $true)][string]$Script,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$TimeoutSec = 300,
    [switch]$KeepSave
)
$ErrorActionPreference = "Stop"
$W = Split-Path -Parent $PSScriptRoot
$Steam = "C:\Program Files (x86)\Steam\steamapps\common\Undertale"
$Lab = Join-Path $W "build\lab_game"
$Save = Join-Path $env:LOCALAPPDATA "UNDERTALE_HEBLAB"

# refuse to start if another Undertale copy is running (one lab at a time)
if (Get-Process -Name "UNDERTALE" -ErrorAction SilentlyContinue) { throw "An UNDERTALE process is already running" }

# lab game folder: hard links to the Steam files (read-only use), our lab data.win
New-Item -ItemType Directory -Force $Lab | Out-Null
Get-ChildItem $Steam -File | Where-Object { $_.Name -ne "data.win" } | ForEach-Object {
    $dst = Join-Path $Lab $_.Name
    if (-not (Test-Path $dst)) { Copy-Item $_.FullName $dst }
}
Copy-Item (Join-Path $W "build\lab\data.win") (Join-Path $Lab "data.win") -Force
Set-Content -Path (Join-Path $Lab "steam_appid.txt") -Value "391540" -Encoding ascii
Copy-Item $Script (Join-Path $Lab "lab_script.txt") -Force

# fresh lab save dir (never the real UNDERTALE one)
if (Test-Path $Save) {
    if ($KeepSave) { Get-ChildItem $Save -Filter *.png | Remove-Item -Force; Remove-Item (Join-Path $Save "lab_log.txt") -ErrorAction SilentlyContinue }
    else { Remove-Item $Save -Recurse -Force }
}

Add-Type @"
using System; using System.Runtime.InteropServices;
public class LabWin {
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int x, y; }
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int l, t, r, b; }
  [StructLayout(LayoutKind.Sequential)] public struct WP { public int len, flags, show; public POINT min, max; public RECT normal; }
  [DllImport("user32.dll")] public static extern bool SetWindowPlacement(IntPtr h, ref WP p);
  [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
}
"@
$p = Start-Process -FilePath (Join-Path $Lab "UNDERTALE.exe") -WorkingDirectory $Lab -PassThru -WindowStyle Minimized
try { $p.PriorityClass = "BelowNormal" } catch {}
$sw = [Diagnostics.Stopwatch]::StartNew()
$placed = $false
while (-not $p.HasExited -and $sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
    if (-not $placed) {
        $p.Refresh()
        if ($p.MainWindowHandle -ne [IntPtr]::Zero) {
            $sx = [LabWin]::GetSystemMetrics(0)
            $wp = New-Object LabWin+WP
            $wp.len = [Runtime.InteropServices.Marshal]::SizeOf($wp)
            $wp.show = 7  # SW_SHOWMINNOACTIVE
            $wp.normal.l = $sx - 500; $wp.normal.t = 60; $wp.normal.r = $sx - 20; $wp.normal.b = 60 + 360 + 30
            [LabWin]::SetWindowPlacement($p.MainWindowHandle, [ref]$wp) | Out-Null
            $placed = $true
        }
    }
    Start-Sleep -Milliseconds 500
}
if (-not $p.HasExited) {
    # report any dialog windows of the process (GML error popups) before killing
    Add-Type -AssemblyName UIAutomationClient
    $root = [Windows.Automation.AutomationElement]::RootElement
    $cond = New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ProcessIdProperty, $p.Id)
    foreach ($el in $root.FindAll([Windows.Automation.TreeScope]::Children, $cond)) {
        Write-Output ("WINDOW: " + $el.Current.Name)
        $txt = $el.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition) | ForEach-Object { $_.Current.Name } | Where-Object { $_ } | Select-Object -First 40
        $txt | ForEach-Object { Write-Output ("  " + $_) }
    }
    Stop-Process -Id $p.Id -Force; Write-Output "TIMEOUT - killed"
}
New-Item -ItemType Directory -Force $Out | Out-Null
if (Test-Path $Save) {
    Get-ChildItem $Save -Filter *.png | Copy-Item -Destination $Out -Force
    if (Test-Path (Join-Path $Save "lab_log.txt")) { Copy-Item (Join-Path $Save "lab_log.txt") $Out -Force }
}
Write-Output ("done in {0:N0}s; shots: {1}" -f $sw.Elapsed.TotalSeconds, (Get-ChildItem $Out -Filter *.png).Count)
