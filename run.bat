@echo off
REM PitchTuna launcher for Windows.
REM Runs directly from the source tree (no install required), only needs numpy.
setlocal
cd /d "%~dp0"

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
  echo [pitchtuna] numpy not found; installing runtime dependency ...
  python -m pip install -r requirements.txt
)

python -m pitchtuna %*
endlocal
