from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

from src.schema import CanonicalProfile


def load_config(config_path: str) -> Dict[str, Any]:
    with Path(config_path).open(encoding="utf-8") as f:
        return json.load(f)
    
def project_profile(profile: CanonicalProfile, config: Dict[str, Any]) -> Dict[str, Any]:
    output: Dict[str, Any] = {"candidate_id": profile.candidate_id}
    on_missing = config.get("on_missing", "null")
    include_confidence = config.get("include_confidence", True)
    include_provenance = config.get("include_provenance", True)

    for field_spec in config.get("fields", []):
        source_field = field_spec["path"]
        output_name = field_spec.get("rename", source_field)

        raw_value = getattr(profile, source_field, None)
        shaped_value = _shape_value(raw_value, include_confidence)

        if shaped_value is None:
            if on_missing == "omit":
                continue
            elif on_missing == "error":
                raise ValueError(f"Required field '{source_field}' is missing for candidate {profile.candidate_id}")
            # "null" -> fall through and include it as None

        output[output_name] = shaped_value

    if include_provenance:
        output["provenance"] = [p.model_dump() for p in profile.provenance]

    output["overall_confidence"] = profile.overall_confidence
    return output


def _shape_value(raw_value, include_confidence: bool):
    if raw_value is None:
        return None
    if isinstance(raw_value, list):
        if not raw_value:
            return None
        if hasattr(raw_value[0], "model_dump"):
            if include_confidence:
                return [item.model_dump() for item in raw_value]
            else:
                return [item.value for item in raw_value]
        return raw_value
    if hasattr(raw_value, "value"):
        if include_confidence:
            return {"value": raw_value.value, "confidence": raw_value.confidence}
        return raw_value.value
    return raw_value