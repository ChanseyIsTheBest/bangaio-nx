# bangaio-nx: one PC test run of app\out\pc-nx\renut.exe, muted and minimised, with its own user data folder (never
# the user's Documents), a PNG capture of the presented image every -ShotsEvery seconds (nfsmw_captura_cada_s) and a
# scripted pad (the SDK's input_script: "seconds:BUTTON,..."). Only this run's process is stopped.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\bangaio_pc_run.ps1 -Name boot1 [-Seconds 90]
#       [-ShotsEvery 15] [-Input "8:A,10:START"] [-Sticks 0] [-Args "--banjo_renderer=renut ..."]
#
# Output: out\pc_runs\<Name>\run.log, shots (capturas\*.png moved there), userdata\.
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [int]$Seconds = 90,
    [int]$ShotsEvery = 15,
    [string]$Input = '',
    [int]$Sticks = 0,
    [string]$Args = ''
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exeDir = Join-Path $root 'app\out\pc-nx'
$exe = Join-Path $exeDir 'renut.exe'
if (-not (Test-Path $exe)) { throw "no $exe" }
# The extracted package next to the executable (renut_app.h: game_root beside the exe), a junction to D:\bango\game.
$gameRoot = Join-Path $exeDir 'game_root'
if (-not (Test-Path $gameRoot)) { New-Item -ItemType Junction -Path $gameRoot -Target 'D:\bango\game' | Out-Null }
$out = Join-Path $root "out\pc_runs\$Name"
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory -Force (Join-Path $out 'userdata') | Out-Null
$caps = Join-Path $exeDir 'capturas'
if (Test-Path $caps) { Get-ChildItem $caps -File | Remove-Item -Force }
$log = Join-Path $out 'run.log'
# The log goes to the exe's logs\ folder (log_to_file): with --log_file the GPU plugin's logger opened the same file
# again and the app's lines were lost (boot1). The newest log there is copied to run.log.
$logs = Join-Path $exeDir 'logs'
$argList = @('--log_to_file=true', '--log_level=info', '--audio_mute=true', '--window_start_minimized=true',
             "--user_data_root=$(Join-Path $out 'userdata')", "--nfsmw_captura_cada_s=$ShotsEvery",
             '--nfsmw_captura_max=200',
             # XBLA: the full game, not the trial (the SDK's default license mask is 0).
             '--license_mask=1')
if ($Input) { $argList += "--input_script=$Input" }
if ($Sticks -gt 0) { $argList += "--input_script_sticks=$Sticks" }
if ($Args) { $argList += ($Args -split ' ' | Where-Object { $_ }) }
$p = Start-Process -FilePath $exe -ArgumentList $argList -WorkingDirectory $exeDir -PassThru -WindowStyle Minimized
$exited = $p.WaitForExit($Seconds * 1000)
if (-not $exited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500
if (Test-Path $caps) { Get-ChildItem $caps -File | Move-Item -Destination $out -Force }
$newest = Get-ChildItem $logs -Recurse -File -Filter renut_*.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
if ($newest) { Copy-Item $newest.FullName $log -Force }
"exit: $(if ($exited) { $p.ExitCode } else { 'stopped after ' + $Seconds + ' s' })"
"shots: $((Get-ChildItem $out -Filter *.png -ErrorAction SilentlyContinue).Count)"
if (Test-Path $log) {
    Select-String -Path $log -Pattern 'access violation|Unhandled|unregistered|FATAL|crash|not implemented|Unimplemented' |
        Select-Object -First 12 | ForEach-Object { $_.Line }
    Get-Content $log -Tail 8
}

