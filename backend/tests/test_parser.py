from app.models.law import LawStatus
from data_pipeline.parser import parse_section_html


def test_parse_section_html_extracts_basic_law_fields() -> None:
    html = """
    <html>
      <body>
        <div class="title-block">
          <h1>RCW 1.20.075</h1>
          <h2>State dance.</h2>
        </div>
        <div id="contentWrapper" class="section-page">
          <div><div style="text-indent: 20px">The square dance is designated as the official dance.</div></div>
          <div style="margin-top:15pt;">[ 1979 c 1 s 1. ]</div>
          <div><h3>Notes:</h3></div>
          <div><div style="font-style:italic;">Effective date.</div></div>
        </div>
      </body>
    </html>
    """

    document = parse_section_html(
        html=html,
        jurisdiction_code="WA",
        title_number="1",
        citation="1.20.075",
        source_url="https://app.leg.wa.gov/RCW/default.aspx?cite=1.20.075",
        raw_html_path="data/raw_html/title_1/1_20_075.html",
    )

    assert document.law.citation == "1.20.075"
    assert document.law.chapter_number == "1.20"
    assert document.law.jurisdiction_code == "WA"
    assert document.law.heading == "State dance."
    assert "square dance" in document.law.text
    assert document.law.history == "[ 1979 c 1 s 1. ]"
    assert document.law.notes == "Effective date."
    assert document.law.status == LawStatus.active


def test_parse_section_html_detects_repealed_status() -> None:
    document = parse_section_html(
        html="<html><body><div id='contentstart'>[Repealed.]</div></body></html>",
        jurisdiction_code="WA",
        title_number="1",
        citation="1.01.010",
        source_url="https://example.test",
        raw_html_path="example.html",
    )

    assert document.law.status == LawStatus.repealed
