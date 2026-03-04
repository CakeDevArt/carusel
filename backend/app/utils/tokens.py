def estimate_tokens(source_text: str, slides_count: int) -> int:
    char_count = len(source_text) if source_text else 0
    return char_count // 4 + slides_count * 180
