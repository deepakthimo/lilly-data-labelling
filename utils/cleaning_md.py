import re

def merge_broken_markdown_headers(markdown_text: str) -> str:
    """
    Scans for lines that look like orphaned headers (e.g., "## 1." or "# 2.1.3")
    and merges them with the text of the very next line.
    
    Example Input:
    ## 1.
    Introduction
    
    Example Output:
    ## 1. Introduction
    """
    print("   -> Pre-processing: Merging broken header lines...")
    
    lines = markdown_text.splitlines()
    merged_lines = []
    i = 0
    n = len(lines)

    # Regex: 
    # ^\s*       : Start of line, optional space
    # #+         : One or more hashtags
    # \s+        : Space
    # \d+        : A number
    # (?:\.\d+)* : Optional groups of .number (e.g. .1.2)
    # \.?        : Optional trailing dot
    # \s*$       : End of line (Crucial: NO text after the number)
    orphan_header_pattern = re.compile(r"^(\s*#+\s*\d+(?:\.\d+)*\.?)\s*$")

    while i < n:
        line = lines[i]
        
        # Check if this line is an orphaned header (just number, no title)
        match = orphan_header_pattern.match(line)
        
        if match:
            # We found a header with no text (e.g., "## 1.")
            header_part = match.group(1).strip()
            
            # Check if there is a next line
            if i + 1 < n:
                next_line = lines[i+1].strip()
                
                # We only merge if the next line exists, is NOT empty, 
                # and does NOT start with another header (#)
                if next_line and not next_line.startswith("#"):
                    # MERGE
                    combined = f"{header_part} {next_line}"
                    merged_lines.append(combined)
                    i += 2  # Skip current and next line
                    continue

        # If no merge happened, keep line as is
        merged_lines.append(line)
        i += 1

    return "\n".join(merged_lines)