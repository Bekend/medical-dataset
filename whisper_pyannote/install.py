#!/usr/bin/env python3
"""
Audio Processor Studio - Backend Dependencies Installer
Installs all required Python backend libraries (Whisper, Pyannote Diarization, PyTorch with CUDA, FastAPI, etc.)
"""

import sys
import os
import subprocess
import shutil
import platform

def print_header():
    print("=" * 70)
    print("   Audio Processor Studio - Backend Python Library Installer")
    print("   (OpenAI Whisper, Pyannote Audio, PyTorch, FastAPI, Transformers)")
    print("=" * 70)
    print()

def run_command(cmd, desc=""):
    if desc:
        print(f"--> {desc}...")
    try:
        res = subprocess.run(cmd, check=True)
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        return False

def check_nvidia_gpu():
    try:
        res = subprocess.run(["nvidia-smi"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except Exception:
        return False

def main():
    print_header()

    py_ver = sys.version.split()[0]
    print(f"[1/5] Detected Python version: {py_ver} ({platform.system()} {platform.machine()})")
    
    # 1. Upgrade pip & build tools
    print("\n[2/5] Upgrading pip, setuptools, and wheel...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    # 2. Check GPU & install PyTorch
    has_gpu = check_nvidia_gpu()
    print("\n[3/5] Checking GPU hardware and installing PyTorch...")
    if has_gpu:
        print("  ✓ NVIDIA GPU detected! Installing PyTorch with CUDA 12.4 acceleration...")
        torch_cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio",
            "--index-url", "https://download.pytorch.org/whl/cu124"
        ]
    else:
        print("  ℹ No NVIDIA GPU detected. Installing standard CPU PyTorch...")
        torch_cmd = [
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio"
        ]
    
    if not run_command(torch_cmd, "Installing PyTorch"):
        print("[!] Warning: PyTorch installation returned a non-zero code. Attempting to continue...")

    # 3. Install requirements
    print("\n[4/5] Installing core backend dependencies from requirements.txt...")
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if os.path.exists(req_file):
        req_cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
        run_command(req_cmd, "Installing requirements.txt")
    else:
        # Fallback list if requirements.txt is missing
        direct_pkgs = [
            "openai-whisper", "pyannote.audio", "soundfile", "scipy", "numpy",
            "tqdm", "fastapi", "uvicorn[standard]", "python-multipart", "pydantic",
            "requests", "transformers", "accelerate", "safetensors", "huggingface_hub"
        ]
        run_command([sys.executable, "-m", "pip", "install"] + direct_pkgs, "Installing direct package list")

    # 4. Verification Check
    print("\n[5/5] Verifying installed packages...")
    verification_code = """
import sys
import torch
import soundfile
import scipy
import fastapi
import uvicorn
import pydantic
import whisper
from pyannote.audio import Pipeline

print(f"  ✓ PyTorch version: {torch.__version__}")
print(f"  ✓ CUDA GPU Acceleration: {'ENABLED (CUDA Available)' if torch.cuda.is_available() else 'CPU Mode'}")
if torch.cuda.is_available():
    print(f"  ✓ GPU Device Name: {torch.cuda.get_device_name(0)}")
print("  ✓ OpenAI Whisper STT: OK")
print("  ✓ Pyannote Community Diarization: OK")
print("  ✓ FastAPI & Uvicorn Web Server: OK")
"""
    try:
        subprocess.run([sys.executable, "-c", verification_code], check=True)
        print("\n" + "=" * 70)
        print("  🎉 INSTALLATION COMPLETED SUCCESSFULLY!")
        print("  All backend libraries are ready to run.")
        print("  You can now start the web application with:")
        print("     python app.py   (or run.bat on Windows)")
        print("=" * 70)
    except Exception as e:
        print(f"\n[!] Verification encountered an error: {e}")
        print("Please check that all dependencies were installed without errors.")

if __name__ == "__main__":
    main()
