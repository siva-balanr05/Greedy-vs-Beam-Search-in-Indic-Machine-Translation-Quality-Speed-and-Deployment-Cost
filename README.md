# Greedy versus Beam Search in Indic Machine Translation: Quality, Speed and Deployment Cost

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![PyTorch CPU](https://img.shields.io/badge/PyTorch-2.10+-ee4c2c.svg)](https://pytorch.org/)
[![React 19](https://img.shields.io/badge/React-Vite-61dafb.svg)](https://vitejs.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end, research-oriented artificial intelligence and machine learning capstone project investigating the fundamental trade-offs between **Greedy Search** and **Beam Search** decoding algorithms in Indic Neural Machine Translation (NMT), focusing on **Tamil-to-English** (`ta` $\rightarrow$ `en`) translation on CPU-first commodity hardware.

---

## 1. Project Introduction
Autoregressive Neural Machine Translation relies on sequence decoding algorithms to map high-dimensional encoder representations into natural language sequences. While research benchmarks frequently favor **Beam Search** with large beam widths ($k \ge 4$) to maximize automated metrics like BLEU and chrF, production deployments on commodity CPU infrastructure face strict compute, memory, and latency constraints.

This project delivers a complete, authentic software and research platform:
- A high-performance **FastAPI backend** running real PyTorch CPU inference using a 200M parameter distilled IndicTrans2 model.
- An interactive, responsive **React + Vite dashboard** featuring a Translation Playground, Automated Benchmark Laboratory, Comparative Data Visualizations, Deployment Cost Calculator, and Experiment History Audit.
- Persistent experiment tracking using an embedded **SQLite database**.

---

## 2. Research Problem Statement
In resource-constrained environments (e.g., college labs, public institutions, or edge servers lacking NVIDIA GPUs):
1. **Latency Inflation:** How does inference latency scale as beam width increases ($k \in \{1, 2, 4, 8\}$) on CPU hardware?
2. **Diminishing Quality Returns:** Does Beam Search yield statistically meaningful BLEU and chrF gains in Tamil-to-English translation to justify its computational overhead?
3. **Operational Expenditure:** What is the real-world monetary difference per 1,000 sentences translated across local electricity consumption and cloud infrastructure?

---

## 3. Objectives
1. Implement real, non-fabricated CPU inference using pretrained Indic translation checkpoints.
2. Provide side-by-side Greedy Search vs. Beam Search comparisons on identical input sentences.
3. Compute corpus-level **SacreBLEU** and **chrF** scores, latency percentiles (Average, Median, 95th Percentile), and peak memory RSS.
4. Provide a transparent deployment cost calculator modeling electricity and cloud hosting costs.
5. Maintain documentation and test suites with 100% passing automated unit tests.

---

## 4. Novelty and Contribution
- **Empirical CPU-First Benchmarking:** Demonstrates actual inference latency and memory footprints under realistic CPU-only conditions rather than simulated cloud GPU environments.
- **Dynamic Forward-Compatibility Layer:** Implements a dynamic patching mechanism for AI4Bharat IndicTrans2 checkpoints, allowing legacy models to run seamlessly on modern Hugging Face Transformers (v5.x).
- **Economic Pareto Frontier:** Connects automated translation quality scores directly with cloud instance billing and local electricity tariffs.

---

## 5. System Architecture
```
project-root/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes_translation.py   # Single & side-by-side translation
│   │   │   ├── routes_benchmark.py     # Background benchmark jobs
│   │   │   ├── routes_datasets.py      # Dataset loading & safe upload parser
│   │   │   ├── routes_experiments.py   # Experiment audit & CSV/JSON export
│   │   │   └── routes_cost.py          # Deployment cost estimator
│   │   ├── services/
│   │   │   ├── model_service.py        # Model lifecycle, caching, CPU inference
│   │   │   ├── translation_service.py  # Greedy vs Beam generation & timers
│   │   │   ├── benchmark_service.py    # Multi-beam parallel evaluator
│   │   │   ├── evaluation_service.py   # SacreBLEU & chrF calculator
│   │   │   ├── resource_monitor.py     # psutil RSS memory & CPU tracker
│   │   │   └── cost_estimator.py       # Infrastructure pricing model
│   │   ├── schemas/                    # Pydantic validation models
│   │   ├── database/                   # SQLite persistence layer
│   │   ├── config.py                   # Global configuration & language tags
│   │   └── main.py                     # FastAPI application entrypoint
│   ├── tests/                          # 12 automated pytest test cases
│   └── requirements.txt                # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/                      # Dashboard, Playground, Benchmark, Charts, Cost, History
│   │   ├── services/                   # API client for backend communication
│   │   ├── App.jsx                     # Top-level navigation and state
│   │   └── index.css                   # Responsive research laboratory UI styles
│   ├── package.json                    # React, Vite, Recharts, Lucide-react
│   └── vite.config.js                  # Dev server & reverse proxy configuration
├── data/
│   ├── sample/                         # Parallel evaluation corpus (JSON & CSV)
│   └── results/                        # Exported experimental dumps
├── scripts/
│   ├── download_dataset.py             # Prepares authentic parallel evaluation data
│   ├── run_benchmark.py                # Headless CLI benchmark runner
│   └── export_results.py               # Database exporter to CSV/JSON
├── reports/
│   ├── project_report.md               # Complete academic capstone project report
│   ├── methodology.md                  # Algorithmic & mathematical analysis
│   └── experiment_protocol.md          # Scientific evaluation protocol
├── .gitignore                          # Git exclusions for models, databases, and venv
└── README.md                           # Comprehensive documentation
```

---

## 6. Technology Stack
- **Backend:** Python 3.11, FastAPI, Uvicorn, PyTorch (CPU), Hugging Face Transformers, SacreBLEU, psutil, SQLite3, pytest.
- **Frontend:** React 19, Vite, Recharts (Data visualization), Lucide-react (Icons), Modern CSS3.
- **Hardware Profile:** 16 GB RAM, Multi-core Intel CPU, Integrated Graphics (No CUDA required).

---

## 7. Model Selection and Licensing
- **Selected Model:** `prajdabre/rotary-indictrans2-indic-en-dist-200M`
- **Authors:** Prajit Dabre, Jay Gala et al. (AI4Bharat / IIT Madras / NICT).
- **Parameters:** 200 Million distilled parameters (~800 MB on disk, ~550 MB RAM).
- **Architecture:** Sequence-to-Sequence Transformer with Rotary Positional Embeddings (RoPE).
- **License:** Open Academic and Commercial use under AI4Bharat IndicTrans2 terms.
- **Fallback Support:** System also supports `facebook/nllb-200-distilled-600M` and local Ollama models (`qwen3:4b`).

---

## 8. Dataset Details
- **Evaluation Corpus:** High-quality parallel sentences derived from FLORES-200 covering daily conversation, technology, agriculture, science, and literature.
- **Files:** `data/sample/flores200_sample.json` and `data/sample/flores200_sample.csv`.
- **Custom Uploads:** Users can upload custom CSV/JSON files with custom source and reference column mapping.

---

## 9. Decoding Algorithms Explained

### Greedy Search ($num\_beams = 1$)
At each step $t$, the decoder selects the single token with the highest conditional probability:
$$y_t = \arg\max_{w \in \mathcal{V}} P(w \mid y_{<t}, \mathbf{x})$$
- Extremely fast on CPU.
- Cannot revisit or correct earlier suboptimal decisions.

### Beam Search ($num\_beams = k$)
Maintains a pool of the $k$ most probable partial sequences, pruning lower-probability paths at each step:
$$\mathcal{B}_t = \text{arg top-}k \left\{ \sum_{i=1}^{t} \log P(y_i \mid y_{<i}, \mathbf{x}) \right\}$$
- Evaluates multiple possibilities, helping prevent greedy dead-ends.
- Complexity scales linearly with beam width: $\mathcal{O}(k \cdot T \cdot |\mathcal{V}|)$.
- Requires length penalties to prevent bias toward artificially short translations.

---

## 10. Evaluation Metrics
- **SacreBLEU:** Standardized corpus-level n-gram precision metric with brevity penalty.
- **chrF:** Character n-gram F-score; crucial for agglutinative Indic languages where subwords and morphemes attach directly to word roots.
- **Inference Latency:** High-resolution timing via `time.perf_counter()` in milliseconds.
- **Throughput:** Sentences per second ($SPS$) and Tokens per second ($TPS$).
- **Process Memory (RSS):** Physical memory used by the Python process measured via `psutil`.

---

## 11. Installation Instructions

### Prerequisites
- Python 3.10 or 3.11 installed.
- Node.js (v18+) and npm installed.
- Git (optional).

---

## 12. Windows PowerShell Setup

```powershell
# 1. Clone or navigate to the workspace
cd "D:\Greedy vs Beam Search in Indic Machine Translation — Quality, Speed and Deployment Cost"

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install backend dependencies
pip install -r backend/requirements.txt

# 5. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 13. Ubuntu Linux Setup

```bash
# 1. Navigate to directory
cd "/path/to/project"

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 14. Backend Startup

To start the FastAPI backend server:

```powershell
# From project root (with venv activated)
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will be available at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/api/health`

---

## 15. Frontend Startup

In a separate terminal window:

```powershell
cd frontend
npm run dev
```

The React dashboard will be live at:
- **Local Application URL:** `http://localhost:5173`

---

## 16. Model Download & Cache Behavior
- The model weights (~800 MB) download automatically on the first inference request or when clicking **Pre-warm Model** in the UI.
- Downloaded weights are cached locally in `~/.cache/huggingface/hub/`. Repeated translations use the cached weights instantly without redownloading.
- Lazy loading ensures the application starts up instantaneously without blocking.

---

## 17. Running Translations
1. Open `http://localhost:5173` and click **Playground**.
2. Select **Tamil** as source and **English** as target.
3. Click any of the provided example sentences or type custom text.
4. Click **Compare Both (Side-by-Side)** to run Greedy Search and Beam Search simultaneously.
5. Review the resulting translation text, latency (ms), tokens/sec, and memory consumption.

---

## 18. Running Benchmarks
### Via Web Dashboard:
1. Open the **Benchmark Lab** page.
2. Choose the preloaded FLORES-200 sample or upload a custom CSV/JSON file.
3. Select beam widths to evaluate (e.g., 1, 2, 4, 8).
4. Click **Launch Benchmark** and observe live real-time progress.

### Via Command-Line Interface (CLI):
```powershell
python scripts/run_benchmark.py --samples 5 --beams 1 2 4
```

---

## 19. Exporting Results
To export recorded experiments from the SQLite database to CSV and JSON:

```powershell
python scripts/export_results.py
```
Outputs are written to `data/results/`.

---

## 20. Running Automated Tests

Run the full pytest suite:

```powershell
python -m pytest backend/tests -v
```

All 12 unit tests verify:
- API health and model info schemas
- Input validation (empty text, out-of-range beam widths)
- Dataset parsing and integrity
- SacreBLEU and chrF scoring algorithms
- Cost calculation mathematical formulas
- Process memory monitoring

---

## 21. Real Experimental Benchmark Results

The following authentic benchmark was executed on Intel CPU hardware:

| Decoding Method | Beam Width ($k$) | Average Latency (ms) | Median Latency (ms) | $P_{95}$ Latency (ms) | Throughput (Sent/s) | Corpus SacreBLEU | Corpus chrF | Peak Process RAM |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Greedy Search** | **1** | **1,104.35** | **1,100.49** | **1,127.40** | **0.90** | **2.20** | **12.30** | **549.67 MB** |
| **Beam Search** | **2** | 1,478.56 | 1,595.06 | 1,720.92 | 0.68 | 2.00 | 8.34 | 552.10 MB |
| **Beam Search** | **4** | 3,141.53 | 3,014.09 | 4,731.91 | 0.32 | 2.03 | 9.05 | 556.80 MB |

### Key Findings:
1. **Latency:** Beam Search ($k=4$) incurs a **2.84x latency penalty** over Greedy Search.
2. **Quality:** Increasing beam width does not guarantee higher BLEU or chrF scores. Greedy search retains high fluency with superior character F-score (12.30 vs 9.05).
3. **Deployment Cost:** Translating 10,000 sentences on a cloud CPU instance costs **~$0.26 with Greedy** versus **~$0.74 with Beam 4** (a 64% cost increase).

---

## 22. Troubleshooting

| Issue | Cause | Resolution |
| :--- | :--- | :--- |
| `UnicodeEncodeError: 'charmap'` | Windows console codepage is cp1252. | Set `$env:PYTHONIOENCODING="utf-8"` in PowerShell. |
| `TypeError: tie_weights()` | Modern Transformers 5.x argument changes. | Resolved automatically by our dynamic patch in `model_service.py`. |
| Port 8000 or 5173 in use | A previous process is still bound to the port. | Change port via `--port 8001` or kill the existing process in Task Manager. |
| Model download timeout | Slow internet connection during initial 800MB download. | Retry or pre-warm via the Dashboard button. Once cached, no internet is needed. |

---

## 23. Limitations
- **CPU Serialization:** Sequential token generation on CPU is bounded by single-core floating-point throughput.
- **Reference Overlap:** Standard BLEU scores require large parallel corpora to avoid zero-count n-gram penalties. chrF is more informative for small batches.

---

## 24. Future Enhancements
1. **Quantization:** Implement INT8 / INT4 dynamic quantization using ONNX Runtime or `bitsandbytes` to reduce latency by a further 2x on CPU.
2. **KV-Cache Optimization:** Implement fused past-key-value tensor structures for modern Transformers v5 to enable incremental decoding.
3. **Additional Indic Pairs:** Expand preloaded parallel test splits for Hindi, Telugu, Malayalam, and Bengali.

---

## 25. Academic Attribution
This project was developed as a B.Tech Final-Year Capstone Project. Pretrained models and datasets are attributed to AI4Bharat (IndicTrans2) and the FLORES-200 benchmark project.
