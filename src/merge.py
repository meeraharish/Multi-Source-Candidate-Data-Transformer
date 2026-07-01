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

def merge_phones(extractions: List[RawExtraction]):
    phone_sources: Dict[str, List[str]] = defaultdict(list)
    phone_types: Dict[str, str] = {}

    for ext in extractions:
        if ext.phone:
            number = ext.phone["number"]
            phone_sources[number].append(ext.source_name)
            phone_types[number] = ext.phone["type"]

    merged = []
    for number, sources in phone_sources.items():
        unique_sources = list(set(sources))
        confidence = min(1.0, 0.5 + 0.25 * len(unique_sources))
        if any(s == "recruiter_csv" for s in unique_sources):
            confidence = min(1.0, confidence + 0.1)
        merged.append(FieldValue(
            value={"number": number, "type": phone_types[number]},
            confidence=round(confidence, 2),
            sources=unique_sources,
        ))
    return merged

from src.schema import CanonicalProfile, FieldValue, Provenance, SkillEntry


def build_canonical_profile(candidate_id: str, extractions: List[RawExtraction]) -> CanonicalProfile:
    provenance_list = []

    def make_field_value(field_name: str) -> FieldValue | None:
        value, source, method, reason, confidence = pick_best_value(extractions, field_name)
        if value is None:
            return None
        provenance_list.append(Provenance(field=field_name, source=source, method=method, reason=reason))
        return FieldValue(value=value, confidence=confidence, sources=[source])

    skills_merged = merge_skills(extractions)
    phones_merged = merge_phones(extractions)
    all_emails = list({e for ext in extractions for e in ext.emails})

    profile = CanonicalProfile(
        candidate_id=candidate_id,
        full_name=make_field_value("full_name"),
        phones=phones_merged,
        headline=make_field_value("headline"),
        emails=all_emails,
        skills=[SkillEntry(**s) for s in skills_merged],
        provenance=provenance_list,
    )

    
    confidences = [profile.full_name.confidence if profile.full_name else 0]
    confidences += [p.confidence for p in profile.phones] if profile.phones else [0]
    profile.overall_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    return profile