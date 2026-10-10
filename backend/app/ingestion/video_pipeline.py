from pathlib import Path

from app.ingestion.audio_extractor import (
    extract_audio
)

from app.ingestion.video_transcriber import (
    transcribe_audio
)

from app.processing.semantic_processor import (
    enrich_content_units
)

from app.processing.embedding_processor import (
    embed_content_units
)

from app.knowledge.course_registry import (
    course_concept_registry
)


def process_video(
    file_path: str
) -> dict:

    video_path = Path(
        file_path
    )


    print(
        f"[Video Pipeline] Processing: "
        f"{video_path.name}"
    )


    # -------------------------------------------------
    # STEP 1 — Extract compressed audio
    # -------------------------------------------------

    audio_path = extract_audio(
        str(video_path)
    )


    print(
        f"[Video Pipeline] Audio: "
        f"{audio_path}"
    )


    # -------------------------------------------------
    # STEP 2 — Whisper transcription
    # -------------------------------------------------

    text_units = transcribe_audio(
        audio_path=audio_path,
        original_video_name=video_path.name
    )


    print(
        f"[Video Pipeline] Transcript units: "
        f"{len(text_units)}"
    )


    # -------------------------------------------------
    # STEP 3 — Visual units
    #
    # Plug your existing keyframe + vision pipeline
    # here if already implemented.
    # -------------------------------------------------

    visual_units = []


    # Example once your keyframe pipeline exists:
    #
    # frames = extract_keyframes(
    #     str(video_path)
    # )
    #
    # visual_units = create_video_visual_units(
    #     frames
    # )


    # -------------------------------------------------
    # STEP 4 — Combine modalities
    # -------------------------------------------------

    all_units = (
        text_units
        +
        visual_units
    )


    # -------------------------------------------------
    # STEP 5 — Semantic enrichment
    # -------------------------------------------------

    all_units = enrich_content_units(
        units=all_units,
        registry=course_concept_registry
    )


    # -------------------------------------------------
    # STEP 6 — Embeddings
    # -------------------------------------------------

    all_units = embed_content_units(
        all_units
    )


    return {
        "text_units": [
            unit
            for unit in all_units
            if unit.content_type == "text"
        ],

        "visual_units": [
            unit
            for unit in all_units
            if unit.content_type == "visual"
        ],

        "all_units":
            all_units
    }