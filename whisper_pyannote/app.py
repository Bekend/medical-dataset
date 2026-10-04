import os
import uuid
import shutil
import json
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
WHISPER_MODELS_DIR = os.path.join(MODELS_DIR, "whisper")
HF_MODELS_DIR = os.path.join(MODELS_DIR, "huggingface")
TORCH_MODELS_DIR = os.path.join(MODELS_DIR, "torch")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)
os.makedirs(HF_MODELS_DIR, exist_ok=True)
os.makedirs(TORCH_MODELS_DIR, exist_ok=True)

# Set environment variables for local model caching
os.environ["HF_HOME"] = HF_MODELS_DIR
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(HF_MODELS_DIR, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_MODELS_DIR, "hub")
os.environ["TORCH_HOME"] = TORCH_MODELS_DIR

try:
    import torch
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.85, 0)
except Exception:
    pass
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from audio_processor import (
    run_whisper_stt,
    run_pyannote_diarization,
    export_diarization_file,
    export_stt_file,
    export_combined_file
)

app = FastAPI(
    title="Whisper & Pyannote Audio Processor",
    description="Speech-to-Text with Timestamps and Speaker Diarization Web Application",
    version="1.0.0"
)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(BASE_DIR, "static")
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

active_processes = {}

def get_job_file(job_id: str) -> str:
    return os.path.join(JOBS_DIR, job_id, "status.json")

def read_job_state(job_id: str) -> dict:
    status_file = get_job_file(job_id)
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "unknown", "message": "Job status unavailable."}

def write_job_state(job_id: str, state: dict):
    status_file = get_job_file(job_id)
    os.makedirs(os.path.dirname(status_file), exist_ok=True)
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_existing_completed_job(filename: str) -> dict | None:
    """
    Checks if a job with the specified audio filename has already been completed in jobs/.
    Returns the job state dict if completed and valid results exist, or None otherwise.
    """
    if not os.path.exists(JOBS_DIR) or not filename:
        return None
    target_clean = os.path.basename(filename.replace("\\", "/")).strip().lower()
    if not target_clean:
        return None
    for folder in os.listdir(JOBS_DIR):
        folder_path = os.path.join(JOBS_DIR, folder)
        if os.path.isdir(folder_path):
            status_file = os.path.join(folder_path, "status.json")
            if os.path.exists(status_file):
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        state = json.load(f)
                    fn_in_state = os.path.basename(state.get("filename", "").replace("\\", "/")).strip().lower()
                    if state.get("status") == "completed" and fn_in_state == target_clean:
                        res = state.get("results") or {}
                        if res.get("merged_file") or res.get("raw_merged_file"):
                            return state
                except Exception:
                    pass
    return None

from pydantic import BaseModel
from typing import List

class CheckFilesRequest(BaseModel):
    filenames: List[str]

from audio_processor import (
    run_whisper_stt,
    run_pyannote_diarization,
    export_diarization_file,
    export_stt_file,
    export_combined_file,
    get_downloaded_whisper_models,
    get_available_gpus,
    process_resumable_audio_job,
    refine_existing_transcript
)
from gemini_service import sanitize_ai_prompt

@app.post("/api/check-files")
async def check_files_exist(req: CheckFilesRequest):
    """
    Checks multiple filenames to see if any are already completed in jobs/.
    Returns a dictionary of filename -> { exists: bool, job_id: str | None, status: str }
    """
    results = {}
    for fn in req.filenames:
        clean_fn = os.path.basename(fn.replace("\\", "/")).strip()
        existing = get_existing_completed_job(clean_fn)
        entry = {
            "exists": bool(existing),
            "job_id": existing.get("job_id") if existing else None,
            "status": "completed" if existing else "new",
            "has_refined": bool(existing.get("results", {}).get("ai_refined_file")) if existing else False
        }
        results[fn] = entry
        if clean_fn != fn:
            results[clean_fn] = entry
    return {"results": results}

