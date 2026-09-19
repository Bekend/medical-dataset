# Whisper STT & Pyannote Diarization Studio

A application that takes `.wav` audio files as input and processes them through **OpenAI Whisper** and **Pyannote Audio** (community pipeline).

It generates two primary outcome files for each processed audio file:
1. **Diarization File (`*_diarization.txt`)**: Shows who talked when with exact timestamp ranges.
2. **STT File with Timestamps (`*_stt_timestamps.txt`)**: Shows OpenAI Whisper speech-to-text transcript with segment/word timestamps.
*(Bonus: A merged speaker-attributed transcript aligning both outputs).*

---

## Quick Start (New PC Setup)

### 1. One-Click Automated Installation (Windows)
Double-click **`install.bat`** (or run `python install.py`).

This automated installer will:
- Check your Python installation (Python 3.10 - 3.12).
- Automatically detect NVIDIA GPU hardware.
- Install PyTorch with **CUDA 12.4** acceleration (or CPU version if no GPU).
- Install all backend libraries (`openai-whisper`, `pyannote.audio`, `fastapi`, `uvicorn`, `soundfile`, `scipy`, `transformers`, etc.).
- Run a self-verification check.

### 2. Manual Installation
```bash
# Optional: Install PyTorch with CUDA (if you have an NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install all backend libraries
pip install -r requirements.txt
```

### 3. Launch Web Application
Double-click **`run.bat`** or run:
```bash
python app.py
```

3. **Open Browser**:
   - Navigate to `http://127.0.0.1:8000`
   - Drag & drop your `.wav` file
   - Enter your **Hugging Face Access Token** (for Pyannote community diarization model access at `https://hf.co/pyannote/speaker-diarization-3.1`)
   - Select Whisper model (`base`, `small`, `medium`, `large-v3`)
   - Click **Start Processing Audio**
   - Preview and download both outcome files directly from the UI!

---

## Command Line Interface (CLI)

You can also run headless audio processing directly from the command line:

```bash
python cli.py sample.wav --hf_token YOUR_HF_TOKEN --whisper_model base --output_dir ./output
```

This will automatically create:
- `./output/sample_diarization.txt` (File #1: Who talked when)
- `./output/sample_stt_timestamps.txt` (File #2: Whisper transcript with timestamps)
- `./output/sample_merged_transcript.txt` (Merged output)

---

## Requirements & Hugging Face Access

- **Python**: 3.10 or 3.11
- **Pyannote Community Access**: The `pyannote/speaker-diarization-3.1` model requires accepting user conditions on Hugging Face:
  1. Visit https://hf.co/pyannote/speaker-diarization-3.1 and accept conditions.
  2. Visit https://hf.co/pyannote/segmentation-3.0 and accept conditions.
  3. Create a Hugging Face Access Token at https://hf.co/settings/tokens and paste it into the app.

---

## Local Models Directory (`models/`)

All downloaded model weights and caches are stored locally inside the project folder:
- `models/whisper/`: Whisper model weights (`base.pt`, `tiny.pt`, `large-v3.pt`, etc.). You can also place `.pt` files directly into `models/` or `models/whisper/`.
- `models/huggingface/`: Pyannote diarization models and Hugging Face Transformers caches.
- `models/torch/`: PyTorch hub checkpoints.
