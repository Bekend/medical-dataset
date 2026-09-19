<div align="center">

# 🎙️ Whisper STT & Pyannote Diarization Studio

**End-to-End Speech-to-Text Transcription & Speaker Diarization Pipeline**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![PyTorch CUDA 12.4](https://img.shields.io/badge/PyTorch-CUDA%2012.4-EE4C2C.svg?logo=pytorch)](https://pytorch.org/)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-brightgreen.svg?logo=openai)](https://github.com/openai/whisper)
[![Pyannote](https://img.shields.io/badge/Pyannote-Audio%203.1-orange.svg)](https://github.com/pyannote/pyannote-audio)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)

[English](#-english) • [فارسی](#-فارسی) • [Credits / سازنده](#-credits--سازنده)

---

</div>

## 🌐 English

An automated audio processing engine that takes `.wav` audio files as input and processes them through **OpenAI Whisper** and **Pyannote Audio 3.1** to deliver synchronized transcription and speaker identification.

### 📦 Key Outputs

| File | Type | Description |
| :--- | :--- | :--- |
| `*_diarization.txt` | **Diarization** | Exact turn-by-turn timestamp ranges identifying who spoke when. |
| `*_stt_timestamps.txt` | **STT** | OpenAI Whisper transcript aligned with segment/word timestamps. |
| `*_merged_transcript.txt` | **Merged** | Unified speaker-attributed transcript matching text to each speaker. |

---

### 🚀 Quick Start (Windows Setup)

#### 1. Automated Setup
Double-click the automated batch installer:
```cmd
install.bat
```
> Alternatively, execute `python install.py`. The script will automatically inspect your Python environment, detect NVIDIA GPU hardware, configure **PyTorch with CUDA 12.4** acceleration (or fallback to CPU), install all required packages, and run a self-check.

#### 2. Manual Installation
```bash
# Optional: Install PyTorch with CUDA 12.4 (if you have an NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Install all backend dependencies
pip install -r requirements.txt
```

#### 3. Launch Web Application
Run the runner batch file or start manually:
```bash
python app.py
# Or double-click run.bat
```
1. Navigate to `http://127.0.0.1:8000` in your browser.
2. Drag & drop your `.wav` file into the upload zone.
3. Enter your **Hugging Face Access Token**.
4. Select your preferred Whisper model (`base`, `small`, `medium`, `large-v3`).
5. Click **Start Processing Audio** to process, preview, and download results.

---

### 💻 Command Line Interface (CLI)

Run headless audio processing directly from your terminal:

```bash
python cli.py sample.wav --hf_token YOUR_HF_TOKEN --whisper_model base --output_dir ./output
```

**Output artifacts created inside `./output/`:**
- `sample_diarization.txt`
- `sample_stt_timestamps.txt`
- `sample_merged_transcript.txt`

---

### 🔑 Hugging Face Authentication & Requirements

- **Python**: 3.10, 3.11, or 3.12
- Access to the `pyannote/speaker-diarization-3.1` pipeline requires accepting the user terms on Hugging Face:
  1. Visit and accept terms on [pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1).
  2. Visit and accept terms on [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0).
  3. Create an access token at [Hugging Face Settings Tokens](https://hf.co/settings/tokens) and supply it to the app or CLI.

---

### 📁 Local Models Directory (`models/`)

All downloaded model weights and checkpoints are cached inside the project root:

```text
models/
├── whisper/         # Whisper model weights (base.pt, large-v3.pt, etc.)
├── huggingface/     # Pyannote models and HF Transformers cache
└── torch/           # PyTorch Hub checkpoints
```

---
---

<div dir="rtl">

## 🇮🇷 فارسی

استودیو پردازش صوتی، فایل‌های صوتی با پسوند `.wav` را دریافت کرده و با بهره‌گیری از **OpenAI Whisper** و **Pyannote Audio 3.1**، تبدیل گفتار به متن و تفکیک هوشمند گویندگان را انجام می‌دهد.

### 📦 فایل‌های خروجی

| نام فایل | نوع فایل | توضیحات |
| :--- | :--- | :--- |
| `*_diarization.txt` | **تفکیک گوینده** | بازه‌های زمانی صحبت هر فرد و مشخص‌کردن این‌که چه کسی در چه زمانی صحبت کرده است. |
| `*_stt_timestamps.txt` | **متن با برچسب زمان** | متن پیاده‌شده توسط Whisper همراه با برچسب‌های زمانی دقیق کلمات یا بخش‌ها. |
| `*_merged_transcript.txt` | **خروجی ادغام‌شده** | متن پیاده‌شده با اتصال قطعی به گوینده مربوطه. |

---

### 🚀 راه‌اندازی سریع (ویندوز)

#### ۱. نصب خودکار
روی فایل نصاب کلیک کنید:
```cmd
install.bat
```
> یا دستور `python install.py` را در ترمینال اجرا کنید. برنامه نسخه پایتون، کارت گرافیک NVIDIA، شتاب‌دهنده **CUDA 12.4** و تمامی پیش‌نیازها را بررسی و نصب می‌کند.

#### ۲. نصب دستی
```bash
# نصب پایتورچ به همراه شتاب‌دهنده CUDA (در صورت وجود کارت گرافیک NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# نصب نیازمندی‌های بک‌اند
pip install -r requirements.txt
```

#### ۳. اجرای رابط کاربری تحت وب
```bash
python app.py
# یا اجرای مستقیم فایل run.bat
```
1. در مرورگر به آدرس `http://127.0.0.1:8000` بروید.
2. فایل `.wav` مورد نظر را بکشید و رها کنید (Drag & Drop).
3. **توکن دسترسی Hugging Face** خود را وارد نمایید.
4. مدل Whisper مورد نظر (`base`، `small`، `medium`، `large-v3`) را انتخاب کنید.
5. دکمه **Start Processing Audio** را بزنید و نتایج را مشاهده و دریافت کنید.

---

### 💻 اجرای مستقیم از خط فرمان (CLI)

برای پردازش بدون نیاز به مرورگر:

```bash
python cli.py sample.wav --hf_token YOUR_HF_TOKEN --whisper_model base --output_dir ./output
```

---

### 🔑 دسترسی‌ها و نیازمندی‌های Hugging Face

- **پایتون**: نسخه ۳.۱۰، ۳.۱۱ یا ۳.۱۲
- برای استفاده از مدل‌های Pyannote 3.1 باید شرایط کاربری را در هاگینگ فیس تایید کنید:
  1. به صفحه [pyannote/speaker-diarization-3.1](https://hf.co/pyannote/speaker-diarization-3.1) رفته و شرایط را تایید کنید.
  2. به صفحه [pyannote/segmentation-3.0](https://hf.co/pyannote/segmentation-3.0) رفته و شرایط را تایید کنید.
  3. در صفحه [Hugging Face Tokens](https://hf.co/settings/tokens) یک توکن بسازید و در برنامه وارد کنید.

---

### 📁 مسیر مدل‌های محلی (`models/`)

مدل‌ها و کش‌های برنامه در پوشه پروژه ذخیره می‌شوند:

```text
models/
├── whisper/         # وزن‌های مدل‌های Whisper (مثل base.pt و large-v3.pt)
├── huggingface/     # مدل‌های تفکیک گوینده Pyannote و کش Transformers
└── torch/           # چک‌پوینت‌های PyTorch Hub
```

</div>

---

## 👤 Credits / سازنده

- **Developer:** [Seyed Shahabeddin Hosseini Bay](https://github.com/Bekend) (سید شهاب الدین حسینی بای)
- **GitHub:** [@Bekend](https://github.com/Bekend)
- **Powered by:** `antigravity`