@app.get("/api/system-info")
async def get_system_info():
    import torch
    cuda_available = torch.cuda.is_available()
    gpus = get_available_gpus()
    gpu_count = len(gpus)
    
    if gpu_count >= 1:
        device_name = f"{gpus[0]['name']} ({gpus[0]['vram_gb']} GB VRAM)"
    else:
        device_name = "CPU Only"

    torch_version = torch.__version__
    cached_models = get_downloaded_whisper_models()
    return {
        "cuda_available": cuda_available,
        "gpu_count": gpu_count,
        "gpus": gpus,
        "device_name": device_name,
        "torch_version": torch_version,
        "cached_models": cached_models
    }

@app.get("/api/ollama/models")
async def get_ollama_models_route(base_url: str = "http://127.0.0.1:11434"):
    from ollama_service import get_ollama_models, DEFAULT_AI_POST_PROCESS_PROMPT
    ollama_models = get_ollama_models(base_url)
    
    gemini_models = [
        {"name": "gemini:gemini-3.5-flash-lite", "label": "⚡ Gemini 3.5 Flash Lite (Ultra Fast Cloud - Recommended)"},
        {"name": "gemini:gemini-3.1-flash-lite", "label": "⚡ Gemini 3.1 Flash Lite (Ultra Fast Cloud)"},
        {"name": "gemini:gemini-3.1-flash", "label": "⚡ Gemini 3.1 Flash (High Performance Cloud)"},
        {"name": "gemini:gemini-3.1-pro", "label": "🧠 Gemini 3.1 Pro (Deep Reasoning Cloud)"},
        {"name": "gemini:gemini-2.5-flash-lite", "label": "☁️ Gemini 2.5 Flash Lite"},
        {"name": "gemini:gemini-2.5-flash", "label": "☁️ Gemini 2.5 Flash"},
        {"name": "gemini:gemini-2.5-pro", "label": "🧠 Gemini 2.5 Pro"}
    ]

    standalone_list = [
        {"name": "hf:CohereForAI/aya-23-8b", "label": "⚡ Standalone: Cohere Aya-23 8B (5.2 GB - Best Persian Model)"},
        {"name": "hf:Qwen/Qwen2.5-14B-Instruct", "label": "⚡ Standalone: Qwen2.5 14B Instruct (14.2 GB - High Capacity)"},
        {"name": "hf:Qwen/Qwen2.5-7B-Instruct", "label": "⚡ Standalone: Qwen2.5 7B Instruct (7.2 GB)"},
        {"name": "hf:meta-llama/Meta-Llama-3.1-8B-Instruct", "label": "⚡ Standalone: Meta Llama 3.1 8B Instruct (5.1 GB - High Accuracy Persian)"},
        {"name": "hf:deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", "label": "⚡ Standalone: DeepSeek R1 Distill 7B (4.7 GB - Reasoning Engine)"},
        {"name": "hf:Qwen/Qwen2.5-3B-Instruct", "label": "⚡ Standalone: Qwen2.5 3B Instruct (3.0 GB)"},
        {"name": "hf:meta-llama/Llama-3.2-3B-Instruct", "label": "⚡ Standalone: Llama 3.2 3B Instruct (3.2 GB)"},
        {"name": "hf:google/gemma-2-2b-it", "label": "⚡ Standalone: Gemma 2 2B IT (2.6 GB)"}
    ]
    return {
        "models": ollama_models,
        "gemini_models": gemini_models,
        "standalone_models": standalone_list,
        "default_prompt": DEFAULT_AI_POST_PROCESS_PROMPT
    }

