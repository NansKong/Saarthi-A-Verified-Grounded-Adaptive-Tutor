from src.ingestion.ingestion.pdf_parser import extract_pdf_content
from src.ingestion.ingestion.pdf_image_extractor import (
    extract_images_from_pdf
)
from src.ingestion.processing.visual_processor import (
    create_visual_units
)

from src.ingestion.processing.semantic_processor import (
    enrich_content_units
)

from src.ingestion.knowledge.course_registry import (
    course_concept_registry
)

from src.ingestion.processing.embedding_processor import (
    embed_content_units
)

def process_pdf(file_path: str):

    text_units = extract_pdf_content(
        file_path
    )

    extracted_images = extract_images_from_pdf(
        file_path
    )

    visual_units = create_visual_units(
        extracted_images
    )

    all_units = text_units + visual_units
    all_units = enrich_content_units(
    units=all_units,
    registry=course_concept_registry
    )
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

        "all_units": all_units
    }