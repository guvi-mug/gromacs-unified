$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$binPath = Join-Path $projectRoot 'bin'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $binPath) {
    [Environment]::SetEnvironmentVariable('Path', "$binPath;$userPath", 'User')
}
if (($env:Path -split ';') -notcontains $binPath) { $env:Path = "$binPath;$env:Path" }
$hook = Join-Path $PSScriptRoot 'powershell-directory-hook.ps1'
$profilePaths = @(
    (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'WindowsPowerShell/profile.ps1'),
    (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'PowerShell/profile.ps1')
)
foreach ($profilePath in $profilePaths) {
    New-Item -ItemType Directory -Force (Split-Path $profilePath) | Out-Null
    $existing = if (Test-Path $profilePath) { [IO.File]::ReadAllText($profilePath) } else { '' }
    if (-not $existing.Contains($hook)) {
        if (Test-Path $profilePath) { Copy-Item $profilePath "$profilePath.gromacs-backup" }
        Add-Content $profilePath "`n# GROMACS project environment`n. '$($hook.Replace("'", "''"))'"
    }
}
Write-Host 'User PATH and PowerShell directory activation configured. Open a new terminal.'