def process_worker_func(
    job_id: str,
    file_path: str,
    filename: str,
    whisper_model: str,
    hf_token: str,
    device: str,
    language: str = "fa",
    initial_prompt: str = "",
    speaker_mode: str = "doctor_patient",
    enable_ai_refinement: bool = False,
    ollama_model: str = "",
    ollama_url: str = "http://127.0.0.1:11434",
    ai_prompt: str = "",
    gemini_api_key: str = ""
):
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    ai_prompt = sanitize_ai_prompt(ai_prompt)
    
    current_state = read_job_state(job_id)

    def is_cancelled():
        s = read_job_state(job_id)
        return bool(s.get("cancelled", False) or s.get("status") == "cancelled")

    def update_progress(percent: int, message: str, step_detail: str = ""):
        if is_cancelled():
            return
        current_state["progress"] = percent
        current_state["message"] = message
        current_state["step_detail"] = step_detail
        write_job_state(job_id, current_state)

    try:
        current_state["status"] = "processing"
        current_state["cancelled"] = False
        write_job_state(job_id, current_state)

        results = process_resumable_audio_job(
            file_path=file_path,
            job_dir=job_dir,
            filename=filename,
            whisper_model=whisper_model,
            hf_token=hf_token if hf_token else None,
            device=device,
            language=language,
            initial_prompt=initial_prompt,
            speaker_mode=speaker_mode,
            chunk_duration_sec=300.0, # 5 minutes per chunk checkpoint
            enable_ai_refinement=enable_ai_refinement,
            ollama_model=ollama_model,
            ollama_url=ollama_url,
            ai_prompt=ai_prompt,
            gemini_api_key=gemini_api_key,
            progress_cb=update_progress,
            is_cancelled_cb=is_cancelled
        )

        if is_cancelled():
            current_state["status"] = "cancelled"
            current_state["message"] = "Processing cancelled by user."
            current_state["step_detail"] = "Process terminated."
            write_job_state(job_id, current_state)
            return

        current_state["status"] = "completed"
        current_state["progress"] = 100
        current_state["message"] = "Processing completed successfully!"
        current_state["step_detail"] = "All 5-minute chunk checkpoints combined into final reports."
        current_state["results"] = results
        write_job_state(job_id, current_state)

    except Exception as e:
        if is_cancelled():
            return
        current_state["status"] = "error"
        current_state["error"] = str(e)
        current_state["message"] = f"Processing error: {str(e)}"
        write_job_state(job_id, current_state)
    finally:
        with job_mutex:
            active_processes.pop(job_id, None)

def refine_worker_func(
    job_id: str,
    ollama_model: str,
    ollama_url: str = "http://127.0.0.1:11434",
    ai_prompt: str = "",
    gemini_api_key: str = ""
):
    job_dir = os.path.join(JOBS_DIR, job_id)
    ai_prompt = sanitize_ai_prompt(ai_prompt)
    current_state = read_job_state(job_id)
    filename = current_state.get("filename", "audio.wav")

    def is_cancelled():
        s = read_job_state(job_id)
        return bool(s.get("cancelled", False) or s.get("status") == "cancelled")

    def update_progress(percent: int, message: str, step_detail: str = ""):
        if is_cancelled():
            return
        current_state["progress"] = percent
        current_state["message"] = message
        current_state["step_detail"] = step_detail
        write_job_state(job_id, current_state)

    try:
        current_state["status"] = "processing"
        current_state["message"] = f"Running AI Refinement with {ollama_model}..."
        current_state["step_detail"] = "Processing dialogue lines..."
        current_state["cancelled"] = False
        write_job_state(job_id, current_state)

        refine_res = refine_existing_transcript(
            job_dir=job_dir,
            filename=filename,
            ollama_model=ollama_model,
            ollama_url=ollama_url,
            ai_prompt=ai_prompt,
            gemini_api_key=gemini_api_key,
            progress_cb=update_progress,
            is_cancelled_cb=is_cancelled
        )

        if is_cancelled():
            current_state["status"] = "cancelled"
            current_state["message"] = "Refinement cancelled by user."
            write_job_state(job_id, current_state)
            return

        if not current_state.get("results"):
            current_state["results"] = {}
        
        current_state["results"]["ai_refined_file"] = refine_res["ai_refined_file"]
        current_state["results"]["refined_file"] = refine_res["refined_file"]
        current_state["results"]["ai_refined_preview"] = refine_res["ai_refined_preview"]
        current_state["results"]["refined_diarization_file"] = refine_res.get("refined_diarization_file", "")
        current_state["results"]["refined_stt_file"] = refine_res.get("refined_stt_file", "")
        current_state["results"]["refined_merged_file"] = refine_res.get("refined_merged_file", "")
        current_state["results"]["refined_diarization_preview"] = refine_res.get("refined_diarization_preview", "")
        current_state["results"]["refined_stt_preview"] = refine_res.get("refined_stt_preview", "")
        current_state["status"] = "completed"
        current_state["progress"] = 100
        current_state["message"] = "AI Refinement completed successfully!"
        current_state["step_detail"] = f"Refined outcomes (Transcript, Diarization, STT) saved to refined/ subfolder."
        write_job_state(job_id, current_state)

    except Exception as e:
        if is_cancelled():
            return
        current_state["status"] = "error"
        current_state["error"] = str(e)
        current_state["message"] = f"AI Refinement error: {str(e)}"
        write_job_state(job_id, current_state)
    finally:
        with job_mutex:
            active_processes.pop(job_id, None)

