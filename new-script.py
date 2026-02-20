import json
import os
import cv2

# ===== INPUTS =====
JSON_PATH = "export-2.json"   # save your big JSON into this file
BASE_IMAGE_DIR = "."  # where LS images are stored
OUTPUT_DIR = "cropped_dataset"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for task in data:
    image_path = task["data"]["ocr"]   # "/data/upload/3/filename.jpeg"
    image_file = image_path.split("/")[-1]
    full_img_path = os.path.join(BASE_IMAGE_DIR, image_file)

    img = cv2.imread(full_img_path)
    if img is None:
        print(f"Cannot read {full_img_path}")
        continue

    task_output_dir = os.path.join(OUTPUT_DIR, f"task_{task['id']}")
    os.makedirs(task_output_dir, exist_ok=True)

    annotations = task.get("annotations", [])
    crop_index = 0

    for ann in annotations:
        for result in ann["result"]:
            if result["type"] != "rectangle":
                continue

            val = result["value"]

            x = val["x"]
            y = val["y"]
            w = val["width"]
            h = val["height"]

            ow = result["original_width"]
            oh = result["original_height"]

            # convert to pixels
            x1 = int(x / 100 * ow)
            y1 = int(y / 100 * oh)
            x2 = int((x + w) / 100 * ow)
            y2 = int((y + h) / 100 * oh)

            crop = img[y1:y2, x1:x2]

            crop_name = f"crop_{crop_index:04}.png"
            crop_path = os.path.join(task_output_dir, crop_name)

            cv2.imwrite(crop_path, crop)
            crop_index += 1

    print(f"Task {task['id']} → {crop_index} crops created")
