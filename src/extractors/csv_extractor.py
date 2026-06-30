from __future__ import annotations
import csv
from pathlib import Path
from typing import List

from src.schema import RawExtraction, Location
from src.normalizers import normalize_phone, normalize_name, normalize_email, split_skills, country_to_region

SOURCE_NAME = "recruiter_csv"


def _parse_location(raw: str) -> Location | None:
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",")]
    city = parts[0] if len(parts) > 0 and parts[0] else None
    region = parts[1] if len(parts) > 1 and parts[1] else None
    country = parts[2] if len(parts) > 2 and parts[2] else None
    if not (city or region or country):
        return None
    return Location(city=city, region=region, country=country)


def extract_csv(file_path: str) -> List[RawExtraction]:
    path = Path(file_path)
    results: List[RawExtraction] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                parsed_location = _parse_location(row.get("location", ""))
                phone_region = country_to_region(parsed_location.country if parsed_location else None)
                results.append(
                    RawExtraction(
                        source_name=SOURCE_NAME,
                        source_type="structured",
                        method="csv_direct_field_map",
                        full_name=normalize_name(row.get("name")),
                        emails=[e for e in [normalize_email(row.get("email"))] if e],
                        location=parsed_location,
                        skills=split_skills(row.get("skills")),
                        phone=normalize_phone(row.get("phone"), default_region=phone_region),
                        
                    )
                )
            except Exception as e:
                print(f"[warn] skipped malformed CSV row: {row} ({e})")
                continue

    return results