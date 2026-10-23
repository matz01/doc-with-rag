"""Manifest loading for the ingestion pipeline.

`data/manifest.yaml` is the single source of truth for what can be ingested and who
can read it. The loader parses it into validated Pydantic models (Pydantic crosses the
file boundary, see the python-backend skill) and derives the `superseded_by` links from
the inverse `supersedes` links, so the YAML never carries the same relation twice.
"""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator, model_validator

_FORMATS = "md", "pdf", "docx"
_STATUSES = "current", "superseded"


class ManifestDocument(BaseModel):
    """One document of the manifest, exactly as the YAML row describes it.

    `path` stays corpus-root-relative (the same string YAML has): resolving it too
    early would make the model depend on where the loader ran.
    """

    # `superseded_by` is intentionally not read from the YAML even when present: it is
    # derived in `Manifest` from the inverse `supersedes` links, so there is exactly one
    # place where a supersession can be declared.
    id: str
    title: str
    path: Path
    department: str
    format: Literal["md", "pdf", "docx"]
    allowed_groups: list[str]
    effective_date: date
    status: Literal["current", "superseded"]
    supersedes: str | None = None
    superseded_by: str | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("path")
    @classmethod
    def _path_must_stay_inside_the_corpus_root(cls, value: Path, info: ValidationInfo) -> Path:
        """Reject absolute paths and any `..` climb: the root must not be escapable.

        `load_manifest` passes the corpus root in the validation context; a plain
        `ManifestDocument(...)` cannot escape-check (no root to check against), so the
        cheap local checks still apply there.
        """
        if value.is_absolute() or ".." in value.parts:
            raise ValueError(f"{value}: path must stay inside the corpus root")
        context = info.context or {}
        corpus_root = context.get("corpus_root")
        if corpus_root is not None:
            # resolve(strict=False) also normalizes the root and target syntaxes on
            # macOS (/path vs /private/path) so the is_relative_to check is exact.
            absolute = (corpus_root / value).resolve()
            if not absolute.is_relative_to(corpus_root):
                raise ValueError(f"{value}: path must stay inside the corpus root")
        return value


class Manifest(BaseModel):
    """The parsed manifest: every document with its permissions."""

    documents: list[ManifestDocument]

    @model_validator(mode="after")
    def _ids_are_unique_and_links_are_derived(self) -> "Manifest":
        """Check id uniqueness, then fill `superseded_by` from the `supersedes` links."""
        ids = [document.id for document in self.documents]
        duplicates = {document_id for document_id in ids if ids.count(document_id) > 1}
        if duplicates:
            raise ValueError(f"duplicate document ids in the manifest: {sorted(duplicates)}")

        # The link lives on the superseding document (`supersedes`); the inverse view is
        # what the rest of the pipeline asks ("who replaced this document?").
        supersedes_to_replacement = {
            document.supersedes: document.id
            for document in self.documents
            if document.supersedes is not None
        }
        for document in self.documents:
            document.superseded_by = supersedes_to_replacement.get(document.id)
        return self


def load_manifest(manifest_path: Path, corpus_root: Path) -> Manifest:
    """Load the manifest at *manifest_path*, with paths relative to *corpus_root*.

    The Pydantic validation context carries the corpus root into the document-level
    path validator; cleaner than module state and it keeps `Manifest` root-agnostic.
    """
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return Manifest.model_validate(raw, context={"corpus_root": corpus_root.resolve()})
