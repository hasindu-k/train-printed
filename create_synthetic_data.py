import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ================= CONFIG =================
TEXT_FILE = "corpus-tier-1.txt"
OUTPUT_DIR = "syn_data_output-tier-1"

FONT_PATHS = [
    "C:/Windows/Fonts/iskpota.ttf",                 # Iskoola Pota
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala-Black.ttf",
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala-Bold.ttf",
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala-Medium.ttf",
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala-Regular.ttf",
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala_Condensed-Regular.ttf",
    "C:/github/train-printed/fonts/noto_sans/NotoSansSinhala_SemiCondensed-Regular.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala-Black.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala-Bold.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala-Medium.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala-Regular.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala_Condensed-Regular.ttf",
    "C:/github/train-printed/fonts/noto_serif/NotoSerifSinhala_SemiCondensed-Regular.ttf",
    "C:/github/train-printed/fonts/yaldevi/Yaldevi-Bold.ttf",
    "C:/github/train-printed/fonts/yaldevi/Yaldevi-Light.ttf",
    "C:/github/train-printed/fonts/yaldevi/Yaldevi-Medium.ttf",
    "C:/github/train-printed/fonts/yaldevi/Yaldevi-Regular.ttf",
    "C:/github/train-printed/fonts/FM-Abhaya-x.ttf",
]

IMAGE_HEIGHT = 48
BASE_PADDING = 20

# Noise / Augmentation probabilities
DOT_NOISE_DENSITY = (0.002, 0.01)   # min, max
BLUR_PROB = 0.3
CONTRAST_PROB = 0.3
ROTATION_PROB = 0.25

FONT_SIZE_RANGE = (28, 36)
ROTATION_RANGE = (-1.5, 1.5)       # degrees
# =========================================


def add_dot_noise(image, density):
    """Add random black pixel noise (dust)."""
    draw = ImageDraw.Draw(image)
    width, height = image.size
    total_pixels = width * height
    dots = int(total_pixels * density)

    for _ in range(dots):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        draw.point((x, y), fill=(0, 0, 0))

    return image


def apply_augmentations(image):
    """Apply realistic scan-like augmentations."""
    # Blur
    if random.random() < BLUR_PROB:
        image = image.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.7)))

    # Contrast
    if random.random() < CONTRAST_PROB:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(random.uniform(0.8, 1.25))

    return image


def create_training_data():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(TEXT_FILE):
        raise FileNotFoundError(f"{TEXT_FILE} not found")

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"Loaded {len(lines)} lines")

    for i, text in enumerate(lines):
        # ---- Random font selection ----
        font_path = random.choice(FONT_PATHS)
        font_size = random.randint(*FONT_SIZE_RANGE)
        font = ImageFont.truetype(font_path, font_size)

        # ---- Measure text width ----
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

        img_width = text_width + BASE_PADDING * 2

        # ---- Create image ----
        image = Image.new("RGB", (img_width, IMAGE_HEIGHT), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        # ---- Baseline jitter ----
        base_y = (IMAGE_HEIGHT - font_size) // 2
        text_y = random.randint(base_y - 6, base_y + 4)

        draw.text((BASE_PADDING, text_y), text, font=font, fill=(0, 0, 0))

        # ---- Rotation (before noise) ----
        if random.random() < ROTATION_PROB:
            angle = random.uniform(*ROTATION_RANGE)
            image = image.rotate(angle, expand=True, fillcolor=(255, 255, 255))

        # ---- Noise ----
        density = random.uniform(*DOT_NOISE_DENSITY)
        image = add_dot_noise(image, density)

        # ---- Scan-like augmentations ----
        image = apply_augmentations(image)

        # ---- Save ----
        base_name = f"syn.history.{i}"

        image.save(os.path.join(OUTPUT_DIR, f"{base_name}.png"))
        with open(os.path.join(OUTPUT_DIR, f"{base_name}.gt.txt"), "w", encoding="utf-8") as gt:
            gt.write(text)

        if i % 1000 == 0 and i > 0:
            print(f"Generated {i} samples...")

    print(f"✅ Done. Generated {len(lines)} samples in '{OUTPUT_DIR}'")


if __name__ == "__main__":
    create_training_data()
