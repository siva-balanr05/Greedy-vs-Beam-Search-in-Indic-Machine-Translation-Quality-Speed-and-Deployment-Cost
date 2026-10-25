"""
Export Script: Dumps all recorded experiments from SQLite into CSV and JSON.
"""

import sys
import csv
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database.db import list_experiments, get_experiment_detail

def export_all():
    results_dir = Path(__file__).resolve().parent.parent / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    experiments = list_experiments()
    print(f"Found {len(experiments)} recorded experiments.")
    
    if not experiments:
        print("No experiments found to export.")
        return

    # Export index JSON
    index_path = results_dir / "experiments_summary.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(experiments, f, indent=2, ensure_ascii=False)
    print(f"Exported summary: {index_path}")
    
    # Export each experiment detail and sentence CSV
    for exp in experiments:
        exp_id = exp["id"]
        detail = get_experiment_detail(exp_id)
        if not detail:
            continue
            
        json_file = results_dir / f"experiment_{exp_id}_full.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(detail, f, indent=2, ensure_ascii=False)
            
        csv_file = results_dir / f"experiment_{exp_id}_sentences.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "sentence_index", "source_text", "reference_text",
                "method", "beam_width", "translation", "latency_ms",
                "sentence_bleu", "sentence_chrf", "tokens_count"
            ])
            for s in detail["sentence_records"]:
                writer.writerow([
                    s["sentence_index"],
                    s["source_text"],
                    s.get("reference_text", ""),
                    s["method"],
                    s["beam_width"],
                    s["translation"],
                    s["latency_ms"],
                    s.get("sentence_bleu", ""),
                    s.get("sentence_chrf", ""),
                    s.get("tokens_count", 0)
                ])
        print(f"Exported Experiment #{exp_id} -> JSON & CSV")

if __name__ == "__main__":
    export_all()
