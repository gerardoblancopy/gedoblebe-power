'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePowerSystemStore } from '@/lib/store';
import {
  runOPF,
  loadCase,
  getExampleCase9,
  loadMatpowerCase,
  getMatpowerExample,
  exportCSV,
  exportJSON,
  downloadBlob,
  getAvailableCases,
  loadServerCase,
} from '@/lib/api';
import NetworkCanvas from '@/components/NetworkCanvas';
import BusEditor from '@/components/BusEditor';
import GeneratorEditor from '@/components/GeneratorEditor';
import LineEditor from '@/components/LineEditor';

export default function HomePage() {
  const pathname = usePathname();
  const [view, setView] = useState<'editor' | 'import' | 'server-cases'>('editor');
  const [serverCases, setServerCases] = useState<string[]>([]);
  const [selectedServerCase, setSelectedServerCase] = useState<string | null>(null);
  const [matpowerText, setMatpowerText] = useState('');
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState(false);
  const [enforceLineLimits, setEnforceLineLimits] = useState(true);
  const [voll, setVoll] = useState(10000);
  const [autoRun, setAutoRun] = useState(false);
  const [dataStale, setDataStale] = useState(false);
  const autoRunTimer = useRef<NodeJS.Timeout | null>(null);
  const hasRanOnce = useRef(false);

  const {
    buses,
    generators,
    lines,
    loads,
    baseMVA,
    results,
    isSolving,
    error,
    setSystem,
    setResults,
    setIsSolving,
    setError,
    clearSystem,
    selectedBus,
    selectedGenerator,
    selectedLine,
    setSelectedBus,
  } = usePowerSystemStore();

  const handleLoadExample = async () => {
    try {
      setIsSolving(true);
      setError(null);
      const exampleCase = await getExampleCase9();
      setSystem(exampleCase);
    } catch (err) {
      setError('Failed to load example case');
    } finally {
      setIsSolving(false);
    }
  };

  const handleRunOPF = useCallback(async () => {
    if (buses.length === 0 || generators.length === 0 || lines.length === 0) {
      setError('Please add buses, generators, and lines before running OPF');
      return;
    }

    try {
      setIsSolving(true);
      setError(null);

      const system = {
        buses,
        generators,
        lines,
        loads,
        base_mva: baseMVA,
      };

      const result = await runOPF(system, enforceLineLimits, voll);
      setResults(result);
      setDataStale(false);
      hasRanOnce.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run OPF');
    } finally {
      setIsSolving(false);
    }
  }, [buses, generators, lines, loads, baseMVA, enforceLineLimits, voll, setIsSolving, setError, setResults]);

  // Mark results as stale when data changes after a run
  useEffect(() => {
    if (hasRanOnce.current) {
      setDataStale(true);
    }
  }, [buses, generators, lines, loads, baseMVA, enforceLineLimits, voll]);

  // Auto-rerun OPF with debounce when autoRun is enabled
  useEffect(() => {
    if (!autoRun) return;
    if (buses.length === 0 || generators.length === 0 || lines.length === 0) return;

    if (autoRunTimer.current) clearTimeout(autoRunTimer.current);
    autoRunTimer.current = setTimeout(() => {
      handleRunOPF();
    }, 600);

    return () => {
      if (autoRunTimer.current) clearTimeout(autoRunTimer.current);
    };
  }, [autoRun, buses, generators, lines, loads, baseMVA, enforceLineLimits, voll, handleRunOPF]);

  const handleImportMATPOWER = async () => {
    if (!matpowerText.trim()) {
      setImportError('Please paste MATPOWER case data');
      return;
    }

    try {
      setImportError(null);
      setImportSuccess(false);
      const parsed = await loadMatpowerCase(matpowerText);
      setSystem({
        buses: parsed.buses,
        generators: parsed.generators,
        lines: parsed.lines,
        loads: parsed.loads,
        base_mva: parsed.base_mva,
      });
      setImportSuccess(true);
      setView('editor');
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to parse MATPOWER case');
    }
  };

  const handleLoadMatpowerExample = async () => {
    try {
      const example = await getMatpowerExample();
      setMatpowerText(example);
    } catch (err) {
      setImportError('Failed to load MATPOWER example');
    }
  };

  const fetchServerCases = async () => {
    try {
      const files = await getAvailableCases();
      setServerCases(files);
    } catch (err) {
      console.error('Failed to fetch server cases', err);
    }
  };

  const handleLoadServerCase = async () => {
    if (!selectedServerCase) return;

    try {
      setIsSolving(true);
      setError(null);
      const system = await loadServerCase(selectedServerCase);
      setSystem(system);
      setView('editor');
    } catch (err) {
      setError(`Failed to load case: ${selectedServerCase}`);
    } finally {
      setIsSolving(false);
    }
  };

  useEffect(() => {
    if (view === 'server-cases') {
      fetchServerCases();
    }
  }, [view]);

  const handleExportCSV = async () => {
    if (!results) return;
    try {
      const blob = await exportCSV();
      downloadBlob(blob, 'opf_results.csv');
    } catch (err) {
      setError('Failed to export CSV');
    }
  };

  const handleExportJSON = async () => {
    if (!results) return;
    try {
      const blob = await exportJSON();
      downloadBlob(blob, 'opf_results.json');
    } catch (err) {
      setError('Failed to export JSON');
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Gedoblebe Power Simulator</h1>
        <nav className="header-nav">
          <Link href="/" className={`nav-btn ${pathname === '/' ? 'active' : ''}`}>
            Editor
          </Link>
          <Link href="/results" className={`nav-btn ${pathname === '/results' ? 'active' : ''}`}>
            Results
          </Link>
        </nav>
      </header>

      <main className="main-content">
        <div className="canvas-container">
          <div className="canvas-toolbar">
            <button
              className={`tool-btn ${view === 'editor' ? 'active' : ''}`}
              onClick={() => setView('editor')}
              title="Network Editor"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="5" cy="5" r="2" />
                <circle cx="19" cy="5" r="2" />
                <circle cx="12" cy="19" r="2" />
                <line x1="7" y1="5" x2="10" y2="5" />
                <line x1="14" y1="5" x2="17" y2="5" />
                <line x1="6" y1="7" x2="10" y2="17" />
              </svg>
            </button>
            <button
              className={`tool-btn ${view === 'import' ? 'active' : ''}`}
              onClick={() => setView('import')}
              title="Import MATPOWER"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </button>
            <button
              className={`tool-btn ${view === 'server-cases' ? 'active' : ''}`}
              onClick={() => setView('server-cases')}
              title="Load Server Case"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 15v4c0 1.1.9 2 2 2h14a2 2 0 0 0 2-2v-4M17 9l-5 5-5-5M12 12.8V2.5" />
              </svg>
            </button>
          </div>

          <div className="canvas-legend">
            <div className="legend-item">
              <span className="legend-dot bus-slack"></span>
              <span>Slack Bus</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot bus-pv"></span>
              <span>PV Bus</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot bus-pq"></span>
              <span>PQ Bus</span>
            </div>
          </div>

          {view === 'editor' ? (
            <NetworkCanvas />
          ) : view === 'import' ? (
            <div style={{ padding: '2rem' }}>
              <h2 style={{ marginBottom: '1rem' }}>Import MATPOWER Case</h2>
              <p style={{ marginBottom: '1rem', color: '#666' }}>
                Paste your MATPOWER format case file below to import the power system.
              </p>
              <textarea
                className="matpower-input"
                value={matpowerText}
                onChange={(e) => setMatpowerText(e.target.value)}
                placeholder="Paste MATPOWER case file here..."
              />
              <div className="btn-group">
                <button className="btn btn-secondary" onClick={handleLoadMatpowerExample}>
                  Load Example
                </button>
                <button className="btn btn-primary" onClick={handleImportMATPOWER}>
                  Import Case
                </button>
              </div>
              {importError && <div className="error-message">{importError}</div>}
              {importSuccess && <div className="success-message">Case imported successfully!</div>}
            </div>
          ) : (
            <div style={{ padding: '2rem' }}>
              <h2 style={{ marginBottom: '1rem' }}>Load Server Case</h2>
              <p style={{ marginBottom: '1rem', color: '#666' }}>
                Select a case file from the server to load.
              </p>

              <div className="element-list" style={{ maxHeight: '400px', overflowY: 'auto', marginBottom: '1rem', border: '1px solid #e5e7eb', borderRadius: '6px' }}>
                {serverCases.length === 0 ? (
                  <div style={{ padding: '1rem', textAlign: 'center', color: '#888' }}>
                    No cases found on server.
                  </div>
                ) : (
                  serverCases.map((file) => (
                    <div
                      key={file}
                      className={`element-item ${selectedServerCase === file ? 'selected' : ''}`}
                      onClick={() => setSelectedServerCase(file)}
                      style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center' }}
                    >
                      <span style={{ marginRight: '0.5rem' }}>
                        {file.endsWith('.m') ? '📄' : '📋'}
                      </span>
                      {file}
                    </div>
                  ))
                )}
              </div>

              <div className="btn-group">
                <button
                  className="btn btn-primary"
                  onClick={handleLoadServerCase}
                  disabled={!selectedServerCase}
                  style={{ opacity: !selectedServerCase ? 0.5 : 1 }}
                >
                  Load Selected Case
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="sidebar">
          <div className="panel">
            <div className="panel-header">
              <span className="panel-title">Actions</span>
            </div>
            <div className="btn-group">
              <button className="btn btn-secondary" onClick={handleLoadExample}>
                Load Example (IEEE 9)
              </button>
            </div>
            <div className="btn-group">
              <button
                className="btn btn-primary"
                onClick={handleRunOPF}
                disabled={isSolving || buses.length === 0}
                style={{ flex: 1 }}
              >
                {isSolving ? (
                  <><span className="loading-spinner" style={{ marginRight: '0.4rem' }} /> Running...</>
                ) : results && !dataStale ? (
                  '✅ OPF Solved'
                ) : results && dataStale ? (
                  '🔄 Re-run OPF'
                ) : (
                  '▶ Run DC OPF'
                )}
              </button>
              <button className="btn btn-secondary" onClick={clearSystem}>
                Clear
              </button>
            </div>

            {/* OPF Options */}
            <div className="panel" style={{ marginTop: '1rem', padding: '0.75rem' }}>
              <div style={{ marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.9rem' }}>OPF Options</div>

              {/* Auto-run toggle */}
              <label style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                marginBottom: '0.6rem', cursor: 'pointer',
                background: autoRun ? 'rgba(52,211,153,0.15)' : 'rgba(99,102,241,0.08)',
                padding: '0.4rem 0.6rem', borderRadius: '6px',
                border: `1px solid ${autoRun ? 'rgba(52,211,153,0.3)' : 'rgba(99,102,241,0.15)'}`,
                transition: 'all 0.2s',
              }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
                  {autoRun ? '⚡ Auto-run ON' : 'Auto-run'}
                </span>
                <div
                  onClick={(e) => { e.preventDefault(); setAutoRun(!autoRun); }}
                  style={{
                    width: '36px', height: '20px', borderRadius: '10px',
                    background: autoRun ? '#34d399' : '#4b5563',
                    position: 'relative', transition: 'background 0.2s', cursor: 'pointer',
                  }}
                >
                  <div style={{
                    width: '16px', height: '16px', borderRadius: '50%',
                    background: '#e8eaf0', position: 'absolute', top: '2px',
                    left: autoRun ? '18px' : '2px',
                    transition: 'left 0.2s', boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                  }} />
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={enforceLineLimits}
                  onChange={(e) => setEnforceLineLimits(e.target.checked)}
                  style={{ marginRight: '0.5rem' }}
                />
                Enforce line limits
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.85rem' }}>VOLL ($/MWh):</label>
                <input
                  type="number"
                  value={voll}
                  onChange={(e) => setVoll(Number(e.target.value))}
                  style={{ width: '80px', padding: '0.25rem' }}
                  min={0}
                />
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}
            {results && dataStale && !autoRun && (
              <div style={{
                background: 'rgba(251,191,36,0.1)', color: '#fbbf24', padding: '0.5rem 0.75rem',
                borderRadius: '6px', fontSize: '0.85rem', marginTop: '0.5rem',
                border: '1px solid rgba(251,191,36,0.2)',
              }}>
                ⚠️ Parameters changed. Click <strong>Re-run OPF</strong> or enable <strong>Auto-run</strong>.
              </div>
            )}
            {results && !dataStale && (
              <div className="success-message">
                OPF solved! Total cost: {results.total_cost.toFixed(2)} $/h
              </div>
            )}
          </div>

          {selectedBus !== null ? (
            <BusEditor busId={selectedBus} />
          ) : selectedGenerator !== null ? (
            <GeneratorEditor bus={selectedGenerator} />
          ) : selectedLine !== null ? (
            <LineEditor lineIndex={selectedLine} />
          ) : (
            <>
              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Buses ({buses.length})</span>
                </div>
                <div className="element-list">
                  {buses.map((bus) => (
                    <div
                      key={bus.id}
                      className={`element-item ${selectedBus === bus.id ? 'selected' : ''}`}
                      onClick={() => setSelectedBus(bus.id)}
                    >
                      <span className="element-id">{bus.name || `Bus ${bus.id}`}</span>
                      <span style={{ fontSize: '0.8rem', color: '#8891a8' }}>
                        {bus.name ? `#${bus.id} · ` : ''}{bus.type === 3 ? 'Slack' : bus.type === 2 ? 'PV' : 'PQ'}
                      </span>
                    </div>
                  ))}
                  {buses.length === 0 && (
                    <p style={{ color: '#8891a8', textAlign: 'center', padding: '1rem' }}>
                      No buses added
                    </p>
                  )}
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Generators ({generators.length})</span>
                </div>
                <div className="element-list">
                  {generators.map((gen) => {
                    const bus = buses.find(b => b.id === gen.bus);
                    const label = bus?.name || `Bus ${gen.bus}`;
                    return (
                      <div
                        key={gen.bus}
                        className={`element-item ${selectedGenerator === gen.bus ? 'selected' : ''}`}
                        onClick={() => usePowerSystemStore.getState().setSelectedGenerator(gen.bus)}
                      >
                        <span className="element-id">Gen @ {label}</span>
                        <span style={{ fontSize: '0.8rem', color: '#8891a8' }}>
                          {gen.cost[1].toFixed(0)} $/MWh
                        </span>
                      </div>
                    );
                  })}
                  {generators.length === 0 && (
                    <p style={{ color: '#8891a8', textAlign: 'center', padding: '1rem' }}>
                      No generators added
                    </p>
                  )}
                </div>
              </div>

              <div className="panel">
                <div className="panel-header">
                  <span className="panel-title">Lines ({lines.length})</span>
                </div>
                <div className="element-list">
                  {lines.map((line, idx) => {
                    const fromBus = buses.find(b => b.id === line.from_bus);
                    const toBus = buses.find(b => b.id === line.to_bus);
                    const fromLabel = fromBus?.name || `Bus ${line.from_bus}`;
                    const toLabel = toBus?.name || `Bus ${line.to_bus}`;
                    return (
                      <div
                        key={idx}
                        className={`element-item ${selectedLine === idx ? 'selected' : ''}`}
                        onClick={() => usePowerSystemStore.getState().setSelectedLine(idx)}
                      >
                        <span className="element-id">
                          {fromLabel} → {toLabel}
                        </span>
                        <span style={{ fontSize: '0.8rem', color: '#8891a8' }}>
                          x={line.x.toFixed(2)}
                        </span>
                      </div>
                    );
                  })}
                  {lines.length === 0 && (
                    <p style={{ color: '#8891a8', textAlign: 'center', padding: '1rem' }}>
                      No lines added
                    </p>
                  )}
                </div>
              </div>
            </>
          )}

          {results && (
            <div className="panel">
              <div className="panel-header">
                <span className="panel-title">Export Results</span>
              </div>
              <div className="export-buttons">
                <button className="btn btn-secondary" onClick={handleExportCSV}>
                  CSV
                </button>
                <button className="btn btn-secondary" onClick={handleExportJSON}>
                  JSON
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
