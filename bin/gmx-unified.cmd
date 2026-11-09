@echo off
setlocal
set "GMX_RUNTIME_ROOT=%~dp0..\.native\windows\runtime"
"%~dp0..\.venv\Scripts\python.exe" -m gromacs_unified %*
exit /b %errorlevel%
