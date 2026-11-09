param(
    [ValidateSet('auto', 'cpu', 'both')][string]$Backend = 'auto',
    [int]$Jobs = 8,
    [string]$CudaArchitectures = 'native'
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}
if (-not (Get-Command cl -ErrorAction SilentlyContinue)) {
    $vswhere = "${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
    if (-not (Test-Path $vswhere)) { throw 'Install Visual Studio C++ Build Tools first.' }
    $vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $vs) { throw 'Visual Studio x64 C++ tools were not found.' }
    $vcvars = Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
    cmd /c "`"$vcvars`" >nul && set" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
    }
}
if (-not $env:CUDA_PATH) {
    $cuda = Get-ChildItem "$env:ProgramFiles/NVIDIA GPU Computing Toolkit/CUDA" -Directory -ErrorAction SilentlyContinue |
        Sort-Object { [version]$_.Name.TrimStart('v') } -Descending | Select-Object -First 1
    if ($cuda) { $env:CUDA_PATH = $cuda.FullName }
}
if ($env:CUDA_PATH -and (Test-Path "$env:CUDA_PATH/bin/nvcc.exe")) {
    $env:Path = "$env:CUDA_PATH/bin;$env:CUDA_PATH/bin/x64;$env:Path"
}
if ($Backend -eq 'auto') { $Backend = if (Get-Command nvcc -ErrorAction SilentlyContinue) { 'both' } else { 'cpu' } }
if (-not (Test-Path .venv/Scripts/python.exe)) { Invoke-Checked uv @('venv', '--python', '3.14', '.venv') }
. ./.venv/Scripts/Activate.ps1
Invoke-Checked uv @('pip', 'install', '--python', '.venv/Scripts/python.exe', '-e', './source', 'ninja')
$env:CMAKE_GENERATOR = 'Ninja'
foreach ($name in @('gromacs', 'fftw')) {
    $version = if ($name -eq 'gromacs') { '2026.4' } else { '3.3.10' }
    if (-not (Test-Path ".native/sources/$name-$version")) {
        Invoke-Checked python @('source/scripts/fetch_sources.py', $name, '--destination', '.native/sources')
    }
}
Invoke-Checked python @('source/scripts/apply_windows_patch.py', '.native/sources/gromacs-2026.4')
Invoke-Checked python @('source/scripts/build_fftw.py', '.native/sources/fftw-3.3.10', '.native/windows/fftw', '--work', '.native/windows/fftw-build', '--jobs', "$Jobs")
$build = @('source/scripts/build_native.py', '.native/sources/gromacs-2026.4', '.native/windows/runtime', '--backend', $Backend, '--fftw-prefix', '.native/windows/fftw', '--work', '.native/windows/build', '--generator', 'Ninja', '--jobs', "$Jobs")
if ($Backend -eq 'both') { $build += "--cmake-arg=-DGMX_CUDA_ARCHITECTURES=$CudaArchitectures" }
Invoke-Checked python $build
Get-ChildItem .native/windows/runtime -Directory | ForEach-Object {
    Copy-Item source/patches/windows-2026.4.patch (Join-Path $_.FullName 'licenses/gromacs-unified-windows.patch')
    Copy-Item source/patches/README.md (Join-Path $_.FullName 'licenses/gromacs-unified-patches.md')
}
foreach ($mode in @('cpu', 'auto')) {
    Invoke-Checked python @('source/scripts/smoke_test.py', '--runtime-root', '.native/windows/runtime', '--backend', $mode)
}
Invoke-Checked python @('source/scripts/package_native.py', '.native/windows/runtime', '--out', 'wheels/windows-built', '--install')
. ./Activate-Gromacs.ps1
Write-Host 'Build, checks, and installation complete. Run gmx-unified doctor.'
