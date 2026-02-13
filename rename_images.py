import os
import shutil
from pathlib import Path

# Configuration
# writer-docID-page-words format
# eg: aa-0001-001-0001
WRITER_ID = "aa"
DOC_ID = "0001"
PAGE_ID = "001"

SOURCE_FOLDER = "words"
OUTPUT_FOLDER = "renamed_images"

def rename_and_move_images():
    """
    Rename images from word_XXXXXX.png to aa-0001-001-XXXX.png format
    and move them to renamed_images folder
    """
    # Create source and output paths
    source_path = Path(SOURCE_FOLDER)
    output_path = Path(OUTPUT_FOLDER)
    
    # Check if source folder exists
    if not source_path.exists():
        print(f"Error: Source folder '{SOURCE_FOLDER}' does not exist.")
        return
    
    # Create output folder if it doesn't exist
    output_path.mkdir(exist_ok=True)
    print(f"Output folder '{OUTPUT_FOLDER}' ready.")
    
    # Get all PNG files from source folder
    image_files = sorted(source_path.glob("word_*.png"))
    
    if not image_files:
        print(f"No word_*.png files found in '{SOURCE_FOLDER}'")
        return
    
    print(f"Found {len(image_files)} image files to process.")
    
    # Process each image
    renamed_count = 0
    for idx, image_file in enumerate(image_files, start=1):
        # Create new filename: aa-0001-001-0001.png
        new_filename = f"{WRITER_ID}-{DOC_ID}-{PAGE_ID}-{idx:04d}.png"
        new_filepath = output_path / new_filename
        
        # Copy file with new name
        shutil.copy2(image_file, new_filepath)
        print(f"Renamed: {image_file.name} -> {new_filename}")
        renamed_count += 1
    
    print(f"\nCompleted! {renamed_count} files renamed and moved to '{OUTPUT_FOLDER}' folder.")

if __name__ == "__main__":
    rename_and_move_images()