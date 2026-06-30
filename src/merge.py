from __future__ import annotations
from typing import List, Dict
from collections import defaultdict

from src.schema import RawExtraction


def group_by_candidate(extractions: List[RawExtraction]) -> Dict[str, List[RawExtraction]]:
    groups: Dict[str, List[RawExtraction]] = defaultdict(list)
    for ext in extractions:
        key = _candidate_key(ext)
        groups[key].append(ext)
    return groups


def _candidate_key(ext: RawExtraction) -> str:
    if ext.emails:
        return ext.emails[0].lower()
    if ext.full_name:
        return ext.full_name.lower()
    return f"unknown_{id(ext)}"

SOURCE_PRIORITY = {
    "structured": 2,
    "unstructured": 1,
}


def pick_best_value(extractions: List[RawExtraction], field_name: str):
    candidates = []
    for ext in extractions:
        value = getattr(ext, field_name, None)
        if value:
            candidates.append((value, ext.source_name, ext.source_type, ext.method))

    if not candidates:
        return None, None, None, None, 0.0

    candidates.sort(key=lambda c: SOURCE_PRIORITY.get(c[2], 0), reverse=True)
    best_value, best_source, best_type, best_method = candidates[0]

    num_sources = len(candidates)
    num_agree = sum(1 for c in candidates if c[0] == best_value)
    confidence = min(1.0, 0.5 + 0.2 * num_agree + (0.1 if best_type == "structured" else 0))

    reason = None
    if num_sources > 1 and num_agree < num_sources:
        reason = f"preferred_{best_type}_source_over_conflicting_alternatives"

    return best_value, best_source, best_method, reason, round(confidence, 2)

def merge_skills(extractions: List[RawExtraction]):
    skill_sources: Dict[str, List[str]] = defaultdict(list)
    for ext in extractions:
        for skill in ext.skills:
            skill_sources[skill].append(ext.source_name)

    merged = []
    for skill, sources in skill_sources.items():
        confidence = min(1.0, 0.5 + 0.25 * len(set(sources)))
        merged.append({"name": skill, "confidence": round(confidence, 2), "sources": list(set(sources))})
    return merged