import urllib.request
import json
import os
import re

def get_ollama_models(base_url: str = "http://127.0.0.1:11434") -> list:
    """
    Fetches list of model names currently installed on local Ollama instance.
    """
    try:
        url = base_url.rstrip("/") + "/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "WhisperPyannoteApp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception as e:
        print(f"Ollama get_models error: {e}")
        return []

from gemini_service import DEFAULT_AI_POST_PROCESS_PROMPT, sanitize_ai_prompt

def _refine_single_chunk(
    chunk_text: str,
    model_name: str,
    system_prompt: str,
    base_url: str
) -> str:
    """
    Refines a single transcript text block via Ollama API with explicit 16k context (num_ctx=16384).
    Neutralizes input speaker tags to force active speaker role classification and clinical reconstruction.
    """
    system_prompt = sanitize_ai_prompt(system_prompt)
    base = base_url.rstrip("/")
    options = {
        "num_ctx": 16384,   # Allocate up to 16,384 tokens context window
        "temperature": 0.2, # Low temperature for deterministic factual clinical corrections
        "num_gpu": 99       # Force 100% of model layers onto NVIDIA GPU VRAM
    }

    # Method 1: Generate API (/api/generate)
    gen_url = f"{base}/api/generate"
    combined_prompt = f"{system_prompt}\n\n[INPUT TRANSCRIPT TO REFINE]\n{chunk_text}\n\n[REFINED TRANSCRIPT]:\n"
    gen_payload = {
        "model": model_name,
        "prompt": combined_prompt,
        "options": options,
        "stream": False
    }

    try:
        data_bytes = json.dumps(gen_payload).encode("utf-8")
        req = urllib.request.Request(gen_url, data=data_bytes, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            out = res.get("response", "").strip()
            if out:
                out = re.sub(r'^```[a-zA-Z0-9_-]*\s*\n', '', out)
                out = re.sub(r'\n```\s*$', '', out).strip()
                return out
    except Exception as e_gen:
        print(f"Ollama /api/generate attempt warning: {e_gen}")

    # Method 2: Chat API (/api/chat) fallback
    chat_url = f"{base}/api/chat"
    chat_payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"لطفاً تمام خطوط دارای زمان‌بندی مکالمه زیر را خط‌به‌خط تصحیح و پالایش کنید (شماره بیماران و تداخل‌های کلامی را حفظ نمایید):\n\n{chunk_text}"}
        ],
        "options": options,
        "stream": False
    }

    try:
        data_bytes = json.dumps(chat_payload).encode("utf-8")
        req = urllib.request.Request(chat_url, data=data_bytes, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            out = res.get("message", {}).get("content", "").strip()
            if out:
                out = re.sub(r'^```[a-zA-Z0-9_-]*\s*\n', '', out)
                out = re.sub(r'\n```\s*$', '', out).strip()
                return out
    except Exception as e_chat:
        print(f"Ollama /api/chat attempt warning: {e_chat}")

    return chunk_text

def run_ollama_refinement(
    transcript_text: str,
    model_name: str = "gemma3:12b",
    system_prompt: str = "",
    base_url: str = "http://127.0.0.1:11434",
    cooling_pause_sec: float = 0.0,
    progress_cb = None,
    is_cancelled_cb = None
) -> str:
    """
    Sends transcript text to local Ollama AI model for post-processing & refinement.
    Handles extra large transcripts (e.g. 63k+ characters / 80KB) by slicing into 25-line dialogue blocks,
    processing each block with num_ctx=16384, and inserting GPU thermal cooling pauses to keep temps ~60°C.
    """
    import time
    if not transcript_text or not transcript_text.strip():
        return ""

    system_prompt = sanitize_ai_prompt(system_prompt)

    # For small transcripts (< 8000 characters), process directly in 1 pass
    if len(transcript_text) <= 8000:
        return _refine_single_chunk(transcript_text, model_name, system_prompt, base_url)

    # For large transcripts (e.g. 63k characters / 80KB), slice by dialogue blocks
    lines = transcript_text.splitlines()
    
    header_lines = []
    dialogue_blocks = []
    
    current_block = []
    for line in lines:
        if line.startswith("=") or line.startswith("Source File") or line.startswith("SPEAKER-ATTRIBUTED"):
            header_lines.append(line)
        elif line.strip().startswith("[") and "-->" in line:
            if len(current_block) >= 25:
                dialogue_blocks.append("\n".join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        elif line.strip():
            current_block.append(line)
            
    if current_block:
        dialogue_blocks.append("\n".join(current_block))

    if not dialogue_blocks:
        return _refine_single_chunk(transcript_text, model_name, system_prompt, base_url)

    total_blocks = len(dialogue_blocks)
    refined_blocks = []

    for idx, block in enumerate(dialogue_blocks):
        if is_cancelled_cb and is_cancelled_cb():
            return transcript_text

        if progress_cb:
            pct = 90 + int(((idx + 1) / total_blocks) * 8)
            progress_cb(pct, f"Ollama AI Refinement ({model_name}): Processing Block {idx+1}/{total_blocks}...", f"Refining block {idx+1}/{total_blocks} (Thermal Cooling Active)")

        refined = _refine_single_chunk(block, model_name, system_prompt, base_url)
        refined_blocks.append(refined)

        # GPU Thermal Cooling Pause between inference blocks to keep temperatures ~60°C
        if cooling_pause_sec > 0 and idx < total_blocks - 1:
            time.sleep(cooling_pause_sec)

    header_str = "\n".join(header_lines) + "\n\n" if header_lines else ""
    return header_str + "\n\n".join(refined_blocks)
