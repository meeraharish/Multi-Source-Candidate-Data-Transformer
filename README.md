# TalentSync — Multi-Source Candidate Data Transformer

One Candidate. One Profile. Multiple Sources.

Ingests candidate data from multiple structured and unstructured sources, merges it into one canonical profile per candidate with confidence scoring and provenance, and outputs JSON reshaped according to a runtime config.

## Pipeline

```
detect → extract → normalize → merge (conflict resolution + confidence/provenance) → project to output schema → validate
```

- **Extract** — one extractor per source type, each emits a `RawExtraction` in a shared intermediate shape.
- **Normalize** — phones → E.164 + type (mobile/landline), skills → canonical names via synonym map, names/emails cleaned.
- **Merge** — records for the same person (matched by email, fallback to name) are combined. Single-value fields prefer structured sources on conflict, with the reason recorded. List fields (skills, phones) are unioned across sources, with confidence boosted when sources agree.
- **Project to output schema** — config controls field selection, renaming, confidence/provenance toggles, and missing-value policy (`null` / `omit` / `error`).
- **Validate** — every stage is a Pydantic model, so malformed shapes are rejected automatically.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run via CLI

```bash
python -m src.cli --csv samples/recruiters.csv --resume samples/resume1.txt --resume samples/resume2.txt --config config/default_config.json --output output/results_default.json
```

Same data, different shape — no code changes:

```bash
python -m src.cli --csv samples/recruiters.csv --resume samples/resume1.txt --config config/minimal_config.json --output output/results_minimal.json
```

`--resume` can repeat, and accepts `.txt`, `.pdf`, `.docx`.

## Run the UI

```bash
streamlit run app.py
```

Upload a CSV and resumes, pick a config, run. Each candidate shows as a card with a raw-source diff view for multi-source candidates, plus a CSV export button (JSON remains the canonical output format).

## Example output

```json
{
  "candidate_id": "C001",
  "full_name": { "value": "Rohan Mehta", "confidence": 1.0 },
  "phones": [
    { "value": { "number": "+918045671234", "type": "landline" }, "confidence": 0.9 },
    { "value": { "number": "+919876511223", "type": "mobile" }, "confidence": 0.75 }
  ],
  "skills": [
    { "name": "Python", "confidence": 1.0, "sources": ["recruiter_csv", "resume_text"] }
  ],
  "provenance": [
    { "field": "full_name", "source": "recruiter_csv", "method": "csv_direct_field_map", "reason": null }
  ],
  "overall_confidence": 0.9
}
```

## Project structure

```
src/
  schema.py              # canonical Pydantic models
  normalizers.py          # phone/email/name/skill normalization
  extractors/
    csv_extractor.py
    resume_extractors.py  # .txt / .pdf / .docx
  merge.py                 # grouping, conflict resolution, skill/phone unioning
  project_output.py        # config-driven output projection
  cli.py
app.py                     # Streamlit UI
config/                    # default_config.json, minimal_config.json
samples/                   # sample CSV + resumes
output/                    # generated results
```

## Testing performed (manual, no automated suite)

- Normalizers tested in isolation: phone formatting/validity, email cleanup, skill canonicalization, name cleanup.
- CSV extractor: correct parsing + graceful handling of missing email, missing location, invalid phone.
- Resume extractor: identical results across `.txt`, `.pdf`, `.docx` for the same resume.
- Candidate grouping: same person across sources correctly merged (email match, name fallback).
- Conflict resolution: verified on a real two-source phone conflict — structured source wins, reason recorded.
- Skill/phone unioning: agreement across sources raises confidence; spelling variants ("JS"/"JavaScript") correctly merge as one skill.
- Output projection: same profile, two configs (`default` vs `minimal`) produce structurally different output.
- `on_missing: "error"`: confirmed it raises a clear error for an unpopulated required field.
- Full pipeline: end-to-end CLI run across all sample candidates (multi-source, single-source, missing-data cases) with no errors.

## Known limitations

- `location`, `links`, `years_experience`, `experience`, `education` are schema-defined but not yet populated in the merged profile — same union pattern used for skills/phones would extend naturally.
- Resume parsing uses positional heuristics (first line = name, etc.) — works for standard layouts, not unusual ones.
- PDF extraction handles text-based resumes; scanned/image PDFs would need OCR.
- `candidate_id` is assigned by run order, not a stable persisted ID.
- No database — stateless by design for this scope; a real system would likely use a document store (e.g. MongoDB) given the nested record shape.