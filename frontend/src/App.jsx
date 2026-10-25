import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, Play, FlaskConical, BarChart2, 
  Calculator, History as HistoryIcon, Cpu, Zap 
} from 'lucide-react';

import Dashboard from './pages/Dashboard';
import Playground from './pages/Playground';
import Benchmark from './pages/Benchmark';
import Visualizations from './pages/Visualizations';
import CostCalculator from './pages/CostCalculator';
import History from './pages/History';
import { fetchHealth } from './services/api';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  async function checkHealth() {
    try {
      const data = await fetchHealth();
      setSystemHealth(data);
    } catch (e) {
      // Backend not yet reachable or starting up
    }
  }

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <header className="navbar">
        <div className="nav-inner">
          <div className="nav-brand">
            <Zap size={22} color="var(--primary)" />
            <span>Indic MT Research Lab</span>
            <span className="brand-badge">B.Tech AI/ML</span>
          </div>

          <nav>
            <ul className="nav-links">
              <li>
                <button 
                  className={`nav-btn ${activePage === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setActivePage('dashboard')}
                >
                  <LayoutDashboard size={15} /> Dashboard
                </button>
              </li>
              <li>
                <button 
                  className={`nav-btn ${activePage === 'playground' ? 'active' : ''}`}
                  onClick={() => setActivePage('playground')}
                >
                  <Play size={15} /> Playground
                </button>
              </li>
              <li>
                <button 
                  className={`nav-btn ${activePage === 'benchmark' ? 'active' : ''}`}
                  onClick={() => setActivePage('benchmark')}
                >
                  <FlaskConical size={15} /> Benchmark Lab
                </button>
              </li>
              <li>
                <button 
                  className={`nav-btn ${activePage === 'visualizations' ? 'active' : ''}`}
                  onClick={() => setActivePage('visualizations')}
                >
                  <BarChart2 size={15} /> Results & Charts
                </button>
              </li>
              <li>
                <button 
                  className={`nav-btn ${activePage === 'cost' ? 'active' : ''}`}
                  onClick={() => setActivePage('cost')}
                >
                  <Calculator size={15} /> Cost Calculator
                </button>
              </li>
              <li>
                <button 
                  className={`nav-btn ${activePage === 'history' ? 'active' : ''}`}
                  onClick={() => setActivePage('history')}
                >
                  <HistoryIcon size={15} /> History
                </button>
              </li>
            </ul>
          </nav>

          {/* System Health Status */}
          <div className="system-status-indicator">
            <span className={`status-dot ${systemHealth?.model_loaded ? '' : 'idle'}`} />
            <span>
              {systemHealth?.model_loaded 
                ? `Ready (${systemHealth.device.toUpperCase()})` 
                : 'Model Standby'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Body */}
      <main className="main-content">
        {activePage === 'dashboard' && <Dashboard setActivePage={setActivePage} />}
        {activePage === 'playground' && <Playground />}
        {activePage === 'benchmark' && <Benchmark setActivePage={setActivePage} />}
        {activePage === 'visualizations' && <Visualizations setActivePage={setActivePage} />}
        {activePage === 'cost' && <CostCalculator />}
        {activePage === 'history' && <History />}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div>
          <strong>Final-Year B.Tech AI/ML Capstone Project:</strong> Greedy vs Beam Search in Indic Machine Translation — Quality, Speed and Deployment Cost
        </div>
        <div style={{ marginTop: '0.35rem', fontSize: '0.75rem', color: 'var(--text-light)' }}>
          Backend: FastAPI & PyTorch on CPU | Evaluation: SacreBLEU & chrF | Storage: SQLite3 | Frontend: React & Vite
        </div>
      </footer>
    </div>
  );
}
