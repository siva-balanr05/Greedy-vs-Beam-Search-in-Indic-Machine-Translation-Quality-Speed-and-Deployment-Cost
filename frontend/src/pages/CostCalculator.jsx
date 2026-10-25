import React, { useState, useEffect } from 'react';
import { 
  Calculator, DollarSign, Server, Zap, Cpu, 
  HelpCircle, Info, RefreshCw 
} from 'lucide-react';
import { postCostEstimate, fetchExperiments } from '../services/api';

export default function CostCalculator() {
  const [workload, setWorkload] = useState(10000);
  const [greedySps, setGreedySps] = useState(4.5);
  const [beamSps, setBeamSps] = useState(1.5);
  const [cloudCpuPrice, setCloudCpuPrice] = useState(0.085);
  const [cloudGpuPrice, setCloudGpuPrice] = useState(0.526);
  const [localWatts, setLocalWatts] = useState(65.0);
  const [kwhCost, setKwhCost] = useState(0.15);

  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Try to auto-populate throughput from latest recorded experiment
    loadMeasuredThroughput();
  }, []);

  async function loadMeasuredThroughput() {
    try {
      const exps = await fetchExperiments();
      if (exps.length > 0) {
        // If an experiment has greedy_latency_ms, approximate sent/sec = 1000 / latency
        const latest = exps[0];
        if (latest.greedy_latency_ms) {
          setGreedySps(Number((1000.0 / latest.greedy_latency_ms).toFixed(2)));
        }
        if (latest.beam_latency_ms) {
          setBeamSps(Number((1000.0 / latest.beam_latency_ms).toFixed(2)));
        }
      }
    } catch (e) {
      console.warn('Could not auto-populate throughput:', e);
    }
    // Calculate initial estimate
    recalculateEstimate();
  }

  async function recalculateEstimate() {
    setLoading(true);
    try {
      const res = await postCostEstimate({
        workload_sentences: workload,
        sentences_per_second_greedy: greedySps,
        sentences_per_second_beam: beamSps,
        cloud_cpu_hourly_cost: cloudCpuPrice,
        cloud_gpu_hourly_cost: cloudGpuPrice,
        local_power_watts: localWatts,
        local_kwh_cost: kwhCost
      });
      setEstimate(res);
    } catch (err) {
      console.error('Cost calculation error:', err);
    } finally {
      setLoading(false);
    }
  }

  // Trigger recalculation on input change
  function handleRecalculate(e) {
    e.preventDefault();
    recalculateEstimate();
  }

  return (
    <div>
      <div className="page-header">
        <span className="brand-badge">Economic Analysis</span>
        <h1 className="page-title" style={{ marginTop: '0.4rem' }}>Deployment Cost Calculator</h1>
        <p className="page-subtitle">
          Transparent compute cost modeling connecting measured inference throughput with real-world infrastructure pricing.
        </p>
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Input Parameters Card */}
        <div className="card">
          <div className="card-title">
            <span>Simulation Parameters</span>
            <Calculator size={18} color="var(--primary)" />
          </div>

          <form onSubmit={handleRecalculate}>
            <div className="form-group">
              <label className="form-label">Workload Volume (Sentences to Translate)</label>
              <input 
                type="number" 
                className="form-input" 
                min={100} 
                max={10000000} 
                step={1000}
                value={workload}
                onChange={(e) => setWorkload(Number(e.target.value))}
              />
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Greedy Speed (Sent / Sec)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  min="0.1"
                  className="form-input" 
                  value={greedySps}
                  onChange={(e) => setGreedySps(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Beam Search Speed (Sent / Sec)</label>
                <input 
                  type="number" 
                  step="0.1" 
                  min="0.1"
                  className="form-input" 
                  value={beamSps}
                  onChange={(e) => setBeamSps(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Cloud CPU Price ($ / hr)</label>
                <input 
                  type="number" 
                  step="0.005" 
                  className="form-input" 
                  value={cloudCpuPrice}
                  onChange={(e) => setCloudCpuPrice(Number(e.target.value))}
                />
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>e.g. AWS c6i.large (~$0.085/hr)</span>
              </div>

              <div className="form-group">
                <label className="form-label">Cloud GPU Price ($ / hr)</label>
                <input 
                  type="number" 
                  step="0.01" 
                  className="form-input" 
                  value={cloudGpuPrice}
                  onChange={(e) => setCloudGpuPrice(Number(e.target.value))}
                />
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>e.g. AWS g4dn.xlarge (~$0.526/hr)</span>
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Local System Power (Watts)</label>
                <input 
                  type="number" 
                  step="5" 
                  className="form-input" 
                  value={localWatts}
                  onChange={(e) => setLocalWatts(Number(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Electricity Tariff ($ / kWh)</label>
                <input 
                  type="number" 
                  step="0.01" 
                  className="form-input" 
                  value={kwhCost}
                  onChange={(e) => setKwhCost(Number(e.target.value))}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
              <RefreshCw size={15} /> Recalculate Projections
            </button>
          </form>
        </div>

        {/* Methodology & Boundary Conditions */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="card-title">
              <span>Scientific Cost Methodology</span>
              <Info size={18} color="var(--primary)" />
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
              <p style={{ marginBottom: '0.75rem' }}>
                <strong>Throughput-Based Billing:</strong> For a given workload of $N$ sentences and measured throughput $R$ sentences/second:
              </p>
              <div style={{ 
                backgroundColor: 'var(--bg-subtle)', 
                fontFamily: 'var(--font-mono)', 
                padding: '0.75rem', 
                borderRadius: 'var(--radius-sm)', 
                marginBottom: '1rem',
                fontSize: '0.8rem',
                color: 'var(--text-main)'
              }}>
                t_seconds = N / R <br />
                compute_cost = (t_seconds / 3600) × hourly_rate
              </div>
              <p style={{ marginBottom: '0.75rem' }}>
                <strong>Local Hardware:</strong> Local CPU execution is not free; active electricity consumption is modeled as:
                <br />
                <code>Cost = (Watts / 1000) × (t / 3600) × Tariff</code>
              </p>
              <p>
                <strong>Beam Search Scaling:</strong> Maintaining $k$ candidate hypotheses increases floating point operations approximately linearly, resulting in higher latency and proportional deployment cost.
              </p>
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--primary-light)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: 'var(--primary)', marginTop: '1rem' }}>
            <strong>Note:</strong> GPU throughput estimates include a 3.5x batching acceleration factor based on Tensor Core parallelism.
          </div>
        </div>
      </div>

      {/* Comparison Tables: Cost per 1,000 sentences & Total Workload */}
      {estimate && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="card-title">
            <span>Estimated Cost Comparison ({workload.toLocaleString()} Sentences)</span>
            <span className="badge badge-green">Traceable Model</span>
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Deployment Environment</th>
                  <th>Greedy Time</th>
                  <th>Beam Time</th>
                  <th>Greedy (Cost / 1K Sentences)</th>
                  <th>Beam (Cost / 1K Sentences)</th>
                  <th>Total Workload (Greedy)</th>
                  <th>Total Workload (Beam)</th>
                  <th>Beam Cost Penalty</th>
                </tr>
              </thead>
              <tbody>
                {/* Local CPU */}
                <tr>
                  <td>
                    <strong>Local CPU (Power Electricity)</strong>
                  </td>
                  <td>{(estimate.local_cpu_greedy.inference_seconds / 60).toFixed(1)} min</td>
                  <td>{(estimate.local_cpu_beam.inference_seconds / 60).toFixed(1)} min</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.local_cpu_greedy.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.local_cpu_beam.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>${estimate.local_cpu_greedy.total_workload_cost.toFixed(4)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--danger)' }}>${estimate.local_cpu_beam.total_workload_cost.toFixed(4)}</td>
                  <td>
                    <span className="badge badge-amber">
                      +{(estimate.local_cpu_beam.total_workload_cost / Math.max(estimate.local_cpu_greedy.total_workload_cost, 0.0001)).toFixed(1)}x
                    </span>
                  </td>
                </tr>

                {/* Cloud CPU */}
                <tr>
                  <td>
                    <strong>Cloud CPU (AWS c6i.large)</strong>
                  </td>
                  <td>{(estimate.cloud_cpu_greedy.inference_seconds / 60).toFixed(1)} min</td>
                  <td>{(estimate.cloud_cpu_beam.inference_seconds / 60).toFixed(1)} min</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.cloud_cpu_greedy.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.cloud_cpu_beam.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>${estimate.cloud_cpu_greedy.total_workload_cost.toFixed(4)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--danger)' }}>${estimate.cloud_cpu_beam.total_workload_cost.toFixed(4)}</td>
                  <td>
                    <span className="badge badge-amber">
                      +{(estimate.cloud_cpu_beam.total_workload_cost / Math.max(estimate.cloud_cpu_greedy.total_workload_cost, 0.0001)).toFixed(1)}x
                    </span>
                  </td>
                </tr>

                {/* Cloud GPU */}
                <tr>
                  <td>
                    <strong>Cloud GPU (AWS g4dn.xlarge)</strong>
                  </td>
                  <td>{(estimate.cloud_gpu_greedy.inference_seconds / 60).toFixed(1)} min</td>
                  <td>{(estimate.cloud_gpu_beam.inference_seconds / 60).toFixed(1)} min</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.cloud_gpu_greedy.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>${estimate.cloud_gpu_beam.cost_per_1000_sentences.toFixed(5)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>${estimate.cloud_gpu_greedy.total_workload_cost.toFixed(4)}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--danger)' }}>${estimate.cloud_gpu_beam.total_workload_cost.toFixed(4)}</td>
                  <td>
                    <span className="badge badge-amber">
                      +{(estimate.cloud_gpu_beam.total_workload_cost / Math.max(estimate.cloud_gpu_greedy.total_workload_cost, 0.0001)).toFixed(1)}x
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="grid-3" style={{ marginTop: '1.5rem', gap: '1rem' }}>
            <div className="metric-box">
              <div className="metric-value">${estimate.cloud_cpu_greedy.cost_per_1000_sentences.toFixed(4)}</div>
              <div className="metric-label">Cloud CPU Cost / 1K Sentences (Greedy)</div>
            </div>

            <div className="metric-box">
              <div className="metric-value">${estimate.cloud_cpu_beam.cost_per_1000_sentences.toFixed(4)}</div>
              <div className="metric-label">Cloud CPU Cost / 1K Sentences (Beam)</div>
            </div>

            <div className="metric-box">
              <div className="metric-value">${estimate.cloud_cpu_greedy.monthly_continuous_cost.toFixed(2)} / mo</div>
              <div className="metric-label">Cloud Instance Standing Charge (730 hrs)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
