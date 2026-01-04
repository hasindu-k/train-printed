from pdf2image import convert_from_path
import os

# PDF_PATH = "history 10 S.pdf" 
# get path from user input
PDF_PATH = input("Enter the path to the PDF file: ")
OUT_DIR = f"pages/{PDF_PATH.split('/')[-1].replace('.pdf', '')}"

os.makedirs(OUT_DIR, exist_ok=True)

pages = convert_from_path(
    PDF_PATH,
    dpi=300,
    # poppler_path=r"C:\poppler\Library\bin"
)

for i, page in enumerate(pages):
    page.save(f"{OUT_DIR}/page_{i+1:04d}.tif", "TIFF")

print("Pages converted to TIFF successfully")
