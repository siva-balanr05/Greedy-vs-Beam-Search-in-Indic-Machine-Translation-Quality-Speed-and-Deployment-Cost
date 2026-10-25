import React, { useState, useEffect } from 'react';
import { 
  History as HistoryIcon, Download, Eye, FileText, 
  CheckCircle2, X, ArrowUpDown, Filter, AlertCircle 
} from 'lucide-react';
import { fetchExperiments, fetchExperimentDetail } from '../services/api';

export default function History() {
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExpDetail, setSelectedExpDetail] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);

  useEffect(() => {
    loadExperimentsList();
  }, []);

  async function loadExperimentsList() {
    try {
      setLoading(true);
      const list = await fetchExperiments();
      setExperiments(list);
    } catch (err) {
      console.error('Failed to load experiments history:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleOpenDetail(id) {
    setModalLoading(true);
    setModalOpen(true);
    try {
      const detail = await fetchExperimentDetail(id);
      setSelectedExpDetail(detail);
    } catch (err) {
      alert('Failed to load details: ' + err.message);
    } finally {
      setModalLoading(false);
    }
  }

  function handleCloseModal() {
    setModalOpen(false);
    setSelectedExpDetail(null);
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span className="brand-badge">Audit & Persistence</span>
          <h1 className="page-title" style={{ marginTop: '0.4rem' }}>Experiment History</h1>
          <p className="page-subtitle">
            All executed translation benchmarks persisted in the local SQLite database with reproducible metadata and sentence-level traces.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading recorded experiment history from SQLite database...
        </div>
      ) : experiments.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <HistoryIcon size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
          <h4 style={{ fontWeight: 600, color: 'var(--text-main)' }}>No Saved Experiments</h4>
          <p style={{ fontSize: '0.85rem', maxWidth: 380, margin: '0.5rem auto' }}>
            Run a test in the Benchmark Laboratory to generate and save your first experimental run.
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="card-title">
            <span>Recorded Benchmark Trials ({experiments.length})</span>
            <span className="badge badge-blue">SQLite Persistent Store</span>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Experiment Name</th>
                  <th>Dataset</th>
                  <th>Samples</th>
                  <th>Greedy BLEU</th>
                  <th>Beam BLEU</th>
                  <th>Greedy Latency</th>
                  <th>Beam Latency</th>
                  <th>Recorded At</th>
                  <th style={{ textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.id}>
                    <td><strong>#{exp.id}</strong></td>
                    <td style={{ fontWeight: 600 }}>{exp.experiment_name}</td>
                    <td>{exp.dataset_name}</td>
                    <td>{exp.sample_count}</td>
                    <td style={{ color: 'var(--primary)', fontWeight: 600 }}>
                      {exp.greedy_bleu !== null ? exp.greedy_bleu : '—'}
                    </td>
                    <td style={{ color: 'var(--accent)', fontWeight: 600 }}>
                      {exp.beam_bleu !== null ? exp.beam_bleu : '—'}
                    </td>
                    <td>{exp.greedy_latency_ms ? `${exp.greedy_latency_ms} ms` : '—'}</td>
                    <td>{exp.beam_latency_ms ? `${exp.beam_latency_ms} ms` : '—'}</td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(exp.created_at).toLocaleString()}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', gap: '0.4rem' }}>
                        <button 
                          className="btn btn-secondary" 
                          style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                          title="Inspect parallel sentence translations"
                          onClick={() => handleOpenDetail(exp.id)}
                        >
                          <Eye size={13} /> View
                        </button>
                        <a 
                          href={`/api/experiments/${exp.id}/export?format=csv`}
                          className="btn btn-secondary"
                          style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}
                          title="Download CSV"
                          download
                        >
                          <Download size={13} /> CSV
                        </a>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Sentence-by-Sentence Parallel Translations */}
      {modalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(3px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)',
            width: '100%',
            maxWidth: '1050px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: 'var(--shadow-lg)',
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
                  Experiment Details #{selectedExpDetail?.summary?.id} — Sentence-by-Sentence Inspection
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Dataset: {selectedExpDetail?.summary?.dataset_name} | Language: {selectedExpDetail?.summary?.source_lang} → {selectedExpDetail?.summary?.target_lang}
                </p>
              </div>
              <button 
                onClick={handleCloseModal}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
              {modalLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>Loading sentence records...</div>
              ) : selectedExpDetail?.sentence_records ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {/* Group sentence records by sentence_index */}
                  {Array.from(new Set(selectedExpDetail.sentence_records.map(r => r.sentence_index))).map(idx => {
                    const group = selectedExpDetail.sentence_records.filter(r => r.sentence_index === idx);
                    const sourceText = group[0]?.source_text;
                    const refText = group[0]?.reference_text;

                    return (
                      <div key={idx} style={{ 
                        border: '1px solid var(--border)', 
                        borderRadius: 'var(--radius-sm)', 
                        padding: '1rem',
                        backgroundColor: 'var(--bg-subtle)'
                      }}>
                        <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                          <span style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Source #{idx + 1}: </span>
                          <span style={{ fontWeight: 500 }}>{sourceText}</span>
                        </div>
                        {refText && (
                          <div style={{ marginBottom: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            <span style={{ fontWeight: 600 }}>Reference: </span>
                            <em>{refText}</em>
                          </div>
                        )}

                        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${group.length}, 1fr)`, gap: '0.75rem' }}>
                          {group.map((item, gIdx) => (
                            <div key={gIdx} style={{ 
                              backgroundColor: 'var(--bg-card)', 
                              padding: '0.75rem', 
                              borderRadius: 'var(--radius-sm)', 
                              border: '1px solid var(--border)' 
                            }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.4rem' }}>
                                <span className={`badge ${item.method === 'greedy' ? 'badge-blue' : 'badge-green'}`}>
                                  {item.method.toUpperCase()} (k={item.beam_width})
                                </span>
                                <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                  {item.latency_ms} ms
                                </span>
                              </div>
                              <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{item.translation}</p>
                              {item.sentence_bleu !== null && (
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', paddingTop: '0.3rem' }}>
                                  BLEU: <strong>{item.sentence_bleu}</strong> | chrF: <strong>{item.sentence_chrf}</strong>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div>No sentence records found.</div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '1rem 1.5rem',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.5rem'
            }}>
              <a 
                href={`/api/experiments/${selectedExpDetail?.summary?.id}/export?format=csv`}
                className="btn btn-secondary"
                download
              >
                <Download size={14} /> Download CSV
              </a>
              <button className="btn btn-primary" onClick={handleCloseModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
