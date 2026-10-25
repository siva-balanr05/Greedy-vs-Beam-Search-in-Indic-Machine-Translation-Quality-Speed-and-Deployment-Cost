import React, { useState } from 'react';
import { 
  Languages, Play, GitCompare, Zap, Clock, 
  Cpu, Award, Info, AlertCircle, RefreshCw 
} from 'lucide-react';
import { postTranslate, postCompare } from '../services/api';

const SAMPLE_SENTENCES = [
  {
    label: "Everyday Greeting",
    source: "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    reference: "Hello, how are you?"
  },
  {
    label: "AI & Technology",
    source: "செயற்கை நுண்ணறிவு இன்றைய உலகில் மிக வேகமாக வளர்ந்து வரும் ஒரு முக்கிய தொழில்நுட்பமாகும்.",
    reference: "Artificial intelligence is an important technology developing very rapidly in today's world."
  },
  {
    label: "Agriculture & Weather",
    source: "மழைக்காலத்தில் கிராமங்களில் விவசாயிகள் பயிர் நடவு செய்யத் தொடங்குகிறார்கள்.",
    reference: "In the rainy season, farmers in villages begin to plant crops."
  },
  {
    label: "Literature & Culture",
    source: "பாரதியார் தமிழ் மொழியின் மேன்மையை போற்றி பல புரட்சிகர கவிதைகளை எழுதியுள்ளார்.",
    reference: "Bharathiyar wrote many revolutionary poems praising the greatness of the Tamil language."
  }
];

