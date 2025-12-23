import re
import requests
from io import BytesIO
from llama_parse import LlamaParse
from utils.helper_func import merge_pages, clean_line_text

from dotenv import load_dotenv
load_dotenv()

class LlamaParseError(RuntimeError):
    """Raised when LlamaParse fails."""

async def extract_text_llamaparse(file_bytes, filename, bbox: str="0.1,0,0.1,0") -> str:
    try:
        parser = LlamaParse(
            result_type="markdown", 
            verbose=True, 
            parse_mode="parse_page_with_llm",
            adaptive_long_table=True,
            outlined_table_extraction=True,
            disable_image_extraction=True,
            skip_diagonal_text=True,
            # hide_headers=True,
            # hide_footers=True,
            bounding_box=bbox
        )
        docs = parser.load_data(file_bytes, extra_info={"file_name": filename})
    except Exception as e:
        # Fail fast and loud
        raise LlamaParseError(f"LlamaParse failed for file '{filename}' with bbox='{bbox}': {e}") from e

    
    # Phase 1 - dynamic page merging
    merged_text = ""
    for doc in docs:
        page_text = doc.text or ""
        merged_text = merge_pages(merged_text, page_text)

    # Phase 2 - line-by-line cleaning
    cleaned_text = clean_line_text(merged_text)

    # Phase 3 - Removing repeated blank Lines
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

    # Phase 4 - Fx hyphenated words at line breaks
    cleaned_text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", cleaned_text)

    return cleaned_text

def download_pdf(url):
    print(f"Downloading PDF: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)