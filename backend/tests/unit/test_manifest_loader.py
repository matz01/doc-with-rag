"""Unit tests for the manifest loader (app.ingestion.manifest)."""

from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ingestion.manifest import Manifest, load_manifest

VALID_ERRORS = (ValueError, ValidationError)

# Paths must not depend on where pytest is launched from (`uv run --directory backend`
# makes backend/ the cwd): resolve the fixture from this file's location.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VALID_MANIFEST = BASE_DIR / "tests" / "fixtures" / "manifest_valid.yaml"


def _load_inline(tmp_path: Path, text: str) -> Manifest:
    """Write inline YAML to tmp_path and load it with that dir as corpus root."""

    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(text)
    return load_manifest(manifest_path, corpus_root=tmp_path)


def _documents_by_id(manifest: Manifest) -> dict:
    """Index manifest documents by id for convenient lookup."""

    return {document.id: document for document in manifest.documents}


def test_returns_documents_with_their_fields_parsed_from_the_manifest():
    """Every document field declared in the YAML is parsed onto the model."""

    manifest = load_manifest(VALID_MANIFEST, corpus_root=BASE_DIR)

    documents = _documents_by_id(manifest)

    alpha = documents["alpha-handbook"]
    assert alpha.title == "Alpha Handbook"
    assert alpha.path == Path("documents/company/alpha-handbook.md")
    assert alpha.department == "company"
    assert alpha.format == "md"
    assert alpha.allowed_groups == ["all_staff", "engineers"]
    assert alpha.effective_date == date(2026, 1, 1)
    assert alpha.status == "current"
    assert alpha.supersedes is None

    beta_2026 = documents["beta-policy-2026"]
    assert beta_2026.effective_date == date(2026, 1, 1)
    assert beta_2026.supersedes == "beta-policy-2025"

    beta_2025 = documents["beta-policy-2025"]
    assert beta_2025.effective_date == date(2025, 1, 1)
    assert beta_2025.status == "superseded"


def test_derives_superseded_by_from_the_inverse_supersedes_links():
    """superseded_by is computed after parsing, from the supersedes links."""

    manifest = load_manifest(VALID_MANIFEST, corpus_root=BASE_DIR)

    documents = _documents_by_id(manifest)

    assert documents["beta-policy-2026"].superseded_by is None
    assert documents["beta-policy-2025"].superseded_by == "beta-policy-2026"


def test_rejects_duplicate_document_ids_with_a_validation_error(tmp_path):
    """Two documents with the same id make the manifest invalid."""

    text = (
        "documents:\n"
        "- id: alpha-handbook\n"
        "  title: Alpha Handbook\n"
        "  path: documents/company/alpha-handbook.md\n"
        "  department: company\n"
        "  format: md\n"
        "  allowed_groups:\n"
        "  - all_staff\n"
        "  effective_date: '2026-01-01'\n"
        "  status: current\n"
        "- id: alpha-handbook\n"
        "  title: Alpha Handbook Again\n"
        "  path: documents/company/alpha-handbook-2.md\n"
        "  department: company\n"
        "  format: md\n"
        "  allowed_groups:\n"
        "  - all_staff\n"
        "  effective_date: '2026-01-01'\n"
        "  status: current\n"
    )

    with pytest.raises(VALID_ERRORS):
        _load_inline(tmp_path, text)


def test_rejects_unknown_format_or_status_with_a_validation_error(tmp_path):
    """A format outside md/pdf/docx is not accepted."""

    text = (
        "documents:\n"
        "- id: alpha-handbook\n"
        "  title: Alpha Handbook\n"
        "  path: documents/company/alpha-handbook.txt\n"
        "  department: company\n"
        "  format: txt\n"
        "  allowed_groups:\n"
        "  - all_staff\n"
        "  effective_date: '2026-01-01'\n"
        "  status: current\n"
    )

    with pytest.raises(VALID_ERRORS):
        _load_inline(tmp_path, text)


def test_rejects_paths_escaping_the_corpus_root(tmp_path):
    """A relative path that climbs out of the corpus root is not accepted."""

    text = (
        "documents:\n"
        "- id: alpha-handbook\n"
        "  title: Alpha Handbook\n"
        "  path: '../../etc/passwd'\n"
        "  department: company\n"
        "  format: md\n"
        "  allowed_groups:\n"
        "  - all_staff\n"
        "  effective_date: '2026-01-01'\n"
        "  status: current\n"
    )

    with pytest.raises(VALID_ERRORS):
        _load_inline(tmp_path, text)
