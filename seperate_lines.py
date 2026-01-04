import cv2
from PIL import Image
import os
import numpy as np

page_no="page_0006"
file_name="history 10 S"
img_path = f"pages/{file_name}/{page_no}.tif"
output_folder = f"lines/{file_name}/{page_no}/"
os.makedirs(output_folder, exist_ok=True)

# Read image
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

# Binarize
_, thresh = cv2.threshold(img, 0, 255,
                           cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# --------- KEY STEP ----------
# Create horizontal kernel to connect letters into lines
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 5))
dilated = cv2.dilate(thresh, kernel, iterations=1)

# Find contours (now they represent lines)
contours, _ = cv2.findContours(dilated,
                               cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)

# Sort top-to-bottom
contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

for i, c in enumerate(contours):
    x, y, w, h = cv2.boundingRect(c)

    # Ignore noise
    if h < 25 or w < 100:
        continue

    line_img = img[y:y+h, x:x+w]
    Image.fromarray(line_img).save(
        f"{output_folder}line_{i+1:04d}.tif"
    )
