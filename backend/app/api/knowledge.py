from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil

from app.ingestion.pdf_pipeline import process_pdf
from app.ingestion.ppt_pipeline import process_ppt


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_course_file(
    file: UploadFile = File(...)
):
    extension = Path(file.filename).suffix.lower()

    if extension not in [".pdf", ".pptx"]:
        raise HTTPException(
            status_code=400,
            detail="Currently supported: PDF and PPTX."
        )

    destination = UPLOAD_DIR / file.filename

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process based on file type
    if extension == ".pdf":
        result = process_pdf(str(destination))
        source_type = "pdf"

    elif extension == ".pptx":
        result = process_ppt(str(destination))
        source_type = "slides"

    content_units = result["all_units"]

    # Count source locations
    pages = {
        unit.location["page"]
        for unit in content_units
        if unit.location and "page" in unit.location
    }

    slides = {
        unit.location["slide"]
        for unit in content_units
        if unit.location and "slide" in unit.location
    }

    empty_units = sum(
        1
        for unit in content_units
        if not unit.text.strip()
        and not (unit.visual_description or "").strip()
    )

    return {
        "filename": file.filename,
        "source_type": source_type,
        "status": "processed",

        "total_pages": len(pages),
        "total_slides": len(slides),

        "text_unit_count": len(
            result["text_units"]
        ),

        "visual_unit_count": len(
            result["visual_units"]
        ),

        "content_unit_count": len(content_units),

        "empty_units": empty_units,

        "content_units": [
            unit.model_dump()
            for unit in content_units
        ]
    }