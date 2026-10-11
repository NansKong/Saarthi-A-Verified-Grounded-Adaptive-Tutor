from app.ingestion.pdf_image_extractor import extract_images_from_pdf


images = extract_images_from_pdf(
    "uploads\\MACHINE LEARNING(R17A0534).pdf"
)

print(f"Total images extracted: {len(images)}")

for image in images[:5]:
    print(image)