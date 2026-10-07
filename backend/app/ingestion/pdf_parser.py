import fitz
from pathlib import Path

from app.schemas.content_unit import ContentUnit
from app.processing.chunker import chunk_text


def extract_pdf_content(file_path: str) -> list[ContentUnit]:
    document = fitz.open(file_path)

    source_name = Path(file_path).name
    source_stem = Path(source_name).stem

    content_units = []

    for page_index in range(len(document)):
        page = document[page_index]

        text = page.get_text("text").strip()

        page_number = page_index + 1

        if not text:
            unit = ContentUnit(
                unit_id=f"{source_stem}_p{page_number}_c0",
                source_id=source_name,
                source_type="pdf",
                location={
                    "page": page_number
                },
                chunk_index=0,
                text="",
                visual_description=None,
                topic=None,
                subtopic=None,
                concept_ids=[]
            )

            content_units.append(unit)
            continue

        chunks = chunk_text(text)

        for chunk_index, chunk in enumerate(chunks, start=1):

            unit = ContentUnit(
                unit_id=f"{source_stem}_p{page_number}_c{chunk_index}",
                source_id=source_name,
                source_type="pdf",
                location={
                    "page": page_number
                },
                chunk_index=chunk_index,
                text=chunk,
                visual_description=None,
                topic=None,
                subtopic=None,
                concept_ids=[]
            )

            content_units.append(unit)

    document.close()

    return content_units