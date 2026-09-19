import os
import re
import gc
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
HF_MODELS_DIR = os.path.join(MODELS_DIR, "huggingface")
HF_HUB_CACHE = os.path.join(HF_MODELS_DIR, "hub")

os.makedirs(HF_HUB_CACHE, exist_ok=True)
os.environ["HF_HOME"] = HF_MODELS_DIR
os.environ["HUGGINGFACE_HUB_CACHE"] = HF_HUB_CACHE
os.environ["TRANSFORMERS_CACHE"] = HF_HUB_CACHE

STANDALONE_MODELS = {
    "hf:CohereForAI/aya-23-8b": {
        "name": "⚡ Standalone: Cohere Aya-23 8B (5.2 GB - Best Persian Model)",
        "repo_id": "CohereForAI/aya-23-8b"
    },
    "hf:Qwen/Qwen2.5-14B-Instruct": {
        "name": "⚡ Standalone: Qwen2.5 14B Instruct (14.2 GB - High Capacity)",
        "repo_id": "Qwen/Qwen2.5-14B-Instruct"
    },
    "hf:Qwen/Qwen2.5-7B-Instruct": {
        "name": "⚡ Standalone: Qwen2.5 7B Instruct (7.2 GB)",
        "repo_id": "Qwen/Qwen2.5-7B-Instruct"
    },
    "hf:meta-llama/Meta-Llama-3.1-8B-Instruct": {
        "name": "⚡ Standalone: Meta Llama 3.1 8B Instruct (5.1 GB - High Accuracy Persian)",
        "repo_id": "meta-llama/Meta-Llama-3.1-8B-Instruct"
    },
    "hf:deepseek-ai/DeepSeek-R1-Distill-Qwen-7B": {
        "name": "⚡ Standalone: DeepSeek R1 Distill 7B (4.7 GB - Reasoning Engine)",
        "repo_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    },
    "hf:Qwen/Qwen2.5-3B-Instruct": {
        "name": "⚡ Standalone: Qwen2.5 3B Instruct (3.0 GB)",
        "repo_id": "Qwen/Qwen2.5-3B-Instruct"
    },
    "hf:meta-llama/Llama-3.2-3B-Instruct": {
        "name": "⚡ Standalone: Llama 3.2 3B Instruct (3.2 GB)",
        "repo_id": "meta-llama/Llama-3.2-3B-Instruct"
    },
    "hf:google/gemma-2-2b-it": {
        "name": "⚡ Standalone: Gemma 2 2B IT (2.6 GB)",
        "repo_id": "google/gemma-2-2b-it"
    }
}

_loaded_model = None
_loaded_tokenizer = None
_current_model_id = None

def load_standalone_model(repo_id: str):
    global _loaded_model, _loaded_tokenizer, _current_model_id
    if _current_model_id == repo_id and _loaded_model is not None:
        return _loaded_model, _loaded_tokenizer

    print(f"Loading Standalone HuggingFace LLM: {repo_id}...")
    if _loaded_model is not None:
        del _loaded_model
        del _loaded_tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    tokenizer = AutoTokenizer.from_pretrained(repo_id, cache_dir=HF_HUB_CACHE, trust_remote_code=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        repo_id,
        cache_dir=HF_HUB_CACHE,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    _loaded_model = model
    _loaded_tokenizer = tokenizer
    _current_model_id = repo_id
    return model, tokenizer

def run_standalone_refinement(
    transcript_text: str,
    repo_id: str,
    system_prompt: str,
    progress_cb=None
) -> str:
    """
    Runs LLM refinement natively via PyTorch & Transformers without requiring Ollama.
    """
    from gemini_service import DEFAULT_AI_POST_PROCESS_PROMPT
    if not system_prompt or not system_prompt.strip():
        system_prompt = DEFAULT_AI_POST_PROCESS_PROMPT

    model, tokenizer = load_standalone_model(repo_id)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"[INPUT DIALOGUE TO RECONSTRUCT]\n{transcript_text}\n\n[RECONSTRUCTED CLINICAL TRANSCRIPT]:\n"}
    ]

    text_input = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([text_input], return_tensors="pt").to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.2,
            do_sample=False
        )

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
    ]
    response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return response_text.strip()
