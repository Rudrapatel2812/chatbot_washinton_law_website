from app.core.citations import extract_rcw_citation


def test_extracts_numeric_rcw_citation() -> None:
    assert extract_rcw_citation("What does RCW 1.20.075 say?") == "1.20.075"


def test_extracts_alphanumeric_title_citation() -> None:
    assert extract_rcw_citation("Explain rcw 9A.04.110") == "9A.04.110"


def test_returns_none_without_citation() -> None:
    assert extract_rcw_citation("What are the rules about theft?") is None
