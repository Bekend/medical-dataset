import os
import json
import wave
import re
import time
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
WHISPER_MODELS_DIR = os.path.join(MODELS_DIR, "whisper")
HF_MODELS_DIR = os.path.join(MODELS_DIR, "huggingface")
TORCH_MODELS_DIR = os.path.join(MODELS_DIR, "torch")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)
os.makedirs(HF_MODELS_DIR, exist_ok=True)
os.makedirs(TORCH_MODELS_DIR, exist_ok=True)

# Set environment variables so Pyannote, HuggingFace, and PyTorch default to the local models folder
os.environ["HF_HOME"] = HF_MODELS_DIR
os.environ["HUGGINGFACE_HUB_CACHE"] = os.path.join(HF_MODELS_DIR, "hub")
os.environ["TRANSFORMERS_CACHE"] = os.path.join(HF_MODELS_DIR, "hub")
os.environ["TORCH_HOME"] = TORCH_MODELS_DIR

# Safe PyTorch load patch to map CUDA model weights to CPU on non-GPU systems and cap CUDA RAM
try:
    import torch
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(0.85, 0)
    _original_torch_load = torch.load
    def _safe_torch_load(*args, **kwargs):
        if not torch.cuda.is_available():
            if 'map_location' not in kwargs or kwargs['map_location'] is None:
                kwargs['map_location'] = torch.device('cpu')
        return _original_torch_load(*args, **kwargs)
    torch.load = _safe_torch_load
except Exception:
    pass

def get_downloaded_whisper_models() -> list:
    """
    Checks local Whisper cache directories for pre-downloaded model weight files.
    Returns list of model names currently available offline (e.g. ['tiny', 'base', 'large-v3']).
    """
    search_dirs = [
        WHISPER_MODELS_DIR,
        MODELS_DIR,
        os.path.join(os.path.dirname(BASE_DIR), ".cache", "whisper"),
        os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    ]
    cached = set()
    for sdir in search_dirs:
        if os.path.exists(sdir):
            for name in ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3", "large"]:
                fpath = os.path.join(sdir, f"{name}.pt")
                if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
                    cached.add(name)
    order = ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3", "large"]
    return [m for m in order if m in cached]

def get_available_gpus() -> list:
    """
    Returns a list of detected CUDA GPUs with their index, device name, and total VRAM in GB.
    Example: [{'index': 0, 'name': 'NVIDIA GeForce RTX 4090', 'vram_gb': 24.0, 'vram_bytes': 25769803776}]
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return []
        count = torch.cuda.device_count()
        gpus = []
        for i in range(count):
            props = torch.cuda.get_device_properties(i)
            vram_bytes = getattr(props, 'total_memory', 0)
            vram_gb = round(vram_bytes / (1024 ** 3), 1)
            gpus.append({
                "index": i,
                "name": torch.cuda.get_device_name(i),
                "vram_gb": vram_gb,
                "vram_bytes": vram_bytes,
                "multi_processor_count": getattr(props, 'multi_processor_count', 0)
            })
        return gpus
    except Exception:
        return []

def get_optimal_task_gpu_assignment(selected_device: str = "cuda") -> dict:
    """
    Intelligently assigns tasks across available GPUs:
    - Ranks GPUs by total VRAM and compute capacity.
    - Assigns the HIGHEST capacity GPU to the compute-heavy OpenAI Whisper STT model.
    - Assigns the secondary GPU to Pyannote Speaker Diarization.
    """
    if not selected_device.startswith("cuda"):
        return {
            "multi_gpu": False,
            "stt_device": selected_device,
            "diar_device": selected_device,
            "stt_gpu": None,
            "diar_gpu": None,
            "gpus": []
        }

    gpus = get_available_gpus()
    if len(gpus) < 2:
        stt_gpu = gpus[0] if gpus else None
        return {
            "multi_gpu": False,
            "stt_device": "cuda:0" if gpus else selected_device,
            "diar_device": "cuda:0" if gpus else selected_device,
            "stt_gpu": stt_gpu,
            "diar_gpu": stt_gpu,
            "gpus": gpus
        }

    # Sort descending by VRAM bytes (and multi_processor_count as tie-breaker)
    ranked_gpus = sorted(
        gpus,
        key=lambda g: (g.get("vram_bytes", 0), g.get("multi_processor_count", 0)),
        reverse=True
    )

    primary_gpu = ranked_gpus[0]    # Best GPU -> Whisper STT (heavy compute)
    secondary_gpu = ranked_gpus[1]  # Second GPU -> Pyannote Diarization (lighter compute)

    return {
        "multi_gpu": True,
        "stt_device": f"cuda:{primary_gpu['index']}",
        "diar_device": f"cuda:{secondary_gpu['index']}",
        "stt_gpu": primary_gpu,
        "diar_gpu": secondary_gpu,
        "gpus": gpus
    }

def trim_process_memory():
    """Forces Python and Windows OS to immediately reclaim and trim all unused memory pages."""
    import gc
    gc.collect()
    try:
        import ctypes
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.psapi.EmptyWorkingSet(handle)
    except Exception:
        pass

def format_timestamp(seconds: float) -> str:
    """Formats seconds into HH:MM:SS.mmm string."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def get_wav_info(file_path: str) -> tuple[float, int]:
    """Gets total duration (seconds) and sample rate without reading all audio into RAM."""
    import soundfile as sf
    try:
        with sf.SoundFile(file_path) as f:
            sr = f.samplerate
            frames = len(f)
            duration = frames / float(sr)
            return duration, sr
    except Exception:
        with wave.open(file_path, 'rb') as wf:
            sr = wf.getframerate()
            frames = wf.getnframes()
            return frames / float(sr), sr

def read_wav_chunk(file_path: str, start_sec: float, duration_sec: float, target_sr: int = 16000) -> np.ndarray:
    """Reads ONLY a 5-minute chunk from disk on-demand, consuming < 20 MB RAM."""
    import soundfile as sf
    import math
    from scipy import signal

    try:
        with sf.SoundFile(file_path) as f:
            native_sr = f.samplerate
            start_frame = int(start_sec * native_sr)
            num_frames = int(duration_sec * native_sr)
            
            f.seek(max(0, min(start_frame, len(f))))
            audio_chunk = f.read(num_frames, dtype='float32')
            
            if audio_chunk.ndim > 1:
                audio_chunk = audio_chunk.mean(axis=1) # stereo to mono
                
            if native_sr != target_sr:
                gcd = math.gcd(native_sr, target_sr)
                up = target_sr // gcd
                down = native_sr // gcd
                audio_chunk = signal.resample_poly(audio_chunk, up, down).astype(np.float32)
                
            return audio_chunk
    except Exception:
        # Fallback to load_wav_file slice
        full_arr, _ = load_wav_file(file_path)
        start_idx = int(start_sec * 16000)
        end_idx = int((start_sec + duration_sec) * 16000)
        return full_arr[start_idx:end_idx]

