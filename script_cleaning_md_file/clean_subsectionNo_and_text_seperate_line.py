import re

from pathlib import Path
import re

def clean_md_text(text):
    # Match:
    # section number
    # followed by optional spaces
    # followed by exactly ONE blank line
    # followed by the title line
    pattern = r"((?:\d+\.)+\d+)\s*\n\s*\n\s*([^\n]+)"


    # Merge section number and title
    cleaned_text = re.sub(pattern, r"\1 \2", text)

    return cleaned_text


if __name__ == "__main__":
    file_path = Path(r"C:\Users\DeepakTM\Music\Projects\Lilly - Data Labelling\script_cleaning_md_file\NCT03153410_raw.md")

    # Read original file
    with open(file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Clean text
    cleaned_text = clean_md_text(md_text)

    # Create new filename: *_cleaned.md
    cleaned_file_path = file_path.with_name(
        file_path.stem + "_cleaned.md"
    )

    # Write cleaned content to new file
    with open(cleaned_file_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    print(f"Cleaned file saved to: {cleaned_file_path}")



