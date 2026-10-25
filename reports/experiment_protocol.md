# Empirical Evaluation Protocol: Greedy vs Beam Search in Indic Machine Translation

## 1. Objective and Research Scope
This experimental protocol establishes a rigorous, reproducible methodology for comparing **Greedy Search** ($num\_beams = 1$) against **Beam Search** ($num\_beams \in \{2, 4, 8\}$) in Neural Machine Translation (NMT) for Indic languages, focusing primarily on the **Tamil $\rightarrow$ English** direction on commodity CPU hardware.

---

## 2. Hardware and Environment Baseline
To simulate accessible academic and low-cost enterprise deployments without dedicated GPU accelerators:
- **Processor:** Intel Core CPU (Multi-core x86_64, AVX2 enabled)
- **Memory:** 16 GB DDR4/DDR5 System RAM
- **Operating System:** Windows 10/11 / Ubuntu 22.04 LTS
- **PyTorch Device:** `cpu` (`torch.device("cpu")`)
- **Float Precision:** FP32 (Single Precision IEEE 754)
- **High-Resolution Timer:** Python `time.perf_counter()` (microsecond accuracy)
- **Process Memory Profiling:** `psutil.Process().memory_info().rss` (Resident Set Size in MB)

---

## 3. Pretrained Model and Tokenization Strategy
- **Selected Model:** `prajdabre/rotary-indictrans2-indic-en-dist-200M`
  - *Architecture:* Sequence-to-Sequence Transformer with Rotary Positional Embeddings (RoPE).
  - *Parameters:* 200 Million distilled parameters.
  - *Weights Footprint:* ~800 MB on disk, ~550 MB resident memory footprint on CPU.
  - *Tokenizer:* Subword SentencePiece BPE vocabulary with unified Indic source and English target vocabularies.
  - *Input Prefix Protocol:* Every source sentence is formatted with explicit source and target language tags: `f"{src_lang_code} {tgt_lang_code} {source_sentence}"` (e.g., `tam_Taml eng_Latn <text>`).
  - *Target Decoding:* `tokenizer.batch_decode(..., src=False, skip_special_tokens=True)`.

---

## 4. Controlled Decoding Configurations
For scientific fairness, **all generation parameters other than beam width are held constant**:

| Parameter | Greedy Search | Beam Search (k=2) | Beam Search (k=4) | Beam Search (k=8) |
| :--- | :--- | :--- | :--- | :--- |
| `num_beams` | **1** | **2** | **4** | **8** |
| `do_sample` | `False` (deterministic) | `False` (deterministic) | `False` (deterministic) | `False` (deterministic) |
| `max_new_tokens` | 128 | 128 | 128 | 128 |
| `length_penalty` | 1.0 | 1.0 | 1.0 | 1.0 |
| `early_stopping` | N/A | `True` | `True` | `True` |
| `use_cache` | `False` | `False` | `False` | `False` |

---

## 5. Evaluation Metrics

### 5.1 Quality Metrics
1. **Corpus SacreBLEU:** Standardized geometric mean of modified n-gram precisions (1-gram through 4-gram) combined with an exponential brevity penalty:
   $$\text{BLEU} = \text{BP} \cdot \exp\left(\sum_{n=1}^{4} w_n \log p_n\right)$$
2. **Corpus chrF:** Character n-gram F-score (beta=2), capturing morphological nuances and agglutinative forms in Indic syntax:
   $$\text{chrF}\beta = (1 + \beta^2) \frac{\text{chrP} \cdot \text{chrR}}{\beta^2 \cdot \text{chrP} + \text{chrR}}$$

### 5.2 Latency and Throughput Metrics
1. **Warm Latency ($t_{infer}$):** Pure token generation duration measured via `time.perf_counter()`, excluding cold model initialization.
2. **Average Latency ($\mu_{lat}$):** Arithmetic mean of per-sentence latencies in milliseconds.
3. **Median Latency ($\tilde{x}_{lat}$):** 50th percentile latency resistant to outliers.
4. **95th Percentile Latency ($P_{95}$):** Tail latency reflecting worst-case response times.
5. **Sentence Throughput ($SPS$):** $SPS = \frac{N_{\text{evaluated}}}{t_{\text{total}}}$.
6. **Token Throughput ($TPS$):** $TPS = \frac{N_{\text{tokens}}}{t_{\text{total}}}$.

### 5.3 System Metrics
1. **Peak Resident Set Size ($\text{RSS}_{\text{peak}}$):** Maximum physical memory held by the process during inference.
2. **Memory Delta ($\Delta \text{RAM}$):** $\text{RSS}_{\text{after}} - \text{RSS}_{\text{before}}$.

---

## 6. Execution Steps
1. **Environment Verification:** Verify Python 3.11+, PyTorch CPU, and dependency integrity.
2. **Database Initialization:** Ensure SQLite table schemas (`experiments`, `benchmark_metrics`, `experiment_sentences`) are generated.
3. **Pre-warm Model:** Execute a one-sentence warm-up forward pass to prime Python imports and memory allocators.
4. **Evaluate Parallel Corpus:** Iterate sequentially over evaluation sentences, recording exact timestamps, outputs, and token counts.
5. **Compute Corpus Statistics:** Evaluate SacreBLEU and chrF across all hypotheses and references.
6. **Persist and Audit:** Commit summary metrics and sentence-level traces into SQLite and export to CSV/JSON.
