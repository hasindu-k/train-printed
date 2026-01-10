import os
import shutil
import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Remove extension and clean up filename for use as folder name."""
    return os.path.splitext(filename)[0].strip()


def create_tiff_from_pdf(pdf_path: str, output_dir: str) -> int:
    """
    Convert PDF to TIFF pages.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save TIFF files
        
    Returns:
        Number of pages created
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        pages = convert_from_path(pdf_path, dpi=300)
        for i, page in enumerate(pages):
            page.save(f"{output_dir}/page_{i+1:04d}.tif", "TIFF")
        return len(pages)
    except Exception as e:
        raise Exception(f"Error converting PDF to TIFF: {str(e)}")


def extract_lines_from_page(img_path: str, output_folder: str) -> int:
    """
    Extract line images from a page using OpenCV.
    
    Args:
        img_path: Path to the TIFF page image
        output_folder: Directory to save line images
        
    Returns:
        Number of lines extracted
    """
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        # Read image
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise Exception(f"Failed to read image: {img_path}")
        
        # Binarize
        _, thresh = cv2.threshold(img, 0, 255,
                                   cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Create horizontal kernel to connect letters into lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (60, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # Find contours (now they represent lines)
        contours, _ = cv2.findContours(dilated,
                                       cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort top-to-bottom
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        
        line_count = 0
        for i, c in enumerate(contours):
            x, y, w, h = cv2.boundingRect(c)
            
            # Ignore noise
            if h < 25 or w < 100:
                continue
            
            line_img = img[y:y+h, x:x+w]
            # Save as TIF for Tesseract training
            Image.fromarray(line_img).save(
                f"{output_folder}/line_{line_count+1:04d}.tif"
            )
            # Save as PNG for browser viewing
            Image.fromarray(line_img).save(
                f"{output_folder}/line_{line_count+1:04d}.png"
            )
            line_count += 1
        
        return line_count
    except Exception as e:
        raise Exception(f"Error extracting lines: {str(e)}")

def generate_line_variant_paths(image_path: str):
    """
    From line_0003.png → line_0003_1.{tif,png,gt.txt}
    """
    import re
    directory, filename = os.path.split(image_path)
    name, _ = os.path.splitext(filename)

    # Remove suffix if exists (line_0003_1 → line_0003)
    base_name = re.sub(r'_\d+$', '', name)

    existing_files = os.listdir(directory)

    max_index = 0
    for f in existing_files:
        if f.startswith(base_name):
            match = re.search(rf"{base_name}_(\d+)", f)
            if match:
                max_index = max(max_index, int(match.group(1)))

    next_index = max_index + 1

    return {
        "line_path": os.path.join(directory, f"{base_name}_{next_index}.tif"),
        "png_path": os.path.join(directory, f"{base_name}_{next_index}.png"),
        "gt_text_path": os.path.join(directory, f"{base_name}_{next_index}.gt.txt"),
    }

def convert_png_to_tiff(png_path: str, tiff_path: str) -> None:
    """
    Convert a PNG image to TIFF format.
    
    Args:
        png_path: Path to the PNG file
        tiff_path: Path to save the TIFF file
    """
    try:
        img = Image.open(png_path)
        img.save(tiff_path, format="TIFF")
    except Exception as e:
        raise Exception(f"Error converting PNG to TIFF: {str(e)}")


def convert_to_tiff(input_path: str, output_path: str) -> None:
    """
    Convert any supported image format to TIFF.
    
    Args:
        input_path: Path to the input image file
        output_path: Path to save the TIFF file
    """
    try:
        with Image.open(input_path) as img:
            img.save(output_path, format="TIFF")
    except Exception as e:
        raise Exception(f"Error converting {input_path} to TIFF: {str(e)}")


def create_gt_text_files(lines_folder: str) -> int:
    """
    Create ground truth text files for each line image.
    
    Args:
        lines_folder: Directory containing line TIFF files
        
    Returns:
        Number of GT files created
    """
    if not os.path.exists(lines_folder):
        raise Exception(f"Lines folder not found: {lines_folder}")
    
    created_count = 0
    for file in os.listdir(lines_folder):
        if file.lower().endswith(".tif"):
            base_name = os.path.splitext(file)[0]
            gt_path = os.path.join(lines_folder, base_name + ".gt.txt")
            
            # Create only if it does not already exist
            if not os.path.exists(gt_path):
                with open(gt_path, "w", encoding="utf-8") as f:
                    f.write("")  # empty file
                created_count += 1
    
    return created_count


def update_gt_text_file(gt_text_path: str, content: str) -> None:
    """
    Update a ground truth text file.
    
    Args:
        gt_text_path: Path to the .gt.txt file
        content: Text content to write
    """
    print(f"Updating GT file: {gt_text_path}")
    os.makedirs(os.path.dirname(gt_text_path), exist_ok=True)
    with open(gt_text_path, "w", encoding="utf-8") as f:
        f.write(content)
        print(f"Wrote content to {gt_text_path}")


def read_gt_text_file(gt_text_path: str) -> str:
    """
    Read a ground truth text file.
    
    Args:
        gt_text_path: Path to the .gt.txt file
        
    Returns:
        Content of the file
    """
    if os.path.exists(gt_text_path):
        with open(gt_text_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def export_dataset(doc_folder: str, output_zip: str) -> None:
    """
    Export dataset as zip file.
    
    Args:
        doc_folder: Root folder containing lines/
        output_zip: Path to output zip file
    """
    import zipfile
    
    if not os.path.exists(doc_folder):
        raise Exception(f"Document folder not found: {doc_folder}")
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(doc_folder):
            for file in files:
                if file.endswith('.tif') or file.endswith('.gt.txt'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, doc_folder)
                    zipf.write(file_path, arcname)


def cleanup_folder(folder_path: str) -> None:
    """Remove a folder and all its contents."""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)


def extract_text_from_image(image_path: str, lang: str = "eng", config: str = "") -> str:
    """Extract text from image using Tesseract OCR.
    
    Args:
        image_path: Path to the image file
        lang: Language for OCR (default: eng, use sin for Sinhala)
        
    Returns:
        Extracted text from the image
    """
    try:
        import pytesseract
        from PIL import Image
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang, config=config)
        return text.strip()
    except ImportError:
        raise ImportError("pytesseract is not installed. Run: pip install pytesseract")
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")

def get_no_of_pages_in_pdf(pdf_path: str) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2 is not installed. Run: pip install PyPDF2")

    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            return len(reader.pages)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {pdf_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")
