from __future__ import annotations
import re
from typing import Optional, List
import phonenumbers


def normalize_phone(raw: Optional[str], default_region: str = "US") -> Optional[str]:
    if not raw:
        return None
    try:
        parsed = phonenumbers.parse(raw, default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None
    
SKILL_SYNONYMS = {
    "js": "JavaScript",
    "java script": "JavaScript",
    "javascript": "JavaScript",
    "py": "Python",
    "python": "Python",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "java": "Java",
    "spring boot": "Spring Boot",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
}

def normalize_skill(raw: str) -> str:
    key = raw.strip().lower()
    if key in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[key]
    return raw.strip().title()

def split_skills(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    parts = re.split(r"[;,]", raw)
    seen = set()
    result = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        canon = normalize_skill(p)
        if canon not in seen:
            seen.add(canon)
            result.append(canon)
    return result


def normalize_name(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    cleaned = " ".join(raw.split())
    return cleaned.title()


def normalize_email(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    cleaned = raw.strip().lower()
    if "@" not in cleaned:
        return None
    return cleaned