from __future__ import annotations
import re
from pathlib import Path
from typing import List, Optional

from src.schema import RawExtraction, Link
from src.normalizers import normalize_phone, normalize_name, normalize_email, split_skills

SOURCE_NAME = "resume_text"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\-\(\) ]{7,}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"github\.com/[\w-]+", re.IGNORECASE)

def _find_name(text: str) -> Optional[str]:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return normalize_name(line)
    return None


def _find_headline(text: str) -> Optional[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[1:4]:
        if "|" in line or len(line.split()) <= 6:
            return line.split("|")[0].strip()
    return None


def _find_skills_block(text: str) -> List[str]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().upper().startswith("SKILLS"):
            rest = " ".join(lines[i + 1: i + 3])
            return split_skills(rest)
    return []

def extract_resume_text(file_path: str) -> List[RawExtraction]:
    path = Path(file_path)
    text = path.read_text(encoding="utf-8", errors="ignore")

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    linkedin_match = LINKEDIN_RE.search(text)
    github_match = GITHUB_RE.search(text)

    links = None
    if linkedin_match or github_match:
        links = Link(
            linkedin=f"https://{linkedin_match.group(0)}" if linkedin_match else None,
            github=f"https://{github_match.group(0)}" if github_match else None,
        )

    extraction = RawExtraction(
        source_name=SOURCE_NAME,
        source_type="unstructured",
        method="resume_regex_heuristic",
        full_name=_find_name(text),
        emails=[e for e in [normalize_email(email_match.group(0))] if email_match and e],
        phone=normalize_phone(phone_match.group(0)) if phone_match else None,
        headline=_find_headline(text),
        skills=_find_skills_block(text),
        links=links,
        raw_text=text,
    )
    return [extraction]