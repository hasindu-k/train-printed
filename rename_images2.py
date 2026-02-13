import shutil
from pathlib import Path

# Configuration
# writer-docID-page-words format
# eg: aa-0001-001-0001
WRITER_ID = "aa"
DOC_ID = "0001"

SOURCE_ROOT = "cropped_dataset"
OUTPUT_FOLDER = "renamed_images"

# Page offset (since page 001 already exists)
PAGE_OFFSET = 1   # Means first task folder becomes page 002

def rename_and_move_images():
    """
    Rename images from word_XXXXXX.png to aa-0001-001-XXXX.png format
    and move them to renamed_images folder
    """

    source_root = Path(SOURCE_ROOT)
    output_path = Path(OUTPUT_FOLDER)

    if not source_root.exists():
        print(f"Error: Source folder '{SOURCE_ROOT}' does not exist.")
        return

    output_path.mkdir(exist_ok=True)
    print(f"Output folder '{OUTPUT_FOLDER}' ready.")

    # Get all task_* folders sorted
    task_folders = sorted(source_root.glob("task_*"))

    if not task_folders:
        print("No task_* folders found.")
        return

    total_count = 0

    for index, task_folder in enumerate(task_folders, start=1):
        # Page numbering starts from 002
        page_number = index + PAGE_OFFSET
        PAGE_ID = f"{page_number:03d}"

        print(f"\nProcessing {task_folder.name} as PAGE {PAGE_ID}")

        image_files = sorted(task_folder.glob("crop_*.png"))

        page_count = 0

        for idx, image_file in enumerate(image_files, start=1):
            page_count += 1
            total_count += 1

            new_filename = f"{WRITER_ID}-{DOC_ID}-{PAGE_ID}-{idx:04d}.png"
            new_filepath = output_path / new_filename

            shutil.copy2(image_file, new_filepath)
            print(f"Renamed: {image_file.name} -> {new_filename}")

        print(f"Page {PAGE_ID}: {page_count} files processed.")

    print(f"\nCompleted! Total {total_count} files renamed.")

if __name__ == "__main__":
    rename_and_move_images()
