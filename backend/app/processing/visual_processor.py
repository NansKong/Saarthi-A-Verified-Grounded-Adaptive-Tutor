from pathlib import Path

from app.schemas.content_unit import ContentUnit
from app.vision.image_captioner import describe_educational_image


def create_visual_units(
    extracted_images: list[dict]
) -> list[ContentUnit]:

    visual_units = []

    for image in extracted_images:

        try:
            caption = describe_educational_image(
                image["image_path"]
            )
        except Exception as exc:
            print(
                f"Vision processing failed for "
                f"{image['image_path']}: {exc}"
            )
            continue

        if not caption:
            continue

        if caption.strip() == "NOT_EDUCATIONAL":
            continue

        source_stem = Path(
            image["source_id"]
        ).stem

        page_number = image["page"]
        image_index = image["image_index"]

        unit = ContentUnit(
            unit_id=(
                f"{source_stem}_p{page_number}_img{image_index}"
            ),
            source_id=image["source_id"],
            source_type="pdf",
            location={
                "page": page_number
            },
            chunk_index=None,
            content_type="visual",
            text="",
            visual_description=caption,
            image_path=image["image_path"],
            topic=None,
            subtopic=None,
            concept_ids=[]
        )

        visual_units.append(unit)

    return visual_units