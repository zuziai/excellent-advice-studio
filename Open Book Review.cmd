@echo off
setlocal
cd /d "%~dp0"
if defined CODEX_PYTHON (
  "%CODEX_PYTHON%" -X utf8 "%~dp0review-data\start-local-review.py"
) else if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 "%~dp0review-data\start-local-review.py"
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -X utf8 "%~dp0review-data\start-local-review.py"
  ) else (
    python -X utf8 "%~dp0review-data\start-local-review.py"
  )
)
if errorlevel 1 (
  pause
  exit /b 1
)
start "" "http://127.0.0.1:8765/"
