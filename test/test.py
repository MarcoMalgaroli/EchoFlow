import os
import sysconfig
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Videolesson transcriber powered by Faster-Whisper"
)

device_group = parser.add_mutually_exclusive_group()

device_group.add_argument(
    "-c", "--cpu",
    dest="device",
    action="store_const",
    const="cpu",
    help="Use the CPU"
)

device_group.add_argument(
    "-g", "--gpu",
    dest="device",
    action="store_const",
    const="cuda",
    help="Use the NVIDIA GPU (default)"
)

parser.set_defaults(device="cuda")
args = parser.parse_args()


_dll_directory_handles = []

if args.device == "cuda" and os.name == "nt":
    print("Loading NVIDIA DLL libraries...")
    site_packages = Path(sysconfig.get_paths()["purelib"])

    dll_dirs = [
        site_packages / "nvidia" / "cublas" / "bin",
        site_packages / "nvidia" / "cudnn" / "bin",
    ]
    for dll_dir in dll_dirs:
        if dll_dir.exists():
            _dll_directory_handles.append(
                os.add_dll_directory(str(dll_dir))
            )
    print("NVIDIA DLL libraries loaded.")

from faster_whisper import WhisperModel

print(f"Loading Whisper on {args.device.upper()}...")
compute_type = "float16" if args.device == "cuda" else "int8"
    
print(f"Using compute type: {compute_type}")

model = WhisperModel(
    "large-v3",
    device=args.device,
    compute_type=compute_type
)
print("Model loaded successfully.")

video_path = Path(__file__).with_name("video.mp4")
print(f"Transcribing {video_path}...")

print("Transcribing videolesson...")
segments, info = model.transcribe(
    str(video_path),
    language="it",
    task="transcribe",
    vad_filter=True,
    #condition_on_previous_text=False,
    beam_size=10,
    initial_prompt="Questa è una lezione in lingua italiana. Mantieni la trascrizione in italiano, preservando i termini tecnici e le parole inglesi nella loro forma originale."
)

print(f"Detected language: {info.language}")
print(f"Probability: {info.language_probability:.2%}")
print(f"Duration before VAD: {info.duration:.2f}s")
print(f"Duration after VAD: {info.duration_after_vad:.2f}s")

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    #print(f"%s" % (segment.text.strip()), end=" ")