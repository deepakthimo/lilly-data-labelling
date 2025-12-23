import re

# -----------------------------------------------------
# Dynamic merge of pages
# -----------------------------------------------------

def merge_pages(prev_text: str, curr_text: str) -> str:
    """
    Smart merge of PDF page text based on:
      • list continuation (- ...)
      • inline sentence continuation
      • header separation rules
    """

    if not prev_text.strip():
        return curr_text  # first page

    prev = prev_text.rstrip()
    curr = curr_text.lstrip()

    # Extract lines
    prev_lines = [l for l in prev.split("\n") if l.strip()]
    curr_lines = [l for l in curr.split("\n") if l.strip()]

    last_prev_line = prev_lines[-1] if prev_lines else ""
    first_curr_line = curr_lines[0] if curr_lines else ""

    # --- Detect list continuation ---
    prev_is_dash_list = last_prev_line.lstrip().startswith("-")
    curr_is_dash_list = first_curr_line.lstrip().startswith("-")

    if prev_is_dash_list and curr_is_dash_list:
        # list continues directly
        return prev + "\n" + curr

    # --- Detect sentence end ---
    prev_ends_sentence = bool(re.search(r"[\.!?]\s*$", prev))

    # --- Detect headers (markdown or numbered) ---
    curr_starts_header = (
        curr.startswith("#") or                                      
        re.match(r"^\s*\*\*[^*].*\*\*", curr) is not None or         
        re.match(r"^\s*\d+(\.\d+)*\.", curr) is not None             
    )

    # --- CASE A: Continue sentence ---
    if (not prev_ends_sentence) and (not curr_starts_header):
        return prev + " " + curr

    # --- CASE B: New block ---
    return prev + "\n\n" + curr

# -----------------------------------------------------
# Cleaning Trailing whitespaces within text
# -----------------------------------------------------

def clean_line_text_single(text: str) -> str:
    if not text:
        return ""

    # Normalize unicode spaces to regular space
    text = re.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000]", " ", text)

    # Trim and collapse multiple spaces
    text = text.strip()
    text = re.sub(r" {2,}", " ", text)

    return text


def clean_line_text(text: str) -> str:
    """
    Clean each line independently while maintaining line boundaries.
    """
    return "\n".join(
        clean_line_text_single(line) for line in text.split("\n")
    )