import re
from datetime import datetime

job_mutex = threading.Lock()

def cancel_all_active_jobs(exclude_job_id: str = None):
    """Cancels and purges any currently active background jobs and marks dangling jobs on disk as cancelled."""
    for j_id in list(active_processes.keys()):
        if j_id == exclude_job_id:
            continue
        try:
            state = read_job_state(j_id)
            if state.get("status") in ["queued", "processing"]:
                state["cancelled"] = True
                state["status"] = "cancelled"
                state["message"] = "Superseded by new job."
                state["step_detail"] = "Cancelled."
                write_job_state(j_id, state)
        except Exception:
            pass
        active_processes.pop(j_id, None)

    # Clean up any leftover 'processing' or 'queued' state on disk
    if os.path.exists(JOBS_DIR):
        for folder in os.listdir(JOBS_DIR):
            if folder == exclude_job_id:
                continue
            folder_path = os.path.join(JOBS_DIR, folder)
            if os.path.isdir(folder_path):
                status_file = os.path.join(folder_path, "status.json")
                if os.path.exists(status_file):
                    try:
                        with open(status_file, "r", encoding="utf-8") as f:
                            s = json.load(f)
                        if s.get("status") in ["queued", "processing"]:
                            s["cancelled"] = True
                            s["status"] = "cancelled"
                            s["message"] = "Cancelled."
                            write_job_state(folder, s)
                    except Exception:
                        pass

