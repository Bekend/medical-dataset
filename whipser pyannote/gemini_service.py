import os
import re
import json
import urllib.request
import urllib.error

DEFAULT_GEMINI_MODELS = [
    {"name": "gemini:gemini-3.5-flash-lite", "label": "⚡ Gemini 3.5 Flash Lite (Ultra Fast Cloud - Recommended)"},
    {"name": "gemini:gemini-3.1-flash-lite", "label": "⚡ Gemini 3.1 Flash Lite (Ultra Fast Cloud)"},
    {"name": "gemini:gemini-3.1-flash", "label": "⚡ Gemini 3.1 Flash (High Performance Cloud)"},
    {"name": "gemini:gemini-3.1-pro", "label": "🧠 Gemini 3.1 Pro (Deep Reasoning Cloud)"},
    {"name": "gemini:gemini-2.5-flash-lite", "label": "☁️ Gemini 2.5 Flash Lite"},
    {"name": "gemini:gemini-2.5-flash", "label": "☁️ Gemini 2.5 Flash"},
    {"name": "gemini:gemini-2.5-pro", "label": "🧠 Gemini 2.5 Pro"}
]

DEFAULT_AI_POST_PROCESS_PROMPT = """شما یک پزشک متخصص و بازساز ارشد پرونده‌های صوتی کلینیک و مطب پزشکی هستید.
متن ورودی زیر مکالمه صوتی پیاده‌سازی شده از گفتگوی بین پزشک و بیماران در مطب است.

وظایف الزامی و بدون تغییر شما:
۱. تعیین و تفکیک دقیق نقش گویندگان و حفظ شماره بیماران (Doctor vs Patients):
   - برچسب "doctor:": برای پزشک (فردی که سوالات تشخیصی و معاینه می‌پرسد، علائم را بررسی می‌کند و دستور مصرف دارو یا آزمایش می‌دهد).
   - حفظ شماره دقیق بیماران: در صورت حضور چند بیمار یا همراه مختلف (مانند patient_1, patient_2, patient_3, ...)، شماره هر بیمار را عیناً و با دقت کامل در خروجی حفظ کنید: "patient_1:", "patient_2:", "patient_3:", ... هرگز شماره بیمار را حذف نکنید و آن را به "patient:" عمومی تبدیل نکنید.
   - اگر فقط یک بیمار در کل مکالمه حضور دارد، از برچسب "patient:" استفاده کنید.
   - اگر گویندگان با برچسب‌های بدون نام مانند SPEAKER_00, SPEAKER_01, SPEAKER_02 آمده‌اند، آن‌ها را بر اساس مکالمه به doctor: و patient_1:, patient_2: تبدیل کنید.
   - هرگز از برچسب نامشخص و خنثی "SPEAKER:" استفاده نکنید.
۲. حفظ کامل برچسب‌های تداخل کلامی و صحبت همزمان (Overlapped Talks):
   - اگر در ورودی هر خط دارای عبارت تداخل کلامی است (مانند "doctor (overlapped by patient_1):" یا "patient_1 (overlapped by doctor):" یا "patient_2 (overlapped by doctor):")، عبارت داخل پرانتز یعنی "(overlapped by ...)" را دقیقاً و به طور کامل در خروجی بعد از نام گوینده حفظ کنید.
   - هرگز خطوط تداخل کلامی را حذف یا در خط دیگر ادغام نکنید.
۳. اصلاح و روان‌سازی اصطلاحات پزشکی و خطاهای شنیداری:
   - املای داروها، بیماری‌ها، آزمایش‌ها و اصطلاحات پزشکی را به شکل صحیح، علمی و استاندارد فارسی اصلاح کنید.
   - کلمات عامیانه، جویده‌شده یا ناقص را بدون تحریف پیام اصلی به فارسی سلیس و روان تبدیل کنید.
۴. پالایش و حذف نویزها و توهمات صوتی:
   - جملات نامربوط ناشی از موزیک پس‌زمینه یا تکرار کلمات بی‌معنی را پالایش کنید.
۵. حفظ ساختار خط‌به‌خط و زمان‌بندی:
   - ساختار زمان‌بندی [HH:MM:SS.mmm --> HH:MM:SS.mmm] را در ابتدای هر خط به طور کامل و بدون کوچک‌ترین تغییری حفظ کنید.
   - تمام خطوط دارای زمان‌بندی ورودی را به ترتیب بازسازی کنید و از حذف، خلاصه کردن یا ادغام بی‌مورد خطوط خودداری نمایید.

قالب خروجی دقیق خط‌به‌خط:
[00:00:30.000 --> 00:00:32.000] patient_1: از دیشب تب شدید دارد.
[00:00:32.000 --> 00:00:34.000] doctor (overlapped by patient_1): تبش چقدر بوده؟
[00:00:34.500 --> 00:00:38.000] patient_2 (overlapped by doctor): منم همراهش بودم، دیشب بالای ۳۹ درجه بود.
"""

