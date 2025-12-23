# import fitz
# import re

# def toc_extraction(pdf_bytes, bbox, specific_pages, logging=True):
#     if not specific_pages:
#         print("Error: You must provide --pages for extraction mode.")
#         return

#     doc = fitz.open(stream=pdf_bytes, filetype="pdf")
#     max_pages = len(doc)

#     def parse_bbox_arg(bbox_str):
#         """Convert "0.1,0,0.2,0" -> (0.1, 0, 0.2, 0)"""
#         try:
#             parts = bbox_str.split(",")
#             if len(parts) != 4:
#                 raise ValueError
#             return tuple(float(x) for x in parts)
#         except Exception:
#             raise ValueError(f"Invalid BBox format: '{bbox_str}'. Expected 'top,right,bottom,left'")

#     bbox = parse_bbox_arg(bbox)

#     # Unpack BBox
#     top_pct, right_pct, bottom_pct, left_pct = bbox

#     if logging:
#         print(f"\n--- EXTRACTING TEXT (BBox: {bbox}) ---")

#     full_text = ""

#     for page_num in specific_pages:
#         # 0-based index conversion
#         idx = page_num - 1
        
#         if not (0 <= idx < max_pages):
#             print(f"Page {page_num} is out of range.")
#             continue

#         page = doc.load_page(idx)
#         page_w = page.rect.width
#         page_h = page.rect.height

#         # Calculate Crop Rectangle
#         x1 = left_pct * page_w
#         y1 = top_pct * page_h
#         x2 = page_w - (right_pct * page_w)
#         y2 = page_h - (bottom_pct * page_h)

#         clip_rect = fitz.Rect(x1, y1, x2, y2)
        
#         # Extract
#         text = page.get_text("text", clip=clip_rect)
#         full_text += clean_toc_text(text.strip()) + "\n"
        
#         if logging:
#             print(f"\n=== PAGE {page_num} OUTPUT START ===")
#             print(clean_toc_text(text.strip()))
#             print(f"=== PAGE {page_num} OUTPUT END ===\n")
 
#     doc.close()
#     return full_text


# def clean_toc_text(raw_text):
#     """
#     Cleans raw TOC text:
#     1. Removes dots and page numbers (e.g., "....... 12").
#     2. Merges split lines (e.g., "1." on one line, "Intro" on next).
#     3. Merges wrapped headings.
#     """
#     cleaned_lines = []
    
#     # Standard standalone headers that don't always have numbers
#     # We treat these as "Start of a new line"
#     section_starters = [
#         "TABLE OF CONTENTS", "SYNOPSIS", "FLOW CHART", "ABBREVIATIONS",
#         "REFERENCES", "APPENDICES", "TITLE PAGE", "INTRODUCTION", "COMPLIANCE"
#     ]

#     # Split into lines
#     raw_lines = raw_text.split('\n')

#     for line in raw_lines:
#         # 1. REMOVE DOTS AND PAGE NUMBERS
#         # Regex explanation:
#         # \s*       -> matches optional whitespace
#         # \.{2,}    -> matches 2 or more dots
#         # .*        -> matches anything after dots (spaces, digits)
#         # $         -> end of string
#         line = re.sub(r'\s*\.{2,}.*$', '', line).strip()
        
#         # Skip empty lines
#         if not line:
#             continue

#         # 2. LOGIC TO MERGE LINES
#         # We need to decide: Is this line a NEW entry, or a CONTINUATION of the previous?
        
#         is_new_entry = False
        
#         # Check A: Does it start with a number? (e.g., "1.", "2.1", "3.1.1")
#         if re.match(r'^\d+(\.\d+)*', line):
#             is_new_entry = True
        
#         # Check B: Is it a known section starter word?
#         elif any(line.upper().startswith(s) for s in section_starters):
#             is_new_entry = True

#         # Check C: Special case - if the PREVIOUS line was just a number (e.g. "1."),
#         # this line MUST be attached to it, even if this line looks like a starter.
#         if cleaned_lines and re.match(r'^\d+(\.\d+)*\.?$', cleaned_lines[-1]):
#              is_new_entry = False # Force merge

