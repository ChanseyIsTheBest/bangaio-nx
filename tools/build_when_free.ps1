# bangaio-nx (2026-10-29): waits until the free commit memory is -MinGB or more (other ports' emulators and builds share
# the RAM), then runs tools\switch_build_bg.bat or tools\pc_build_bg.bat with -Jobs jobs into -Log. Never starts while
# this port's own Ryujinx run is going (its data folder ryu-data\bangaio on the command line).
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\build_when_free.ps1 -Kind switch -Log out\x.log
#       [-BuildDir app\out\switch] [-Jobs 6] [-MinGB 9] [-ExtraCmake "..."] [-Clean]
# -Clean: cmake --build --clean-first (a PGO use build after a new profile: every object must read it).
param(
    [ValidateSet('switch', 'pc')][string]$Kind = 'switch',
    [Parameter(Mandatory = $true)][string]$Log,
    [string]$BuildDir = '',
    [int]$Jobs = 6,
    [int]$MinGB = 9,
    [string]$ExtraCmake = '',
    [switch]$Clean
)
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
while ($true) {
    $mine = @(Get-CimInstance Win32_Process -Filter "Name='Ryujinx.exe'" | Where-Object { $_.CommandLine -match 'ryu-data\\bangaio\\' }).Count
    $free = [int]((Get-CimInstance Win32_OperatingSystem).FreeVirtualMemory / 1MB)
    if ($mine -eq 0 -and $free -ge $MinGB) { break }
    Start-Sleep -Seconds 15
}
"$(Get-Date -Format HH:mm) free commit $free GB: building ($Kind, $Jobs jobs)"
$env:JOBS = "$Jobs"
if ($BuildDir) { $env:BUILD_DIR = (Join-Path $root $BuildDir) }
if ($ExtraCmake) { $env:EXTRA_CMAKE = $ExtraCmake }
$bat = if ($Kind -eq 'switch') { 'switch_build_bg.bat' } else { 'pc_build_bg.bat' }
$first = if ($Clean) { '--clean-first ' } else { '' }
& "$env:SystemRoot\System32\cmd.exe" /c "`"$root\tools\$bat`" `"$(Join-Path $root $Log)`" $first-- -k 0"
"$(Get-Date -Format HH:mm) done"
Get-Content (Join-Path $root $Log) -Tail 4
