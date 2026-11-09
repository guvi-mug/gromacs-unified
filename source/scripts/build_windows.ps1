param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Output,
    [Parameter(Mandatory=$true)][string]$FftwPrefix,
    [ValidateSet('cpu','cuda','both')][string]$Backend = 'both',
    [int]$Jobs = 2
)
$ErrorActionPreference = 'Stop'
# Run in an x64 Visual Studio developer shell with CUDA on PATH for CUDA builds.
python "$PSScriptRoot/build_native.py" $Source $Output --backend $Backend --fftw-prefix $FftwPrefix --jobs $Jobs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
