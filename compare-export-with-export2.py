import json
import os
import shutil
from pathlib import Path

def get_image_names_from_json(file_path):
    """Extract file upload names from Label Studio export JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    image_names = []
    for task in data:
        if 'file_upload' in task:
            image_names.append(task['file_upload'])
    
    return set(image_names)

def get_file_mapping_from_json(file_path):
    """Extract file upload names and create mapping from export-2.json"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    file_mapping = {}
    for task in data:
        if 'file_upload' in task:
            new_name = task['file_upload']
            # Extract original name by removing UUID prefix and converting underscores back to spaces
            # Pattern: "483bf0a4-WhatsApp_Image_2026-02-20_at_6.53.45_PM.jpeg"
            # Remove UUID part (everything before first dash + dash)
            if '-' in new_name:
                original_part = new_name.split('-', 1)[1]  # Get part after first dash
                # Convert underscores back to spaces, but keep _at_ as " at "
                original_name = original_part.replace('_at_', ' at ').replace('_', ' ')
                file_mapping[original_name] = new_name
    
    return file_mapping

def rename_new_images_only():
    """Rename only new WhatsApp files (not in export.json) to match export-2.json format"""
    print("Reading export.json...")
    existing_images = get_image_names_from_json('export.json')
    print(f"Found {len(existing_images)} images in export.json")
    
    print("\nReading export-2.json...")
    all_images = get_image_names_from_json('export-2.json')
    print(f"Found {len(all_images)} images in export-2.json")
    
    # Find new images (in export-2.json but not in export.json)
    new_images = all_images - existing_images
    print(f"Found {len(new_images)} new images")
    
    print("\nGetting file mapping from export-2.json...")
    file_mapping = get_file_mapping_from_json('export-2.json')
    
    # Filter mapping to only include new images
    new_file_mapping = {}
    for original_name, new_name in file_mapping.items():
        if new_name in new_images:
            new_file_mapping[original_name] = new_name
    
    print(f"Found {len(new_file_mapping)} new files to rename")
    
    if not new_file_mapping:
        print("No new files to rename")
        return
    
    # Create mapping file for reference
    mapping_file = "rename_mapping.txt"
    renamed_count = 0
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("Original Name -> New Name (Export-2 Format) - NEW FILES ONLY\n")
        f.write("=" * 70 + "\n")
        
        for i, (original_name, new_name) in enumerate(new_file_mapping.items(), 1):
            print(f"{i:3d}. Mapping: {original_name} -> {new_name}")
            
            # Check if original file exists
            original_path = Path(original_name)
            if original_path.exists():
                new_path = Path(new_name)
                
                try:
                    # Rename the file
                    shutil.move(str(original_path), str(new_path))
                    print(f"     ✓ Successfully renamed")
                    f.write(f"{original_name} -> {new_name} (SUCCESS)\n")
                    renamed_count += 1
                except Exception as e:
                    print(f"     ✗ ERROR: {e}")
                    f.write(f"{original_name} -> {new_name} (ERROR: {e})\n")
            else:
                print(f"     ✗ Original file not found")
                f.write(f"{original_name} -> {new_name} (FILE NOT FOUND)\n")
    
    print(f"\nCompleted! Successfully renamed {renamed_count} out of {len(new_file_mapping)} new files.")
    print(f"Mapping saved to: {mapping_file}")
    
    return new_file_mapping

if __name__ == "__main__":
    rename_new_images_only()

