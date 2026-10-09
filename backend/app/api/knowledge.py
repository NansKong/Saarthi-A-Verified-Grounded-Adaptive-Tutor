from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.knowledge.knowledge_base_builder import (
    build_knowledge_base
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"]
)


UPLOAD_DIR = Path(
    "uploads"
)

UPLOAD_DIR.mkdir(
    exist_ok=True
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".mp4"
}


@router.post("/upload")
async def upload_course_file(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )


    extension = (
        Path(file.filename)
        .suffix
        .lower()
    )


    if extension not in SUPPORTED_EXTENSIONS:

        raise HTTPException(
            status_code=400,

            detail=(
                "Unsupported file type. "
                "Supported formats: "
                "PDF, PPTX, MP4."
            )
        )


    destination = (
        UPLOAD_DIR
        /
        file.filename
    )


    try:

        # ---------------------------------
        # Save uploaded file
        # ---------------------------------

        with open(
            destination,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        # ---------------------------------
        # Run complete KB pipeline
        # ---------------------------------

        result = build_knowledge_base(
            str(destination)
        )


        # ---------------------------------
        # Convert Pydantic units to JSON
        # ---------------------------------

        result["content_units"] = [
            unit.model_dump(
                exclude={"embedding"}
            )
            for unit
            in result["content_units"]
        ]


        return {
            "status":
                "processed",

            **result
        }


    except Exception as exc:

        print(
            f"[Knowledge Upload Error] "
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        raise HTTPException(
            status_code=500,

            detail=(
                f"Knowledge processing failed: "
                f"{str(exc)}"
            )
        )