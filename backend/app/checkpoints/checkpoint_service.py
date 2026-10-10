import json
import hashlib
from pathlib import Path
from typing import Any


CHECKPOINT_ROOT = Path("checkpoints")

PREREQUISITE_CHECKPOINT_DIR = (
    CHECKPOINT_ROOT
    / "prerequisites"
)

SEMANTIC_CHECKPOINT_DIR = (
    CHECKPOINT_ROOT
    / "semantic"
)


CHECKPOINT_ROOT.mkdir(
    exist_ok=True
)

PREREQUISITE_CHECKPOINT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SEMANTIC_CHECKPOINT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def _safe_filename(
    value: str
) -> str:

    return (
        value
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(" ", "_")
    )


def content_hash(
    value: str
) -> str:

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]


# =====================================================
# Generic JSON checkpoint helpers
# =====================================================

def save_json_checkpoint(
    path: Path,
    data: dict[str, Any]
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = path.with_suffix(
        ".tmp"
    )


    with open(
        temporary_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


    temporary_path.replace(
        path
    )


def load_json_checkpoint(
    path: Path
) -> dict | None:

    if not path.exists():
        return None


    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )


    except (
        json.JSONDecodeError,
        OSError
    ):

        print(
            f"[Checkpoint] "
            f"Invalid checkpoint ignored: "
            f"{path}"
        )

        return None


# =====================================================
# Prerequisite checkpoints
# =====================================================

def prerequisite_checkpoint_path(
    concept_id: str
) -> Path:

    filename = (
        _safe_filename(
            concept_id
        )
        + ".json"
    )

    return (
        PREREQUISITE_CHECKPOINT_DIR
        /
        filename
    )


def load_prerequisite_checkpoint(
    concept_id: str
) -> dict | None:

    path = prerequisite_checkpoint_path(
        concept_id
    )

    return load_json_checkpoint(
        path
    )


def save_prerequisite_checkpoint(
    concept_id: str,
    concept_name: str,
    prerequisites: list[str]
) -> None:

    path = prerequisite_checkpoint_path(
        concept_id
    )


    data = {
        "concept_id":
            concept_id,

        "concept_name":
            concept_name,

        "status":
            "completed",

        "prerequisites":
            prerequisites
    }


    save_json_checkpoint(
        path,
        data
    )


    print(
        f"[Checkpoint] "
        f"Saved prerequisite checkpoint: "
        f"{concept_name}"
    )


def delete_prerequisite_checkpoint(
    concept_id: str
) -> None:

    path = prerequisite_checkpoint_path(
        concept_id
    )

    if path.exists():
        path.unlink()


# =====================================================
# Semantic checkpoints
# =====================================================

def semantic_checkpoint_path(
    unit_id: str
) -> Path:

    filename = (
        _safe_filename(
            unit_id
        )
        + ".json"
    )

    return (
        SEMANTIC_CHECKPOINT_DIR
        /
        filename
    )


def load_semantic_checkpoint(
    unit_id: str
) -> dict | None:

    path = semantic_checkpoint_path(
        unit_id
    )

    return load_json_checkpoint(
        path
    )


def save_semantic_checkpoint(
    unit_id: str,
    topic: str | None,
    subtopic: str | None,
    concept_ids: list[str]
) -> None:

    path = semantic_checkpoint_path(
        unit_id
    )


    data = {
        "unit_id":
            unit_id,

        "status":
            "completed",

        "topic":
            topic,

        "subtopic":
            subtopic,

        "concept_ids":
            concept_ids
    }


    save_json_checkpoint(
        path,
        data
    )


    print(
        f"[Checkpoint] "
        f"Saved semantic checkpoint: "
        f"{unit_id}"
    )


def delete_semantic_checkpoint(
    unit_id: str
) -> None:

    path = semantic_checkpoint_path(
        unit_id
    )

    if path.exists():
        path.unlink()