def generate_job_id(filename: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_base = os.path.basename(filename.replace("\\", "/"))
    base_name = os.path.splitext(clean_base)[0]
    clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')[:30]
    if not clean_name or len(clean_name) < 2:
        clean_name = "audio_job"
    short_uid = uuid.uuid4().hex[:6]
    return f"{clean_name}_{timestamp}_{short_uid}"

@app.post("/api/process")
async def start_process(
    file: UploadFile = File(...),
    whisper_model: str = Form("large-v3"),
    hf_token: str = Form(""),
    device: str = Form("cuda"),
    language: str = Form("fa"),
    initial_prompt: str = Form(""),
    speaker_mode: str = Form("doctor_patient"),
    enable_ai: bool = Form(False),
    ollama_model: str = Form(""),
    ollama_url: str = Form("http://127.0.0.1:11434"),
    ai_prompt: str = Form(""),
    gemini_api_key: str = Form(""),
    skip_if_exists: bool = Form(False)
):
    raw_name = file.filename or "audio.wav"
    clean_filename = os.path.basename(raw_name.replace("\\", "/")).strip()
    if not clean_filename:
        clean_filename = "audio.wav"

    if not clean_filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav audio files are supported.")

    existing_completed = get_existing_completed_job(clean_filename)
    if existing_completed:
        if skip_if_exists:
            return {
                "job_id": existing_completed.get("job_id"),
                "status": "already_completed",
                "skipped": True,
                "filename": clean_filename,
                "message": f"File '{clean_filename}' has already been processed in job '{existing_completed.get('job_id')}'. Skipped.",
                "results": existing_completed.get("results")
            }
        else:
            raise HTTPException(
                status_code=409,
                detail=f"File '{clean_filename}' has already been processed in job '{existing_completed.get('job_id')}'. To re-run from scratch, please delete the existing job from history first, or open results to view or refine with AI."
            )

    ollama_model_clean = ollama_model.strip() if ollama_model else ""
    enable_ai_clean = bool(enable_ai or bool(ollama_model_clean))

    with job_mutex:
        cancel_all_active_jobs()

        job_id = generate_job_id(clean_filename)
        job_dir = os.path.join(JOBS_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        file_path = os.path.join(job_dir, clean_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        ai_prompt_clean = sanitize_ai_prompt(ai_prompt.strip())
        initial_state = {
            "job_id": job_id,
            "filename": clean_filename,
            "whisper_model": whisper_model,
            "hf_token": hf_token.strip(),
            "device": device,
            "language": language,
            "initial_prompt": initial_prompt.strip(),
            "speaker_mode": speaker_mode,
            "enable_ai": enable_ai_clean,
            "ollama_model": ollama_model_clean,
            "ollama_url": ollama_url.strip(),
            "ai_prompt": ai_prompt_clean,
            "gemini_api_key": gemini_api_key.strip(),
            "status": "queued",
            "progress": 5,
            "message": "File uploaded, queued for processing...",
            "step_detail": "Preparing execution worker",
            "cancelled": False,
            "error": None,
            "results": None
        }
        write_job_state(job_id, initial_state)

        proc = threading.Thread(
            target=process_worker_func,
            args=(
                job_id,
                file_path,
                clean_filename,
                whisper_model,
                hf_token.strip(),
                device,
                language,
                initial_prompt.strip(),
                speaker_mode,
                enable_ai_clean,
                ollama_model_clean,
                ollama_url.strip(),
                ai_prompt_clean,
                gemini_api_key.strip()
            ),
            daemon=True
        )
        proc.start()
        active_processes[job_id] = proc

        return {"job_id": job_id, "status": "queued"}

@app.post("/api/resume/{job_id}")
async def resume_job(job_id: str):
    with job_mutex:
        cancel_all_active_jobs()

        state = read_job_state(job_id)
        job_dir = os.path.join(JOBS_DIR, job_id)
        raw_fn = state.get("filename", "audio.wav")
        clean_filename = os.path.basename(raw_fn.replace("\\", "/")).strip() if raw_fn else "audio.wav"
        file_path = os.path.join(job_dir, clean_filename) if clean_filename else None

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Audio file for this job no longer exists on disk.")

        state["filename"] = clean_filename
        state["status"] = "queued"
        state["cancelled"] = False
        state["message"] = "Resuming processing from last saved 5-minute checkpoint..."
        state["step_detail"] = "Re-launching execution worker"
        write_job_state(job_id, state)

        ollama_model_clean = state.get("ollama_model", "").strip()
        enable_ai_clean = bool(state.get("enable_ai", False) or bool(ollama_model_clean))

        proc = threading.Thread(
            target=process_worker_func,
            args=(
                job_id,
                file_path,
                clean_filename,
                state.get("whisper_model", "large-v3"),
                state.get("hf_token", ""),
                state.get("device", "cuda"),
                state.get("language", "fa"),
                state.get("initial_prompt", ""),
                state.get("speaker_mode", "doctor_patient"),
                enable_ai_clean,
                ollama_model_clean,
                state.get("ollama_url", "http://127.0.0.1:11434"),
                state.get("ai_prompt", ""),
                state.get("gemini_api_key", "")
            ),
            daemon=True
        )
        proc.start()
        active_processes[job_id] = proc

        return {"job_id": job_id, "status": "resumed"}

@app.post("/api/refine/{job_id}")
async def refine_job(
    job_id: str,
    ollama_model: str = Form("gemini:gemini-3.5-flash-lite"),
    ollama_url: str = Form("http://127.0.0.1:11434"),
    ai_prompt: str = Form(""),
    gemini_api_key: str = Form("")
):
    with job_mutex:
        cancel_all_active_jobs()
        state = read_job_state(job_id)
        job_dir = os.path.join(JOBS_DIR, job_id)
        if not os.path.exists(job_dir):
            raise HTTPException(status_code=404, detail="Job directory not found.")

        ai_prompt_clean = sanitize_ai_prompt(ai_prompt.strip())
        state["status"] = "processing"
        state["cancelled"] = False
        state["progress"] = 5
        state["message"] = f"Starting AI Refinement with {ollama_model}..."
        state["step_detail"] = "Initializing refinement worker..."
        state["enable_ai"] = True
        state["ollama_model"] = ollama_model
        state["ollama_url"] = ollama_url
        state["ai_prompt"] = ai_prompt_clean
        state["gemini_api_key"] = gemini_api_key
        write_job_state(job_id, state)

        proc = threading.Thread(
            target=refine_worker_func,
            args=(
                job_id,
                ollama_model.strip(),
                ollama_url.strip(),
                ai_prompt_clean,
                gemini_api_key.strip()
            ),
            daemon=True
        )
        proc.start()
        active_processes[job_id] = proc

        return {"job_id": job_id, "status": "processing"}

@app.get("/api/history")
async def get_job_history():
    jobs = []
    if os.path.exists(JOBS_DIR):
        for folder in os.listdir(JOBS_DIR):
            folder_path = os.path.join(JOBS_DIR, folder)
            if os.path.isdir(folder_path):
                status_file = os.path.join(folder_path, "status.json")
                if os.path.exists(status_file):
                    try:
                        with open(status_file, "r", encoding="utf-8") as f:
                            state = json.load(f)
                            state["mtime"] = os.path.getmtime(status_file)
                            jobs.append(state)
                    except Exception:
                        pass
    jobs.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return {"jobs": jobs}

@app.delete("/api/job/{job_id}")
async def delete_job(job_id: str):
    job_dir = os.path.join(JOBS_DIR, job_id)
    if os.path.exists(job_dir):
        if job_id in active_processes:
            del active_processes[job_id]
        shutil.rmtree(job_dir, ignore_errors=True)
        return {"status": "deleted", "job_id": job_id}
    raise HTTPException(status_code=404, detail="Job not found.")

@app.post("/api/cancel/{job_id}")
async def cancel_job(job_id: str):
    if job_id in active_processes:
        del active_processes[job_id]

    state = read_job_state(job_id)
    state["cancelled"] = True
    state["status"] = "cancelled"
    state["message"] = "Processing cancelled by user."
    state["step_detail"] = "Process terminated immediately."
    write_job_state(job_id, state)

    return {"status": "cancelled", "job_id": job_id}

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    state = read_job_state(job_id)
    if state.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="Job not found.")
    return state

@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    state = read_job_state(job_id)
    if state.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed or found.")

    res = state.get("results") or {}
    job_dir = os.path.join(JOBS_DIR, job_id)
    filename = state.get("filename", "audio.wav")
    base_name = os.path.splitext(filename)[0]

    if file_type == "diarization":
        file_name = res.get("diarization_file") or f"{base_name}_diarization.txt"
        sub_dir = "raw"
    elif file_type == "stt":
        file_name = res.get("stt_file") or f"{base_name}_stt_timestamps.txt"
        sub_dir = "raw"
    elif file_type == "merged":
        file_name = res.get("merged_file") or f"{base_name}_merged_transcript.txt"
        sub_dir = "raw"
    elif file_type in ("ai_refined", "refined_merged"):
        file_name = res.get("ai_refined_file") or f"{base_name}_ai_refined_transcript.txt"
        sub_dir = "refined"
    elif file_type == "refined_diarization":
        file_name = f"{base_name}_diarization.txt"
        sub_dir = "refined"
    elif file_type == "refined_stt":
        file_name = f"{base_name}_stt_timestamps.txt"
        sub_dir = "refined"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # Search in subdirectory (raw/ or refined/), then fallback to root of job_dir
    target_path = os.path.join(job_dir, sub_dir, file_name)
    if not os.path.exists(target_path):
        target_path = os.path.join(job_dir, file_name)
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    return FileResponse(target_path, filename=os.path.basename(target_path), media_type="text/plain")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    cancel_all_active_jobs()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
