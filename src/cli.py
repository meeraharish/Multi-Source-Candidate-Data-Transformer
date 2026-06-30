from __future__ import annotations
import json
from pathlib import Path
import click

from src.extractors.csv_extractor import extract_csv
from src.extractors.resume_extractors import extract_resume_text
from src.merge import group_by_candidate, build_canonical_profile
from src.project_output import load_config, project_profile


@click.command()
@click.option("--csv", "csv_path", default=None, help="Path to recruiter CSV file")
@click.option("--resume", "resume_paths", multiple=True, help="Path to a resume text file (can repeat)")
@click.option("--config", "config_path", default="config/default_config.json", help="Path to output config JSON")
@click.option("--output", "output_path", default="output/results.json", help="Where to write the result JSON")
def run_pipeline(csv_path, resume_paths, config_path, output_path):
    all_records = []

    if csv_path:
        all_records.extend(extract_csv(csv_path))
        click.echo(f"Extracted {len(all_records)} record(s) from CSV: {csv_path}")

    for r_path in resume_paths:
        recs = extract_resume_text(r_path)
        all_records.extend(recs)
        click.echo(f"Extracted {len(recs)} record(s) from resume: {r_path}")

    if not all_records:
        click.echo("No input sources provided. Use --csv and/or --resume.")
        return

    groups = group_by_candidate(all_records)
    config = load_config(config_path)

    results = []
    for idx, (key, records) in enumerate(groups.items(), start=1):
        candidate_id = f"C{idx:03d}"
        profile = build_canonical_profile(candidate_id, records)
        projected = project_profile(profile, config)
        results.append(projected)
        click.echo(f"Built profile for {key} -> {candidate_id} ({len(records)} source record(s))")

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    click.echo(f"\nWrote {len(results)} candidate profile(s) to {output_path}")


if __name__ == "__main__":
    run_pipeline()