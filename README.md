# Persian Clinical Conversations Corpus (PCCC)
## پیکره صوتی و متنی گفتگوی بالینی پزشک–بیمار

[![Domain: Healthcare & AI](https://img.shields.io/badge/Domain-Healthcare%20%26%20Clinical%20AI-blue.svg)](#)
[![Audio Format: Linear PCM WAV](https://img.shields.io/badge/Audio-16kHz%20%7C%2016--bit%20%7C%20Mono-green.svg)](#)
[![Language: Persian (Farsi)](https://img.shields.io/badge/Language-Persian%20(fa)-orange.svg)](#)
[![Tasks: STT & Diarization & Clinical NLP](https://img.shields.io/badge/Tasks-STT%20%7C%20Diarization%20%7C%20NLP-purple.svg)](#)

---### مشخصات پژوهش و دست‌اندرکاران (Research Credits)
* **پژوهشگر و گردآورنده (Researcher & Data Collector):** سید شهاب‌الدین حسینی بای (*Seyyed Shahabeddin Hosseini Bay*)
* **اساتید راهنما (Supervisors):**
  * جناب آقای دکتر رضا یزدی (*Dr. Reza Yazdi*)
  * جناب آقای دکتر مهدی یعقوبی (*Dr. Mehdi Yaghoobi*)
## 📑 فهرست مطالب / Table of Contents
1. [بخش فارسی / Persian Section](#-بخش-فارسی-persian-documentation)
   - [مقدمه و چکیده](#۱-مقدمه-و-چکیده-dataset-overview--motivation)
   - [روش‌شناسی جمع‌آوری داده‌ها](#۲-روششناسی-جمعآوری-دادهها-data-collection-methodology)
   - [خط لوله پردازش و معماری سیستم](#۳-خط-لوله-پردازش-و-معماری-سیستم-data-processing-pipeline)
   - [بستر سخت‌افزاری و ارزیابی محاسباتی](#۴-بستر-سختافزاری-و-ارزیابی-محاسباتی-hardware--benchmarking)
   - [تشریح جامع ساختار پوشه‌ها و محتوای فایل‌ها](#۵-تشریح-جامع-ساختار-پوشهها-و-محتوای-فایلها-directory-structure)
   - [مقایسه داده‌های خام در برابر داده‌های پالایش‌شده](#۶-مقایسه-دادههای-خام-در-برابر-دادههای-پالایششده)
   - [کاربردهای پژوهشی](#۷-کاربردهای-پژوهشی-research-applications)
2. [English Section](#-english-section-dataset-datasheet)
   - [Dataset Overview & Motivation](#1-dataset-overview--motivation)
   - [Data Collection Methodology](#2-data-collection-methodology)
   - [Processing Pipeline Architecture](#3-processing-pipeline-architecture)
   - [Hardware & Benchmarking](#4-hardware--benchmarking)
   - [Directory Structure & File Taxonomy](#5-directory-structure--file-taxonomy)
   - [Raw vs. Refined Data Comparison](#6-raw-vs-refined-data-comparison)
   - [Research Applications](#7-research-applications)

---

# 🇮🇷 بخش فارسی (Persian Documentation)

## ۱. مقدمه و چکیده (Dataset Overview & Motivation)
مجموعه داده **PCCC** (پیکره گفتگوی بالینی فارسی) با هدف برطرف کردن کمبود منابع داده‌ای طبیعی و بدون سناریو در حوزه پردازش گفتار و زبان طبیعی بالینی برای زبان فارسی طراحی و جمع‌آوری شده است. اغلب پیکره‌های موجود یا مبتنی بر متون ترجمه‌شده هستند و یا در محیط‌های آزمایشگاهی و کنترل‌شده بازسازی شده‌اند که فاقد چالش‌های مکالمات دنیای واقعی (نویز محیطی، تداخل گفتار، زبان محاوره و لحن‌های بالینی) می‌باشند. 

این پیکره شامل ضبط پیوسته و کامل شیفت‌های کاری **۵ پزشک** در طول روزهای کاری متوالی در بازه‌های زمانی ۳ تا ۸ ساعته بوده و شامل فایل‌های صوتی خام بدون افت کیفیت، خروجی‌های تبدیل گفتار به متن (STT)، نتایج تفکیک گوینده (Speaker Diarization) و نسخه‌های پالایش‌شده بالینی توسط مدل‌های زبانی بزرگ است.

---

## ۲. روش‌شناسی جمع‌آوری داده‌ها (Data Collection Methodology)

### ۲.۱. جامعه آماری و مشخصات بالینی
* **تعداد پزشکان:** ۵ پزشک شاغل در مطب‌های شخصی (۲ پزشک آقا، ۳ پزشک خانم).
* **تخصص‌ها:** 
  * ۱ پزشک عمومی (شامل مراجعین با بیماری‌های مزمن، گوارشی، پوست و مو، استخوان و...).
  * ۴ متخصص اطفال و کودکان (مکالمات سه‌جانبه میان پزشک، مادر/پدر و کودک، پایش رشد، واکسیناسیون و بیماری‌های عفونی).
* **دوره ضبط:** ۲ الی ۶ روز کاری به‌ازای هر پزشک.
* **طول جلسات صوتی:** ۳ تا ۸ ساعت فایل پیوسته در هر شیفت (بدون قطع ضبط حین مکالمات محرمانه یا استراحت جهت حفظ پیوستگی جریان زمان).

### ۲.۲. مشخصات فنی آکوستیک
ضبط صدا با استفاده از اپلیکیشن‌های زمان‌بندی‌شده (Automated Scheduling) بر روی دستگاه‌های اختصاصی بدون نیاز به دخالت پرسنل بالینی انجام پذیرفته است:

| ویژگی فنی | مقدار / مشخصات | دلیل انتخاب آکادمیک |
| :--- | :--- | :--- |
| **فرمت صوتی** | Linear PCM WAV (`.wav`) | نگهداری بدون فشرده‌سازی و بدون افت سیگنال (Lossless) |
| **نرخ نمونه‌برداری (Sampling Rate)** | $16,000\text{ Hz}$ ($16\text{ kHz}$) | استاندارد مدل‌های روز یادگیری عمیق در صوت |
| **عمق بیت (Bit Depth)** | $16\text{-bit Signed}$ | پوشش کامل دامنه دینامیکی بین نجوا و صحبت رسا |
| **کانال صوتی** | تک‌کاناله (Mono) | استاندارد یکنواخت برای شبکه‌های عصبی |
| **محیط صوتی** | Far-field / Clinical In-the-wild | ثبت کامل نویز محیطی، گریه کودک، صدای کاغذ نسخه و موسیقی |

---

## ۳. خط لوله پردازش و معماری سیستم (Data Processing Pipeline)

فرآیند پردازش با یک نرم‌افزار خودکار شامل ۴ فاز اصلی پیاده‌سازی شده است:

```
                  +----------------------------------------------+
                  | فایل صوتی کامل شیفت (WAV, 16kHz, 16bit, Mono)|
                  +----------------------------------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   [۱. تبدیل گفتار به متن (STT)]                     [۲. تفکیک گوینده (Diarization)]
         OpenAI Whisper                                   pyannote.audio
          (large-v3)                                   (Community Pipeline)
                 │                                               │
        سگمنت‌های زمانی متن                                بازه‌های زمانی گویندگان
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                     [۳. تلفیق و تراز زمانی (Merging)]
                      تطبیق زمانی متن با گوینده مربوطه
                      ثبت تداخل‌ها: (overlapped by ...)
                                         │
                                         ▼
                            [پوشه داده‌های اولیه: raw/]
                                         │
                                         ▼
              [۴. پالایش متنی و بازسازی بالینی با مدل زبانی (LLM)]
               ├── سرویس‌های ابری نظیر Google Gemini API
               ├── فریم‌ورک محلی Ollama (کلیه مدل‌های Llama, Qwen و...)
               └── استنتاج کاملاً محلی و مستقیم بدون نیاز به Ollama (Standalone)
                                         │
                                         ▼
                        [پوشه داده‌های نهایی: refined/]
```

### ۳.۱. ماژول تبدیل گفتار به متن (STT)
* **مدل پایه:** `OpenAI Whisper Large-v3`
* **مدیریت نشت حافظه (Memory Leak):** با تقسیم فایل‌های طولانی به قطعات ۵ دقیقه‌ای (Chunking)، مصرف حافظه گرافیکی در حد مجاز تثبیت شد.
* **چالش‌های مدل:** عدم شناخت کامل برخی اسامی داروها، دوزها و بیماری‌ها در زبان فارسی و وقوع توهم تکرار کلمات در زمان سکوت.

### ۳.۲. ماژول تفکیک گوینده (Speaker Diarization)
* **مدل پایه:** `pyannote/speaker-diarization-3.1` (نسخه رایگان Community)
* **عملکرد:** سرعت استنتاج فوق‌العاده بالا (پردازش فایل ۸ ساعته در حدود ۲۰ الی ۳۰ دقیقه روی GPU).
* **محدودیت:** این نسخه فاقد توانایی انتساب هویت سراسری (Cross-session Identity) بوده و گویندگان را صرفاً در یک فایل و به‌صورت محلی خوشه‌بندی می‌کند (`SPEAKER_00`, `SPEAKER_01`, ...).

### ۳.۳. تلفیق و هم‌ترازی (Merge)
تطبیق بازه‌های زمانی خروجی STT با گویندگان استخراج‌شده انجام شده و در صورت وقوع هم‌زمان کلام، برچسب ساختاریافته `(overlapped by ...)` درج می‌شود.

### ۳.۴. فاز پالایش با مدل‌های زبانی (LLM Refinement)
نرم‌افزار به‌گونه‌ای طراحی شده که کاربر در انتخاب مدل زبانی آزادی کامل دارد:
1. **APIهای ابری:** اتصال به Gemini Flash/Pro برای سرعت و دقت بالا.
2. **اتصال به فریم‌ورک Ollama:** قابلیت اتصال به انواع مدل‌های محلی خانواده Qwen ،Llama و Mistral.
3. **اجرای محلی و Standalone:** پشتیبانی از اسکریپت‌های بومی برای اجرای مستقیم مدل‌ها بر روی PyTorch و فرمت‌های GGUF بدون وابستگی به نصب Ollama.
* **دستاورد پالایش:** اصلاح دیکته داروها، حذف توهمات سکوت، و نگاشت کدهای تصادفی گوینده به نقش‌های معنادار بالینی (`doctor` و `patient_N`).

---

## ۴. بستر سخت‌افزاری و ارزیابی محاسباتی (Hardware & Benchmarking)

* **پردازنده گرافیکی (GPU):** NVIDIA GeForce RTX 3060 با ۱۲ گیگابایت VRAM
* **پردازنده مرکزی (CPU):** Intel Core i5-12400F
* **حافظه رم:** ۶۴ گیگابایت DDR4
* **معیار سرعت پردازش (Benchmark):** پردازش یک فایل صوتی کامل ۸ ساعته (شامل STT و Diarization) در حدود **۶۰ دقیقه** انجام می‌پذیرد (سرعت پردازش تقریباً ۸ برابر سریع‌تر از زمان واقعی: $\text{RTF} \approx 0.125$).

---

## ۵. تشریح جامع ساختار پوشه‌ها و محتوای فایل‌ها (Directory Structure)

```text
PCCC_Dataset/
├── final data/
│   ├── Session_Full_20260912_142552_b2fdf1/           # پوشه یک جلسه ضبط‌شده کامل
│   │   ├── Session_Full_XXXXXXXX_XXXXXX.wav           # فایل صوتی خام و دست‌نخورده
│   │   ├── Session_Full_..._ai_refined_transcript.txt # متن نهایی تمیز در ریشه جلسه
│   │   ├── status.json                                # مشخصات فنی، هایپرپارامترها و لاگ
│   │   │
│   │   ├── checkpoints/                               # چک‌پوینت‌های ۵ دقیقه‌ای پایداری حافظه
│   │   │   ├── chunk_000.json
│   │   │   ├── chunk_001.json
│   │   │   └── ...
│   │   │
│   │   ├── raw/                                       # خروجی‌های اولیه و بدون روتوش
│   │   │   ├── *_stt_timestamps.txt                   # خروجی خام Whisper با زمان‌بندی
│   │   │   ├── *_diarization.txt                      # نوبت‌های خام گویندگان از pyannote
│   │   │   └── *_merged_transcript.txt                # ادغام خام صوت و گوینده
│   │   │
│   │   └── refined/                                   # خروجی‌های اصلاح‌شده و بازسازی‌شده
│   │       ├── *_ai_refined_transcript.txt            # رونوشت تمیز نهایی با اسامی علمی و نقش‌ها
│   │       ├── *_diarization.txt                      # نوبت‌های گفتار همگام‌شده با نقش‌های جدید
│   │       ├── *_merged_transcript.txt                # متن تلفیقی بازبینی‌شده نهایی
│   │       └── *_stt_timestamps.txt                   # قطعات زمانی متنی اصلاح‌شده
```

### شرح تفکیکی فایل‌ها:
* `status.json`: شامل نسخه مدل‌ها، پارامترهای اجرایی، نام فایل، پرامپت اولیه تزریق‌شده و لاگ وضعیت اتمام کار.
* `checkpoints/chunk_XXX.json`: حاوی ساختار JSON برای بازه‌های ۳۰۰ ثانیه‌ای صوت؛ مناسب برای بازیابی در صورت قطعی یا تحلیل فاز به فاز.
* `raw/*`: مناسب برای ارزیابی عملکرد واقعی و خام مدل‌های Whisper و Pyannote بدون دستکاری.
* `refined/*`: فایل‌های تمیز و آماده جهت آموزش سیستم‌های پزشکی، استخراج خلاصه بیمار و ارزیابی NLP.

---

## ۶. مقایسه داده‌های خام در برابر داده‌های پالایش‌شده

### نمونه داده خام (`raw/*_merged_transcript.txt`)
```text
[00:01:22.000 --> 00:01:30.000] patient_1: دوره یکمان استامینوفن میریم با دینتاکیل دوره این دندونشه و میرونن طبش بند نمیان پرسید
[00:01:30.000 --> 00:01:51.000] doctor: این هم معمولا تبهای ویروسی است؛ یعنی دندان یک تب خفید میدهید...
[00:05:00.000 --> 00:05:36.000] patient_1: با این حالات، با این حالات، با این حالات...
```

### نمونه داده پالایش‌شده (`refined/*_ai_refined_transcript.txt`)
```text
[00:01:22.000 --> 00:01:30.000] patient_1: دوره یک‌ماهه استامینوفن می‌دهیم با دیفن‌هیدرامین، دوره این دندانش است و می‌آورند تبش بند نمی‌آید، پرسید.
[00:01:30.000 --> 00:01:51.000] doctor: این هم معمولاً تب‌های ویروسی است؛ یعنی دندان یک تب خفیف می‌دهد، در طی چند دقیقه، بخشید، دو سه ساعت یعنی خوب می‌شود...
[00:01:51.000 --> 00:01:53.000] doctor (overlapped by patient_1): دست و پاها خنک است.
[00:01:53.000 --> 00:01:55.000] patient_1: نه، اتفاقاً دست‌هایشان داغ است.
```

---

## ۷. کاربردهای پژوهشی (Research Applications)
1. **آموزش و Fine-Tuning مدل‌های STT تخصصی فارسی:** استفاده از زوج صوت و متن پالایش‌شده جهت ارتقای دقت اصطلاحات درمانی.
2. **ارزیابی تفکیک گوینده در شرایط تداخل شدید:** مطالعه بر روی هم‌پوشانی‌های طبیعی کلام میان مادر، کودک و پزشک.
3. **خلاصه‌سازی بالینی و ایجاد پرونده الکترونیک (EHR / SOAP Notes):** تست و ارزیابی توانایی مدل‌های زبانی در استخراج علائم اصلی بیماری (Chief Complaint)، شرح حال و برنامه درمان.
4. **تحلیل و مطالعه پدیده توهم در پردازش صوت (STT Hallucination Research).**

---
---

# 🇬🇧 English Section (Dataset Datasheet)

## 1. Dataset Overview & Motivation
The **Persian Clinical Conversations Corpus (PCCC)** is a domain-specific, in-the-wild audio-textual dataset designed to bridge the severe shortage of conversational medical data in Persian. Most existing clinical datasets are either synthesized, translated from English, or recorded in artificial settings. PCCC captures spontaneous, unscripted dialogues occurring in real-world clinical consultations.

The corpus comprises continuous, multi-hour recordings across shifts of **5 practicing physicians** (3 to 8 hours per session) over multiple consecutive working days. It features raw lossless audio, intermediate processing checkpoints, direct acoustic model transcripts, speaker turns, and LLM-refined clinical dialogues.

---

## 2. Data Collection Methodology

### 2.1. Cohort & Clinical Setup
* **Physicians:** 5 licensed medical practitioners operating in outpatient clinics (2 males, 3 females).
* **Specialties:**
  * 1 General Practitioner (covering adult internal medicine, dermatology, gastroenterology, etc.).
  * 4 Pediatric Specialists (covering triadic discussions: doctor-parent-child, infant examinations, developmental milestones, vaccination, and seasonal pediatric infections).
* **Duration:** Between 2 to 6 working days per practitioner.
* **Recording Length:** 3 to 8 continuous hours per audio file, matching the entire working shift without manual pauses.

### 2.2. Acoustic Specifications
Audio was captured via automated scheduling software installed on dedicated Android devices deployed in the examination room:

| Parameter | Specification | Technical Motivation |
| :--- | :--- | :--- |
| **Container Format** | Linear PCM WAV (`.wav`) | Lossless uncompressed raw audio signal preservation |
| **Sampling Rate** | $16,000\text{ Hz}$ ($16\text{ kHz}$) | Standard input frequency for contemporary speech models |
| **Bit Depth** | $16\text{-bit Signed Integer}$ | Preserves dynamic range between whispers and loud voices |
| **Channels** | Mono (Single Channel) | Uniform standard for deep neural network audio pipelines |
| **Acoustic Environment**| Far-field / Clinical In-the-wild | Captures background clinical noise, child crying, ambient sounds |

---

## 3. Processing Pipeline Architecture

The automated backend consists of four primary processing phases:

```
                  +----------------------------------------------+
                  |  Full Shift Raw Audio (WAV, 16kHz, 16-bit)   |
                  +----------------------------------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
         [1. Speech-to-Text]                            [2. Diarization]
           OpenAI Whisper                                pyannote.audio
            (large-v3)                                (Community Pipeline)
                 │                                               │
          Time-stamped Text                               Speaker Bounds
              Segments                                      and Turns
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
                     [3. Alignment & Merging (Temporal Overlap)]
                      Assign speaker identity to each text segment
                      Tag overlaps: (overlapped by ...)
                                         │
                                         ▼
                            [Raw Directory: raw/]
                                         │
                                         ▼
                     [4. Post-Processing & Clinical LLM Refinement]
               ├── Cloud-based APIs (e.g., Google Gemini Flash/Pro)
               ├── Local Ollama Framework (Llama, Qwen, Mistral series)
               └── Standalone Local Inference (Direct PyTorch/GGUF execution)
                                         │
                                         ▼
                         [Refined Directory: refined/]
```

### 3.1. Speech-to-Text (STT) Module
* **Base Model:** `OpenAI Whisper Large-v3`
* **VRAM Stabilization:** Continuous multi-hour audio was processed using **5-minute dynamic chunking** combined with active garbage collection to eliminate CUDA Out-Of-Memory (OOM) leaks.
* **Inherent Limitations:** Challenges in recognizing localized pharmaceutical trade names and occasional repetition hallucinations during silent examination phases.

### 3.2. Speaker Diarization Module
* **Base Model:** `pyannote/speaker-diarization-3.1` (Community Release)
* **Performance:** Extremely efficient inference, processing an 8-hour audio session in 20–30 minutes on consumer-grade GPUs.
* **Constraint:** The community release clusters speakers locally per session without global enrolment support (`SPEAKER_00`, `SPEAKER_01`, ...).

### 3.3. Alignment & Merging
Matches word-level STT boundaries with speaker segments. Speech overlaps are explicitly tagged with `(overlapped by ...)`.

### 3.4. LLM Refinement Architecture
The software provides modular flexibility for clinical refinement:
1. **Cloud APIs:** Seamless connection to Gemini API.
2. **Ollama Integration:** Seamless communication with any local LLM served via Ollama.
3. **Native Standalone Local Inference:** Fully capable of running local open-weights models (via PyTorch or GGUF) directly **without requiring Ollama**.
* **Key Tasks:** Normalization of medical terms, filtering silence artifacts, and mapping arbitrary speaker tags to clinical roles (`doctor`, `patient_1`, `patient_2`).

---

## 4. Hardware & Benchmarking

* **GPU:** NVIDIA GeForce RTX 3060 (12 GB GDDR6 VRAM)
* **CPU:** Intel Core i5-12400F
* **System RAM:** 64 GB DDR4
* **Throughput Benchmark:** Complete end-to-end STT and Diarization for an **8-hour continuous file takes ~60 minutes** ($\text{RTF} \approx 0.125$, executing approximately $8\times$ faster than real-time).

---

## 5. Directory Structure & File Taxonomy

```text
PCCC_Dataset/
├── final data/
│   ├── Session_Full_20260912_142552_b2fdf1/           # Complete recording session folder
│   │   ├── Session_Full_XXXXXXXX_XXXXXX.wav           # Pristine master audio file
│   │   ├── Session_Full_..._ai_refined_transcript.txt # Clean final transcript
│   │   ├── status.json                                # Run parameters, configuration & logs
│   │   │
│   │   ├── checkpoints/                               # 5-minute fault-tolerant checkpoints
│   │   │   ├── chunk_000.json
│   │   │   ├── chunk_001.json
│   │   │   └── ...
│   │   │
│   │   ├── raw/                                       # Unaltered pipeline outputs
│   │   │   ├── *_stt_timestamps.txt                   # Raw Whisper output with timestamps
│   │   │   ├── *_diarization.txt                      # Raw pyannote speaker intervals
│   │   │   └── *_merged_transcript.txt                # Merged pre-LLM alignment
│   │   │
│   │   └── refined/                                   # Post-processed final assets
│   │       ├── *_ai_refined_transcript.txt            # Final clinically refined transcript
│   │       ├── *_diarization.txt                      # Synced speaker intervals
│   │       ├── *_merged_transcript.txt                # Final merged transcript
│   │       └── *_stt_timestamps.txt                   # Refined text segments
```

### File Specifications:
* `status.json`: Contains model identifiers, processing parameters, and task execution progress.
* `checkpoints/chunk_XXX.json`: Serialized representations of speech segments and speaker boundaries per 300-second audio slice.
* `raw/*`: Preserves native model behavior, ideal for benchmark evaluations of acoustic and STT models.
* `refined/*`: Standardized, clinically accurate assets ready for downstream NLP tasks.

---

## 6. Raw vs. Refined Data Comparison

### Raw Output (`raw/*_merged_transcript.txt`)
```text
[00:01:22.000 --> 00:01:30.000] patient_1: دوره یکمان استامینوفن میریم با دینتاکیل دوره این دندونشه و میرونن طبش بند نمیان پرسید
[00:01:30.000 --> 00:01:51.000] doctor: این هم معمولا تبهای ویروسی است؛ یعنی دندان یک تب خفید میدهید...
[00:05:00.000 --> 00:05:36.000] patient_1: با این حالات، با این حالات، با این حالات...
```

### Refined Output (`refined/*_ai_refined_transcript.txt`)
```text
[00:01:22.000 --> 00:01:30.000] patient_1: دوره یک‌ماهه استامینوفن می‌دهیم با دیفن‌هیدرامین، دوره این دندانش است و می‌آورند تبش بند نمی‌آید، پرسید.
[00:01:30.000 --> 00:01:51.000] doctor: این هم معمولاً تب‌های ویروسی است؛ یعنی دندان یک تب خفیف می‌دهد، در طی چند دقیقه، بخشید، دو سه ساعت یعنی خوب می‌شود...
[00:01:51.000 --> 00:01:53.000] doctor (overlapped by patient_1): دست و پاها خنک است.
[00:01:53.000 --> 00:01:55.000] patient_1: نه، اتفاقاً دست‌هایشان داغ است.
```

---

## 7. Research Applications
1. **Domain-Adapted Persian STT:** Fine-tuning acoustic and sequence-to-sequence models on spontaneous medical vocabulary.
2. **Overlapping Speech Diarization:** Benchmarking conversational turn-taking during multi-party pediatric consults.
3. **Automated Clinical Summarization:** Evaluating LLMs on converting unconstrained spoken dialogues into structured medical records (SOAP notes).
4. **Hallucination Detection:** Analyzing repetitive patterns generated by speech decoders during non-verbal audio segments.
