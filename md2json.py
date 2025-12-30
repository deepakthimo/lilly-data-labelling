import requests
import argparse
import json
import asyncio
import io
import zipfile

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

def extract_headings(md_text):
    return [
        line.strip()
        for line in md_text.splitlines()
        if line.lstrip().startswith("#")
    ]

def extract_instructions(json_obj):
    return [
        item.get("instruction", "").strip()
        for item in json_obj
    ]


def download_pdf_from_url(pdf_url):
    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()
    return response.content


def create_zip_bytes(filename, pdf_bytes, json_str):
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(f"{filename}.pdf", pdf_bytes)
        zipf.writestr(f"{filename}.json", json_str)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()
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
    # Col K (No of Headings) = Index 10
    # Col L (JSON Status) = index 11 (Target for update)

    # Safely get columns
    print(f"Title: {row_data[2]}, \nAudit Status: {row_data[9]}, \nPhase: {row_data[3]}")
    title = row_data[2] if len(row_data) > 2 else ""
    phase = row_data[3] if len(row_data) > 3 else ""
    audit_status = row_data[9] if len(row_data) > 4 else ""
    no_of_headings = int(row_data[10])

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
        cleaned_folder_id = get_or_create_folder("03_Manual_cleaned_MD_Audit", PARENT_DRIVE_FOLDER_ID)
        json_folder_id = get_or_create_folder("04_Raw_json", PARENT_DRIVE_FOLDER_ID)
        final_zip_folder_id = get_or_create_folder("05_final_zipped_output", PARENT_DRIVE_FOLDER_ID)

        # 4. Fetch File from Drive
        print("   -> Fetching file content from '03_Manual_Cleaned_MD_Audit'...")
        # This downloads the text content of the markdown file
        markdown_content = download_file_content(filename, cleaned_folder_id)

        # 5. Run Your Parsing Logic
        print("   -> Parsing text to JSON structure...")
        json_obj = md_to_flat_json(markdown_content, title, phase)

        # Extract from MD and JSON
        headings = extract_headings(markdown_content)
        instructions = extract_instructions(json_obj)

        num_headings = len(headings)
        num_instructions = len(instructions)

        # checking if the Number of Instruction created == No of Heading
        if num_headings == num_instructions:
    
            # Convert list of dicts to JSON string
            json_str = json.dumps(json_obj, indent=4)

            # 6. Upload JSON to Drive
            output_filename = f"{filename}.json"
            print(f"   -> Uploading {output_filename} to '04_Raw_json'...")
            
            json_link = upload_or_update_file(
                content=json_str, 
                filename=output_filename, 
                folder_id=json_folder_id, 
                mime_type='application/json'
            )
            print(f"   -> JSON Drive Link: {json_link}")


            # 7. Update Sheet (Column L: JSON_Status to "Done")
            print("   -> Updating Sheet Status to 'Done'...")
            # 'L' is the column for JSON_Status based on your table
            update_cell(row_index, 'L', "Done")

            # 8. Download pdf, Zip pdf+json, upload ZIP
            print("   -> Fetching PDF URL from Sheet...")
            pdf_url = row_data[0]

            if not pdf_url:
                raise ValueError("PDF URL is missing in Column A")
            
            print("   -> Downloading PDF...")
            pdf_bytes = download_pdf_from_url(pdf_url)

            print("   -> Creating ZIP with PDF and JSON...")
            zip_bytes = create_zip_bytes(
                filename=filename,
                pdf_bytes=pdf_bytes,
                json_str=json_str
            )

            zip_filename = f"{filename}.zip"

            print(f"   -> Uploading ZIP to '05_final_zipped_output'...")
            zip_link = upload_or_update_file(
                content=zip_bytes,
                filename=zip_filename,
                folder_id=final_zip_folder_id,
                mime_type="application/zip"
            )
            # 'M' is the column for ZIP_Status based on your table
            update_cell(row_index, 'M', "Done")
            print("--- Process Complete ---")

        else:
            print("=" * 50)
            print(f"Total Number of headings: {no_of_headings}")
            print(f"Total Instructions in JSON: {len(json_obj)}")
            print("=" * 50)

            max_len = max(num_headings, num_instructions)

            print("=" * 60)
            print(f"Headings found in MD        : {num_headings}")
            print(f"Instructions found in JSON : {num_instructions}")
            print("=" * 60)

            # Print index-wise comparison
            for idx in range(max_len):
                heading = headings[idx] if idx < num_headings else "[MISSING HEADING]"
                instruction = instructions[idx] if idx < num_instructions else "[MISSING INSTRUCTION]"

                print(f"\nIndex {idx + 1}")
                print(f"Heading     : {heading}")
                print(f"Instruction : {instruction}")

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"ERROR: {error_msg}")
        # Log error to sheet in Column L (JSON_Status)
        update_cell(row_index, 'L', error_msg)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", required=True, help="The filename (e.g., NCT12345678) to process")
    args = parser.parse_args()

    process_json_conversion(args.filename)