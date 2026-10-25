"""
Standalone CLI Benchmark Runner.
Runs reproducible experiments comparing Greedy Search vs Beam Search (widths 1, 2, 4, 8)
on Tamil-English parallel data using the CPU inference pipeline.
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.model_service import model_service
from backend.app.services.translation_service import translation_service
from backend.app.services.evaluation_service import evaluation_service
from backend.app.services.resource_monitor import resource_monitor
from backend.app.database.db import init_db, save_experiment

def run_cli_benchmark(sample_count: int = 5, beam_widths: list = None):
    if beam_widths is None:
        beam_widths = [1, 2, 4]
        
    init_db()
    
    # 1. Load dataset
    sample_file = Path(__file__).resolve().parent.parent / "data" / "sample" / "flores200_sample.json"
    with open(sample_file, "r", encoding="utf-8") as f:
        samples = json.load(f)[:sample_count]
        
    print(f"=== Starting CLI Benchmark ({len(samples)} samples) ===")
    print(f"Model Checkpoint: {model_service.model_name}")
    print(f"Evaluating Beam Widths: {beam_widths}")
    print(f"Pre-warming model on CPU...")
    
    model_service.load_model()
    
    summaries = []
    sentence_records = []
    
    for beam in beam_widths:
        method = "greedy" if beam == 1 else "beam"
        print(f"\n--- Testing {method.upper()} (Beam width {beam}) ---")
        
        latencies = []
        tokens_list = []
        hyps = []
        refs = []
        t0 = time.perf_counter()
        
        for idx, s in enumerate(samples):
            src = s["source_text"]
            ref = s["reference_text"]
            
            inputs, lang_meta = model_service.prepare_input(src, "ta", "en")
            m = translation_service._generate_with_metrics(
                inputs=inputs,
                lang_meta=lang_meta,
                method=method,
                beam_width=beam,
                max_new_tokens=100,
                length_penalty=1.0,
                reference_text=ref
            )
            
            latencies.append(m.latency_ms)
            tokens_list.append(m.tokens_generated)
            hyps.append(m.translation)
            refs.append(ref)
            
            sentence_records.append({
                "sentence_index": idx,
                "source_text": src,
                "reference_text": ref,
                "method": method,
                "beam_width": beam,
                "translation": m.translation,
                "latency_ms": m.latency_ms,
                "sentence_bleu": m.sentence_bleu,
                "sentence_chrf": m.sentence_chrf,
                "tokens_count": m.tokens_generated
            })
            print(f"  [{idx+1}/{len(samples)}] Latency: {m.latency_ms} ms | Tokens: {m.tokens_generated}")
            
        t1 = time.perf_counter()
        total_sec = round(t1 - t0, 2)
        avg_lat = round(sum(latencies) / len(latencies), 2)
        med_lat = round(sorted(latencies)[len(latencies)//2], 2)
        p95_lat = round(sorted(latencies)[int(len(latencies)*0.95)], 2)
        sps = round(len(samples) / max(total_sec, 0.001), 2)
        tps = round(sum(tokens_list) / max(total_sec, 0.001), 2)
        peak_mem = resource_monitor.get_process_memory_mb()
        
        corpus_eval = evaluation_service.compute_corpus_metrics(hyps, refs)
        
        print(f"  Summary: Corpus BLEU = {corpus_eval['corpus_bleu']} | chrF = {corpus_eval['corpus_chrf']} | Avg Latency = {avg_lat} ms | Throughput = {sps} sent/s")
        
        summaries.append({
            "method": method,
            "beam_width": beam,
            "evaluated_samples": len(samples),
            "corpus_bleu": corpus_eval.get("corpus_bleu"),
            "corpus_chrf": corpus_eval.get("corpus_chrf"),
            "total_time_seconds": total_sec,
            "avg_latency_ms": avg_lat,
            "median_latency_ms": med_lat,
            "p95_latency_ms": p95_lat,
            "sentences_per_second": sps,
            "tokens_per_second": tps,
            "peak_memory_mb": peak_mem,
            "errors": 0
        })
        
    exp_id = save_experiment(
        experiment_name=f"CLI_Benchmark_ta-en_{int(time.time())}",
        model_name=model_service.model_name,
        source_lang="ta",
        target_lang="en",
        dataset_name="flores200_sample",
        sample_count=len(samples),
        metrics=summaries,
        sentence_records=sentence_records,
        environment_info=resource_monitor.get_system_metrics()
    )
    
    print(f"\n=== Benchmark Complete! Saved to SQLite as Experiment #{exp_id} ===")
    return exp_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Indic MT decoding benchmark")
    parser.add_argument("--samples", type=int, default=5, help="Number of sentences to evaluate")
    parser.add_argument("--beams", nargs="+", type=int, default=[1, 2, 4], help="Beam widths (e.g. 1 2 4)")
    args = parser.parse_args()
    
    run_cli_benchmark(sample_count=args.samples, beam_widths=args.beams)
