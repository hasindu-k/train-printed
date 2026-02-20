import shutil
from pathlib import Path

# Configuration
# writer-docID-page-words format
# eg: aa-0001-001-0001
WRITER_ID = "ab"
DOC_ID = "0001"

SOURCE_ROOT = "cropped_dataset"
OUTPUT_FOLDER = "renamed_images"

# Task range configuration
START_TASK = 7    # First task to process (task_7)
END_TASK = 11     # Last task to process (task_11)

# Page numbering configuration
PAGE_START_NUMBER = 1  # What page number should the first task become

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

    # Get task folders based on configuration
    target_tasks = [f"task_{i}" for i in range(START_TASK, END_TASK + 1)]
    task_folders = []
    
    for task_name in target_tasks:
        task_folder = source_root / task_name
        if task_folder.exists():
            task_folders.append(task_folder)
        else:
            print(f"Warning: {task_name} folder not found, skipping...")

    if not task_folders:
        print(f"No target task folders (task_{START_TASK} to task_{END_TASK}) found.")
        return

    total_count = 0

    for task_folder in task_folders:
        # Extract task number from folder name (e.g., task_7 -> 7)
        task_number = int(task_folder.name.split('_')[1])
        # Calculate page number: task_7 -> page 1, task_8 -> page 2, etc.
        page_number = (task_number - START_TASK) + PAGE_START_NUMBER
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
