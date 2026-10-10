from pathlib import Path

import cv2
import numpy as np


KEYFRAME_ROOT = Path(
    "extracted_keyframes"
)

KEYFRAME_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


def _resize_frame(
    frame,
    max_width: int = 1280
):
    """
    Resize large frames before saving.
    """

    height, width = frame.shape[:2]

    if width <= max_width:
        return frame

    scale = max_width / width

    new_width = max_width
    new_height = int(
        height * scale
    )

    return cv2.resize(
        frame,
        (
            new_width,
            new_height
        ),
        interpolation=cv2.INTER_AREA
    )


def _frame_difference(
    previous_frame,
    current_frame
) -> float:
    """
    Calculate average visual difference between
    two frames.
    """

    previous_gray = cv2.cvtColor(
        previous_frame,
        cv2.COLOR_BGR2GRAY
    )

    current_gray = cv2.cvtColor(
        current_frame,
        cv2.COLOR_BGR2GRAY
    )

    previous_gray = cv2.resize(
        previous_gray,
        (
            320,
            180
        )
    )

    current_gray = cv2.resize(
        current_gray,
        (
            320,
            180
        )
    )

    difference = cv2.absdiff(
        previous_gray,
        current_gray
    )

    return float(
        np.mean(
            difference
        )
    )


def _read_frame_at_timestamp(
    capture,
    timestamp: float
):
    """
    Seek to a timestamp and return the decoded frame.
    """

    capture.set(
        cv2.CAP_PROP_POS_MSEC,
        timestamp * 1000
    )

    success, frame = capture.read()

    if not success:
        return None

    return frame


def extract_keyframes(
    video_path: str,
    max_frames: int = 12,
    candidates_per_segment: int = 3
) -> list[dict]:
    """
    Extract representative keyframes across the
    ENTIRE video.

    Strategy:

        video duration
            ↓
        divide into N temporal segments
            ↓
        inspect several frames inside each segment
            ↓
        choose the most visually different frame
        from the previous selected frame
            ↓
        save one representative per segment

    This prevents all keyframes from being selected
    from only the first half of a long lecture.
    """

    video_path = Path(
        video_path
    )

    if not video_path.exists():

        raise FileNotFoundError(
            f"Video not found: "
            f"{video_path}"
        )


    source_stem = (
        video_path.stem
    )


    output_directory = (
        KEYFRAME_ROOT
        /
        source_stem
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )


    capture = cv2.VideoCapture(
        str(video_path)
    )


    if not capture.isOpened():

        raise RuntimeError(
            f"Could not open video: "
            f"{video_path}"
        )


    fps = capture.get(
        cv2.CAP_PROP_FPS
    )

    frame_count = capture.get(
        cv2.CAP_PROP_FRAME_COUNT
    )


    if not fps or fps <= 0:

        capture.release()

        raise RuntimeError(
            "Could not determine video FPS."
        )


    duration = (
        frame_count
        /
        fps
    )


    print(
        f"[Keyframe Extractor] "
        f"Duration: "
        f"{duration:.2f}s"
    )


    print(
        f"[Keyframe Extractor] "
        f"Target frames: "
        f"{max_frames}"
    )


    print(
        "[Keyframe Extractor] "
        "Selecting frames across entire video."
    )


    # =====================================================
    # Divide entire video into temporal regions
    # =====================================================

    segment_boundaries = np.linspace(
        0.0,
        duration,
        max_frames + 1
    )


    keyframes = []

    previous_selected_frame = None


    for segment_index in range(
        max_frames
    ):

        segment_start = float(
            segment_boundaries[
                segment_index
            ]
        )

        segment_end = float(
            segment_boundaries[
                segment_index + 1
            ]
        )


        # Avoid decoding exactly at video end
        segment_end = min(
            segment_end,
            duration - 0.5
        )


        print(
            f"[Keyframe Extractor] "
            f"Segment "
            f"{segment_index + 1}/"
            f"{max_frames}: "
            f"{segment_start:.1f}s "
            f"-> "
            f"{segment_end:.1f}s"
        )


        # =================================================
        # Sample several candidate frames inside segment
        # =================================================

        candidate_timestamps = np.linspace(
            segment_start,
            segment_end,
            candidates_per_segment + 2
        )[1:-1]


        best_frame = None
        best_timestamp = None
        best_difference = -1.0


        for timestamp in candidate_timestamps:

            timestamp = float(
                timestamp
            )


            frame = _read_frame_at_timestamp(
                capture,
                timestamp
            )


            if frame is None:
                continue


            # First selected segment:
            # just choose middle-ish usable frame.
            if previous_selected_frame is None:

                best_frame = frame
                best_timestamp = timestamp

                break


            difference = _frame_difference(
                previous_selected_frame,
                frame
            )


            if difference > best_difference:

                best_difference = difference
                best_frame = frame
                best_timestamp = timestamp


        # =================================================
        # Could not read any frame in this segment
        # =================================================

        if best_frame is None:

            print(
                f"[Keyframe Extractor] "
                f"No usable frame found "
                f"in segment "
                f"{segment_index + 1}"
            )

            continue


        # =================================================
        # Save selected frame
        # =================================================

        resized_frame = _resize_frame(
            best_frame
        )


        timestamp_int = int(
            round(
                best_timestamp
            )
        )


        filename = (
            f"{source_stem}"
            f"_frame_"
            f"{timestamp_int:06d}s.jpg"
        )


        image_path = (
            output_directory
            /
            filename
        )


        written = cv2.imwrite(
            str(image_path),
            resized_frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                88
            ]
        )


        if not written:
            continue


        keyframes.append(
            {
                "timestamp":
                    float(
                        best_timestamp
                    ),

                "image_path":
                    str(
                        image_path
                    )
            }
        )


        previous_selected_frame = (
            best_frame.copy()
        )


        if best_difference >= 0:

            print(
                f"[Keyframe Extractor] "
                f"Saved @ "
                f"{best_timestamp:.1f}s "
                f"(difference="
                f"{best_difference:.2f})"
            )

        else:

            print(
                f"[Keyframe Extractor] "
                f"Saved @ "
                f"{best_timestamp:.1f}s"
            )


    capture.release()


    # =====================================================
    # Summary
    # =====================================================

    print(
        f"[Keyframe Extractor] "
        f"{len(keyframes)} "
        f"keyframe(s) extracted."
    )


    if keyframes:

        print(
            "[Keyframe Extractor] "
            f"Coverage: "
            f"{keyframes[0]['timestamp']:.1f}s "
            f"-> "
            f"{keyframes[-1]['timestamp']:.1f}s"
        )


    return keyframes