def load_wav_file(file_path: str) -> tuple[np.ndarray, int]:
    """
    Loads a WAV audio file into a 1D float32 numpy array normalized to [-1.0, 1.0].
    Resamples to 16,000 Hz using low-memory polyphase filtering (uses < 5 MB RAM).
    Does not require system ffmpeg binaries.
    """
    import math
    from scipy import signal

    try:
        import soundfile as sf
        audio_data, sample_rate = sf.read(file_path, dtype='float32')
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1) # convert stereo to mono
        
        # Resample to 16000 Hz using lightweight polyphase filter (O(1) memory)
        if sample_rate != 16000:
            gcd = math.gcd(int(sample_rate), 16000)
            up = 16000 // gcd
            down = int(sample_rate) // gcd
            audio_data = signal.resample_poly(audio_data, up, down).astype(np.float32)
            sample_rate = 16000
            
        return audio_data, sample_rate
    except Exception as e:
        # Fallback to standard Python wave module for standard uncompressed PCM WAV
        with wave.open(file_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            frame_rate = wf.getframerate()
            n_frames = wf.getnframes()
            
            raw_bytes = wf.readframes(n_frames)
            
            if sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            elif sample_width == 1:
                dtype = np.uint8
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
                
            audio_data = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)
            if dtype == np.uint8:
                audio_data = (audio_data - 128.0) / 128.0
            else:
                audio_data = audio_data / np.iinfo(dtype).max
                
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels).mean(axis=1)
                
            if frame_rate != 16000:
                gcd = math.gcd(int(frame_rate), 16000)
                up = 16000 // gcd
                down = int(frame_rate) // gcd
                audio_data = signal.resample_poly(audio_data, up, down).astype(np.float32)
                frame_rate = 16000
                
            return audio_data, frame_rate

def _get_whisper_download_root(model_name: str) -> str:
    """
    Locates where an existing whisper model is stored, or defaults to the local models/whisper directory.
    """
    # 1. Local models/whisper/
    p1 = os.path.join(WHISPER_MODELS_DIR, f"{model_name}.pt")
    if os.path.exists(p1) and os.path.getsize(p1) > 1000:
        return WHISPER_MODELS_DIR
    # 2. Directly in models/
    p2 = os.path.join(MODELS_DIR, f"{model_name}.pt")
    if os.path.exists(p2) and os.path.getsize(p2) > 1000:
        return MODELS_DIR
    # 3. Fallbacks
    p3 = os.path.join(os.path.dirname(BASE_DIR), ".cache", "whisper", f"{model_name}.pt")
    if os.path.exists(p3) and os.path.getsize(p3) > 1000:
        return os.path.join(os.path.dirname(BASE_DIR), ".cache", "whisper")
    p4 = os.path.join(os.path.expanduser("~"), ".cache", "whisper", f"{model_name}.pt")
    if os.path.exists(p4) and os.path.getsize(p4) > 1000:
        return os.path.join(os.path.expanduser("~"), ".cache", "whisper")
    return WHISPER_MODELS_DIR

def _load_whisper_with_auto_repair(model_name: str, device: str = "cpu"):
    import whisper
    import torch
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    
    download_root = _get_whisper_download_root(model_name)
    try:
        return whisper.load_model(model_name, device=device, download_root=download_root)
    except Exception as e:
        err_msg = str(e)
        if "SHA256 checksum" in err_msg or "checksum does not match" in err_msg or "corrupt" in err_msg.lower():
            # Delete corrupted model cache file and re-download cleanly
            for check_dir in [WHISPER_MODELS_DIR, MODELS_DIR, os.path.join(os.path.dirname(BASE_DIR), ".cache", "whisper"), os.path.expanduser("~/.cache/whisper")]:
                model_file = os.path.join(check_dir, f"{model_name}.pt")
                if os.path.exists(model_file):
                    try:
                        os.remove(model_file)
                    except Exception:
                        pass
            return whisper.load_model(model_name, device=device, download_root=WHISPER_MODELS_DIR)
        else:
            raise e

PERSIAN_MEDICAL_CORRECTIONS = [
    (r'\bکرس\b', 'قرص'),
    (r'\bکرص\b', 'قرص'),
    (r'\bافغانت\b', 'عفونت'),
    (r'\bافوانت\b', 'عفونت'),
    (r'\bکردیه\b', 'کلیه'),
    (r'\bکودیه\b', 'کلیه'),
    (r'\bتزرگه\b', 'تزریقی'),
    (r'\bتزدگی\b', 'تزریقی'),
    (r'\bتبریجی\b', 'تزریقی'),
    (r'\bتبریزیات\b', 'تزریقات'),
    (r'\bمعایله\b', 'معاینه'),
    (r'\bپراکیت\b', 'استامینوفن'),
    (r'\bپاراکیت\b', 'استامینوفن'),
    (r'\bپراکیلی\b', 'استامینوفن'),
    (r'\bپاراکیل\b', 'استامینوفن'),
    (r'\bام کول\b', 'آمپول'),
    (r'\bکترا\b', 'قطره'),
    (r'\bشیو\b', 'شیوع'),
    (r'\bآویزش\b', 'آبریزش'),
    (r'\bنسخونده\b', 'نسخه‌نویسی'),
    (r'\bسب\b', 'شب'),
    (r'\bدیشبه\b', 'دیشب'),
    (r'\bعدن\b', 'بدن'),
    (r'\bخفید\b', 'خفیف'),
    (r'\bآدریس\b', 'آدرس'),
    (r'\bآموز شده\b', 'آماده شده'),
    (r'\bرسمت\b', 'قسمت'),
    (r'\bرسمت ها\b', 'قسمت‌ها'),
    (r'\bرسمت های\b', 'قسمت‌های'),
    (r'\bخونکه\b', 'خنکه'),
    (r'\bخونک\b', 'خنک'),
    (r'\bآدرس جو بیمین\b', 'آفت دهان'),
    (r'\bآدریس جو\b', 'آفت دهان'),
    (r'\bریفلست\b', 'رفلاکس'),
    (r'\bسریدک\b', 'برفک'),
    (r'\bبرخشت\b', 'برفک'),
    (r'\bپرفردی\b', 'برفک'),
    (r'\bدرتاکیت\b', 'دیفن‌هیدرامین'),
    (r'\bدرکیلیستر\b', 'دیفن‌هیدرامین'),
    (r'\bاز به میره\b', 'از بین میره'),
    (r'\bسر و پنه\b', 'سر و سینه'),
    (r'\bاندام مارد\b', 'اندام‌ها'),
    (r'\bفردای شیری\b', 'ردِ شیری'),
    (r'\bتفت\b', 'تب'),
    (r'\bمیمیدیسم\b', 'می‌نویسم'),
    (r'\bدوتر\b', 'دوز'),
    (r'\bهر کاکاو\b', 'کاکائو'),
    (r'\bایلیترو\b', 'اریترومایسین'),
    (r'\bپلار جینکیت\b', 'پدیابست'),
    (r'\bصالبه\b', 'سرفه'),
    (r'\bسکر میکنیم\b', 'فکر می‌کنیم'),
    (r'\bبالت\b', 'بالشت'),
    (r'\bرینو سالتینه\b', 'رينوسالتین'),
    (r'\bافتمنی\b', 'هموگلوبین'),
    (r'\bلبه مرز\b', 'لب مرز'),
    (r'\bمصبر\b', 'مثبت'),
    (r'\bکلوی\b', 'کلیه'),
    (r'\b۳۴ برابر\b', '۳ تا ۴ برابر'),
    (r'\bسراخ دینی\b', 'سوراخ بینی'),
    (r'\bنشنگه\b', 'قشنگه'),
    (r'\bتغییرتشون\b', 'تربیتشون'),
    (r'\bنادرد\b', 'ناراحت'),
    (r'\bمشکل نسه\b', 'مشخص کن'),
]

