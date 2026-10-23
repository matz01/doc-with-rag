"""Unit tests for document parsing (app.ingestion.parsing)."""

from pathlib import Path

import pytest

from app.ingestion.parsing import ParsedBlock, parse_document

# Paths must not depend on where pytest is launched from (`uv run --directory backend`
# makes backend/ the cwd): resolve the fixtures from this file's location.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES = BASE_DIR / "tests" / "fixtures"


def test_returns_markdown_sections_and_code_blocks_from_a_markdown_file():
    """A .md file is split into paragraphs attributed to the open h2 heading, and a
    fenced code block becomes a single block with its raw content."""

    blocks = parse_document(FIXTURES / "tiny.md")

    assert [(block.text, block.section) for block in blocks] == [
        ("First paragraph of a Markdown document.", "Intro"),
        ("Run the installer. Longer setup paragraph with more words.", "Setup"),
        ("bundle exec install", "Setup"),
    ]


def test_returns_the_text_before_the_first_markdown_heading_without_a_section(tmp_path):
    """A paragraph that precedes any heading belongs to no section (None)."""

    document = tmp_path / "inline.md"
    document.write_text(
        "Preamble paragraph before any heading.\n\n## Setup\n\nBody after the first heading.\n"
    )

    blocks = parse_document(document)

    assert [(block.text, block.section) for block in blocks] == [
        ("Preamble paragraph before any heading.", None),
        ("Body after the first heading.", "Setup"),
    ]


def test_returns_one_block_per_pdf_page_in_page_order():
    """A .pdf file yields one block per page, in page order, without sections."""

    blocks = parse_document(FIXTURES / "tiny.pdf")

    assert isinstance(blocks[0], ParsedBlock)
    assert [(block.text, block.section) for block in blocks] == [
        ("Tiny PDF page 1 text.", None),
        ("Tiny PDF page 2 text.", None),
    ]


def test_returns_docx_paragraphs_attributed_to_their_heading_section():
    """In a .docx file, Heading-styled paragraphs open sections but are not blocks;
    ordinary paragraphs carry the section opened by the nearest heading above."""

    blocks = parse_document(FIXTURES / "tiny.docx")

    assert [(block.text, block.section) for block in blocks] == [
        ("Introduction body paragraph.", "Policy Title"),
        ("Detail body paragraph.", "Details"),
    ]


def test_rejects_unknown_suffixes_with_a_value_error(tmp_path):
    """A file whose suffix is not md/pdf/docx is not accepted."""

    document = tmp_path / "tiny.txt"
    document.write_text("Just some plain text.")

    with pytest.raises(ValueError):
        parse_document(document)
