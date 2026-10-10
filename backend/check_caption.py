from app.vision.image_captioner import describe_educational_image

caption = describe_educational_image(
    "extracted_images/MACHINE LEARNING(R17A0534)_p7_img1.png"
)

print(caption)