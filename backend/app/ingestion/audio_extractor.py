import subprocess
from pathlib import Path


AUDIO_DIR = Path("extracted_audio")
AUDIO_DIR.mkdir(exist_ok=True)


def extract_audio(video_path: str) -> str:
    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    output_path = (
        AUDIO_DIR
        /
        f"{video_path.stem}.mp3"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "32k",
        str(output_path)
    ]

    print(
        f"[Audio Extraction] "
        f"{video_path.name}"
    )

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg was not found. "
            "Make sure ffmpeg is installed and available in PATH."
        )

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"FFmpeg audio extraction failed: {exc}"
        )

    print(
        f"[Audio Extraction] Created: "
        f"{output_path}"
    )

    return str(output_path)