import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ================= CONFIG =================
TEXT_FILE = "corpus-tier-1.txt"
OUTPUT_DIR = "synthetic-data/syn_data_output-tier-1"

FONT_PATHS = [
    "C:/Windows/Fonts/iskpota.ttf",
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

FONT_SIZE_RANGE = (28, 36)

DOT_NOISE_DENSITY = (0.002, 0.01)
BLUR_PROB = 0.3
CONTRAST_PROB = 0.3
ROTATION_PROB = 0.25
ROTATION_RANGE = (-1.5, 1.5)
# =========================================


def add_dot_noise(image, density):
    draw = ImageDraw.Draw(image)
    w, h = image.size
    for _ in range(int(w * h * density)):
        draw.point(
            (random.randint(0, w - 1), random.randint(0, h - 1)),
            fill=(0, 0, 0),
        )
    return image


def apply_augmentations(image):
    if random.random() < BLUR_PROB:
        image = image.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 0.7)))

    if random.random() < CONTRAST_PROB:
        image = ImageEnhance.Contrast(image).enhance(random.uniform(0.8, 1.25))

    return image


def create_training_data():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(TEXT_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"Loaded {len(lines)} lines")

    for i, text in enumerate(lines):
        font_path = random.choice(FONT_PATHS)
        font_size = random.randint(*FONT_SIZE_RANGE)
        font = ImageFont.truetype(font_path, font_size)

        print(f"Generating sample {i}: '{text}' with font '{os.path.basename(font_path)}' size {font_size}")

        # ---- Correct Sinhala-safe bounding box ----
        dummy = Image.new("RGB", (1, 1))
        ddraw = ImageDraw.Draw(dummy)
        left, top, right, bottom = ddraw.textbbox((0, 0), text, font=font)

        text_w = right - left
        text_h = bottom - top

        pad_x = random.randint(16, 24)
        pad_y = random.randint(14, 22)

        img_w = text_w + pad_x * 2
        img_h = text_h + pad_y * 2

        image = Image.new("RGB", (img_w, img_h), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        draw.text(
            (pad_x - left, pad_y - top),
            text,
            font=font,
            fill=(0, 0, 0),
        )

        # ---- Rotation ----
        if random.random() < ROTATION_PROB:
            image = image.rotate(
                random.uniform(*ROTATION_RANGE),
                expand=True,
                fillcolor=(255, 255, 255),
            )

        # ---- Noise & augmentation ----
        image = add_dot_noise(image, random.uniform(*DOT_NOISE_DENSITY))
        image = apply_augmentations(image)

        base = f"syn.history.{i}"
        image.save(os.path.join(OUTPUT_DIR, base + ".png"))

        with open(os.path.join(OUTPUT_DIR, base + ".gt.txt"), "w", encoding="utf-8") as gt:
            gt.write(text)

        if i and i % 1000 == 0:
            print(f"Generated {i} samples")

    print(f"✅ Done. Generated {len(lines)} samples")


if __name__ == "__main__":
    create_training_data()
