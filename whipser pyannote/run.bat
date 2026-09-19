@echo off
title Audio Processor Studio
chcp 65001 >nul

:: Ensure working directory is the script folder
cd /d "%~dp0"
set "APP_DIR=%~dp0"

:: Set local models and PyTorch cache paths
set "HF_HOME=%APP_DIR%models\huggingface"
set "HUGGINGFACE_HUB_CACHE=%APP_DIR%models\huggingface\hub"
set "TRANSFORMERS_CACHE=%APP_DIR%models\huggingface\hub"
set "TORCH_HOME=%APP_DIR%models\torch"
set "PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128"

:: Check for Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_EXE=python"
    goto :START_SERVER
)

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_EXE=py"
    goto :START_SERVER
)

echo [ERROR] Python was not found on your system PATH!
echo.
echo Please run install.bat first, or install Python 3.10/3.11/3.12 and check "Add Python to PATH".
echo.
pause
exit /b 1

:START_SERVER
echo.
echo ====================================================================
echo    Starting Whisper and Pyannote Audio Processor Studio...
echo ====================================================================
echo Models Directory : %APP_DIR%models
echo Web Application  : http://127.0.0.1:8000
echo ====================================================================
echo.

%PY_EXE% app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTICE] Server stopped or encountered an issue.
    echo If backend packages are missing, please run install.bat first.
    echo.
)

pause


