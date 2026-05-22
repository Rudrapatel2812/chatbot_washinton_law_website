import re


RCW_PATTERN = re.compile(r"\b(?:RCW\s*)?(\d+[A-Z]?\.\d+\.\d+)\b", re.IGNORECASE)


def extract_rcw_citation(text: str) -> str | None:
    match = RCW_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).upper()