def sanitize_ai_prompt(prompt: str) -> str:
    """
    Sanitizes AI refinement prompt.
    If empty or matches legacy single-patient/overlap-stripping prompt, upgrades to DEFAULT_AI_POST_PROCESS_PROMPT.
    """
    if not prompt or not prompt.strip():
        return DEFAULT_AI_POST_PROCESS_PROMPT

    # Legacy indicators from older versions
    legacy_indicators = [
        'هر خط باید منحصراً و حتماً با برچسب "doctor:" یا "patient:" مشخص شود',
        'هر خط باید منحصرا و حتما با برچسب "doctor:" یا "patient:" مشخص شود',
        'هر خط باید منحصراً و حتماً با برچسب',
        'هر خط باید منحصرا و حتما با برچسب',
    ]
    for leg in legacy_indicators:
        if leg in prompt:
            return DEFAULT_AI_POST_PROCESS_PROMPT

    if "patient_1" not in prompt and ("Doctor vs Patient" in prompt or "doctor:" in prompt):
        return DEFAULT_AI_POST_PROCESS_PROMPT

    return prompt

def _refine_single_gemini_chunk(
    chunk_text: str,
    clean_model: str,
    api_key: str,
    system_prompt: str,
    max_retries: int = 5
) -> str:
    import time
    system_prompt = sanitize_ai_prompt(system_prompt)

    endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key.strip()}"

    combined_prompt = f"{system_prompt}\n\nتأکید خیلی مهم و حیاتی:\n۱. تمام خطوط ورودی را خط‌به‌خط پردازش کنید و هیچ خط دارای زمان‌بندی را حذف یا ادغام نکنید.\n۲. شماره بیماران (patient_1:, patient_2:, ...) را دقیقاً حفظ کنید.\n۳. عبارت‌های تداخل کلامی (overlapped by ...) را دقیقاً بعد از نام گوینده حفظ کنید.\n۴. هرگز از برچسب عمومی SPEAKER: استفاده نکنید.\n\n[INPUT DIALOGUE TO RECONSTRUCT]\n{chunk_text}\n\n[RECONSTRUCTED CLINICAL TRANSCRIPT]:\n"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined_prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192
        }
    }

    data_bytes = json.dumps(payload).encode("utf-8")

    for attempt in range(max_retries):
        req = urllib.request.Request(
            endpoint_url,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                candidates = res.get("candidates", [])
                if not candidates:
                    return chunk_text
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    return chunk_text
                refined_text = parts[0].get("text", "").strip()
                # Strip markdown code fences if present
                refined_text = re.sub(r'^```[a-zA-Z0-9_-]*\s*\n', '', refined_text)
                refined_text = re.sub(r'\n```\s*$', '', refined_text).strip()
                return refined_text
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                sleep_time = (attempt + 1) * 8
                print(f"Gemini API rate limit (HTTP {e.code}). Backing off for {sleep_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(sleep_time)
            else:
                print(f"Gemini chunk HTTP Error {e.code}: {e}")
                return chunk_text
        except Exception as e:
            print(f"Gemini chunk error: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                return chunk_text

    return chunk_text

def run_gemini_refinement(
    transcript_text: str,
    model_name: str,
    api_key: str,
    system_prompt: str,
    progress_cb=None
) -> str:
    """
    Sends transcript text to Google Gemini REST API for clinical post-processing & refinement.
    Takes advantage of Gemini's 1M+ context window using large 80-line dialogue blocks (~3,500 words each).
    Enforces Request-Per-Minute (RPM) rate limiting (3.5s delay) and exponential backoff retries on HTTP 429.
    """
    import time
    system_prompt = sanitize_ai_prompt(system_prompt)
    if not api_key or not api_key.strip():
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Google Gemini API Key is required. Please enter your GEMINI_API_KEY in the app settings.")

    clean_model = model_name.replace("gemini:", "").strip()
    if not clean_model:
        clean_model = "gemini-3.5-flash-lite"

    lines = transcript_text.splitlines()
    header_lines = []
    dialogue_blocks = []
    current_block = []

    # Large context block: 80 dialogue lines (~3,500 words per block)
    # Reduces 60+ API calls down to ~10-12 for a 4-hour consultation!
    BLOCK_SIZE = 80

    for line in lines:
        if line.startswith("=") or line.startswith("Source File") or line.startswith("SPEAKER-ATTRIBUTED"):
            header_lines.append(line)
        elif line.strip().startswith("[") and "-->" in line:
            if len(current_block) >= BLOCK_SIZE:
                dialogue_blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        elif line.strip():
            current_block.append(line)

    if current_block:
        dialogue_blocks.append("\n".join(current_block))

    if not dialogue_blocks:
        return _refine_single_gemini_chunk(transcript_text, clean_model, api_key, system_prompt)

    total_blocks = len(dialogue_blocks)
    refined_blocks = []

    for idx, block in enumerate(dialogue_blocks):
        if progress_cb:
            pct = 90 + int(((idx + 1) / total_blocks) * 8)
            start_line = idx * BLOCK_SIZE + 1
            end_line = min((idx + 1) * BLOCK_SIZE, len(lines))
            progress_cb(pct, f"Gemini Cloud Refinement ({clean_model}): Block {idx+1}/{total_blocks}...", f"Refining dialogue lines {start_line} -> {end_line}")

        refined = _refine_single_gemini_chunk(block, clean_model, api_key, system_prompt)
        refined_blocks.append(refined)
        
        # Pacing delay to stay well under Gemini free/standard tier Requests-Per-Minute (RPM) limits
        if idx < total_blocks - 1:
            time.sleep(3.5)

    header_str = "\n".join(header_lines) + "\n\n" if header_lines else ""
    return header_str + "\n\n".join(refined_blocks)
