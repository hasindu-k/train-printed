import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
TEXT_FILE = "corpus.txt"
OUTPUT_DIR = "syn_data_output"
FONT_PATH = "C:/Windows/Fonts/iskpota.ttf" # Iskoola Pota is safe for Unicode
FONT_SIZE = 32
IMAGE_HEIGHT = 48  # Tesseract likes lines around 32-64px high
# ---------------------

def create_training_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load the words/sentences
    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(lines)} lines. Generating images...")

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    for i, text_line in enumerate(lines):
        # 2. Determine Image Size
        # We draw on a temporary dummy image to calculate text width
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        # Get the bounding box of the text (left, top, right, bottom)
        bbox = dummy_draw.textbbox((0, 0), text_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Add some padding
        img_width = text_width + 40 
        
        # 3. Create the actual image (White Background)
        image = Image.new("RGB", (img_width, IMAGE_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 4. Draw the Text (Black Color)
        # Centering the text vertically roughly
        text_y = (IMAGE_HEIGHT - FONT_SIZE) // 2 - 5 # -5 is a tweak for Sinhala vowels
        draw.text((20, text_y), text_line, font=font, fill=(0, 0, 0))

        # 5. Save Files (GT Convention)
        # Filename: [model_name].[index].png
        base_name = f"syn.history.{i}"
        
        # Save Image
        image_path = os.path.join(OUTPUT_DIR, f"{base_name}.png")
        image.save(image_path)

        # Save Text
        text_path = os.path.join(OUTPUT_DIR, f"{base_name}.gt.txt")
        with open(text_path, "w", encoding="utf-8") as gt_file:
            gt_file.write(text_line)

    print(f"Success! Generated {len(lines)} pairs in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    create_training_data()