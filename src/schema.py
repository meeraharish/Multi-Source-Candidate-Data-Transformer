"""
Canonical schema for the Eightfold Candidate Data Transformer.

This is the FIXED internal shape that every source (structured or
unstructured) gets mapped into before merging. Keeping one canonical
shape means the merge engine never has to deal with source-specific
quirks -- by the time data reaches merge.py, it's already uniform.

Field-level values are wrapped in FieldValue so we can carry
provenance + confidence alongside the actual value, all the way
through the pipeline.
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Provenance: where did this value come from, and why did it win (if there
# was a conflict with another source)?
# ---------------------------------------------------------------------------
class Provenance(BaseModel):
    field: str                     # which canonical field this refers to
    source: str                    # e.g. "recruiter_csv", "resume_pdf"
    method: str                    # e.g. "direct_field", "regex_extract", "ner"
    reason: Optional[str] = None   # WHY this source won, if there was a conflict


# ---------------------------------------------------------------------------
# A single field value, carrying its own confidence score.
# Confidence is computed in merge.py using a principled formula, not a
# hardcoded number.
# ---------------------------------------------------------------------------
class FieldValue(BaseModel):
    value: Optional[object] = None
    confidence: float = 0.0
    sources: List[str] = Field(default_factory=list)


class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None


class Link(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: Optional[str] = None


class SkillEntry(BaseModel):
    name: str
    confidence: float = 0.0
    sources: List[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None   # YYYY-MM
    end: Optional[str] = None     # YYYY-MM or "present"
    source: Optional[str] = None


class EducationEntry(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None
    source: Optional[str] = None


# ---------------------------------------------------------------------------
# RawExtraction: what a single extractor returns for ONE source.
# This is intentionally "loose" -- a partial canonical record, since no
# single source supplies every field. It also tags itself with its own
# source name and extraction method so provenance can be built downstream.
# ---------------------------------------------------------------------------
class RawExtraction(BaseModel):
    source_name: str               # e.g. "recruiter_csv", "resume_pdf"
    source_type: Literal["structured", "unstructured"]
    method: str                    # e.g. "csv_parse", "pdf_text_regex"

    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    
    phone: Optional[dict] = None   # {"number": str, "type": str}
    location: Optional[Location] = None
    links: Optional[Link] = None
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)

    raw_text: Optional[str] = None  # kept for debugging / diff view


# ---------------------------------------------------------------------------
# CanonicalProfile: the fully merged record, BEFORE the runtime config
# projection is applied. This always has the full default schema shape.
# ---------------------------------------------------------------------------
class CanonicalProfile(BaseModel):
    candidate_id: str
    full_name: Optional[FieldValue] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[FieldValue] = Field(default_factory=list)
    location: Optional[FieldValue] = None
    links: Optional[FieldValue] = None
    headline: Optional[FieldValue] = None
    years_experience: Optional[FieldValue] = None
    skills: List[SkillEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    provenance: List[Provenance] = Field(default_factory=list)
    overall_confidence: float = 0.0