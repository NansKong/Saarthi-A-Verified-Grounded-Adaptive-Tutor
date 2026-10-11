import pymupdf as fitz
from pathlib import Path


IMAGE_DIR = Path("extracted_images")
IMAGE_DIR.mkdir(exist_ok=True)


def extract_images_from_pdf(file_path: str) -> list[dict]:
    document = fitz.open(file_path)

    source_name = Path(file_path).name
    source_stem = Path(source_name).stem

    extracted_images = []

    for page_index in range(len(document)):
        page = document[page_index]

        page_number = page_index + 1

        images = page.get_images(full=True)

        for image_index, image_info in enumerate(images, start=1):

            xref = image_info[0]

            image_data = document.extract_image(xref)

            image_bytes = image_data["image"]
            image_ext = image_data["ext"]

            image_name = (
                f"{source_stem}_p{page_number}_img{image_index}.{image_ext}"
            )

            image_path = IMAGE_DIR / image_name

            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)

            extracted_images.append(
                {
                    "source_id": source_name,
                    "page": page_number,
                    "image_index": image_index,
                    "image_path": str(image_path),
                    "extension": image_ext
                }
            )

    document.close()

    return extracted_images