# 💠 TalentSync – Multi-Source Candidate Data Transformer

**One Candidate. One Profile. Multiple Sources.**

TalentSync is a Python-based data transformation pipeline that combines candidate information from multiple sources such as recruiter CSVs and resumes into a single, unified candidate profile.

The goal of the project is to resolve conflicting information, keep track of where each piece of data came from, assign confidence scores, and generate the final output in different JSON formats using a configurable schema.

---

## How the pipeline works

```
Detect
   ↓
Extract
   ↓
Normalize
   ↓
Merge (Conflict Resolution + Confidence + Provenance)
   ↓
Project to Output Schema
   ↓
Validate
```

### Extract
Each supported source has its own extractor. Regardless of whether the input is a CSV, TXT, PDF, or DOCX file, every extractor converts the data into a common intermediate format (`RawExtraction`).

### Normalize
Before merging, extracted values are cleaned and standardized.

- Phone numbers are converted to E.164 format and classified as mobile/landline.
- Skill names are mapped to a canonical form (for example, **JS → JavaScript**).
- Names and email addresses are cleaned to maintain consistency.

### Merge
Records belonging to the same candidate are grouped together (matched by email, with name used as a fallback).

- Single-value fields (like name or headline) choose the best value when conflicts occur.
- Multi-value fields (such as skills and phone numbers) are merged instead of replaced.
- When multiple sources agree on the same value, the confidence score increases.
- Every selected field records its source through provenance information.

### Project Output
The final profile can be reshaped using a JSON configuration file.

The configuration controls:

- Fields to include
- Field renaming
- Confidence/provenance visibility
- Missing value behaviour (`null`, `omit`, or `error`)

### Validation
Every stage of the pipeline uses **Pydantic** models to ensure that the generated data follows the expected schema.

---

# Setup

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

# Running from the CLI

```bash
python -m src.cli \
--csv samples/recruiters.csv \
--resume samples/resume1.txt \
--resume samples/resume2.txt \
--config config/default_config.json \
--output output/results_default.json
```

To generate a different output format, simply switch the configuration file.

```bash
python -m src.cli \
--csv samples/recruiters.csv \
--resume samples/resume1.txt \
--config config/minimal_config.json \
--output output/results_minimal.json
```

Multiple `--resume` arguments are supported (`.txt`, `.pdf`, and `.docx`).

---

# Running the UI

```bash
streamlit run app.py
```

The Streamlit interface allows you to:

- Upload recruiter CSVs
- Upload one or more resumes
- Choose an output configuration
- View merged candidate profiles
- Compare raw extracted data before merging
- Download the merged profiles as CSV
- Export the merged candidate profiles as a CSV file, while JSON remains the canonical output format 

---

# Sample Output

```json
{
  "candidate_id": "C001",
  "full_name": {
    "value": "Rohan Mehta",
    "confidence": 1.0
  },
  "phones": [
    {
      "value": {
        "number": "+918045671234",
        "type": "landline"
      },
      "confidence": 0.9
    }
  ],
  "skills": [
    {
      "name": "Python",
      "confidence": 1.0,
      "sources": [
        "recruiter_csv",
        "resume_text"
      ]
    }
  ],
  "overall_confidence": 0.9
}
```

---

# Project Structure

```
src/
│
├── schema.py
├── normalizers.py
├── merge.py
├── project_output.py
├── cli.py
│
├── extractors/
│   ├── csv_extractor.py
│   └── resume_extractors.py
│
app.py
config/
samples/
output/
```

---

# Testing

The project was tested manually across different scenarios.

- Verified phone, email, name, and skill normalization.
- Tested CSV extraction with missing fields and invalid phone numbers.
- Verified that TXT, PDF, and DOCX versions of the same resume produce consistent results.
- Confirmed that candidate records from different sources are grouped correctly.
- Tested conflict resolution between recruiter data and resume data.
- Verified skill and phone merging across multiple sources.
- Tested both output configurations (`default` and `minimal`).
- Verified the behaviour of `on_missing: "error"`.
- Ran the complete pipeline end-to-end on sample datasets.

---

# Current Limitations

- `location`, `links`, `years_experience`, `experience`, and `education` are defined in the schema but are not yet populated in the merged profile.
- Resume parsing relies on simple positional heuristics, so very unusual resume layouts may not be parsed correctly.
- Image-based PDFs are not supported yet (OCR would be required).
- Candidate IDs are generated for each run and are not persistent.
- The project is currently stateless and does not use a database.
