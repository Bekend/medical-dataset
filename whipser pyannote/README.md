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

# استودیو تبدیل گفتار به متن Whisper و تفکیک گوینده Pyannote[cite: 1]

برنامه‌ای که فایل‌های صوتی با فرمت `.wav` را به عنوان ورودی دریافت کرده و آن‌ها را با استفاده از **OpenAI Whisper** و **Pyannote Audio** (پایپ‌لاین عمومی) پردازش می‌کند[cite: 1].

این برنامه برای هر فایل صوتی پردازش‌شده، دو فایل خروجی اصلی تولید می‌کند[cite: 1]:
1. **فایل تفکیک گوینده (`*_diarization.txt`)**: مشخص می‌کند چه کسی در چه بازه زمانی دقیقی صحبت کرده است[cite: 1].
2. **فایل تبدیل گفتار به متن همراه با برچسب زمان (`*_stt_timestamps.txt`)**: متن پیاده‌شده توسط OpenAI Whisper را همراه با برچسب‌های زمانی بخش‌ها یا کلمات نمایش می‌دهد[cite: 1].
*(امتیاز ویژه: یک متن ادغام‌شده که خروجی هر دو بخش را تطبیق داده و سخنان هر گوینده را مشخص می‌کند).*[cite: 1]

---

## راه‌اندازی سریع (نصب روی سیستم جدید)[cite: 1]

### ۱. نصب خودکار با یک کلیک (ویندوز)[cite: 1]
روی فایل **`install.bat`** دوبار کلیک کنید (یا دستور `python install.py` را اجرا کنید)[cite: 1].

این نصب‌کننده خودکار مراحل زیر را انجام می‌دهد:
- نسخه پایتون شما را بررسی می‌کند (پایتون ۳.۱۰ تا ۳.۱۲)[cite: 1].
- کارت گرافیک NVIDIA را به صورت خودکار شناسایی می‌کند[cite: 1].
- کتابخانه PyTorch را با شتاب‌دهنده **CUDA 12.4** (یا نسخه پردازنده مرکزی/CPU در صورت نبود کارت گرافیک) نصب می‌کند[cite: 1].
- تمام کتابخانه‌های بک‌اند (`openai-whisper`، `pyannote.audio`، `fastapi`، `uvicorn`، `soundfile`، `scipy`، `transformers` و غیره) را نصب می‌کند[cite: 1].
- یک بررسی خودکار برای اطمینان از صحت نصب اجرا می‌کند[cite: 1].

### ۲. نصب دستی[cite: 1]
```bash
# اختیاری: نصب PyTorch به همراه CUDA (اگر کارت گرافیک NVIDIA دارید)
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu124](https://download.pytorch.org/whl/cu124)

# نصب تمام کتابخانه‌های بک‌اند
pip install -r requirements.txt
```[cite: 1]

### ۳. اجرای برنامه تحت وب[cite: 1]
روی فایل **`run.bat`** دوبار کلیک کنید یا دستور زیر را اجرا نمایید:
```bash
python app.py
```[cite: 1]

۳. **باز کردن مرورگر**:
   - به آدرس `http://127.0.0.1:8000` بروید[cite: 1].
   - فایل `.wav` خود را بکشید و رها کنید (Drag & Drop)[cite: 1].
   - **توکن دسترسی هاگینگ فیس (Hugging Face Access Token)** خود را وارد کنید (جهت دسترسی به مدل تفکیک گوینده Pyannote در `https://hf.co/pyannote/speaker-diarization-3.1`)[cite: 1].
   - مدل Whisper مورد نظر خود را انتخاب کنید (`base`، `small`، `medium`، `large-v3`)[cite: 1].
   - روی دکمه **Start Processing Audio** کلیک کنید[cite: 1].
   - پیش‌نمایش هر دو فایل خروجی را مشاهده کرده و آن‌ها را مستقیماً از محیط کاربری دانلود کنید![cite: 1]

---

## رابط خط فرمان (CLI)[cite: 1]

همچنین می‌توانید پردازش فایل‌های صوتی را به صورت مستقیم و بدون نیاز به رابط کاربری گرافیکی (Headless) از خط فرمان اجرا کنید:[cite: 1]

```bash
python cli.py sample.wav --hf_token YOUR_HF_TOKEN --whisper_model base --output_dir ./output
```[cite: 1]

این دستور خروجی‌های زیر را به صورت خودکار ایجاد می‌کند:
- `./output/sample_diarization.txt` (فایل شماره ۱: چه کسی در چه زمانی صحبت کرده است)[cite: 1]
- `./output/sample_stt_timestamps.txt` (فایل شماره ۲: متن پیاده‌شده توسط Whisper همراه با برچسب‌های زمانی)[cite: 1]
- `./output/sample_merged_transcript.txt` (فایل خروجی ادغام‌شده)[cite: 1]

---

## نیازمندی‌ها و دسترسی هاگینگ فیس[cite: 1]

- **پایتون**: نسخه ۳.۱۰ یا ۳.۱۱[cite: 1]
- **دسترسی به مدل‌های عمومی Pyannote**: مدل `pyannote/speaker-diarization-3.1` مستلزم پذیرش قوانین کاربری در سایت Hugging Face است[cite: 1]:
  1. به آدرس https://hf.co/pyannote/speaker-diarization-3.1 رفته و شرایط را تأیید کنید[cite: 1].
  2. به آدرس https://hf.co/pyannote/segmentation-3.0 رفته و شرایط را تأیید کنید[cite: 1].
  3. از طریق آدرس https://hf.co/settings/tokens یک توکن دسترسی بسازید و آن را داخل برنامه قرار دهید[cite: 1].

---

## پوشه مدل‌های محلی (`models/`)[cite: 1]

تمام وزن‌ها و کش‌های دانلودشده مدل‌ها به صورت محلی در پوشه پروژه ذخیره می‌شوند[cite: 1]:
- `models/whisper/`: وزن‌های مدل‌های Whisper (مانند `base.pt`، `tiny.pt`، `large-v3.pt` و غیره)[cite: 1]. همچنین می‌توانید فایل‌های `.pt` را مستقیماً داخل پوشه `models/` یا `models/whisper/` قرار دهید[cite: 1].
- `models/huggingface/`: مدل‌های تفکیک گوینده Pyannote و کش مدل‌های Transformers هاگینگ فیس[cite: 1].
- `models/torch/`: چک‌پوینت‌های PyTorch hub[cite: 1].
