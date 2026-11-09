# Automatically activate only this project's uv environment when entering it.
if (-not $global:GromacsDirectoryHookInstalled) {
    $global:GromacsDirectoryHookInstalled = $true
    $global:GromacsProjectRoot = (Split-Path $PSScriptRoot -Parent)
    $global:GromacsPreviousPrompt = (Get-Command prompt).ScriptBlock
    $global:GromacsPromptHook = {
        $projectVenv = Join-Path $global:GromacsProjectRoot '.venv'
        $currentDirectory = $ExecutionContext.SessionState.Path.CurrentFileSystemLocation.Path
        $inside = $currentDirectory -eq $global:GromacsProjectRoot -or $currentDirectory.StartsWith($global:GromacsProjectRoot + '\', [StringComparison]::OrdinalIgnoreCase)
        if ($inside -and -not $env:VIRTUAL_ENV -and (Test-Path "$projectVenv\Scripts\Activate.ps1")) {
            $global:GromacsPreviousRuntimeRoot = $env:GMX_RUNTIME_ROOT
            . (Join-Path $global:GromacsProjectRoot 'Activate-Gromacs.ps1')
            $global:GromacsAutoActivated = $true
            Set-Item Function:global:prompt -Value $global:GromacsPromptHook
        } elseif (-not $inside -and $global:GromacsAutoActivated -and $env:VIRTUAL_ENV -eq $projectVenv) {
            deactivate
            if ($null -eq $global:GromacsPreviousRuntimeRoot) {
                Remove-Item Env:GMX_RUNTIME_ROOT -ErrorAction SilentlyContinue
            } else {
                $env:GMX_RUNTIME_ROOT = $global:GromacsPreviousRuntimeRoot
            }
            $global:GromacsAutoActivated = $false
            Set-Item Function:global:prompt -Value $global:GromacsPromptHook
        }
        if ($env:VIRTUAL_ENV -eq $projectVenv) { Write-Host '(gromacs) ' -NoNewline -ForegroundColor Green }
        & $global:GromacsPreviousPrompt
    }
    Set-Item Function:global:prompt -Value $global:GromacsPromptHook
}
