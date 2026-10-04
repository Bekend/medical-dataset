@echo off
setlocal enabledelayedexpansion
title Audio Processor - Backend Library Installer
chcp 65001 >nul

echo ====================================================================
echo    Audio Processor Studio - Backend Dependencies Installer
echo    (OpenAI Whisper, Pyannote Diarization, FastAPI, PyTorch)
echo ====================================================================
echo.

:: 1. Check for Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python is not found on your system PATH!
        echo.
        echo Please download and install Python 3.10, 3.11, or 3.12 from:
        echo    https://www.python.org/downloads/
        echo.
        echo IMPORTANT: During installation, make sure to check:
        echo    [x] "Add Python to PATH"
        echo.
        pause
        exit /b 1
    ) else (
        set "PY_CMD=py"
    )
) else (
    set "PY_CMD=python"
)

for /f "delims=" %%v in ('%PY_CMD% --version 2^>^&1') do echo [OK] Found %%v
echo.

:: 2. Upgrade core pip tooling
echo [2/5] Upgrading pip, setuptools, and wheel...
%PY_CMD% -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pip upgrade encountered an issue, proceeding with installation...
)
echo.

:: 3. Detect NVIDIA GPU & Install PyTorch (CUDA vs CPU)
echo [3/5] Detecting GPU hardware for PyTorch acceleration...
nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] NVIDIA GPU detected! Installing PyTorch with CUDA 12.4 acceleration...
    %PY_CMD% -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
) else (
    echo [INFO] No NVIDIA GPU detected. Installing standard CPU PyTorch...
    %PY_CMD% -m pip install torch torchvision torchaudio
)
echo.

:: 4. Install requirements from requirements.txt
echo [4/5] Installing backend libraries from requirements.txt...
set "APP_DIR=%~dp0"
%PY_CMD% -m pip install -r "%APP_DIR%requirements.txt"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Some packages failed to install. Please check your internet connection.
    pause
    exit /b 1
)
echo.

:: 5. Verification Check
echo [5/5] Verifying installed backend libraries...
%PY_CMD% -c "import torch, soundfile, scipy, fastapi, uvicorn, pydantic, tqdm; import whisper; from pyannote.audio import Pipeline; print('\n[SUCCESS] PyTorch version:', torch.__version__); print('[SUCCESS] CUDA Acceleration:', 'Enabled (GPU)' if torch.cuda.is_available() else 'Disabled (CPU Mode)'); print('[SUCCESS] Whisper STT & Pyannote Diarization backend packages verified!')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] One or more libraries had a verification warning.
) else (
    echo.
    echo ====================================================================
    echo   INSTALLATION COMPLETED SUCCESSFULLY!
    echo   You can now start the application anytime by double-clicking:
    echo      run.bat
    echo ====================================================================
)

echo.
pause
