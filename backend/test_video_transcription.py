from app.ingestion.video_transcriber import transcribe_audio


def format_timestamp(seconds: float) -> str:
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"

    return f"{minutes:02}:{secs:02}"


units = transcribe_audio(
    audio_path="extracted_audio/lecture_audio.mp3",
    original_video_name="Lecture 1 _ Machine Learning (Stanford)-UzxYlbK2c7E (1).mp4"
)

print(f"\nTotal transcript units: {len(units)}")
print("=" * 80)


for index, unit in enumerate(units, start=1):

    timestamp = unit.location["timestamp"]

    start = timestamp["start"]
    end = timestamp["end"]

    duration = end - start

    print(f"\nChunk {index}")
    print("-" * 80)

    print(
        f"Timeline: "
        f"{format_timestamp(start)} "
        f"→ "
        f"{format_timestamp(end)}"
    )

    print(f"Start seconds: {start:.2f}")
    print(f"End seconds:   {end:.2f}")
    print(f"Duration:      {duration:.2f} seconds")

    print("\nTranscript:")
    print(unit.text)

    print("-" * 80)