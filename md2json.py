import argparse
import json
import asyncio

# Import your updated utils
from utils.gcp import (
    get_or_create_folder,
    upload_or_update_file,
    download_file_content,
    get_row_data,
    update_cell,
    PARENT_DRIVE_FOLDER_ID
)

from utils.json_constructor import md_to_flat_json

def process_json_conversion(filename):
    print(f"--- Processing JSON Conversion: {filename} ---")

    # 1. Fetch Sheet Data
    # Returns the row index (e.g., 2) and the list of values in that row
    row_index, row_data = get_row_data(filename)

    if not row_index:
        print(f"ERROR: Filename {filename} not found in sheet.")
        return

    # Column Mapping (0-based index from list):
    # Col C (Title) = index 2
    # Col J (Manual_Cleaning_Audit_Status) = index 9
    # Col K (JSON Status) = index 10 (Target for update)

    # Safely get columns
    print(f"Title: {row_data[2]}, \nAudit Status: {row_data[9]}, \nPhase: {row_data[3]}")
    title = row_data[2] if len(row_data) > 2 else ""
    phase = row_data[3] if len(row_data) > 3 else ""
    audit_status = row_data[9] if len(row_data) > 4 else ""

    print(f"   -> Found Row {row_index}. Title: '{title}', Audit Status: '{audit_status}'")

    # 2. Check Conditions
    if audit_status.lower() != "done":
        print(f"SKIPPING: Manual_Cleaning_Audit_Status is '{audit_status}' (Needs to be 'Done').")
        return
    
    if not title:
        print("SKIPPING: Title is empty.")
        return

    try:
        # 3. Setup Folders
        cleaned_folder_id = get_or_create_folder("02_Manually_Cleaned_Markdown", PARENT_DRIVE_FOLDER_ID)
        json_folder_id = get_or_create_folder("03_Raw_json", PARENT_DRIVE_FOLDER_ID)

        # 4. Fetch File from Drive
        print("   -> Fetching file content from '02_Manually_Cleaned_Markdown'...")
        # This downloads the text content of the markdown file
        markdown_content = download_file_content(filename, cleaned_folder_id)

        # 5. Run Your Parsing Logic
        print("   -> Parsing text to JSON structure...")
        json_obj = md_to_flat_json(markdown_content, title, phase)
        
        # Convert list of dicts to JSON string
        json_str = json.dumps(json_obj, indent=4)

        # 6. Upload JSON to Drive
        output_filename = f"{filename}.json"
        print(f"   -> Uploading {output_filename} to '03_Raw_json'...")
        
        json_link = upload_or_update_file(
            content=json_str, 
            filename=output_filename, 
            folder_id=json_folder_id, 
            mime_type='application/json'
        )
        print(f"   -> JSON Drive Link: {json_link}")

        # 7. Update Sheet (Column K: JSON_Status to "Done")
        print("   -> Updating Sheet Status to 'Done'...")
        # 'K' is the column for JSON_Status based on your table
        update_cell(row_index, 'K', "Done")

        print("=" * 50)
        print(f"\n Total Instructions in JSON: {len(json_obj)} \n")
        print("=" * 50)

        instructions = [i['instructions'] for i in json_obj]
        print(instructions, sep="\n")

        
        print("--- Process Complete ---")

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"ERROR: {error_msg}")
        # Log error to sheet in Column K (JSON_Status)
        update_cell(row_index, 'K', error_msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", required=True, help="The filename (e.g., NCT12345678) to process")
    args = parser.parse_args()

    process_json_conversion(args.filename)