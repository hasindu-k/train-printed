import json
import cv2
import os

ANNOTATIONS = "export.json"   # Label Studio export
IMAGE_ROOT = "."             # folder where images exist
OUT_DIR = "words"

os.makedirs(OUT_DIR, exist_ok=True)

with open(ANNOTATIONS, "r", encoding="utf-8") as f:
    tasks = json.load(f)

word_idx = 0

for task in tasks:
    # Extract image path from Label Studio format
    img_path = task["data"]["image"]

    # Label Studio usually stores as /data/upload/1/filename.jpg
    img_path = img_path.split("/")[-1]
    img_path = os.path.join(IMAGE_ROOT, img_path)

    img = cv2.imread(img_path)
    if img is None:
        print("❌ Image not found:", img_path)
        continue

    H, W = img.shape[:2]

    annotations = task.get("annotations", [])
    if not annotations:
        continue

    for ann in annotations:
        for r in ann["result"]:
            if r["type"] != "rectanglelabels":
                continue

            v = r["value"]

            # Convert % → pixels
            x = int(v["x"] / 100 * W)
            y = int(v["y"] / 100 * H)
            w = int(v["width"] / 100 * W)
            h = int(v["height"] / 100 * H)

            # Optional padding (VERY useful for Sinhala modifiers)
            pad = 3
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(W, x + w + pad)
            y1 = min(H, y + h + pad)

            crop = img[y0:y1, x0:x1]

            if crop.size == 0:
                continue

            out_name = f"word_{word_idx:06d}.png"
            cv2.imwrite(os.path.join(OUT_DIR, out_name), crop)
            word_idx += 1

print("✅ Total word images saved:", word_idx)
