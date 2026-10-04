import argparse
import os
import sys
from audio_processor import (
    run_whisper_stt,
    run_pyannote_diarization,
    export_diarization_file,
    export_stt_file,
    export_combined_file
)

def main():
    parser = argparse.ArgumentParser(
        description="Process WAV audio files with OpenAI Whisper (STT timestamps) and Pyannote Community (Speaker Diarization)."
    )
    parser.add_argument("wav_file", help="Path to input .wav audio file")
    parser.add_argument("--hf_token", default=None, help="Hugging Face access token for pyannote/speaker-diarization-3.1")
    parser.add_argument("--whisper_model", default="base", choices=["tiny", "base", "small", "medium", "large-v3"], help="Whisper model size")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Execution device (cpu or cuda)")
    parser.add_argument("--output_dir", default=".", help="Output directory to save the outcome files")

    args = parser.parse_args()

    if not os.path.exists(args.wav_file):
        print(f"Error: Input file '{args.wav_file}' does not exist.")
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    filename = os.path.basename(args.wav_file)
    base_name = os.path.splitext(filename)[0]

    print(f"=== Audio Processor starting for: {filename} ===")
    
    # 1. Diarization
    print("[1/3] Running Speaker Diarization (Pyannote)...")
    try:
        turns = run_pyannote_diarization(args.wav_file, hf_token=args.hf_token, device=args.device)
        print(f"      Identified {len(set(t['speaker'] for t in turns))} speaker(s) across {len(turns)} turns.")
    except Exception as e:
        print(f"Error during Diarization: {e}")
        sys.exit(1)

    # 2. Whisper STT
    print(f"[2/3] Running Speech-to-Text with Timestamps (Whisper '{args.whisper_model}')...")
    try:
        stt_result = run_whisper_stt(args.wav_file, model_name=args.whisper_model, device=args.device)
        print(f"      Transcribed {len(stt_result.get('segments', []))} text segment(s).")
    except Exception as e:
        print(f"Error during Whisper STT: {e}")
        sys.exit(1)

    # 3. Export Outcome Files
    print("[3/3] Exporting outcome files...")
    
    diar_path = os.path.join(args.output_dir, f"{base_name}_diarization.txt")
    stt_path = os.path.join(args.output_dir, f"{base_name}_stt_timestamps.txt")
    merged_path = os.path.join(args.output_dir, f"{base_name}_merged_transcript.txt")

    export_diarization_file(turns, diar_path, filename=filename)
    export_stt_file(stt_result, stt_path, filename=filename)
    export_combined_file(turns, stt_result, merged_path, filename=filename)

    print("\nSUCCESS! outcome files generated:")
    print(f" 1. Diarization File   : {diar_path}")
    print(f" 2. STT Timestamps File: {stt_path}")
    print(f" 3. Merged Transcript   : {merged_path}\n")

if __name__ == "__main__":
    main()
