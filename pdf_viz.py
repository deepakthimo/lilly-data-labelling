import fitz
import os
import shutil
import argparse
import asyncio
from PIL import Image, ImageDraw
from io import BytesIO

from utils.llamaparse import download_pdf
from utils.toc_parse import toc_extraction
from utils.arg_functions import parse_pages_arg

# -----------------------------
# CONSTANTS
# -----------------------------
DEFAULT_VISUALIZATION_BBOXES = [
    (0.05, 0, 0.05, 0),
    (0.1,  0, 0.1,  0),
    (0.1,  0, 0.2,  0),
    (0.15, 0, 0.2,  0),
    (0.2,  0, 0.25, 0),
]

# -----------------------------
# LOGIC: VISUALIZE
# -----------------------------
def draw_bbox_on_page(image: Image.Image, bbox_tuple, save_path):
    top, right, bottom, left = bbox_tuple
    w, h = image.size
    
    # Calculate pixel coordinates
    x1 = left * w
    y1 = top * h
    x2 = w - (right * w)
    y2 = h - (bottom * h)

    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    # Draw red rectangle
    draw.rectangle([x1, y1, x2, y2], outline="red", width=5)
    img_copy.save(save_path)

def run_visualization(pdf_bytes, bbox_list, specific_pages=None):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    print(f"→ PDF has {len(doc)} pages.")
    
    OUTPUT_DIR = "bbox_visualizations"
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    # If specific_pages is None, do all pages. Else filter.
    pages_to_process = specific_pages if specific_pages else range(1, len(doc) + 1)

    count = 0
    for page_num in pages_to_process:
        # Convert 1-based user input to 0-based index
        idx = page_num - 1
        if idx < 0 or idx >= len(doc):
            print(f"Skipping page {page_num} (out of range)")
            continue

        page = doc[idx]
        pix = page.get_pixmap(dpi=150)
        img = Image.open(BytesIO(pix.tobytes("png")))

        for bbox in bbox_list:
            def parse_bbox_arg(bbox_str):
                """Convert "0.1,0,0.2,0" -> (0.1, 0, 0.2, 0)"""
                try:
                    parts = bbox_str.split(",")
                    if len(parts) != 4:
                        raise ValueError
                    return tuple(float(x) for x in parts)
                except Exception:
                    raise ValueError(f"Invalid BBox format: '{bbox_str}'. Expected 'top,right,bottom,left'")

            # ✅ FIX: always define bbox_tuple
            if isinstance(bbox, str):
                bbox_tuple = parse_bbox_arg(bbox)
            else:
                bbox_tuple = tuple(bbox)

            top, right, bottom, left = bbox_tuple
            # Filename includes bbox details to avoid overwriting
            filename = f"Page_{page_num}_BBox_{top}-{right}-{bottom}-{left}.png"
            save_path = os.path.join(OUTPUT_DIR, filename)
            draw_bbox_on_page(img, bbox_tuple, save_path)
        
        count += 1
        print(f"✓ Generated images for Page {page_num}")

    doc.close()
    print(f"\nVisualizations saved to folder: ./{OUTPUT_DIR}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF BBox Tool: Visualize or Extract")
    
    # Common arguments
    parser.add_argument("--url", required=True, help="URL of the PDF")
    parser.add_argument("--mode", choices=["visualize", "extract"], required=True, 
                        help="'visualize' to save images, 'extract' to print text")
    parser.add_argument("--pages", help="Comma separated page numbers (e.g. '1,13'). Optional for visualize, Required for extract.")
    parser.add_argument("--bbox", action="append", help="BBox 'top,right,bottom,left'. For extract, use only one.")

    args = parser.parse_args()

    # 1. Download
    try:
        pdf_data = download_pdf(args.url)
    except Exception as e:
        print(f"Failed to download PDF: {e}")
        exit(1)

    # 2. Parse Pages
    target_pages = parse_pages_arg(args.pages) if args.pages else None

    # 3. Handle Visualization Mode
    if args.mode == "visualize":
        if args.bbox:
            run_visualization(pdf_data, args.bbox, target_pages)
        else:
            bboxes = DEFAULT_VISUALIZATION_BBOXES
            print("No --bbox provided. Using default candidate list.")
            run_visualization(pdf_data, DEFAULT_VISUALIZATION_BBOXES, target_pages)

    # 4. Handle Extraction Mode
    elif args.mode == "extract":
        if not args.bbox:
            print("No --bbox provided. Extracting full page (0,0,0,0).")
            selected_bbox = "0,0,0,0"
        else:
            selected_bbox = args.bbox[0]
            if len(args.bbox) > 1:
                print("Warning: Multiple bboxes provided for extraction. Using only the first one.")

        toc_text = asyncio.run(toc_extraction(pdf_data, selected_bbox, target_pages, logging=True))