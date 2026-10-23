"""Document parsing: read a corpus file (md, pdf, docx) into path-aware text blocks."""

import re
from dataclasses import dataclass
from pathlib import Path

import pypdf
from docx import Document as read_docx


@dataclass(frozen=True)
class ParsedBlock:
    """A paragraph-sized piece of a document, with the section it belongs to.

    `section` is the nearest heading above the block (md/docx know it; pdf does not
    and leaves it None). Chunking later keeps this attribution stable per chunk.
    """

    text: str
    section: str | None = None


_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def parse_document(path: Path) -> list[ParsedBlock]:
    """Parse a corpus file into blocks, format inferred from the suffix."""
    format_by_suffix = {
        ".md": _parse_markdown_of,
        ".pdf": _parse_pdf_of,
        ".docx": _parse_docx_of,
    }
    parser = format_by_suffix.get(path.suffix)
    if parser is None:
        raise ValueError(f"{path}: only md, pdf and docx files are supported")
    return parser(path)


def _parse_markdown_of(path: Path) -> list[ParsedBlock]:
    """Linear scan of a Markdown file: headings open sections, fences keep code verbatim.

    Hand-rolled instead of a Markdown library because the corpus uses a narrow subset
    (headings, paragraphs, fences) and section attribution is the classifier we
    actually need for chunking.
    """
    blocks: list[ParsedBlock] = []
    section: str | None = None
    paragraph: list[str] = []
    fenced_code: list[str] | None = None

    def flush() -> None:
        if paragraph:
            text = " ".join(paragraph).strip()
            if text:
                blocks.append(ParsedBlock(text=text, section=section))
            paragraph.clear()

    for line in path.read_text(encoding="utf-8").splitlines():
        if fenced_code is not None:
            # Inside a fence every line (except the delimiters) is verbatim code.
            if line.startswith("```"):
                blocks.append(ParsedBlock(text="\n".join(fenced_code), section=section))
                fenced_code = None
            else:
                fenced_code.append(line)
        elif line.startswith("```"):
            flush()
            fenced_code = []
        else:
            heading = _HEADING.match(line)
            if heading is not None:
                flush()
                section = heading.group(2).strip()
            elif line.strip():
                # Blank lines separate paragraphs; wrapped lines are one paragraph.
                paragraph.append(line.strip())
            else:
                flush()
    flush()
    return blocks


def _parse_pdf_of(path: Path) -> list[ParsedBlock]:
    """One block per page, in page order: a PDF has no reliable heading structure."""
    reader = pypdf.PdfReader(path)
    blocks = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            blocks.append(ParsedBlock(text=text))
    return blocks


def _parse_docx_of(path: Path) -> list[ParsedBlock]:
    """Heading paragraphs open sections; body paragraphs become attributable blocks."""
    blocks: list[ParsedBlock] = []
    section: str | None = None
    for paragraph in read_docx(str(path)).paragraphs:
        if paragraph.style is not None and paragraph.style.name.startswith("Heading"):
            section = paragraph.text.strip()
        elif paragraph.text.strip():
            blocks.append(ParsedBlock(text=paragraph.text.strip(), section=section))
    return blocks
