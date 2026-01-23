@echo off
REM Dock2K8s - Docker Compose to Kubernetes Converter
REM Wrapper script to run dock2k8s from command line

REM Get the directory where this script is located
setlocal enabledelayedexpansion
set "SCRIPT_DIR=%~dp0"

REM Run the CLI with all arguments passed through
python "%SCRIPT_DIR%cli.py" %*

REM Preserve exit code
exit /b %errorlevel%