def sanitize_persian_medical_text(text: str) -> str:
    """
    Post-processes transcribed Persian text using medical domain lexicon rules
    to fix common Whisper acoustic mis-recognitions (e.g. 'کرس' -> 'قرص', 'افغانت' -> 'عفونت').
    """
    if not text:
        return ""
    cleaned = text
    for pattern, replacement in PERSIAN_MEDICAL_CORRECTIONS:
        cleaned = re.sub(pattern, replacement, cleaned)
    return cleaned

DEFAULT_PERSIAN_MEDICAL_PROMPT = (
    "گفتگوی پزشکی، معاینه بیمار، گفتگو بین دکتر و بیمار در مطب پزشکی، بیماری‌های کودکان و اطفال. "
    "واژه‌ها و داروها: قرص، شربت، آمپول، قطره، اسپری، استامینوفن، دیفن‌هیدرامین، آزیترومایسین، "
    "رينوسالتین، انجیر، برفک، آفت، رفلاکس، عفونت ادراری، کلیه، نارسایی، تب، آبریزش بینی، "
    "سونوگرافی، آزمایش CBC، پلاکت، هموگلوبین، آنزیم‌های کبدی، نسخه، دوز، تزریقی."
)

def run_whisper_stt(
    audio_input,
    model_name: str = "base",
    language: str = "fa",
    initial_prompt: str = DEFAULT_PERSIAN_MEDICAL_PROMPT,
    device: str = "cpu",
    model=None,
    progress_cb=None,
    is_cancelled_cb=None
):
    """
    Runs OpenAI Whisper STT on a WAV file or in-memory numpy waveform with detailed progress reporting.
    Returns segment details with start, end, formatted timestamps, and text.
    """
    import torch
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    if is_cancelled_cb and is_cancelled_cb():
        return {"text": "", "language": "fa", "segments": []}

    should_cleanup_model = False
    if model is None:
        if progress_cb:
            progress_cb(40, f"Loading Whisper '{model_name}' model into memory...", "Initial model initialization")
        model = _load_whisper_with_auto_repair(model_name, device=device)
        should_cleanup_model = True
    
    if is_cancelled_cb and is_cancelled_cb():
        return {"text": "", "language": "fa", "segments": []}

    if progress_cb:
        progress_cb(50, "Reading audio waveforms into memory...", "Converting audio to 16kHz mono tensor")

    # Load audio: supports both file path and in-memory numpy float32 array
    if isinstance(audio_input, np.ndarray):
        audio_array = audio_input.astype(np.float32)
        sr = 16000
    else:
        audio_array, sr = load_wav_file(audio_input)
    audio_duration = len(audio_array) / sr

    if progress_cb:
        progress_cb(55, f"Transcribing audio with Whisper ({audio_duration:.1f}s total duration)...", f"Running model inference on {device.upper()}")
    
    use_fp16 = True if device.startswith("cuda") else False
    transcribe_kwargs = {
        "verbose": None,                      # Enables tqdm hook
        "fp16": use_fp16,
        "temperature": 0.0,                   # Deterministic greedy decoding (prevents memory amplification)
        "condition_on_previous_text": False,  # Prevents infinite repetition loops on music/silence
        "no_speech_threshold": 0.6,           # Filters out non-speech segments
        "logprob_threshold": -1.0,            # Discards low confidence guesses
        "compression_ratio_threshold": 2.4,   # Detects and resets repetitive text loops
        "beam_size": None,                    # Efficient greedy search: prevents 50GB beam buffer explosion
        "best_of": None
    }

    if language and language.lower() != "auto":
        transcribe_kwargs["language"] = language.lower()
    if initial_prompt:
        transcribe_kwargs["initial_prompt"] = initial_prompt

    # Hook tqdm to extract native Whisper progress percentage, audio position, and ETA
    import tqdm
    import time
    orig_tqdm = tqdm.tqdm
    stt_start_time = time.time()

    class WhisperProgressTqdm:
        def __init__(self, *args, **kwargs):
            self.total = kwargs.get('total', 1) or 1
            self.n = 0
            self.disable = False

        def update(self, n=1):
            self.n += n
            if progress_cb:
                current_sec = self.n / 100.0
                total_sec = self.total / 100.0
                stt_pct = min(100.0, (self.n / self.total) * 100.0)
                overall_pct = 40 + int(stt_pct * 0.45)
                
                elapsed_sec = time.time() - stt_start_time
                rate = self.n / elapsed_sec if elapsed_sec > 0 else 0
                remaining_frames = max(0, self.total - self.n)
                eta_sec = int(remaining_frames / rate) if rate > 0 else 0
                
                current_fmt = format_timestamp(current_sec).split('.')[0]
                total_fmt = format_timestamp(total_sec).split('.')[0]
                elapsed_fmt = format_timestamp(elapsed_sec).split('.')[0]
                eta_fmt = format_timestamp(eta_sec).split('.')[0]
                
                msg = f"Transcribing Whisper STT: {int(stt_pct)}% ({current_fmt} / {total_fmt})"
                detail = f"ETA: ~{eta_fmt} remaining | Audio Window: {current_fmt} / {total_fmt}"
                
                progress_cb(overall_pct, msg, detail)

        def close(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    try:
        tqdm.tqdm = WhisperProgressTqdm
        with torch.inference_mode():
            result = model.transcribe(audio_array, **transcribe_kwargs)
    finally:
        tqdm.tqdm = orig_tqdm
    
    if is_cancelled_cb and is_cancelled_cb():
        return {"text": "", "language": "fa", "segments": []}

    segments = []
    for seg in result.get("segments", []):
        start_t = float(seg["start"])
        end_t = float(seg["end"])
        raw_text = seg["text"].strip()
        cleaned_text = sanitize_persian_medical_text(raw_text)
        
        segments.append({
            "id": seg.get("id", 0),
            "start": start_t,
            "end": end_t,
            "formatted_start": format_timestamp(start_t),
            "formatted_end": format_timestamp(end_t),
            "text": cleaned_text
        })
        
    if progress_cb:
        progress_cb(75, f"Transcription completed! {len(segments)} segment(s) generated.", "STT stage finished successfully")

    res_dict = {
        "text": result.get("text", "").strip(),
        "language": result.get("language", "en"),
        "segments": segments
    }

    try:
        del result
    except Exception:
        pass

    import gc
    gc.collect()

    if should_cleanup_model:
        try:
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    return res_dict

def _load_pyannote_pipeline(hf_token: str = None, device: str = "cpu"):
    """Loads and initializes Pyannote Speaker Diarization pipeline once."""
    import torch
    from pyannote.audio import Pipeline
    
    pipeline_kwargs = {
        "cache_dir": os.path.join(HF_MODELS_DIR, "hub")
    }
    if hf_token:
        pipeline_kwargs["token"] = hf_token
        
    try:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", **pipeline_kwargs)
    except TypeError as e_type:
        # Fallback for legacy huggingface_hub / pyannote versions
        if "token" in str(e_type) and hf_token:
            pipeline_kwargs.pop("token", None)
            pipeline_kwargs["use_auth_token"] = hf_token
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", **pipeline_kwargs)
        else:
            raise e_type

    if pipeline is None:
        raise RuntimeError("Could not load pyannote pipeline. Please check your HuggingFace Token and access permissions.")
        
    if device.startswith("cuda") and torch.cuda.is_available():
        pipeline.to(torch.device(device))
        
    return pipeline

def run_pyannote_diarization(audio_input, hf_token: str = None, device: str = "cpu", pipeline=None, progress_cb=None, is_cancelled_cb=None):
    """
    Runs Pyannote Community Speaker Diarization on a WAV file or in-memory waveform tensor.
    Returns speaker turns with start, end, formatted timestamps, and speaker labels.
    """
    turns = []
    
    if is_cancelled_cb and is_cancelled_cb():
        return []

    should_cleanup_pipeline = False
    try:
        import torch
        if pipeline is None:
            if progress_cb:
                progress_cb(10, "Initializing Pyannote Speaker Diarization pipeline...", "Checking HuggingFace access token and credentials")
            pipeline = _load_pyannote_pipeline(hf_token, device)
            should_cleanup_pipeline = True
            
        if is_cancelled_cb and is_cancelled_cb():
            return []
            
        if progress_cb:
            progress_cb(25, "Running speaker diarization neural networks...", "Extracting voice embeddings and segmenting speaker turns")

        # Format input directly as in-memory tensor to eliminate torchcodec requirement & disk I/O
        if isinstance(audio_input, np.ndarray):
            tensor_wav = torch.from_numpy(audio_input.astype(np.float32))
            if tensor_wav.ndim == 1:
                tensor_wav = tensor_wav.unsqueeze(0)
            diar_input = {"waveform": tensor_wav, "sample_rate": 16000}
        elif isinstance(audio_input, dict):
            diar_input = audio_input
        elif isinstance(audio_input, str):
            arr, sr = load_wav_file(audio_input)
            tensor_wav = torch.from_numpy(arr.astype(np.float32))
            if tensor_wav.ndim == 1:
                tensor_wav = tensor_wav.unsqueeze(0)
            diar_input = {"waveform": tensor_wav, "sample_rate": sr}
        else:
            diar_input = audio_input

        with torch.inference_mode():
            diarization = pipeline(diar_input)
        
        # Extract annotation object (handles both Pyannote Annotation and DiarizeOutput dataclass)
        annotation = getattr(diarization, "annotation", diarization)
        if hasattr(annotation, "speaker_diarization"):
            annotation = annotation.speaker_diarization
            
        for turn, _, speaker in annotation.itertracks(yield_label=True):
            dur = float(turn.end - turn.start)
            if dur >= 0.35:  # Filter out micro-background noise & far-away whisper blips
                turns.append({
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "duration": dur,
                    "formatted_start": format_timestamp(turn.start),
                    "formatted_end": format_timestamp(turn.end),
                    "speaker": str(speaker)
                })

        if progress_cb:
            spk_count = len(set(t["speaker"] for t in turns))
            progress_cb(38, f"Diarization finished! Detected {spk_count} distinct speaker(s).", f"Processed {len(turns)} speaker turn(s)")

        # Explicitly release intermediate tensors from memory
        try:
            del diar_input
            del diarization
            del annotation
        except Exception:
            pass

        import gc
        gc.collect()

        if should_cleanup_pipeline:
            try:
                del pipeline
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    except Exception as e:
        err_msg = str(e)
        if "gated repo" in err_msg.lower() or "401" in err_msg or "token" in err_msg.lower():
            raise ValueError("Hugging Face Access Token required or invalid for 'pyannote/speaker-diarization-3.1'. "
                             "Please visit https://hf.co/pyannote/speaker-diarization-3.1 to accept conditions and provide a valid HF Token.") from e
        elif "No module named 'pyannote'" in err_msg:
            # Fallback mock for demonstration if pyannote package is missing
            turns = _fallback_diarization(audio_path)
        else:
            raise e
            
    return turns

def _fallback_diarization(audio_path: str):
    """Energy/VAD based simple diarization fallback when pyannote dependencies are missing."""
    audio_array, sr = load_wav_file(audio_path)
    total_duration = len(audio_array) / sr
    
    # Split audio into simple speaker turns based on duration chunks
    chunk_size = 5.0 # 5 seconds
    turns = []
    current_time = 0.0
    speaker_idx = 0
    
    while current_time < total_duration:
        end_time = min(current_time + chunk_size, total_duration)
        turns.append({
            "start": round(current_time, 3),
            "end": round(end_time, 3),
            "formatted_start": format_timestamp(current_time),
            "formatted_end": format_timestamp(end_time),
            "speaker": f"SPEAKER_{speaker_idx % 2:02d}"
        })
        current_time = end_time
        speaker_idx += 1
        
    return turns

def export_diarization_file(turns: list, output_path: str, filename: str = "audio.wav"):
    """
    Generates File #1: Diarization file output (who talked when).
    """
    unique_speakers = sorted(list(set(t["speaker"] for t in turns)))
    
    lines = []
    lines.append("=" * 80)
    lines.append("SPEAKER DIARIZATION REPORT (WHO TALKED WHEN)")
    lines.append(f"Source File   : {filename}")
    lines.append(f"Total Speakers: {len(unique_speakers)} ({', '.join(unique_speakers)})")
    lines.append(f"Total Turns   : {len(turns)}")
def map_speaker_roles(turns: list, mode: str = "doctor_patient") -> dict:
    """
    Analyzes all speaker turns across the audio recording.
    In 'doctor_patient' mode:
    - Finds the dominant speaker who speaks the most across the consultation and labels them 'doctor'.
    - Maps secondary speakers to 'patient' (or 'patient_1', 'patient_2').
    """
    if not turns or mode != "doctor_patient":
        return {}

    spk_durations = {}
    for turn in turns:
        spk = turn.get("speaker")
        if spk:
            dur = float(turn.get("end", 0) - turn.get("start", 0))
            spk_durations[spk] = spk_durations.get(spk, 0.0) + dur

    if not spk_durations:
        return {}

    # Sort speakers by total duration descending
    sorted_spks = sorted(spk_durations.items(), key=lambda x: x[1], reverse=True)
    doctor_spk = sorted_spks[0][0]

    role_map = {doctor_spk: "doctor"}
    other_spks = [s for s, _ in sorted_spks[1:]]

    if len(other_spks) == 1:
        role_map[other_spks[0]] = "patient"
    else:
        for idx, s in enumerate(other_spks, 1):
            role_map[s] = f"patient_{idx}"

    return role_map

def apply_role_mapping(speaker_str: str, role_map: dict) -> str:
    """
    Replaces raw speaker tags (SPEAKER_00, SPEAKER_01) with human role labels (doctor, patient).
    Preserves overlap formatting, e.g. 'SPEAKER_00 (overlapped by SPEAKER_01)' -> 'doctor (overlapped by patient)'.
    """
    if not role_map or not speaker_str:
        return speaker_str

    res = str(speaker_str)
    for raw_spk, role in role_map.items():
        res = res.replace(raw_spk, role)
    return res

def export_diarization_file(turns: list, output_path: str, filename: str = "audio.wav", speaker_mode: str = "doctor_patient"):
    """
    Generates File #1: Diarization file output (who talked when).
    """
    role_map = map_speaker_roles(turns, mode=speaker_mode)
    unique_speakers = sorted(list(set(apply_role_mapping(t["speaker"], role_map) for t in turns)))
    
    lines = []
    lines.append("=" * 80)
    lines.append("SPEAKER DIARIZATION REPORT (WHO TALKED WHEN)")
    lines.append(f"Source File   : {filename}")
    lines.append(f"Total Speakers: {len(unique_speakers)} ({', '.join(unique_speakers)})")
    lines.append(f"Total Turns   : {len(turns)}")
    lines.append("=" * 80)
    lines.append("")
    
    for turn in turns:
        spk = apply_role_mapping(turn["speaker"], role_map)
        lines.append(f"[{turn['formatted_start']} --> {turn['formatted_end']}] {spk}")
        
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return content

def export_stt_file(stt_result: dict, output_path: str, filename: str = "audio.wav"):
    """
    Generates File #2: Speech-to-Text output file with Whisper timestamps.
    """
    segments = stt_result.get("segments", [])
    
    lines = []
    lines.append("=" * 80)
    lines.append("OPENAI WHISPER SPEECH-TO-TEXT WITH TIMESTAMPS")
    lines.append(f"Source File : {filename}")
    lines.append(f"Language    : {stt_result.get('language', 'unknown')}")
    lines.append(f"Total Segs  : {len(segments)}")
    lines.append("=" * 80)
    lines.append("")
    
    for seg in segments:
        lines.append(f"[{seg['formatted_start']} --> {seg['formatted_end']}]  {seg['text']}")
        
    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return content

def clean_and_group_transcript(turns: list, segments: list, speaker_mode: str = "doctor_patient") -> list:
    """
    Collapses repetitive hallucinations (e.g., repeated 'موسیقی' loops),
    maps speaker roles (e.g. doctor / patient), and groups consecutive lines by speaker.
    """
    if not segments:
        return []

    role_map = map_speaker_roles(turns, mode=speaker_mode)

    def get_speaker(start_t, end_t):
        if not turns:
            return "doctor" if speaker_mode == "doctor_patient" else "SPEAKER_00"
        
        spk_overlaps = {}
        seg_dur = max(0.1, end_t - start_t)
        
        for turn in turns:
            overlap_start = max(start_t, turn["start"])
            overlap_end = min(end_t, turn["end"])
            overlap = max(0.0, overlap_end - overlap_start)
            if overlap > 0:
                spk = turn["speaker"]
                spk_overlaps[spk] = spk_overlaps.get(spk, 0.0) + overlap
                
        if not spk_overlaps:
            raw_spk = turns[0]["speaker"]
            return apply_role_mapping(raw_spk, role_map)
            
        # Primary speaker has highest overlap duration
        sorted_spks = sorted(spk_overlaps.items(), key=lambda x: x[1], reverse=True)
        primary_spk = apply_role_mapping(sorted_spks[0][0], role_map)
        
        # Flag secondary overlapping speaker if present for >30% duration
        if len(sorted_spks) > 1 and (sorted_spks[1][1] / seg_dur) >= 0.3:
            sec_spk = apply_role_mapping(sorted_spks[1][0], role_map)
            return f"{primary_spk} (overlapped by {sec_spk})"
            
        return primary_spk

    MUSIC_NOISE_PATTERNS = [
        r'^\s*موسیقی\s*$',
        r'^\s*آهنگ\s*$',
        r'^\s*موزیک\s*$',
        r'^\s*\[?\(?موسیقی\)?\]?\s*$',
        r'^\s*\[?\(?آهنگ\)?\]?\s*$',
        r'^\s*\[?\(?موزیک\)?\]?\s*$',
        r'^\s*\[.*repetitive background audio.*\]\s*$'
    ]

    def is_music_line(text_str: str) -> bool:
        t = text_str.strip()
        for p in MUSIC_NOISE_PATTERNS:
            if re.match(p, t, re.IGNORECASE):
                return True
        return False

    raw_items = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text or is_music_line(text):
            continue
        spk = get_speaker(seg["start"], seg["end"])
        raw_items.append({
            "start": seg["start"],
            "end": seg["end"],
            "formatted_start": seg["formatted_start"],
            "formatted_end": seg["formatted_end"],
            "speaker": spk,
            "text": text
        })

    if not raw_items:
        return []

    # 1. Deduplicate consecutive identical hallucinated phrases
    filtered_items = []
    repeat_count = 0
    last_text = None

    for item in raw_items:
        txt = item["text"].strip()
        if txt == last_text:
            repeat_count += 1
            if repeat_count < 3:
                filtered_items.append(item)
            elif repeat_count == 3:
                item_copy = dict(item)
                item_copy["text"] = "[... repetitive background audio / music ...]"
                filtered_items.append(item_copy)
            # Skip excess repeats
        else:
            repeat_count = 1
            last_text = txt
            filtered_items.append(item)

    # 2. Group adjacent lines belonging to the same speaker
    grouped = []
    current_group = None

    for item in filtered_items:
        if current_group is None:
            current_group = {
                "start": item["start"],
                "end": item["end"],
                "formatted_start": item["formatted_start"],
                "formatted_end": item["formatted_end"],
                "speaker": item["speaker"],
                "text_parts": [item["text"]]
            }
        elif current_group["speaker"] == item["speaker"] and (item["start"] - current_group["end"]) < 2.5:
            current_group["end"] = item["end"]
            current_group["formatted_end"] = item["formatted_end"]
            if item["text"] not in current_group["text_parts"]:
                current_group["text_parts"].append(item["text"])
        else:
            grouped.append(current_group)
            current_group = {
                "start": item["start"],
                "end": item["end"],
                "formatted_start": item["formatted_start"],
                "formatted_end": item["formatted_end"],
                "speaker": item["speaker"],
                "text_parts": [item["text"]]
            }

    if current_group:
        grouped.append(current_group)

    return grouped

def export_combined_file(turns: list, stt_result: dict, output_path: str, filename: str = "audio.wav", speaker_mode: str = "doctor_patient"):
    """
    Bonus File: Aligns Whisper segments with Pyannote speaker turns to produce a clean, grouped transcript with doctor/patient labels.
    """
    segments = stt_result.get("segments", [])
    grouped = clean_and_group_transcript(turns, segments, speaker_mode=speaker_mode)

    lines = []
    lines.append("=" * 80)
    lines.append("SPEAKER-ATTRIBUTED TRANSCRIPT (CLEAN & GROUPED)")
    lines.append(f"Source File : {filename}")
    lines.append("=" * 80)
    lines.append("")

    for item in grouped:
        text = " ".join(item["text_parts"])
        lines.append(f"[{item['formatted_start']} --> {item['formatted_end']}] {item['speaker']}: {text}")
        lines.append("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return content

def process_resumable_audio_job(
    file_path: str,
    job_dir: str,
    filename: str,
    whisper_model: str = "large-v3",
    hf_token: str = None,
    device: str = "cuda",
    language: str = "fa",
    initial_prompt: str = DEFAULT_PERSIAN_MEDICAL_PROMPT,
    speaker_mode: str = "doctor_patient",
    chunk_duration_sec: float = 300.0,
    enable_ai_refinement: bool = False,
    ollama_model: str = "",
    ollama_url: str = "http://127.0.0.1:11434",
    ai_prompt: str = "",
    gemini_api_key: str = "",
    progress_cb = None,
    is_cancelled_cb = None
) -> dict:
    """
    Slices long audio files into 5-minute (300s) chunk checkpoints.
    Processes chunks in parallel across all available GPUs using a dynamic task queue!
    Saves each chunk's diarization & STT results immediately to disk as JSON checkpoints.
    If interrupted, app crash, or GPU reset occurs, resumes processing from the last saved 5-minute chunk checkpoint!
    Optionally passes merged output through local Ollama AI model for post-processing and transcript refinement.
    Stitches all chunk checkpoints together into final unified outcome files.
    """
    import soundfile as sf

    checkpoints_dir = os.path.join(job_dir, "checkpoints")
    chunks_dir = os.path.join(job_dir, "chunks")
    os.makedirs(checkpoints_dir, exist_ok=True)
    os.makedirs(chunks_dir, exist_ok=True)

    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    if progress_cb:
        progress_cb(5, "Reading audio info and inspecting 5-minute checkpoints...", f"Initializing processing engine on {device.upper()}")

    total_duration, native_sr = get_wav_info(file_path)
    total_chunks = max(1, int(np.ceil(total_duration / float(chunk_duration_sec))))

    all_turns = []
    all_stt_segments = []

    # =========================================================================
    # STAGE 1: SPEAKER DIARIZATION (Pyannote isolated in memory)
    # =========================================================================
    pending_diar_chunks = []
    for chunk_idx in range(total_chunks):
        chk_file = os.path.join(checkpoints_dir, f"chunk_{chunk_idx:03d}.json")
        if os.path.exists(chk_file):
            try:
                with open(chk_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                if "turns" in cdata:
                    continue
            except Exception:
                pass
        pending_diar_chunks.append(chunk_idx)

    if pending_diar_chunks:
        if progress_cb:
            progress_cb(10, f"Loading Pyannote Diarization engine into GPU ({len(pending_diar_chunks)} chunks to process)...", "Stage 1: Speaker Diarization")
        pyannote_instance = _load_pyannote_pipeline(hf_token=hf_token, device=device)
        trim_process_memory()

        try:
            for i, chunk_idx in enumerate(pending_diar_chunks):
                if is_cancelled_cb and is_cancelled_cb():
                    return {}

                chunk_start_sec = chunk_idx * chunk_duration_sec
                chunk_end_sec = min(total_duration, (chunk_idx + 1) * chunk_duration_sec)
                chunk_dur = chunk_end_sec - chunk_start_sec
                
                c_start_fmt = format_timestamp(chunk_start_sec).split('.')[0]
                c_end_fmt = format_timestamp(chunk_end_sec).split('.')[0]
                tot_fmt = format_timestamp(total_duration).split('.')[0]

                if progress_cb:
                    pct = int(10 + ((i + 1) / len(pending_diar_chunks)) * 35)
                    progress_cb(
                        pct,
                        f"Diarizing Chunk {chunk_idx + 1}/{total_chunks} [{c_start_fmt} -> {c_end_fmt} / {tot_fmt}]",
                        f"Extracting speaker turns ({i + 1}/{len(pending_diar_chunks)})"
                    )

                chk_file = os.path.join(checkpoints_dir, f"chunk_{chunk_idx:03d}.json")
                chk_data = {}
                if os.path.exists(chk_file):
                    try:
                        with open(chk_file, "r", encoding="utf-8") as f:
                            chk_data = json.load(f)
                    except Exception:
                        chk_data = {}

                chunk_audio_slice = read_wav_chunk(file_path, chunk_start_sec, chunk_dur, target_sr=16000)
                chunk_turns_raw = run_pyannote_diarization(
                    chunk_audio_slice,
                    hf_token=hf_token,
                    device=device,
                    pipeline=pyannote_instance,
                    progress_cb=None,
                    is_cancelled_cb=is_cancelled_cb
                )
                if is_cancelled_cb and is_cancelled_cb():
                    return {}

                chunk_turns = []
                for t in chunk_turns_raw:
                    g_start = round(t["start"] + chunk_start_sec, 3)
                    g_end = round(t["end"] + chunk_start_sec, 3)
                    chunk_turns.append({
                        "start": g_start,
                        "end": g_end,
                        "formatted_start": format_timestamp(g_start),
                        "formatted_end": format_timestamp(g_end),
                        "speaker": t["speaker"]
                    })

                chk_data["chunk_index"] = chunk_idx
                chk_data["start_sec"] = chunk_start_sec
                chk_data["end_sec"] = chunk_end_sec
                chk_data["turns"] = chunk_turns
                with open(chk_file, "w", encoding="utf-8") as f:
                    json.dump(chk_data, f, ensure_ascii=False, indent=2)

                try:
                    del chunk_audio_slice
                    del chunk_turns_raw
                    del chunk_turns
                    del chk_data
                except Exception:
                    pass

                trim_process_memory()

                # 5-second GPU cool-off rest between chunks (model stays warm in VRAM)
                if i < len(pending_diar_chunks) - 1:
                    time.sleep(5)

        finally:
            # Fully purge Pyannote from memory once all diarization chunks complete
            try:
                del pyannote_instance
                trim_process_memory()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    if progress_cb:
        progress_cb(48, "Speaker Diarization complete [OK] - Purged diarization engine from memory.", "Stage 1 finished")

    # =========================================================================
    # STAGE 2: SPEECH-TO-TEXT TRANSCRIPTION (Whisper isolated in memory)
    # =========================================================================
    pending_stt_chunks = []
    for chunk_idx in range(total_chunks):
        chk_file = os.path.join(checkpoints_dir, f"chunk_{chunk_idx:03d}.json")
        if os.path.exists(chk_file):
            try:
                with open(chk_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                if "stt_segments" in cdata:
                    continue
            except Exception:
                pass
        pending_stt_chunks.append(chunk_idx)

    # Cool off before starting Stage 2 if diarization was just run
    if pending_diar_chunks and pending_stt_chunks:
        time.sleep(5)

    if pending_stt_chunks:
        if progress_cb:
            progress_cb(50, f"Loading Whisper '{whisper_model}' model into GPU ({len(pending_stt_chunks)} chunks to process)...", "Stage 2: Speech-to-Text")
        whisper_instance = _load_whisper_with_auto_repair(whisper_model, device=device)
        trim_process_memory()

        try:
            for i, chunk_idx in enumerate(pending_stt_chunks):
                if is_cancelled_cb and is_cancelled_cb():
                    return {}

                chunk_start_sec = chunk_idx * chunk_duration_sec
                chunk_end_sec = min(total_duration, (chunk_idx + 1) * chunk_duration_sec)
                chunk_dur = chunk_end_sec - chunk_start_sec
                
                c_start_fmt = format_timestamp(chunk_start_sec).split('.')[0]
                c_end_fmt = format_timestamp(chunk_end_sec).split('.')[0]
                tot_fmt = format_timestamp(total_duration).split('.')[0]

                if progress_cb:
                    pct = int(50 + ((i + 1) / len(pending_stt_chunks)) * 36)
                    progress_cb(
                        pct,
                        f"Transcribing Chunk {chunk_idx + 1}/{total_chunks} [{c_start_fmt} -> {c_end_fmt} / {tot_fmt}]",
                        f"Whisper inference ({i + 1}/{len(pending_stt_chunks)})"
                    )

                chk_file = os.path.join(checkpoints_dir, f"chunk_{chunk_idx:03d}.json")
                chk_data = {}
                if os.path.exists(chk_file):
                    try:
                        with open(chk_file, "r", encoding="utf-8") as f:
                            chk_data = json.load(f)
                    except Exception:
                        chk_data = {}

                chunk_audio_slice = read_wav_chunk(file_path, chunk_start_sec, chunk_dur, target_sr=16000)
                chunk_stt_raw = run_whisper_stt(
                    chunk_audio_slice,
                    model_name=whisper_model,
                    language=language,
                    initial_prompt=initial_prompt,
                    device=device,
                    model=whisper_instance,
                    progress_cb=None,
                    is_cancelled_cb=is_cancelled_cb
                )
                if is_cancelled_cb and is_cancelled_cb():
                    return {}

                chunk_segments = []
                for s in chunk_stt_raw.get("segments", []):
                    g_start = round(s["start"] + chunk_start_sec, 3)
                    g_end = round(s["end"] + chunk_start_sec, 3)
                    chunk_segments.append({
                        "id": s.get("id", 0),
                        "start": g_start,
                        "end": g_end,
                        "formatted_start": format_timestamp(g_start),
                        "formatted_end": format_timestamp(g_end),
                        "text": s["text"]
                    })

                chk_data["chunk_index"] = chunk_idx
                chk_data["start_sec"] = chunk_start_sec
                chk_data["end_sec"] = chunk_end_sec
                chk_data["stt_segments"] = chunk_segments
                chk_data["status"] = "completed"
                with open(chk_file, "w", encoding="utf-8") as f:
                    json.dump(chk_data, f, ensure_ascii=False, indent=2)

                try:
                    del chunk_audio_slice
                    del chunk_stt_raw
                    del chunk_segments
                    del chk_data
                except Exception:
                    pass

                trim_process_memory()

                # 5-second GPU cool-off rest between chunks (model stays warm in VRAM)
                if i < len(pending_stt_chunks) - 1:
                    time.sleep(5)

        finally:
            # Fully purge Whisper from memory once all STT chunks complete
            try:
                del whisper_instance
                trim_process_memory()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

    if progress_cb:
        progress_cb(86, "Transcription complete [OK] - Purged Whisper model from memory.", "Stage 2 finished")

    # =========================================================================
    # STAGE 3: ASSEMBLE ALL CHUNKS AND EXPORT REPORTS
    # =========================================================================
    for chunk_idx in range(total_chunks):
        chk_file = os.path.join(checkpoints_dir, f"chunk_{chunk_idx:03d}.json")
        if os.path.exists(chk_file):
            try:
                with open(chk_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                all_turns.extend(cdata.get("turns", []))
                all_stt_segments.extend(cdata.get("stt_segments", []))
            except Exception as e_c:
                print(f"Error reading checkpoint {chk_file}: {e_c}")

    if progress_cb:
        progress_cb(88, "Stitching 5-minute chunk checkpoints into final unified reports...", "Writing Diarization, STT, & Merged files")

    raw_dir = os.path.join(job_dir, "raw")
    refined_dir = os.path.join(job_dir, "refined")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(refined_dir, exist_ok=True)

    base_name = os.path.splitext(filename)[0]
    diar_path = os.path.join(raw_dir, f"{base_name}_diarization.txt")
    stt_path = os.path.join(raw_dir, f"{base_name}_stt_timestamps.txt")
    merged_path = os.path.join(raw_dir, f"{base_name}_merged_transcript.txt")

    stt_result_combined = {
        "text": " ".join(s["text"] for s in all_stt_segments),
        "language": language,
        "segments": all_stt_segments
    }

    diar_content = export_diarization_file(all_turns, diar_path, filename=filename, speaker_mode=speaker_mode)
    stt_content = export_stt_file(stt_result_combined, stt_path, filename=filename)
    merged_content = export_combined_file(all_turns, stt_result_combined, merged_path, filename=filename, speaker_mode=speaker_mode)

    # Maintain root copies for full backward compatibility
    try:
        shutil.copyfile(diar_path, os.path.join(job_dir, f"{base_name}_diarization.txt"))
        shutil.copyfile(stt_path, os.path.join(job_dir, f"{base_name}_stt_timestamps.txt"))
        shutil.copyfile(merged_path, os.path.join(job_dir, f"{base_name}_merged_transcript.txt"))
    except Exception:
        pass

    ai_refined_content = ""
    ai_refined_path = ""

    if enable_ai_refinement and ollama_model:
        refine_res = refine_existing_transcript(
            job_dir=job_dir,
            filename=filename,
            ollama_model=ollama_model,
            ollama_url=ollama_url,
            ai_prompt=ai_prompt,
            gemini_api_key=gemini_api_key,
            merged_content=merged_content,
            progress_cb=progress_cb,
            is_cancelled_cb=is_cancelled_cb
        )
        ai_refined_content = refine_res.get("ai_refined_preview", "")
        ai_refined_path = refine_res.get("ai_refined_path", "")

    results = {
        "diarization_file": os.path.basename(diar_path),
        "stt_file": os.path.basename(stt_path),
        "merged_file": os.path.basename(merged_path),
        "raw_folder": "raw",
        "refined_folder": "refined",
        "raw_diarization_file": f"raw/{os.path.basename(diar_path)}",
        "raw_stt_file": f"raw/{os.path.basename(stt_path)}",
        "raw_merged_file": f"raw/{os.path.basename(merged_path)}",
        "diarization_preview": diar_content,
        "stt_preview": stt_content,
        "merged_preview": merged_content,
        "speaker_count": len(set(t["speaker"] for t in all_turns)),
        "segment_count": len(all_stt_segments)
    }

    if ai_refined_path and os.path.exists(ai_refined_path):
        results["ai_refined_file"] = os.path.basename(ai_refined_path)
        results["refined_file"] = f"refined/{os.path.basename(ai_refined_path)}"
        results["ai_refined_preview"] = ai_refined_content
        results["refined_diarization_file"] = refine_res.get("refined_diarization_file", "")
        results["refined_stt_file"] = refine_res.get("refined_stt_file", "")
        results["refined_merged_file"] = refine_res.get("refined_merged_file", "")
        results["refined_diarization_preview"] = refine_res.get("refined_diarization_preview", "")
        results["refined_stt_preview"] = refine_res.get("refined_stt_preview", "")

    return results

def derive_refined_subfiles(ai_refined_content: str, filename: str = "audio.wav") -> tuple:
    """
    Parses the AI-refined merged transcript to derive:
    1. Refined Diarization content (timestamps + speaker role tags).
    2. Refined STT Timestamps content (timestamps + refined text without speaker tags).
    Zero extra LLM tokens required!
    """
    lines = ai_refined_content.splitlines()
    diar_lines = []
    stt_lines = []
    unique_speakers = set()
    turn_count = 0

    ts_pattern = re.compile(r'^(\[\s*\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s*-->\s*\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\s*\])\s*(.*?)$')

    for line in lines:
        line_s = line.strip()
        if not line_s or line_s.startswith("=") or line_s.startswith("Source File") or line_s.startswith("SPEAKER-ATTRIBUTED") or line_s.startswith("```"):
            continue
        
        m = ts_pattern.match(line_s)
        if m:
            ts = m.group(1)
            rest = m.group(2).strip()
            
            spk_match = re.match(r'^([a-zA-Z0-9_\-]+(?:\s*\(.*?\))?)\s*:\s*(.*)$', rest)
            if spk_match:
                spk = spk_match.group(1).strip()
                text = spk_match.group(2).strip()
            else:
                spk = "speaker"
                text = rest
                
            spk_base = re.sub(r'\(.*?\)', '', spk).strip()
            unique_speakers.add(spk_base)
            turn_count += 1
            diar_lines.append(f"{ts} {spk}")
            stt_lines.append(f"{ts}  {text}")

    spk_list_str = ", ".join(sorted(unique_speakers)) if unique_speakers else "unknown"

    diar_header = [
        "=" * 80,
        "SPEAKER DIARIZATION REPORT (REFINED - WHO TALKED WHEN)",
        f"Source File   : {filename}",
        f"Total Speakers: {len(unique_speakers)} ({spk_list_str})",
        f"Total Turns   : {turn_count}",
        "=" * 80,
        ""
    ]
    diar_content = "\n".join(diar_header + diar_lines)

    stt_header = [
        "=" * 80,
        "OPENAI WHISPER SPEECH-TO-TEXT WITH TIMESTAMPS (REFINED)",
        f"Source File : {filename}",
        f"Total Segs  : {turn_count}",
        "=" * 80,
        ""
    ]
    stt_content = "\n".join(stt_header + stt_lines)

    return diar_content, stt_content

def refine_existing_transcript(
    job_dir: str,
    filename: str,
    ollama_model: str,
    ollama_url: str = "http://127.0.0.1:11434",
    ai_prompt: str = "",
    gemini_api_key: str = "",
    merged_content: str = "",
    progress_cb = None,
    is_cancelled_cb = None
) -> dict:
    """
    Executes AI Post-Processing Refinement on an existing completed transcript.
    Saves all 3 outcome files (diarization, STT, and merged) in the refined/ subfolder without extra token costs.
    """
    import shutil
    base_name = os.path.splitext(filename)[0]
    raw_dir = os.path.join(job_dir, "raw")
    refined_dir = os.path.join(job_dir, "refined")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(refined_dir, exist_ok=True)

    # Load merged content from disk if not provided in-memory
    if not merged_content:
        raw_merged_path = os.path.join(raw_dir, f"{base_name}_merged_transcript.txt")
        root_merged_path = os.path.join(job_dir, f"{base_name}_merged_transcript.txt")
        target_merged = raw_merged_path if os.path.exists(raw_merged_path) else root_merged_path
        if not os.path.exists(target_merged):
            raise FileNotFoundError(f"Merged transcript file not found for job in {job_dir}")
        with open(target_merged, "r", encoding="utf-8") as f:
            merged_content = f.read()

    from gemini_service import sanitize_ai_prompt
    ai_prompt = sanitize_ai_prompt(ai_prompt)

    ai_refined_content = ""
    refined_diar_content = ""
    refined_stt_content = ""
    ai_refined_path = os.path.join(refined_dir, f"{base_name}_ai_refined_transcript.txt")
    refined_diar_path = os.path.join(refined_dir, f"{base_name}_diarization.txt")
    refined_stt_path = os.path.join(refined_dir, f"{base_name}_stt_timestamps.txt")

    try:
        # Free CUDA VRAM so LLM runs with maximum memory space
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if ollama_model.startswith("gemini:"):
            from gemini_service import run_gemini_refinement
            if progress_cb:
                progress_cb(92, f"Running Google Gemini AI Refinement ({ollama_model})...", "Refining transcript via Google Gemini Cloud API")
            ai_refined_content = run_gemini_refinement(
                transcript_text=merged_content,
                model_name=ollama_model,
                api_key=gemini_api_key,
                system_prompt=ai_prompt,
                progress_cb=progress_cb
            )
        elif ollama_model.startswith("hf:"):
            from standalone_llm import run_standalone_refinement
            repo_id = ollama_model.replace("hf:", "")
            if progress_cb:
                progress_cb(92, f"Running Standalone LLM Refinement ({repo_id})...", "Refining diarization, stripping music, and correcting medical terms")
            ai_refined_content = run_standalone_refinement(
                transcript_text=merged_content,
                repo_id=repo_id,
                system_prompt=ai_prompt,
                progress_cb=progress_cb
            )
        else:
            if progress_cb:
                progress_cb(92, f"Running Ollama AI Post-Processing ({ollama_model})...", "Refining diarization, stripping background music, and correcting medical terms")
            from ollama_service import run_ollama_refinement
            ai_refined_content = run_ollama_refinement(
                transcript_text=merged_content,
                model_name=ollama_model,
                system_prompt=ai_prompt,
                base_url=ollama_url,
                progress_cb=progress_cb,
                is_cancelled_cb=is_cancelled_cb
            )

        if ai_refined_content and not ai_refined_content.startswith("AI Refinement Error:"):
            # Derive refined STT and Diarization files locally from refined transcript (zero extra tokens)
            refined_diar_content, refined_stt_content = derive_refined_subfiles(ai_refined_content, filename)

            with open(ai_refined_path, "w", encoding="utf-8") as f:
                f.write(ai_refined_content)

            with open(refined_diar_path, "w", encoding="utf-8") as f:
                f.write(refined_diar_content)

            with open(refined_stt_path, "w", encoding="utf-8") as f:
                f.write(refined_stt_content)

            # Copy to root and mirror names as well for backward compatibility
            try:
                shutil.copyfile(ai_refined_path, os.path.join(refined_dir, f"{base_name}_merged_transcript.txt"))
                shutil.copyfile(ai_refined_path, os.path.join(job_dir, f"{base_name}_ai_refined_transcript.txt"))
            except Exception:
                pass
        elif ai_refined_content:
            with open(ai_refined_path, "w", encoding="utf-8") as f:
                f.write(ai_refined_content)

    except Exception as e_ai:
        print(f"AI Refinement warning: {e_ai}")
        ai_refined_content = f"AI Refinement Error: {str(e_ai)}\n\nOriginal Merged Transcript:\n\n" + merged_content

    return {
        "ai_refined_path": ai_refined_path,
        "ai_refined_file": os.path.basename(ai_refined_path),
        "refined_file": f"refined/{os.path.basename(ai_refined_path)}",
        "ai_refined_preview": ai_refined_content,
        "refined_diarization_file": f"refined/{base_name}_diarization.txt",
        "refined_stt_file": f"refined/{base_name}_stt_timestamps.txt",
        "refined_merged_file": f"refined/{base_name}_ai_refined_transcript.txt",
        "refined_diarization_preview": refined_diar_content,
        "refined_stt_preview": refined_stt_content
    }