export default function Playground() {
  const [sourceLang, setSourceLang] = useState('ta');
  const [targetLang, setTargetLang] = useState('en');
  const [sourceText, setSourceText] = useState(SAMPLE_SENTENCES[0].source);
  const [referenceText, setReferenceText] = useState(SAMPLE_SENTENCES[0].reference);
  const [beamWidth, setBeamWidth] = useState(4);
  const [maxNewTokens, setMaxNewTokens] = useState(128);
  const [lengthPenalty, setLengthPenalty] = useState(1.0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Results
  const [comparisonResult, setComparisonResult] = useState(null);
  const [singleResult, setSingleResult] = useState(null);

  function handleSelectSample(sample) {
    setSourceText(sample.source);
    setReferenceText(sample.reference);
    setComparisonResult(null);
    setSingleResult(null);
  }

  async function handleTranslate(method) {
    if (!sourceText.trim()) return;
    setLoading(true);
    setError(null);
    setComparisonResult(null);

    try {
      const res = await postTranslate({
        source_text: sourceText,
        source_lang: sourceLang,
        target_lang: targetLang,
        decoding_method: method,
        beam_width: method === 'greedy' ? 1 : beamWidth,
        max_new_tokens: maxNewTokens,
        length_penalty: lengthPenalty,
        reference_text: referenceText.trim() ? referenceText : null
      });
      setSingleResult(res.result);
    } catch (err) {
      setError(err.message || 'Translation failed.');
    } finally {
      setLoading(false);
    }
  }

  async function handleCompare() {
    if (!sourceText.trim()) return;
    setLoading(true);
    setError(null);
    setSingleResult(null);

    try {
      const res = await postCompare({
        source_text: sourceText,
        source_lang: sourceLang,
        target_lang: targetLang,
        beam_width: beamWidth,
        max_new_tokens: maxNewTokens,
        length_penalty: lengthPenalty,
        reference_text: referenceText.trim() ? referenceText : null
      });
      setComparisonResult(res);
    } catch (err) {
      setError(err.message || 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <span className="brand-badge">Interactive Evaluation</span>
        <h1 className="page-title" style={{ marginTop: '0.4rem' }}>Translation Playground</h1>
        <p className="page-subtitle">
          Test individual sentences under Greedy Search vs Beam Search with real-time latency, throughput, and memory tracking.
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

      {/* Input Form Card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Languages size={18} color="var(--primary)" />
            <select 
              className="form-select" 
              style={{ width: 'auto' }}
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
            >
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="ml">Malayalam (മലയാളം)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
            </select>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <select 
              className="form-select" 
              style={{ width: 'auto' }}
              value={targetLang}
              disabled
            >
              <option value="en">English (en)</option>
            </select>
          </div>

          {/* Sample quick selectors */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Try Example:</span>
            {SAMPLE_SENTENCES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                onClick={() => handleSelectSample(s)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Source Text Input */}
        <div className="form-group">
          <label className="form-label">Source Text (Indic Input)</label>
          <textarea
            className="form-textarea"
            rows={3}
            placeholder="Enter Tamil sentence here..."
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
          />
        </div>

        {/* Reference Text (Optional) */}
        <div className="form-group">
          <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Ground Truth Reference Translation (Optional for BLEU / chrF scoring)</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Required for automated quality evaluation</span>
          </label>
          <input
            type="text"
            className="form-input"
            placeholder="Enter reference English translation..."
            value={referenceText}
            onChange={(e) => setReferenceText(e.target.value)}
          />
        </div>

        {/* Parameter Controls */}
        <div className="grid-3" style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
          <div>
            <label className="form-label">Beam Width (k)</label>
            <select 
              className="form-select"
              value={beamWidth}
              onChange={(e) => setBeamWidth(Number(e.target.value))}
            >
              <option value={2}>Width 2 (Fast exploration)</option>
              <option value={4}>Width 4 (Standard research baseline)</option>
              <option value={8}>Width 8 (Deep search / High compute)</option>
            </select>
          </div>

          <div>
            <label className="form-label">Max Generated Tokens: {maxNewTokens}</label>
            <input 
              type="range" 
              min={32} 
              max={256} 
              step={16}
              value={maxNewTokens}
              onChange={(e) => setMaxNewTokens(Number(e.target.value))}
              style={{ width: '100%', marginTop: '0.5rem' }}
            />
          </div>

          <div>
            <label className="form-label">Length Penalty: {lengthPenalty}</label>
            <input 
              type="range" 
              min={0.5} 
              max={2.0} 
              step={0.1}
              value={lengthPenalty}
              onChange={(e) => setLengthPenalty(Number(e.target.value))}
              style={{ width: '100%', marginTop: '0.5rem' }}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => handleTranslate('greedy')}
            disabled={loading || !sourceText.trim()}
          >
            <Play size={15} />
            Translate with Greedy Search
          </button>

          <button 
            className="btn btn-secondary" 
            onClick={() => handleTranslate('beam')}
            disabled={loading || !sourceText.trim()}
          >
            <Play size={15} />
            Translate with Beam Search (k={beamWidth})
          </button>

          <button 
            className="btn btn-primary" 
            onClick={handleCompare}
            disabled={loading || !sourceText.trim()}
          >
            <GitCompare size={15} />
            Compare Both (Side-by-Side)
          </button>
        </div>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <RefreshCw size={32} className="spin" style={{ color: 'var(--primary)', marginBottom: '1rem', animation: 'spin 1s linear infinite' }} />
          <h4 style={{ fontWeight: 600 }}>Executing Model Inference on CPU...</h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Measuring inference latency, memory allocations, and token generation speed.
          </p>
        </div>
      )}

      {/* Comparison Results (Side-by-Side) */}
      {comparisonResult && !loading && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Comparison Results</h3>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <span className={`badge ${comparisonResult.identical_output ? 'badge-amber' : 'badge-green'}`}>
                {comparisonResult.identical_output ? 'Identical Output' : 'Translations Diverged'}
              </span>
              <span className="badge badge-blue">
                Latency Ratio: {comparisonResult.latency_ratio}x slower in Beam
              </span>
            </div>
          </div>

          <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
            {/* Greedy Result Card */}
            <div className="card" style={{ borderLeft: '4px solid #3b82f6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontWeight: 700, color: '#2563eb', fontSize: '1.05rem' }}>
                  Greedy Search (num_beams=1)
                </span>
                <span className="badge badge-blue">Single Hypothesis</span>
              </div>

              <div style={{ 
                backgroundColor: 'var(--bg-subtle)', 
                padding: '1rem', 
                borderRadius: 'var(--radius-sm)', 
                fontSize: '1.05rem',
                minHeight: '80px',
                marginBottom: '1rem'
              }}>
                {comparisonResult.greedy.translation || '<Empty output>'}
              </div>

              <div className="grid-3" style={{ gap: '0.5rem' }}>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.greedy.latency_ms} ms</div>
                  <div className="metric-label">Latency</div>
                </div>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.greedy.tokens_per_second}</div>
                  <div className="metric-label">Tokens / Sec</div>
                </div>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.greedy.tokens_generated}</div>
                  <div className="metric-label">Tokens</div>
                </div>
              </div>

              {comparisonResult.greedy.sentence_bleu !== null && (
                <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Sentence BLEU: <strong>{comparisonResult.greedy.sentence_bleu}</strong></span>
                  <span>Sentence chrF: <strong>{comparisonResult.greedy.sentence_chrf}</strong></span>
                </div>
              )}
            </div>

            {/* Beam Search Result Card */}
            <div className="card" style={{ borderLeft: '4px solid #8b5cf6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span style={{ fontWeight: 700, color: '#7c3aed', fontSize: '1.05rem' }}>
                  Beam Search (k={comparisonResult.beam.beam_width})
                </span>
                <span className="badge badge-green">Width {comparisonResult.beam.beam_width}</span>
              </div>

              <div style={{ 
                backgroundColor: 'var(--bg-subtle)', 
                padding: '1rem', 
                borderRadius: 'var(--radius-sm)', 
                fontSize: '1.05rem',
                minHeight: '80px',
                marginBottom: '1rem'
              }}>
                {comparisonResult.beam.translation || '<Empty output>'}
              </div>

              <div className="grid-3" style={{ gap: '0.5rem' }}>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.beam.latency_ms} ms</div>
                  <div className="metric-label">Latency</div>
                </div>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.beam.tokens_per_second}</div>
                  <div className="metric-label">Tokens / Sec</div>
                </div>
                <div className="metric-box">
                  <div className="metric-value">{comparisonResult.beam.tokens_generated}</div>
                  <div className="metric-label">Tokens</div>
                </div>
              </div>

              {comparisonResult.beam.sentence_bleu !== null && (
                <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Sentence BLEU: <strong>{comparisonResult.beam.sentence_bleu}</strong></span>
                  <span>Sentence chrF: <strong>{comparisonResult.beam.sentence_chrf}</strong></span>
                </div>
              )}
            </div>
          </div>

          {/* Scientific Evaluation Callout */}
          <div style={{ 
            backgroundColor: 'var(--bg-card)', 
            border: '1px solid var(--border)', 
            padding: '1rem', 
            borderRadius: 'var(--radius-md)',
            fontSize: '0.85rem',
            color: 'var(--text-muted)',
            display: 'flex',
            gap: '0.75rem',
            alignItems: 'flex-start'
          }}>
            <Info size={18} color="var(--primary)" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <strong>Scientific Evaluation Note:</strong> Sentence-level BLEU scores on single sentences can suffer from zero higher-order n-gram matches. 
              Corpus-level SacreBLEU computed over a full parallel dataset in the <strong>Benchmark Laboratory</strong> is required for rigorous statistical evaluation.
            </div>
          </div>
        </div>
      )}

      {/* Single Result */}
      {singleResult && !loading && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>
              Translation Output ({singleResult.method.toUpperCase()} - Beam {singleResult.beam_width})
            </span>
            <span className="badge badge-blue">{singleResult.latency_ms} ms</span>
          </div>

          <div style={{ 
            backgroundColor: 'var(--bg-subtle)', 
            padding: '1.25rem', 
            borderRadius: 'var(--radius-sm)', 
            fontSize: '1.1rem',
            marginBottom: '1rem'
          }}>
            {singleResult.translation}
          </div>

          <div className="grid-4" style={{ gap: '0.75rem' }}>
            <div className="metric-box">
              <div className="metric-value">{singleResult.latency_ms} ms</div>
              <div className="metric-label">Inference Time</div>
            </div>
            <div className="metric-box">
              <div className="metric-value">{singleResult.tokens_generated}</div>
              <div className="metric-label">Tokens Generated</div>
            </div>
            <div className="metric-box">
              <div className="metric-value">{singleResult.tokens_per_second}</div>
              <div className="metric-label">Tokens / Sec</div>
            </div>
            <div className="metric-box">
              <div className="metric-value">{singleResult.process_memory_mb} MB</div>
              <div className="metric-label">Process Memory</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
