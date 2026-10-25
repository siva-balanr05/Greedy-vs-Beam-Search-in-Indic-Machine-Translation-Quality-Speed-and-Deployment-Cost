import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..config import settings

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table 1: Experiments summary
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_name TEXT NOT NULL,
        model_name TEXT NOT NULL,
        source_lang TEXT NOT NULL,
        target_lang TEXT NOT NULL,
        dataset_name TEXT NOT NULL,
        sample_count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL,
        environment_info TEXT
    )
    """)
    
    # Table 2: Benchmark decoding results (per beam width / greedy)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmark_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_id INTEGER NOT NULL,
        method TEXT NOT NULL,
        beam_width INTEGER NOT NULL,
        evaluated_samples INTEGER NOT NULL,
        corpus_bleu REAL,
        corpus_chrf REAL,
        total_time_seconds REAL NOT NULL,
        avg_latency_ms REAL NOT NULL,
        median_latency_ms REAL NOT NULL,
        p95_latency_ms REAL NOT NULL,
        sentences_per_second REAL NOT NULL,
        tokens_per_second REAL NOT NULL,
        peak_memory_mb REAL NOT NULL,
        errors INTEGER NOT NULL,
        FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
    )
    """)
    
    # Table 3: Sentence-level evaluation records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiment_sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experiment_id INTEGER NOT NULL,
        sentence_index INTEGER NOT NULL,
        source_text TEXT NOT NULL,
        reference_text TEXT,
        method TEXT NOT NULL,
        beam_width INTEGER NOT NULL,
        translation TEXT NOT NULL,
        latency_ms REAL NOT NULL,
        sentence_bleu REAL,
        sentence_chrf REAL,
        tokens_count INTEGER,
        FOREIGN KEY (experiment_id) REFERENCES experiments (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

def save_experiment(
    experiment_name: str,
    model_name: str,
    source_lang: str,
    target_lang: str,
    dataset_name: str,
    sample_count: int,
    metrics: List[Dict[str, Any]],
    sentence_records: List[Dict[str, Any]],
    environment_info: Optional[Dict[str, Any]] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    env_str = json.dumps(environment_info) if environment_info else None
    
    cursor.execute("""
    INSERT INTO experiments (
        experiment_name, model_name, source_lang, target_lang,
        dataset_name, sample_count, created_at, status, environment_info
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        experiment_name, model_name, source_lang, target_lang,
        dataset_name, sample_count, now, "completed", env_str
    ))
    exp_id = cursor.lastrowid
    
    for m in metrics:
        cursor.execute("""
        INSERT INTO benchmark_metrics (
            experiment_id, method, beam_width, evaluated_samples,
            corpus_bleu, corpus_chrf, total_time_seconds, avg_latency_ms,
            median_latency_ms, p95_latency_ms, sentences_per_second,
            tokens_per_second, peak_memory_mb, errors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exp_id, m["method"], m["beam_width"], m["evaluated_samples"],
            m.get("corpus_bleu"), m.get("corpus_chrf"), m["total_time_seconds"],
            m["avg_latency_ms"], m["median_latency_ms"], m["p95_latency_ms"],
            m["sentences_per_second"], m["tokens_per_second"], m["peak_memory_mb"],
            m.get("errors", 0)
        ))
        
    for s in sentence_records:
        cursor.execute("""
        INSERT INTO experiment_sentences (
            experiment_id, sentence_index, source_text, reference_text,
            method, beam_width, translation, latency_ms,
            sentence_bleu, sentence_chrf, tokens_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            exp_id, s["sentence_index"], s["source_text"], s.get("reference_text"),
            s["method"], s["beam_width"], s["translation"], s["latency_ms"],
            s.get("sentence_bleu"), s.get("sentence_chrf"), s.get("tokens_count", 0)
        ))
        
    conn.commit()
    conn.close()
    return exp_id

def list_experiments() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT e.*,
        (SELECT corpus_bleu FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'greedy' LIMIT 1) as greedy_bleu,
        (SELECT corpus_chrf FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'greedy' LIMIT 1) as greedy_chrf,
        (SELECT avg_latency_ms FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'greedy' LIMIT 1) as greedy_latency_ms,
        (SELECT corpus_bleu FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'beam' ORDER BY beam_width DESC LIMIT 1) as beam_bleu,
        (SELECT corpus_chrf FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'beam' ORDER BY beam_width DESC LIMIT 1) as beam_chrf,
        (SELECT avg_latency_ms FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'beam' ORDER BY beam_width DESC LIMIT 1) as beam_latency_ms,
        (SELECT beam_width FROM benchmark_metrics WHERE experiment_id = e.id AND method = 'beam' ORDER BY corpus_bleu DESC LIMIT 1) as best_beam_width
    FROM experiments e
    ORDER BY e.id DESC
    """)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results

def get_experiment_detail(experiment_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
    exp_row = cursor.fetchone()
    if not exp_row:
        conn.close()
        return None
        
    exp = dict(exp_row)
    cursor.execute("SELECT * FROM benchmark_metrics WHERE experiment_id = ?", (experiment_id,))
    metrics = [dict(r) for r in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM experiment_sentences WHERE experiment_id = ? ORDER BY sentence_index, beam_width", (experiment_id,))
    sentences = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "summary": exp,
        "metrics": metrics,
        "sentence_records": sentences
    }
