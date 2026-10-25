import React, { useEffect, useState } from 'react';
import { 
  Cpu, HardDrive, Zap, BarChart2, CheckCircle2, 
  ArrowRight, Activity, Clock, ShieldCheck, Database
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { fetchHealth, fetchModelInfo, fetchExperiments, postLoadModel } from '../services/api';

export default function Dashboard({ setActivePage }) {
  const [health, setHealth] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [warming, setWarming] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    try {
      setLoading(true);
      const [h, m, exps] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchModelInfo().catch(() => null),
        fetchExperiments().catch(() => [])
      ]);
      setHealth(h);
      setModelInfo(m);
      setExperiments(exps);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handlePreWarm() {
    try {
      setWarming(true);
      await postLoadModel();
      await loadDashboardData();
    } catch (err) {
      alert('Failed to pre-warm model: ' + err.message);
    } finally {
      setWarming(false);
    }
  }

  // Find latest completed experiment for dashboard charts
  const latestExp = experiments.length > 0 ? experiments[0] : null;

  const chartData = latestExp ? [
    {
      metric: 'BLEU Score',
      Greedy: latestExp.greedy_bleu || 0,
      'Beam Search': latestExp.beam_bleu || 0,
    },
    {
      metric: 'chrF Score',
      Greedy: latestExp.greedy_chrf || 0,
      'Beam Search': latestExp.beam_chrf || 0,
    }
  ] : [];

  return (
    <div>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span className="brand-badge">Academic Research Dashboard</span>
          <h1 className="page-title" style={{ marginTop: '0.4rem' }}>
            Greedy vs Beam Search in Indic Machine Translation
          </h1>
          <p className="page-subtitle">
            Rigorous empirical comparison of translation quality (BLEU, chrF), inference latency, and deployment cost on CPU hardware.
          </p>
        </div>
        {!modelInfo?.loaded && (
          <button 
            className="btn btn-primary" 
            onClick={handlePreWarm} 
            disabled={warming}
            style={{ whiteSpace: 'nowrap' }}
          >
            <Zap size={16} />
            {warming ? 'Pre-warming Model...' : 'Pre-warm Model'}
          </button>
        )}
      </div>

      {/* Model & System Cards */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
            <Cpu size={16} /> MODEL STATUS
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className={`status-dot ${modelInfo?.loaded ? '' : 'idle'}`} />
            {modelInfo?.loaded ? 'Loaded (In Memory)' : 'Lazy Loaded'}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {modelInfo?.model_name || 'IndicTrans2 200M Distilled'}
          </p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
            <Activity size={16} /> PROCESS MEMORY (RSS)
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {modelInfo?.memory_rss_mb ? `${modelInfo.memory_rss_mb} MB` : '0.0 MB'}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            System RAM: {health?.system_ram_gb || 16} GB (Device: {health?.device?.toUpperCase() || 'CPU'})
          </p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
            <Database size={16} /> RECORDED BENCHMARKS
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {experiments.length}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            Stored in local SQLite database
          </p>
        </div>

        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
            <Clock size={16} /> LATEST INFERENCE LATENCY
          </div>
          <div style={{ marginTop: '0.5rem', fontSize: '1.4rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
            {latestExp?.greedy_latency_ms ? `${latestExp.greedy_latency_ms} ms` : '—'}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.3rem' }}>
            Beam Avg: {latestExp?.beam_latency_ms ? `${latestExp.beam_latency_ms} ms` : '—'}
          </p>
        </div>
      </div>

      {/* Main Comparative Overview */}
      <div className="grid-2" style={{ marginBottom: '2rem' }}>
        {/* Left: Quality Metric Comparison */}
        <div className="card">
          <div className="card-title">
            <span>Quality Comparison (Latest Benchmark)</span>
            <span className="badge badge-blue">Corpus-Level Scores</span>
          </div>

          {latestExp && chartData.length > 0 ? (
            <div>
              <div style={{ height: 260, width: '100%', marginTop: '1rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Greedy" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Beam Search" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.75rem', borderTop: '1px solid var(--border)', paddingTop: '0.5rem' }}>
                Evaluated on {latestExp.sample_count} parallel sentences from dataset: <strong>{latestExp.dataset_name}</strong>.
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
              <BarChart2 size={40} style={{ opacity: 0.4, marginBottom: '0.75rem' }} />
              <h4 style={{ fontWeight: 600, color: 'var(--text-main)' }}>No Benchmark Runs Yet</h4>
              <p style={{ fontSize: '0.85rem', maxWidth: 350, margin: '0.5rem auto' }}>
                Run an evaluation in the Benchmark Laboratory to generate authentic BLEU and chrF comparative charts.
              </p>
              <button 
                className="btn btn-primary" 
                style={{ marginTop: '1rem' }}
                onClick={() => setActivePage('benchmark')}
              >
                Go to Benchmark Laboratory <ArrowRight size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Right: Research Objectives & Quick Actions */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-title">
              <span>Core Research Investigations</span>
              <span className="badge badge-green">Tamil → English MT</span>
            </div>

            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.85rem', marginTop: '1rem' }}>
              <li style={{ display: 'flex', gap: '0.75rem', fontSize: '0.875rem' }}>
                <CheckCircle2 size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Decoding Search Algorithms:</strong> Compare 1-hypothesis Greedy generation vs multi-path Beam Search (widths 2, 4, 8).
                </div>
              </li>
              <li style={{ display: 'flex', gap: '0.75rem', fontSize: '0.875rem' }}>
                <CheckCircle2 size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Quality vs Speed Trade-off:</strong> Quantify whether modest BLEU/chrF gains justify a 2x-4x latency penalty on CPU.
                </div>
              </li>
              <li style={{ display: 'flex', gap: '0.75rem', fontSize: '0.875rem' }}>
                <CheckCircle2 size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>Deployment Economics:</strong> Model real-world electrical and cloud infrastructure costs per 1,000 translated sentences.
                </div>
              </li>
              <li style={{ display: 'flex', gap: '0.75rem', fontSize: '0.875rem' }}>
                <CheckCircle2 size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <strong>CPU-Constrained Scalability:</strong> Verify stability, peak RSS memory consumption, and deterministic inference.
                </div>
              </li>
            </ul>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
            <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => setActivePage('playground')}>
              Interactive Playground
            </button>
            <button className="btn btn-secondary" style={{ flex: 1 }} onClick={() => setActivePage('benchmark')}>
              Run New Benchmark
            </button>
          </div>
        </div>
      </div>

      {/* Recent Experiments Table */}
      <div className="card">
        <div className="card-title">
          <span>Recent Benchmark Experiments</span>
          <button className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }} onClick={() => setActivePage('history')}>
            View All ({experiments.length})
          </button>
        </div>

        {experiments.length > 0 ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Experiment ID</th>
                  <th>Dataset</th>
                  <th>Samples</th>
                  <th>Greedy BLEU</th>
                  <th>Beam BLEU</th>
                  <th>Greedy Latency</th>
                  <th>Beam Latency</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {experiments.slice(0, 5).map((exp) => (
                  <tr key={exp.id}>
                    <td><strong>#{exp.id}</strong></td>
                    <td>{exp.dataset_name}</td>
                    <td>{exp.sample_count}</td>
                    <td>{exp.greedy_bleu !== null ? `${exp.greedy_bleu}` : '—'}</td>
                    <td>{exp.beam_bleu !== null ? `${exp.beam_bleu}` : '—'}</td>
                    <td>{exp.greedy_latency_ms ? `${exp.greedy_latency_ms} ms` : '—'}</td>
                    <td>{exp.beam_latency_ms ? `${exp.beam_latency_ms} ms` : '—'}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(exp.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            No experiments recorded in SQLite yet. Go to the Benchmark Laboratory to run your first experiment.
          </div>
        )}
      </div>
    </div>
  );
}
