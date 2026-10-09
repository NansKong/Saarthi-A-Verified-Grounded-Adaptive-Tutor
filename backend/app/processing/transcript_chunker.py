def merge_transcript_segments(
    segments: list,
    target_duration: float = 45.0
) -> list[dict]:

    merged = []

    current_text = []
    current_start = None
    current_end = None

    for segment in segments:

        if isinstance(segment, dict):
            start = float(segment.get("start", 0))
            end = float(segment.get("end", 0))
            text = segment.get("text", "").strip()
        else:
            start = float(getattr(segment, "start", 0))
            end = float(getattr(segment, "end", 0))
            text = getattr(segment, "text", "").strip()

        if not text:
            continue

        if current_start is None:
            current_start = start

        current_end = end
        current_text.append(text)

        if current_end - current_start >= target_duration:

            merged.append({
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_text)
            })

            current_text = []
            current_start = None
            current_end = None

    if current_text:
        merged.append({
            "start": current_start,
            "end": current_end,
            "text": " ".join(current_text)
        })

    return merged