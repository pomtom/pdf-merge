"""Pydantic request/response schemas for the REST API."""

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


def sanitize_pdf_name(name: str, default: str) -> str:
    """Reduce a user-supplied output name to a safe bare filename ending in .pdf."""
    name = (name or "").strip().replace("\\", "/").split("/")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "", name).strip(". ")
    if not name:
        name = default
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


# ---- files ----------------------------------------------------------------

class PageInfo(BaseModel):
    index: int
    width_pt: float
    height_pt: float
    rotation: int


class FileEntry(BaseModel):
    file_id: str
    name: str
    size_bytes: int
    page_count: int
    pages: list[PageInfo]


class RejectedFile(BaseModel):
    name: str
    code: str
    message: str


class UploadResponse(BaseModel):
    files: list[FileEntry]
    rejected: list[RejectedFile]


class FilesResponse(BaseModel):
    files: list[FileEntry]


class OrderRequest(BaseModel):
    order: list[str] = Field(min_length=1)


# ---- jobs ------------------------------------------------------------------

class PageOp(BaseModel):
    index: int = Field(ge=0)
    rotate: Literal[0, 90, 180, 270] = 0


class MergeItem(BaseModel):
    file_id: str
    pages: Optional[list[PageOp]] = None  # None = all pages, in order


class MergeRequest(BaseModel):
    output_name: str = "merged.pdf"
    items: list[MergeItem] = Field(min_length=1)

    @field_validator("output_name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        return sanitize_pdf_name(v, "merged.pdf")


class SplitRequest(BaseModel):
    file_id: str
    mode: Literal["ranges", "every_page", "chunks"]
    ranges: Optional[list[tuple[int, int]]] = None  # 1-based inclusive
    chunk_size: Optional[int] = Field(default=None, ge=1)
    output_basename: str = "part"

    @field_validator("output_basename")
    @classmethod
    def _clean_basename(cls, v: str) -> str:
        return sanitize_pdf_name(v, "part")[:-4]  # sanitize, then drop ".pdf"


class ExtractRequest(BaseModel):
    file_id: str
    output_name: str = "extracted.pdf"
    pages: list[PageOp] = Field(min_length=1)

    @field_validator("output_name")
    @classmethod
    def _clean_name(cls, v: str) -> str:
        return sanitize_pdf_name(v, "extracted.pdf")


class JobCreated(BaseModel):
    job_id: str


class JobProgress(BaseModel):
    current: int
    total: int
    message: str


class OutputRef(BaseModel):
    output_id: str
    name: str
    size_bytes: int


class JobStatus(BaseModel):
    job_id: str
    kind: str
    status: Literal["queued", "running", "done", "error"]
    progress: JobProgress
    error: Optional[dict] = None
    outputs: list[OutputRef]


# ---- outputs ---------------------------------------------------------------

class OutputInfo(BaseModel):
    output_id: str
    name: str
    size_bytes: int
    created_at: str
    job_id: str


class OutputsResponse(BaseModel):
    outputs: list[OutputInfo]
