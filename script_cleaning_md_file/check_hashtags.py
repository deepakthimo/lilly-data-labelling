import argparse

def extract_headings(md_text):
    return [line for line in md_text.splitlines() if line.lstrip().startswith("#")]


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


if __name__ == "__main__":
    main()