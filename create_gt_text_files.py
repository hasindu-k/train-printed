# need to create ground truth text files for each line image
import os

# CHANGE THIS to your line images folder
LINES_DIR = r"lines/history 10 S/page_0006"

for file in os.listdir(LINES_DIR):
    if file.lower().endswith(".tif"):
        base_name = os.path.splitext(file)[0]
        gt_path = os.path.join(LINES_DIR, base_name + ".gt.txt")

        # Create only if it does not already exist
        if not os.path.exists(gt_path):
            with open(gt_path, "w", encoding="utf-8") as f:
                f.write("")  # empty file

            print(f"Created: {gt_path}")
        else:
            print(f"Exists:  {gt_path}")

print("Ground truth files creation complete.")
