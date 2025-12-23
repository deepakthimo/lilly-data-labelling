import argparse
import asyncio
import re

from utils.gcp import (
    get_or_create_folder,
    upload_or_update_file,
    update_or_append_sheet,
    PARENT_DRIVE_FOLDER_ID,
    TITLE
)
from utils.llamaparse import extract_text_llamaparse, download_pdf
from utils.toc_parse import toc_extraction, apply_toc_structure_to_markdown
from utils.llm_call import cortex_call_llm_for_toc_extraction, personal_call_llm_for_toc_extraction
from utils.cleaning_md import merge_broken_markdown_headers
from config import cookie


async def process_single_url(url, filename, phase, assigned_to, bbox, specific_pages=None):
    print(f"--- Processing: {filename} ---")

    raw_folder_id = get_or_create_folder("01_Raw_Markdown", PARENT_DRIVE_FOLDER_ID)
    
    # --- FIX 1: Initialize variables to prevent UnboundLocalError ---
    toc_text = None
    structured_toc = None
    final_content = ""

    try:
        # 1. Download & Extract
        file_bytes = download_pdf(url)
        markdown_text = await extract_text_llamaparse(file_bytes, filename, bbox)            
        print("   -> Extraction complete.")

        # 2. Preprocess markdown to fix broken headers
        markdown_text = merge_broken_markdown_headers(markdown_text) 
        final_content = markdown_text

        # 3. Extracting the cleaned TOC from the file
        if specific_pages:
            try:
                # passing 'specific_pages' works because updated util accepts it
                toc_text = await toc_extraction(
                    file_bytes, 
                    bbox=bbox, 
                    specific_pages=specific_pages, 
                    logging=False
                )
            except Exception as e:
                print(f"   -> Warning: TOC Text Extraction failed ({str(e)}). Skipping TOC cleaning.")
        else:
            print("   -> No specific pages provided; skipping TOC extraction.")

        # 4. sending the cleaned TOC to LLM for structured output
        if toc_text:
            print("   -> TOC Text found. Querying LLM...")
            print(f"Prompt Message: \n{toc_text}")
            try:
                #structured_toc = await cortex_call_llm_for_toc_extraction(prompt=toc_text, cookie=cookie)
                structured_toc = await personal_call_llm_for_toc_extraction(toc_content=toc_text)
            except Exception as e:
                print(f"   -> Warning: LLM TOC Structuring failed ({str(e)}). Skipping TOC cleaning.")
            
    
        # 5. Cleaning the markdown based on structured TOC
        if structured_toc and isinstance(structured_toc, dict): 
            print(f"LLM Ouput: \n{structured_toc}")
            try:
                # Apply the Final Structure cleaning
                final_content = apply_toc_structure_to_markdown(final_content, structured_toc)
                print("   -> Markdown successfully cleaned using TOC structure.")
                        
            except Exception as e:
                print(f"   -> Warning: Error applying TOC structure ({str(e)}). Reverting to pre-processed markdown.")
        else:
            print("   -> Skipping cleaning (No valid TOC found). Using pre-processed markdown.")
        
        # 6. Upload/Update Drive Files
        raw_link = upload_or_update_file(final_content, f"{filename}_raw.md", raw_folder_id)
        print(f"   -> Drive Link: {raw_link}")

        # 7. Update/Append Sheet Row
        row_data = [
            url,
            filename,
            TITLE,
            phase,
            assigned_to,
            "Done",
            raw_link
        ]
        
        update_or_append_sheet(row_data, filename)
        print("--- Process Complete ---")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        # Log error to sheet
        error_row = [url, filename, TITLE, phase, assigned_to, f"Error: {str(e)}", "" ] 
        update_or_append_sheet(error_row, filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--phase", required=False, default=None)
    parser.add_argument("--bbox", required=False, help="Bounding box as 'top,right,bottom,left'.")
    parser.add_argument("--assigned", default="Unassigned")
    parser.add_argument("--pages", required=False, help="Comma-separated list of pages (e.g., '1,2,5').")
    
    args = parser.parse_args()

    target_pages = None
    if args.pages:
        try:
            target_pages = [int(p.strip()) for p in args.pages.split(",")]
        except ValueError:
            print("Error: --pages must be comma-separated integers.")
            exit(1)

    asyncio.run(process_single_url(
        args.url, 
        args.filename, 
        args.phase, 
        args.assigned, 
        args.bbox, 
        target_pages
    ))