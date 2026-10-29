# bangaio-nx: the console package (out\package_<Name>), never with game data:
#   sd\switch\bangaio-nx\bangaio-nx.nro       the NRO (the user's own game_root goes beside it: the extracted package)
#   sd\switch\bangaio-nx\renut.toml           the player's settings (1.0.0: docked_resolution, smaa and language only;
#                                             the test tomls renut_log / renut_play / renut_ab stay in dist\)
#   elf\bangaio-nx_<Name>.elf / .map           the NRO's ELF and link map (a console profile maps to source lines)
#   source\bangaio-nx_<Name>_<commit>.zip     git archive of the commit the NRO was built from (no game data)
#   README.txt                                 setting up, the settings and the credits (dist\README.txt)
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\bangaio_package.ps1 -Name 20261029 -BuildDir app\out\switch
#   -Commit <rev>: the commit the NRO was built from (default HEAD); the settings, configs, README and source
#   archive are that commit's (2026-10-29: so an older build's package is not given a newer build's settings).
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$BuildDir = 'app\out\switch',
    [string]$Commit = 'HEAD'
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$pkg = Join-Path $root "out\package_$Name"
if (Test-Path $pkg) { Remove-Item -Recurse -Force $pkg }
$sd = Join-Path $pkg 'sd\switch\bangaio-nx'
New-Item -ItemType Directory -Force $sd, "$pkg\elf", "$pkg\source" | Out-Null
$nro = Join-Path $BuildDir 'renut.nro'
$elf = Join-Path $BuildDir 'renut'
$map = Join-Path $BuildDir 'renut.map'
foreach ($f in $nro, $elf, $map) { if (-not (Test-Path $f)) { throw "missing $f" } }
$commit = (git rev-parse --short $Commit).Trim()
if ($LASTEXITCODE -ne 0 -or -not $commit) { throw "unknown commit $Commit" }
# The commit's dist\ (git archive and the system tar: bytes as committed).
$files = Join-Path $pkg '_commit'
New-Item -ItemType Directory -Force $files | Out-Null
git archive --format=tar -o "$files.tar" $commit dist
if ($LASTEXITCODE -ne 0) { throw "git archive of $commit failed" }
& "$env:SystemRoot\System32\tar.exe" -xf "$files.tar" -C $files
if ($LASTEXITCODE -ne 0) { throw "tar failed" }
Copy-Item $nro "$sd\bangaio-nx.nro"
Copy-Item "$files\dist\switch\bangaio-nx\renut.toml" "$sd\renut.toml"
Copy-Item $elf "$pkg\elf\bangaio-nx_$Name.elf"
Copy-Item $map "$pkg\elf\bangaio-nx_$Name.map"
git archive --format=zip -o "$pkg\source\bangaio-nx_${Name}_$commit.zip" $commit
if (Test-Path "$files\dist\README.txt") { Copy-Item "$files\dist\README.txt" "$pkg\README.txt" }
Remove-Item -Recurse -Force $files, "$files.tar"
$hash = (Get-FileHash "$sd\bangaio-nx.nro" -Algorithm SHA256).Hash.Substring(0, 16)
"package: $pkg"
"  NRO $([math]::Round((Get-Item "$sd\bangaio-nx.nro").Length / 1MB, 1)) MB, sha256 $hash..., commit $commit"
Get-ChildItem $pkg -Recurse -File | Select-Object @{n = 'File'; e = { $_.FullName.Substring($pkg.Length + 1) } }, Length
