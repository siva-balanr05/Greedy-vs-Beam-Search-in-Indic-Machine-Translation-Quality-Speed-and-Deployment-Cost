import React, { useState, useEffect, useRef } from 'react';
import { 
  FlaskConical, Upload, CheckSquare, Square, Play, 
  XCircle, Download, FileText, CheckCircle2, AlertCircle, RefreshCw 
} from 'lucide-react';
import { 
  fetchDatasets, postParseDataset, postStartBenchmark, 
  fetchBenchmarkStatus, postCancelBenchmark 
} from '../services/api';

export default function Benchmark({ setActivePage }) {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState('flores200_sample');
  const [uploadedSamples, setUploadedSamples] = useState(null);
  
  // Benchmark Config
  const [beamWidths, setBeamWidths] = useState([1, 2, 4, 8]);
  const [maxSamples, setMaxSamples] = useState(15);
  const [maxNewTokens, setMaxNewTokens] = useState(128);

  // Job Status
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [benchmarkCompleted, setBenchmarkCompleted] = useState(false);
  const [error, setError] = useState(null);

  // Upload UI state
  const [uploadLoading, setUploadLoading] = useState(false);
  const [sourceCol, setSourceCol] = useState('source_text');
  const [refCol, setRefCol] = useState('reference_text');
  const fileInputRef = useRef(null);
  const pollTimerRef = useRef(null);

  useEffect(() => {
    loadDatasetsList();
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  async function loadDatasetsList() {
    try {
      const data = await fetchDatasets();
      setDatasets(data);
    } catch (err) {
      console.error('Failed to load datasets:', err);
    }
  }

  // Toggle beam width selection
  function toggleBeam(width) {
    if (beamWidths.includes(width)) {
      if (beamWidths.length === 1) return; // Keep at least one
      setBeamWidths(beamWidths.filter(w => w !== width));
    } else {
      setBeamWidths([...beamWidths, width].sort((a, b) => a - b));
    }
  }

  // Handle dataset file upload
  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    setUploadLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_column', sourceCol);
    formData.append('reference_column', refCol);

    try {
      const parsed = await postParseDataset(formData);
      setUploadedSamples(parsed.samples);
      setSelectedDataset(`custom_${file.name}`);
      setMaxSamples(Math.min(parsed.samples.length, 25));
    } catch (err) {
      setError(err.message || 'Dataset parsing failed.');
    } finally {
      setUploadLoading(false);
    }
  }

  // Start benchmark run
  async function handleStartBenchmark() {
    setError(null);
    setBenchmarkCompleted(false);
    setJobStatus(null);

    const payload = {
      dataset_name: selectedDataset,
      source_lang: 'ta',
      target_lang: 'en',
      beam_widths: beamWidths,
      max_samples: maxSamples,
      max_new_tokens: maxNewTokens,
      samples: uploadedSamples || null
    };

    try {
      const res = await postStartBenchmark(payload);
      setActiveJobId(res.job_id);
      startPolling(res.job_id);
    } catch (err) {
      setError(err.message || 'Failed to start benchmark.');
    }
  }

  function startPolling(jobId) {
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);

    pollTimerRef.current = setInterval(async () => {
      try {
        const status = await fetchBenchmarkStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          clearInterval(pollTimerRef.current);
          if (status.status === 'completed') {
            setBenchmarkCompleted(true);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1500);
  }

  async function handleCancel() {
    if (!activeJobId) return;
    try {
      await postCancelBenchmark(activeJobId);
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      setJobStatus(prev => prev ? { ...prev, status: 'cancelled', current_step: 'Cancelled by user' } : null);
    } catch (err) {
      alert('Failed to cancel: ' + err.message);
    }
  }

  const isRunning = jobStatus?.status === 'running' || jobStatus?.status === 'pending';

  return (
    <div>
      <div className="page-header">
        <span className="brand-badge">Automated Evaluation Suite</span>
        <h1 className="page-title" style={{ marginTop: '0.4rem' }}>Benchmark Laboratory</h1>
        <p className="page-subtitle">
          Execute reproducible evaluations across Greedy Search and multi-width Beam Search to measure SacreBLEU, chrF, latency distributions, and memory.
        </p>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: 'var(--danger-light)', 
          color: 'var(--danger)', 
          padding: '1rem', 
          borderRadius: 'var(--radius-sm)', 
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Benchmark Setup Cards */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Dataset Selection */}
        <div className="card">
          <div className="card-title">
            <span>1. Dataset Selection</span>
            <FlaskConical size={18} color="var(--primary)" />
          </div>

          <div className="form-group">
            <label className="form-label">Available Benchmark Corpora</label>
            <select 
              className="form-select"
              value={selectedDataset}
              onChange={(e) => {
                setSelectedDataset(e.target.value);
                if (e.target.value === 'flores200_sample') {
                  setUploadedSamples(null);
                }
              }}
              disabled={isRunning}
            >
              <option value="flores200_sample">FLORES-200 Sample (Tamil-English Parallel Sentences)</option>
              {uploadedSamples && (
                <option value={selectedDataset}>Uploaded Dataset ({uploadedSamples.length} sentences)</option>
              )}
            </select>
          </div>

          {/* Upload Custom Dataset Section */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '1rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, display: 'block', marginBottom: '0.5rem' }}>
              Or Upload Custom Dataset (CSV / JSON)
            </span>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Source Column (e.g., source_text)" 
                value={sourceCol}
                onChange={(e) => setSourceCol(e.target.value)}
                style={{ fontSize: '0.8rem' }}
                disabled={isRunning}
              />
              <input 
                type="text" 
                className="form-input" 
                placeholder="Reference Column (e.g., reference_text)" 
                value={refCol}
                onChange={(e) => setRefCol(e.target.value)}
                style={{ fontSize: '0.8rem' }}
                disabled={isRunning}
              />
            </div>
            <input 
              type="file" 
              ref={fileInputRef} 
              accept=".csv,.json" 
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
            <button 
              type="button" 
              className="btn btn-secondary" 
              style={{ width: '100%', fontSize: '0.8rem' }}
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadLoading || isRunning}
            >
              <Upload size={14} />
              {uploadLoading ? 'Parsing Dataset...' : 'Upload CSV / JSON File'}
            </button>
          </div>
        </div>

        {/* Experiment Configuration */}
        <div className="card">
          <div className="card-title">
            <span>2. Decoding Strategies to Compare</span>
            <CheckSquare size={18} color="var(--primary)" />
          </div>

          <div className="form-group">
            <label className="form-label">Beam Widths</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem', marginTop: '0.5rem' }}>
              {[
                { width: 1, label: 'Greedy Search (Beam = 1)' },
                { width: 2, label: 'Beam Search (k = 2)' },
                { width: 4, label: 'Beam Search (k = 4)' },
                { width: 8, label: 'Beam Search (k = 8)' },
              ].map(({ width, label }) => {
                const selected = beamWidths.includes(width);
                return (
                  <div 
                    key={width}
                    onClick={() => !isRunning && toggleBeam(width)}
                    style={{
                      border: `1px solid ${selected ? 'var(--primary)' : 'var(--border)'}`,
                      backgroundColor: selected ? 'var(--primary-light)' : 'var(--bg-card)',
                      padding: '0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      cursor: isRunning ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      fontSize: '0.85rem',
                      fontWeight: selected ? 600 : 400
                    }}
                  >
                    {selected ? <CheckSquare size={16} color="var(--primary)" /> : <Square size={16} color="var(--text-muted)" />}
                    <span>{label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid-2" style={{ marginTop: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Sample Count Limit</label>
              <input 
                type="number" 
                className="form-input" 
                min={1} 
                max={100}
                value={maxSamples}
                onChange={(e) => setMaxSamples(Number(e.target.value))}
                disabled={isRunning}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Use 5-15 for quick test, 25-50 for deeper evaluation</span>
            </div>

            <div className="form-group">
              <label className="form-label">Max Tokens / Sentence</label>
              <input 
                type="number" 
                className="form-input" 
                min={32} 
                max={256}
                value={maxNewTokens}
                onChange={(e) => setMaxNewTokens(Number(e.target.value))}
                disabled={isRunning}
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button 
              className="btn btn-primary" 
              style={{ flex: 1 }}
              onClick={handleStartBenchmark}
              disabled={isRunning}
            >
              <Play size={16} />
              {isRunning ? 'Benchmark Running...' : 'Launch Benchmark'}
            </button>
            {isRunning && (
              <button className="btn btn-danger" onClick={handleCancel}>
                <XCircle size={16} /> Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live Benchmark Execution Status */}
      {jobStatus && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontWeight: 700, fontSize: '1rem' }}>
                Job ID: #{jobStatus.job_id} ({jobStatus.status.toUpperCase()})
              </span>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {jobStatus.current_step}
              </p>
            </div>
            <span className="badge badge-blue">
              {jobStatus.completed_steps} / {jobStatus.total_steps} Steps ({jobStatus.progress_percent}%)
            </span>
          </div>

          <div className="progress-bar-container">
            <div 
              className="progress-bar-fill" 
              style={{ width: `${jobStatus.progress_percent}%` }}
            />
          </div>

          {jobStatus.status === 'completed' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
              <CheckCircle2 size={16} />
              <span>Experiment completed and persisted into SQLite database.</span>
            </div>
          )}
        </div>
      )}

      {/* Benchmark Results Table */}
      {jobStatus?.results && (
        <div className="card">
          <div className="card-title">
            <span>Benchmark Experimental Results</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button 
                className="btn btn-secondary" 
                style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}
                onClick={() => setActivePage('visualizations')}
              >
                View Detailed Charts
              </button>
            </div>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Beam Width</th>
                  <th>Corpus SacreBLEU</th>
                  <th>Corpus chrF</th>
                  <th>Avg Latency</th>
                  <th>Median Latency</th>
                  <th>P95 Latency</th>
                  <th>Sentences / Sec</th>
                  <th>Tokens / Sec</th>
                  <th>Peak Memory</th>
                </tr>
              </thead>
              <tbody>
                {jobStatus.results.map((r, idx) => (
                  <tr key={idx}>
                    <td>
                      <span className={`badge ${r.method === 'greedy' ? 'badge-blue' : 'badge-green'}`}>
                        {r.method.toUpperCase()}
                      </span>
                    </td>
                    <td><strong>{r.beam_width}</strong></td>
                    <td style={{ fontWeight: 700, color: 'var(--primary)' }}>
                      {r.corpus_bleu !== null ? r.corpus_bleu : 'N/A'}
                    </td>
                    <td style={{ fontWeight: 700 }}>
                      {r.corpus_chrf !== null ? r.corpus_chrf : 'N/A'}
                    </td>
                    <td>{r.avg_latency_ms} ms</td>
                    <td>{r.median_latency_ms} ms</td>
                    <td>{r.p95_latency_ms} ms</td>
                    <td>{r.sentences_per_second}</td>
                    <td>{r.tokens_per_second}</td>
                    <td>{r.peak_memory_mb} MB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
            <strong>Metric Definitions:</strong> Corpus BLEU and chrF are calculated across all reference pairs using SacreBLEU. Latencies record pure PyTorch inference time via high-resolution timers. Peak memory represents highest observed Python process RSS.
          </div>
        </div>
      )}
    </div>
  );
}
