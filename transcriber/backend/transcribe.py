from pathlib import Path
import os
import sysconfig


# https://huggingface.co/openai/whisper-large-v3

PROJECT_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output"

MODEL_NAME = "large-v3"
LANGUAGE = "it"
VIDEO_EXTENSION = ".mp4"
DEVICE = os.getenv("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "float16" if DEVICE == "cuda" else "int8",
)

_dll_directory_handles = []

if DEVICE == "cuda" and os.name == "nt":
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

def format_timestamp(seconds: float) -> str:
    """Return a timestamp in HH:MM:SS.ss format."""
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, whole_seconds = divmod(remainder, 60)
    centiseconds = int((seconds - total_seconds) * 100)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02}.{centiseconds:02}"


def transcribe_file(model: WhisperModel, video_path: Path) -> str:
    """Transcribe one video and return its timestamped text."""
    segments, _ = model.transcribe(
        str(video_path),
        language=LANGUAGE,
        task="transcribe",
        beam_size=5,
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        word_timestamps=False,
    )

    lines = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            lines.append(f"[{start} - {end}] {text}")

    return "\n".join(lines)


def output_path_for(video_path: Path) -> Path:
    """Return the mirrored output path for a video inside INPUT_DIR."""
    relative_path = video_path.resolve().relative_to(INPUT_DIR.resolve())
    return (OUTPUT_DIR / relative_path).with_suffix(".txt")


def transcribe_and_save(model: WhisperModel, video_path: Path) -> Path:
    """Transcribe a video and save its text in the mirrored output tree."""
    output_path = output_path_for(video_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcribe_file(model, video_path) + "\n", encoding="utf-8")
    return output_path


def load_model() -> WhisperModel:
    """Load Whisper Large-v3, falling back to CPU when CUDA is unavailable."""
    print(f"Loading Whisper model {MODEL_NAME} on {DEVICE.upper()} using {COMPUTE_TYPE}...")
    try:
        model = WhisperModel(
            MODEL_NAME,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
        )
    except RuntimeError as error:
        if DEVICE != "cuda":
            raise

        print(f"CUDA model loading failed: {error}")
        print("Retrying with the CPU configuration.")
        model = WhisperModel(
            MODEL_NAME,
            device="cpu",
            compute_type="int8",
        )
    
    print("Whisper model loaded successfully.")
    return model


def main() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_files = sorted(
        path
        for path in INPUT_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() == VIDEO_EXTENSION
    )

    if not video_files:
        print(f"No {VIDEO_EXTENSION} video files found in {INPUT_DIR}.")
        return

    model = load_model()

    for index, video_path in enumerate(video_files, start=1):
        output_path = output_path_for(video_path)
        if output_path.exists():
            print(
                f"[{index}/{len(video_files)}] Skipping {video_path.name}: "
                f"{output_path.name} already exists."
            )
            continue

        print(f"[{index}/{len(video_files)}] Transcribing {video_path.name}...")
        transcribe_and_save(model, video_path)
        print(f"Saved {output_path.name}.")

    print("Transcription completed.")


if __name__ == "__main__":
    main()
