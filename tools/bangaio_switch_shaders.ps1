# bangaio-nx: the Switch build's shader inputs from the PC build (zumasrevenge-nx's docs/building.md section 3, banjo-nx's
# tools): Renut's XenosRecomp (built by the PC build) translates out/renut_shader_dump again with the deko3d SPIR-V
# dump on and the early-alpha HLSL of the PC build, then SPIR-V -> uam GLSL -> DKSH check (deko3d_shaders.py), the
# GLSL passes (deko3d_glsl_opt.py --check), the NRO's GLSL package (deko3d_shader_package.py) and the Switch copy of
# the shader cache table (renut_switch_shader_cache.py). Outputs: app/out/renut_switch/{deko3d_glsl_switch.cpp,
# deko3d_glsl.bin, shader_cache_switch.cpp, spirv_cache.zst}. Game data: build tree only.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\bangaio_switch_shaders.ps1
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root
$pc = Join-Path $root 'app\out\pc-nx'
$recomp = Join-Path $pc 'xenos_recomp\build\XenosRecomp\XenosRecomp.exe'
if (-not (Test-Path $recomp)) { throw "no ${recomp}: build the PC tree first" }
$spirv = Join-Path $root 'out\deko3d_shaders\spirv'
if (Test-Path $spirv) { Remove-Item -Recurse -Force $spirv }
New-Item -ItemType Directory -Force $spirv | Out-Null
$env:BANJO_HLSL_OVERRIDE = Join-Path $pc 'renut_gpu\early_alpha_hlsl'
$env:BANJO_DEKO3D_SPIRV_DIR = $spirv
try {
    & $recomp (Join-Path $root 'out\renut_shader_dump') (Join-Path $root 'out\deko3d_shaders\scratch_cache.cpp') `
        (Join-Path $root 'app\thirdparty\reblue-XenosRecomp\XenosRecomp\shader_common.h') | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "XenosRecomp failed ($LASTEXITCODE)" }
} finally {
    Remove-Item env:BANJO_HLSL_OVERRIDE, env:BANJO_DEKO3D_SPIRV_DIR -ErrorAction SilentlyContinue
}
"spirv: $((Get-ChildItem $spirv -Filter *.spv).Count) shaders"
python tools\deko3d_shaders.py --spirv out\deko3d_shaders\spirv --out out\deko3d_shaders --jobs 8
if ($LASTEXITCODE -ne 0) { throw "deko3d_shaders failed" }
python tools\deko3d_glsl_opt.py --in out\deko3d_shaders\glsl --out out\deko3d_shaders\glsl_opt --check
if ($LASTEXITCODE -ne 0) { throw "deko3d_glsl_opt failed" }
python tools\deko3d_shader_package.py --glsl out\deko3d_shaders\glsl_opt --out app\out\renut_switch
if ($LASTEXITCODE -ne 0) { throw "deko3d_shader_package failed" }
python tools\renut_switch_shader_cache.py --pc app\out\pc-nx
if ($LASTEXITCODE -ne 0) { throw "renut_switch_shader_cache failed" }
Get-ChildItem app\out\renut_switch | Select-Object Name, Length
