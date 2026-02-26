import cv2
import numpy as np
import os
import shutil

input_folder = r"C:\Users\Hasindu\Desktop\create-dataset\renamed-annotated-handwritten"
output_folder = r"C:\Users\Hasindu\Desktop\create-dataset\padded-renamed-annotated-handwritten"
padding = 50  # space around text line in pixels

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    path = os.path.join(input_folder, filename)

    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp")):
        # read image
        img = cv2.imread(path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # binarize (helps detect text area)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # find contours (text regions)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # get bounding box covering all text
            x_min, y_min, x_max, y_max = img.shape[1], img.shape[0], 0, 0

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + w)
                y_max = max(y_max, y + h)

            cropped = img[y_min:y_max, x_min:x_max]
        else:
            cropped = img  # fallback if no contour found

        # add padding
        padded = cv2.copyMakeBorder(
            cropped,
            top=padding,
            bottom=padding,
            left=padding,
            right=padding,
            borderType=cv2.BORDER_CONSTANT,
            value=[255, 255, 255]  # white background
        )

        cv2.imwrite(os.path.join(output_folder, filename), padded)
    elif filename.lower().endswith(".gt.txt"):
        shutil.copy2(path, os.path.join(output_folder, filename))

print("Processing completed.")