#         # EXECUTE MERGE OR APPEND
#         if is_new_entry or not cleaned_lines:
#             cleaned_lines.append(line)
#         else:
#             # It's a continuation (wrapped text), append to previous line
#             cleaned_lines[-1] = cleaned_lines[-1] + " " + line

#     return "\n".join(cleaned_lines)

# def apply_toc_structure_to_markdown(markdown_text: str, toc_dict: dict) -> str:
#     """
#     1. Removes all existing markdown headers (#).
#     2. Scans text for lines matching TOC entries (Section Number + Title).
#     3. Re-inserts # headers based on the hierarchy depth of the section number.
#     """
#     print("   -> Applying TOC structure to markdown...")

#     # -----------------------------
#     # STEP 1: Remove ALL '#' from every line
#     # -----------------------------
#     lines = markdown_text.splitlines()
#     clean_lines = []
    
#     for line in lines:
#         # Remove any number of # at the start of the line, keeping the rest
#         # matches: "## 1. Intro" -> "1. Intro"
#         cleaned = re.sub(r"^\s*#+\s*", "", line)
#         clean_lines.append(cleaned)

#     # Rejoin to a single string for block regex processing
#     clean_text = "\n".join(clean_lines)

#     # -----------------------------
#     # STEP 2: Insert correct '#' only for TOC sections
#     # -----------------------------
#     # Sort keys longest-first (descending length) so "5.2.1" is processed before "5.2" or "5"
#     # This prevents partial matching errors.
#     sorted_keys = sorted(toc_dict.keys(), key=lambda x: (-len(x), x))

#     for num in sorted_keys:
#         title = toc_dict[num]
        
#         # Determine heading level (1 dot = ## (H2), 0 dots = # (H1))
#         # Logic: "1" -> 1 #, "1.1" -> 2 #, "1.1.1" -> 3 #
#         heading_level = num.count('.') + 1
#         hashes = '#' * heading_level

#         # Regex Explanation:
#         # ^          : Start of line (multiline mode)
#         # {num}      : The section number (e.g., 1.1)
#         # \.?        : Optional dot after number
#         # \s+        : Whitespace
#         # {title}    : The title text (escaped to handle special chars)
#         pattern = rf"^{re.escape(num)}\.?\s+{re.escape(title)}"
        
#         # Replacement: "## 1.1. Title"
#         replacement = f"{hashes} {num}. {title}"
        
#         # Perform substitution
#         clean_text = re.sub(pattern, replacement, clean_text, flags=re.MULTILINE)

#     return clean_text

import fitz  # PyMuPDF
import re
from io import BytesIO

# -----------------------------
# LOGIC: TEXT CLEANING
# -----------------------------
def clean_toc_text(raw_text):
    """
    Cleans raw TOC text:
    1. Removes dots and page numbers (e.g., "....... 12").
    2. Merges split lines.
    """
    cleaned_lines = []
    
    section_starters = [
        "TABLE OF CONTENTS", "SYNOPSIS", "FLOW CHART", "ABBREVIATIONS",
        "REFERENCES", "APPENDICES", "TITLE PAGE", "INTRODUCTION", "COMPLIANCE"
    ]

    raw_lines = raw_text.split('\n')

    for line in raw_lines:
        # 1. REMOVE DOTS AND PAGE NUMBERS
        # Matches 2+ dots followed by anything to end of line
        line = re.sub(r'\s*\.{2,}.*$', '', line).strip()
        
        # Also remove trailing numbers if there were no dots (e.g. "Title 12")
        # Be careful not to remove section numbers like "1. Title"
        # Look for number at the very end preceded by space
        line = re.sub(r'\s+\d+$', '', line).strip()

        if not line:
            continue

        # 2. LOGIC TO MERGE LINES
        is_new_entry = False
        
        # Starts with number? "1.", "2.1"
        if re.match(r'^\d+(\.\d+)*', line):
            is_new_entry = True
        # Known word?
        elif any(line.upper().startswith(s) for s in section_starters):
            is_new_entry = True
        
        # Special case: Previous line was just a number -> merge
        if cleaned_lines and re.match(r'^\d+(\.\d+)*\.?$', cleaned_lines[-1]):
             is_new_entry = False

        if is_new_entry or not cleaned_lines:
            cleaned_lines.append(line)
        else:
            cleaned_lines[-1] = cleaned_lines[-1] + " " + line

    return "\n".join(cleaned_lines)

