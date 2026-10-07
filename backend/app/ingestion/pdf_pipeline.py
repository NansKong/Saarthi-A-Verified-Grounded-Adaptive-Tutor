from app.ingestion.pdf_parser import extract_pdf_content
from app.ingestion.pdf_image_extractor import (
    extract_images_from_pdf
)
from app.processing.visual_processor import (
    create_visual_units
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

    return {
        "text_units": text_units,
        "visual_units": visual_units,
        "all_units": all_units
    }