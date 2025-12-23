def parse_pages_arg(pages_str):
    """Convert "1,2,5" -> [0, 1, 4] (0-indexed for code, user inputs 1-indexed)"""
    if not pages_str:
        return None
    try:
        return [int(p.strip()) for p in pages_str.split(",")]
    except ValueError:
        raise ValueError("Pages must be comma-separated integers (e.g. '1,3,5')")