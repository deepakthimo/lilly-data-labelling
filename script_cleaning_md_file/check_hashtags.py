import argparse
import re

def extract_headings(md_text):
    heading_pattern = re.compile(
        r'^(#+)\s+(\d+(?:\.\d+)*\.?)\s+(.*)$'
    )

    headings = []

    for line in md_text.splitlines():
        line = line.rstrip()
        if heading_pattern.match(line):
            headings.append(line)

    return headings

def main():
    parser = argparse.ArgumentParser(
        description="Extract Markdown headings (#, ##, ###, etc.) from a file"
    )
    parser.add_argument(
        "file_path",
        help="Path to the Markdown (.md) file"
    )

    args = parser.parse_args()

    # Read the file
    with open(args.file_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Extract headings
    headings = extract_headings(md_text)
    
    # Print results
    for heading in headings:
        print(heading)

    print("=" * 50)
    print (f"\n Total Number of Heading and Sub-Heading: {len(headings)} \n")
    print("=" * 50)

if __name__ == "__main__":
    main()