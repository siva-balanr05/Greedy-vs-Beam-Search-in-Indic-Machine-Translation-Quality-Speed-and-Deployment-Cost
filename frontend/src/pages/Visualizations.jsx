import React, { useState, useEffect } from 'react';
import { 
  BarChart2, TrendingUp, Cpu, Clock, Activity, 
  Layers, ArrowRight, Download, Filter 
} from 'lucide-react';
import { 
  LineChart, Line, BarChart, Bar, ScatterChart, Scatter, 
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { fetchExperiments, fetchExperimentDetail } from '../services/api';

export default function Visualizations({ setActivePage }) {
  const [experiments, setExperiments] = useState([]);
  const [selectedExpId, setSelectedExpId] = useState(null);
  const [experimentDetail, setExperimentDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExperiments();
  }, []);

  async function loadExperiments() {
    try {
      setLoading(true);
      const list = await fetchExperiments();
      setExperiments(list);
      if (list.length > 0) {
        setSelectedExpId(list[0].id);
        loadDetail(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load experiments:', err);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(id) {
    try {
      const detail = await fetchExperimentDetail(id);
      setExperimentDetail(detail);
    } catch (err) {
      console.error('Failed to load detail for exp:', id, err);
    }
  }

  function handleSelectExp(e) {
    const id = Number(e.target.value);
    setSelectedExpId(id);
    loadDetail(id);
  }

  const metrics = experimentDetail?.metrics || [];

  // Prepare chart series
  const qualityData = metrics.map(m => ({
    beam: `Width ${m.beam_width}`,
    beam_width: m.beam_width,
    method: m.method,
    BLEU: m.corpus_bleu || 0,
    chrF: m.corpus_chrf || 0,
  }));

  const latencyData = metrics.map(m => ({
    beam: `Width ${m.beam_width}`,
    beam_width: m.beam_width,
    avg_latency_ms: m.avg_latency_ms,
    median_latency_ms: m.median_latency_ms,
    p95_latency_ms: m.p95_latency_ms,
  }));

  const throughputData = metrics.map(m => ({
    beam: `Width ${m.beam_width}`,
    beam_width: m.beam_width,
    sentences_per_sec: m.sentences_per_second,
    tokens_per_sec: m.tokens_per_second,
  }));

  const tradeOffData = metrics.map(m => ({
    name: `${m.method.toUpperCase()} (k=${m.beam_width})`,
    latency: m.avg_latency_ms,
    bleu: m.corpus_bleu || 0,
    beam_width: m.beam_width
  }));

  const memoryData = metrics.map(m => ({
    name: `k=${m.beam_width}`,
    peak_memory_mb: m.peak_memory_mb,
  }));

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span className="brand-badge">Comparative Analytics</span>
          <h1 className="page-title" style={{ marginTop: '0.4rem' }}>Results & Visualizations</h1>
          <p className="page-subtitle">
            Empirical trade-off curves connecting decoding beam width, translation quality metrics, throughput, and CPU memory footprint.
          </p>
        </div>

        {experiments.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Filter size={16} color="var(--text-muted)" />
            <select 
              className="form-select" 
              style={{ width: 'auto', fontWeight: 600 }}
              value={selectedExpId || ''}
              onChange={handleSelectExp}
            >
              {experiments.map(e => (
                <option key={e.id} value={e.id}>
                  Exp #{e.id} — {e.dataset_name} ({e.sample_count} samples)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {experiments.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
          <BarChart2 size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3 style={{ fontWeight: 600 }}>No Experimental Data Recorded</h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: 400, margin: '0.5rem auto' }}>
            Visualizations are plotted strictly from authentic experimental runs. Launch a benchmark in the laboratory to generate charts.
          </p>
          <button 
            className="btn btn-primary" 
            style={{ marginTop: '1.25rem' }}
            onClick={() => setActivePage('benchmark')}
          >
            Launch Benchmark Laboratory <ArrowRight size={14} />
          </button>
        </div>
      ) : (
        <div>
          {/* Chart Row 1: Quality vs Beam & Latency vs Beam */}
          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            {/* Chart 1: Quality Metrics vs Beam Width */}
            <div className="card">
              <div className="card-title">
                <span>1. Translation Quality vs Beam Width</span>
                <span className="badge badge-blue">BLEU & chrF</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Higher score indicates greater overlap with reference translations.
              </p>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={qualityData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="beam" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="BLEU" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="chrF" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Latency vs Beam Width */}
            <div className="card">
              <div className="card-title">
                <span>2. Inference Latency Scaling (ms)</span>
                <span className="badge badge-amber">Scaling Law</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Average, Median, and 95th-percentile execution latency per sentence.
              </p>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={latencyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="beam" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} unit=" ms" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="avg_latency_ms" name="Average Latency" stroke="#ef4444" strokeWidth={2} />
                    <Line type="monotone" dataKey="median_latency_ms" name="Median Latency" stroke="#f59e0b" strokeWidth={2} strokeDasharray="4 4" />
                    <Line type="monotone" dataKey="p95_latency_ms" name="95th Percentile" stroke="#8b5cf6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Chart Row 2: Throughput & Quality-Latency Trade-Off */}
          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            {/* Chart 3: Throughput */}
            <div className="card">
              <div className="card-title">
                <span>3. Throughput (Sentences / Second)</span>
                <span className="badge badge-green">Efficiency</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Sentence throughput drops as beam width expands exploration trees.
              </p>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={throughputData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="beam" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="sentences_per_sec" name="Sentences / Sec" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="tokens_per_sec" name="Tokens / Sec" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 4: Quality vs Latency Pareto Front */}
            <div className="card">
              <div className="card-title">
                <span>4. Quality vs Latency Trade-Off</span>
                <span className="badge badge-blue">Pareto Front</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                Scatter plot: Optimal frontier balances BLEU improvement vs latency cost.
              </p>
              <div style={{ height: 260 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis type="number" dataKey="latency" name="Latency (ms)" unit=" ms" tick={{ fontSize: 12 }} />
                    <YAxis type="number" dataKey="bleu" name="BLEU" domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter name="Decoding Strategy" data={tradeOffData} fill="#ec4899" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Experiment Metric Comparison Table */}
          <div className="card">
            <div className="card-title">
              <span>Detailed Metric Breakdown for Selected Experiment (#{selectedExpId})</span>
              <a 
                href={`/api/experiments/${selectedExpId}/export?format=csv`}
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                download
              >
                <Download size={14} /> Export CSV
              </a>
            </div>

            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Decoding Method</th>
                    <th>Beam Width (k)</th>
                    <th>Corpus SacreBLEU</th>
                    <th>Corpus chrF</th>
                    <th>Average Latency</th>
                    <th>Median Latency</th>
                    <th>P95 Latency</th>
                    <th>Throughput (Sent/s)</th>
                    <th>Peak RAM</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((m, idx) => (
                    <tr key={idx}>
                      <td>
                        <span className={`badge ${m.method === 'greedy' ? 'badge-blue' : 'badge-green'}`}>
                          {m.method.toUpperCase()}
                        </span>
                      </td>
                      <td><strong>{m.beam_width}</strong></td>
                      <td style={{ fontWeight: 700, color: 'var(--primary)' }}>
                        {m.corpus_bleu !== null ? m.corpus_bleu : 'N/A'}
                      </td>
                      <td style={{ fontWeight: 700 }}>
                        {m.corpus_chrf !== null ? m.corpus_chrf : 'N/A'}
                      </td>
                      <td>{m.avg_latency_ms} ms</td>
                      <td>{m.median_latency_ms} ms</td>
                      <td>{m.p95_latency_ms} ms</td>
                      <td>{m.sentences_per_second}</td>
                      <td>{m.peak_memory_mb} MB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
