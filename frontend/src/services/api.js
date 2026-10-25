const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}

export async function fetchModelInfo() {
  const res = await fetch(`${API_BASE}/model/info`);
  if (!res.ok) throw new Error('Failed to fetch model info');
  return res.json();
}

export async function postLoadModel() {
  const res = await fetch(`${API_BASE}/model/load`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to pre-warm model');
  return res.json();
}

export async function postTranslate(payload) {
  const res = await fetch(`${API_BASE}/translate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Translation failed');
  }
  return res.json();
}

export async function postCompare(payload) {
  const res = await fetch(`${API_BASE}/translate/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Comparison failed');
  }
  return res.json();
}

export async function fetchDatasets() {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function postParseDataset(formData) {
  const res = await fetch(`${API_BASE}/datasets/parse`, {
    method: 'POST',
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to parse uploaded dataset');
  }
  return res.json();
}

export async function postStartBenchmark(payload) {
  const res = await fetch(`${API_BASE}/benchmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start benchmark');
  }
  return res.json();
}

export async function fetchBenchmarkStatus(jobId) {
  const res = await fetch(`${API_BASE}/benchmark/${jobId}`);
  if (!res.ok) throw new Error('Failed to fetch benchmark status');
  return res.json();
}

export async function postCancelBenchmark(jobId) {
  const res = await fetch(`${API_BASE}/benchmark/${jobId}/cancel`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to cancel benchmark');
  return res.json();
}

export async function fetchExperiments() {
  const res = await fetch(`${API_BASE}/experiments`);
  if (!res.ok) throw new Error('Failed to fetch experiments');
  return res.json();
}

export async function fetchExperimentDetail(id) {
  const res = await fetch(`${API_BASE}/experiments/${id}`);
  if (!res.ok) throw new Error('Failed to fetch experiment detail');
  return res.json();
}

export async function postCostEstimate(payload) {
  const res = await fetch(`${API_BASE}/cost/estimate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Cost estimation failed');
  }
  return res.json();
}
