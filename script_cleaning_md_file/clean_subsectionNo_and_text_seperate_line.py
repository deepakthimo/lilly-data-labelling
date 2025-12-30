import argparse
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

def main():
    parser = argparse.ArgumentParser(
        description="Clean Markdown file by merging subsection numbers with titles"
    )
    parser.add_argument(
        "file_path",
        help="Path to the Markdown (.md) file"
    )

    args = parser.parse_args()

    # Read original file
    with open(args.file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Clean text
    cleaned_text = clean_md_text(md_text)

    # Create new filename: *_cleaned.md
    cleaned_file_path = Path(args.file_path).with_name(
        Path(args.file_path).stem + "_merged_section_title_number.md"
    )

    # Write cleaned content to new file
    with open(cleaned_file_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    print(f"Cleaned file saved to: {cleaned_file_path}")


if __name__ == "__main__":
    main()



