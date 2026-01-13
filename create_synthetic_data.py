import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
TEXT_FILE = "corpus.txt"
OUTPUT_DIR = "syn_data_output"
# Ensure this path is correct for your system
FONT_PATH = "C:/Windows/Fonts/iskpota.ttf" 
FONT_SIZE = 32
IMAGE_HEIGHT = 48
NOISE_DENSITY = 0.01  # 2% of the image will be "dirt". Adjust: 0.01 (cleaner) to 0.05 (very dirty)
# ---------------------

def add_noise(image, density):
    """
    Randomly adds black dots to the image to simulate dirty paper/scanner noise.
    """
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    # Calculate how many dots to draw based on the density percentage
    total_pixels = width * height
    number_of_dots = int(total_pixels * density)
    
    for _ in range(number_of_dots):
        # Pick a random x, y position
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Draw a tiny black dot (fill=0 for black in RGB)
        # You can make dots larger by drawing a small circle instead of a point if needed
        draw.point((x, y), fill=(0, 0, 0)) 
        
    return image

def create_training_data():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load the words/sentences
    if not os.path.exists(TEXT_FILE):
        print(f"Error: {TEXT_FILE} not found! Create it first.")
        return

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(lines)} lines. Generating images with noise...")

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    for i, text_line in enumerate(lines):
        # 2. Determine Image Size
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        bbox = dummy_draw.textbbox((0, 0), text_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        img_width = text_width + 40 
        
        # 3. Create the actual image (White Background)
        image = Image.new("RGB", (img_width, IMAGE_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 4. Draw the Text (Black Color)
        text_y = (IMAGE_HEIGHT - FONT_SIZE) // 2 - 5
        draw.text((20, text_y), text_line, font=font, fill=(0, 0, 0))
        
        # --- NEW STEP: ADD NOISE ---
        # We apply the noise function before saving
        image = add_noise(image, NOISE_DENSITY)

        # 5. Save Files
        base_name = f"syn.history.{i}"
        
        image_path = os.path.join(OUTPUT_DIR, f"{base_name}.png")
        image.save(image_path)

        text_path = os.path.join(OUTPUT_DIR, f"{base_name}.gt.txt")
        with open(text_path, "w", encoding="utf-8") as gt_file:
            gt_file.write(text_line)

    print(f"Success! Generated {len(lines)} noisy images in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    create_training_data()