# -----------------------------
# MAIN EXTRACTION FUNCTION
# -----------------------------
async def toc_extraction(file_bytes, bbox, pages=None, specific_pages=None, logging=False):
    """
    Extracts text from specific pages within a bbox.
    Accepts both 'pages' and 'specific_pages' to avoid TypeError.
    """
    # Handle argument alias
    target_pages = specific_pages if specific_pages else pages
    
    if not target_pages:
        if logging:
            print("No pages provided for TOC extraction.")
        return None

    if logging:
        print(f"Extracting TOC from pages: {target_pages} with BBox: {bbox}")

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    max_pages = len(doc)
    def parse_bbox_arg(bbox_str):
        """
        Converts "0.1,0,0.2,0" -> (0.1, 0.0, 0.2, 0.0)
        """
        if not bbox_str:
            return None
        try:
            parts = bbox_str.split(",")
            if len(parts) != 4:
                raise ValueError("BBox must have exactly 4 values.")
            return tuple(float(x.strip()) for x in parts)
        except Exception as e:
            print(f"Error parsing bbox: {e}")
            return None
    bbox_tuple = parse_bbox_arg(bbox)
    
    # Unpack BBox (top, right, bottom, left) percentages
    top_pct, right_pct, bottom_pct, left_pct = bbox_tuple

    full_text_buffer = ""

    for page_num in target_pages:
        idx = page_num - 1 # Convert 1-based to 0-based
        if not (0 <= idx < max_pages):
            continue

        page = doc.load_page(idx)
        page_w = page.rect.width
        page_h = page.rect.height

        # Calculate Crop Rectangle
        x1 = left_pct * page_w
        y1 = top_pct * page_h
        x2 = page_w - (right_pct * page_w)
        y2 = page_h - (bottom_pct * page_h)

        clip_rect = fitz.Rect(x1, y1, x2, y2)
        
        # Extract text
        text = page.get_text("text", clip=clip_rect)
        full_text_buffer += text + "\n"
        if logging:
            print(f"\n=== PAGE {page_num} OUTPUT START ===")
            print(clean_toc_text(text.strip()))
            print(f"=== PAGE {page_num} OUTPUT END ===\n")

    doc.close()

    # Clean the result
    final_toc = clean_toc_text(full_text_buffer)
    return final_toc

# -----------------------------
# LOGIC: APPLY STRUCTURE TO MD
# -----------------------------
def apply_toc_structure_to_markdown(markdown_text: str, toc_dict: dict) -> str:
    # (Same function as before)
    lines = markdown_text.splitlines()
    clean_lines = []
    for line in lines:
        cleaned = re.sub(r"^\s*#+\s*", "", line)
        clean_lines.append(cleaned)
    clean_text = "\n".join(clean_lines)

    sorted_keys = sorted(toc_dict.keys(), key=lambda x: (-len(x), x))

    for num in sorted_keys:
        title = toc_dict[num]
        heading_level = num.count('.') + 1
        hashes = '#' * heading_level
        pattern = rf"^{re.escape(num)}\.?\s+{re.escape(title)}"
        replacement = f"{hashes} {num}. {title}"
        clean_text = re.sub(
            pattern,
            replacement,
            clean_text,
            flags=re.MULTILINE | re.IGNORECASE
        )

    return clean_text

if __name__ == "__main__":
    import json
    # Example usage
    input_markdown = ""
    with open(r"C:\Users\DeepakTM\Music\Projects\Lilly - Data Labelling\debug_preprocessed.md", 'r', encoding='utf-8') as f:
        input_markdown = f.read()
    
    sample_toc = {}
    with open(r"C:\Users\DeepakTM\Music\Projects\Lilly - Data Labelling\debug_structured_toc.json", 'r', encoding='utf-8') as f:
        import ast
        #sample_toc = ast.literal_eval(f.read())
        sample_toc = json.load(f)

    result = apply_toc_structure_to_markdown(input_markdown, sample_toc)


    with open("debug_final_output.md", 'w', encoding='utf-8') as f:
        f.write(result)