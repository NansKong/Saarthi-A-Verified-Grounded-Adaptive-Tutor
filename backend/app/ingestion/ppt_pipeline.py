from app.ingestion.ppt_parser import (
    extract_ppt_content
)
from app.ingestion.ppt_image_extractor import (
    extract_images_from_ppt
)
from app.processing.ppt_visual_processor import (
    create_ppt_visual_units
)


def process_ppt(file_path: str):

    text_units = extract_ppt_content(
        file_path
    )

    extracted_images = extract_images_from_ppt(
        file_path
    )

    visual_units = create_ppt_visual_units(
        extracted_images
    )

    all_units = text_units + visual_units

    return {
        "text_units": text_units,
        "visual_units": visual_units,
        "all_units": all_units
    }